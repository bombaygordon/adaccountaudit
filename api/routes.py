import os
from flask import Blueprint, jsonify, request, send_from_directory
from flask_login import login_required, current_user
from ad_platform.connector import AdPlatformConnector
from analysis.analyzer import AdAccountAnalyzer
from auth.models import Client
import logging
import requests
from enhanced_audit import EnhancedAdAccountAudit

# Set up logging
logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/connect', methods=['POST'])
@login_required
def connect():
    """Connect to ad platforms"""
    credentials = request.json or {}
    connector = AdPlatformConnector(credentials)
    
    # Try to connect to platforms
    fb_status = connector.connect_facebook()
    tiktok_status = connector.connect_tiktok()
    
    return jsonify({
        'success': fb_status or tiktok_status,
        'platforms': {
            'facebook': fb_status,
            'tiktok': tiktok_status
        }
    })

@api_bp.route('/connect/facebook', methods=['POST'])
@login_required
def connect_facebook():
    """Connect to Facebook Ads API"""
    data = request.json or {}
    
    # Validate required credentials
    required_fields = ['fb_app_id', 'fb_app_secret', 'fb_access_token']
    if not all(field in data for field in required_fields):
        return jsonify({
            'success': False,
            'error': 'Missing required credentials'
        }), 400
    
    try:
        # Create connector with provided credentials
        credentials = {
            'fb_app_id': data['fb_app_id'],
            'fb_app_secret': data['fb_app_secret'],
            'fb_access_token': data['fb_access_token']
        }
        
        connector = AdPlatformConnector(credentials)
        
        # Attempt to connect
        fb_connected = connector.connect_facebook()
        
        if fb_connected:
            # Store connection in database
            # In a production app, you would encrypt these credentials
            # and store them associated with the user
            
            # For now, let's just return success
            return jsonify({
                'success': True,
                'message': 'Successfully connected to Facebook Ads API'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to Facebook Ads API with provided credentials'
            }), 401
            
    except Exception as e:
        logger.error(f"Error connecting to Facebook: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/connect/facebook-oauth', methods=['POST'])
@login_required
def connect_facebook_oauth():
    """Connect to Facebook Ads API using OAuth"""
    data = request.json or {}
    
    # Check for required fields
    if 'access_token' not in data or 'account_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing access token or account ID'
        }), 400
    
    access_token = data['access_token']
    account_id = data['account_id']
    
    try:
        # Test the access token by making a simple API call
        # This will validate the token and permissions
        test_url = f"https://graph.facebook.com/v18.0/act_{account_id}/campaigns?fields=id,name&limit=1&access_token={access_token}"
        response = requests.get(test_url)
        
        if response.status_code != 200:
            error_data = response.json().get('error', {})
            return jsonify({
                'success': False,
                'error': error_data.get('message', 'Failed to validate access token')
            }), 401
        
        # Store the connection in the database
        # In a real implementation, you should store this securely
        # and associate it with the current user
        
        # For now, just return success
        return jsonify({
            'success': True,
            'account_id': account_id,
            'message': 'Successfully connected to Facebook Ads'
        })
        
    except Exception as e:
        logger.error(f"Error connecting to Facebook via OAuth: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/audit', methods=['POST'])
@login_required
def audit():
    """Run an audit on ad account data"""
    data = request.json or {}
    
    # Get credentials and account IDs
    credentials = data.get('credentials', {})
    account_ids = data.get('account_ids', {})
    days_lookback = data.get('days_lookback', 30)
    client_id = data.get('client_id')
    
    # Validate client if provided
    client_name = None
    if client_id:
        client = Client.query.get(client_id)
        if client and client.user_id == current_user.id:
            client_name = client.name
    
    # Connect to platforms
    connector = AdPlatformConnector(credentials)
    results = {}
    
    # Initialize enhanced audit
    enhanced_audit = EnhancedAdAccountAudit()
    
    # Audit each platform if account ID is provided
    if 'facebook' in account_ids:
        fb_connected = connector.connect_facebook()
        if fb_connected:
            fb_data = connector.fetch_account_data('facebook', account_ids['facebook'], days_lookback)
            fb_result = enhanced_audit.run_audit(
                fb_data,
                platform='facebook',
                client_name=client_name,
                agency_name=current_user.agency_name
            )
            results['facebook'] = fb_result.get('analysis_results', {})
    
    if 'tiktok' in account_ids:
        tiktok_connected = connector.connect_tiktok()
        if tiktok_connected:
            tiktok_data = connector.fetch_account_data('tiktok', account_ids['tiktok'], days_lookback)
            tiktok_result = enhanced_audit.run_audit(
                tiktok_data,
                platform='tiktok',
                client_name=client_name,
                agency_name=current_user.agency_name
            )
            results['tiktok'] = tiktok_result.get('analysis_results', {})
    
    # Combine recommendations from all platforms
    all_recommendations = []
    for platform, platform_results in results.items():
        platform_recommendations = platform_results.get('recommendations', [])
        # Add platform identifier to recommendations
        for rec in platform_recommendations:
            rec['platform'] = platform
        all_recommendations.extend(platform_recommendations)
    
    # Sort combined recommendations
    prioritized_recommendations = sorted(
        all_recommendations, 
        key=lambda x: x.get('priority_score', 0) if 'priority_score' in x else 0,
        reverse=True
    )[:15]  # Top 15 overall recommendations
    
    audit_result = {
        'platforms_audited': list(results.keys()),
        'platform_specific_results': results,
        'prioritized_recommendations': prioritized_recommendations,
        'success': len(results) > 0,
        'agency_name': current_user.agency_name,
        'client_name': client_name
    }
    
    return jsonify(audit_result)

@api_bp.route('/audit/facebook', methods=['POST'])
@login_required
def audit_facebook():
    """Run an audit on Facebook ad account data using OAuth token"""
    data = request.json or {}
    
    # Get account ID and access token
    access_token = data.get('access_token')
    account_id = data.get('account_id')
    days_lookback = data.get('days_lookback', 30)
    client_id = data.get('client_id')
    
    if not account_id or not access_token:
        return jsonify({
            'success': False,
            'error': 'Missing account ID or access token'
        }), 400
    
    # Validate client if provided
    client_name = None
    if client_id:
        client = Client.query.get(client_id)
        if client and client.user_id == current_user.id:
            client_name = client.name
    
    try:
        # Create credentials with the OAuth token
        credentials = {
            'fb_access_token': access_token
        }
        
        # Connect to Facebook
        connector = AdPlatformConnector(credentials)
        fb_connected = connector.connect_facebook()
        
        if not fb_connected:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to Facebook Ads API'
            }), 401
        
        # Fetch data
        fb_data = connector.fetch_account_data('facebook', account_id, days_lookback)
        
        # Run enhanced analysis instead of original analyzer
        enhanced_audit = EnhancedAdAccountAudit()
        
        audit_result = enhanced_audit.run_audit(
            fb_data,
            platform='facebook',
            client_name=client_name or "Facebook Ads Account",
            agency_name=current_user.agency_name
        )
        
        # Add client info
        if 'analysis_results' in audit_result:
            audit_result['analysis_results']['client_name'] = client_name
            audit_result['analysis_results']['agency_name'] = current_user.agency_name
        
        # Save audit results to database if client is specified
        if client_id:
            # Here you would save the audit to the database
            pass
        
        return jsonify({
            'success': True,
            'results': audit_result.get('analysis_results', audit_result)
        })
        
    except Exception as e:
        logger.error(f"Error running Facebook audit: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/test-audit', methods=['GET'])
def test_audit():
    """Run a test audit with mock data"""
    # Create connector with mock credentials
    credentials = {'test': 'test'}
    connector = AdPlatformConnector(credentials)
    connector.connect_facebook()
    
    # Get mock data
    mock_data = connector.fetch_account_data('facebook', '12345', days_lookback=30)
    
    # Initialize enhanced audit
    enhanced_audit = EnhancedAdAccountAudit()
    
    # Run enhanced audit
    audit_result = enhanced_audit.run_audit(
        mock_data,
        platform='facebook',
        client_name="Demo Client",
        agency_name="Your Agency" if not current_user.is_authenticated else current_user.agency_name
    )
    
    # Return the analysis results
    return jsonify(audit_result.get('analysis_results', {}))

@api_bp.route('/generate-report', methods=['POST'])
@login_required
def generate_report():
    """Generate a PDF report from audit results"""
    try:
        data = request.json or {}
        
        # Get client information
        client_id = data.get('client_id')
        
        if client_id:
            # Get client from database
            client = Client.query.get(client_id)
            
            # Verify client belongs to current user
            if not client or client.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'error': 'Invalid client selection'
                }), 403
                
            client_name = client.name
        else:
            # Use default or provided client name
            client_name = data.get('client_name', 'Client')
        
        # Use current user's agency name
        agency_name = current_user.agency_name
        
        # Check if we have cached results
        enhanced_audit = EnhancedAdAccountAudit()
        
        # Try to use cached results first
        cached_analysis = enhanced_audit.load_cached_analysis(client_name)
        
        if cached_analysis:
            # Generate report from cached analysis
            report_path = enhanced_audit.report_generator.generate_report(
                cached_analysis,
                client_name,
                agency_name
            )
        else:
            # For demonstration, we'll use test audit data
            credentials = {'test': 'test'}
            connector = AdPlatformConnector(credentials)
            connector.connect_facebook()
            
            # Get mock data
            mock_data = connector.fetch_account_data('facebook', '12345', days_lookback=30)
            
            # Run analysis
            audit_result = enhanced_audit.run_audit(
                mock_data,
                platform='facebook',
                client_name=client_name,
                agency_name=agency_name,
                generate_report=True
            )
            
            report_path = audit_result.get('report_path')
        
        # Get the filename from the path
        filename = os.path.basename(report_path) if report_path else None
        
        # Return the report details
        return jsonify({
            'success': True,
            'report_path': report_path,
            'download_url': f'/api/reports/{filename}' if filename else None,
            'message': 'Report generated successfully',
            'client_name': client_name
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/reports/<filename>', methods=['GET'])
@login_required
def get_report(filename):
    """Download a generated report"""
    reports_dir = os.path.join(os.getcwd(), 'reports')
    return send_from_directory(reports_dir, filename, as_attachment=True)

@api_bp.route('/clients', methods=['GET'])
@login_required
def get_clients():
    """Get list of clients for current user"""
    clients = Client.query.filter_by(user_id=current_user.id).all()
    
    client_list = [{
        'id': client.id,
        'name': client.name,
        'email': client.email
    } for client in clients]
    
    return jsonify({
        'success': True,
        'clients': client_list
    })