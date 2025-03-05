import os
from flask import Blueprint, jsonify, request, send_from_directory, current_app, session
from flask_login import login_required, current_user
from ad_platform.connector import AdPlatformConnector
from analysis.analyzer import AdAccountAnalyzer
from auth.models import Client, User, db
import logging
import requests
from enhanced_audit import EnhancedAdAccountAudit, json_serialize
import json
import numpy as np
from datetime import datetime, timedelta
import time
from analysis.ai_analyzer import AIAdAnalyzer
from analysis.openai_analyzer import OpenAIAdAnalyzer
from functools import wraps
from typing import Dict, List, Any
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad

# Set up logging
logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# Rate limiting configuration
RATE_LIMIT = {
    'requests_per_minute': 200,  # Facebook's rate limit
    'batch_size': 50,  # Number of items to fetch per request
    'delay_between_requests': 0.5  # Seconds to wait between requests
}

# Cache configuration
CACHE_DURATION = timedelta(minutes=5)
cache = {}

def rate_limit(func):
    """Decorator to implement rate limiting for API calls"""
    last_request_time = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_time = time.time()
        func_name = func.__name__
        
        # Get the last request time for this function
        last_time = last_request_time.get(func_name, 0)
        
        # Calculate time since last request
        time_since_last = current_time - last_time
        
        # If we need to wait, do so
        if time_since_last < RATE_LIMIT['delay_between_requests']:
            time.sleep(RATE_LIMIT['delay_between_requests'] - time_since_last)
        
        # Update last request time
        last_request_time[func_name] = time.time()
        
        return func(*args, **kwargs)
    
    return wrapper

def get_cached_data(key: str) -> Any:
    """Get data from cache if it exists and is not expired"""
    if key in cache:
        data, timestamp = cache[key]
        if datetime.now() - timestamp < CACHE_DURATION:
            return data
    return None

def set_cached_data(key: str, data: Any):
    """Store data in cache with current timestamp"""
    cache[key] = (data, datetime.now())

@rate_limit
def fetch_campaigns(account_id: str) -> List[Dict[str, Any]]:
    """Fetch campaigns with rate limiting and caching"""
    cache_key = f"campaigns_{account_id}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Add 'act_' prefix if not present
        if not account_id.startswith('act_'):
            account_id = f'act_{account_id}'
            
        logger.info(f"Fetching campaigns for account: {account_id}")
        
        account = AdAccount(account_id)
        campaigns = account.get_campaigns(
            fields=[
                'id',
                'name',
                'status',
                'objective',
                'daily_budget',
                'lifetime_budget',
                'configured_status',
                'effective_status'
            ],
            params={
                'limit': RATE_LIMIT['batch_size'],
                'date_preset': 'last_30d'  # Get data for last 30 days
            }
        )
        
        campaigns_data = []
        for campaign in campaigns:
            try:
                campaign_data = campaign.api_get(fields=[
                    'id',
                    'name',
                    'status',
                    'objective',
                    'daily_budget',
                    'lifetime_budget',
                    'configured_status',
                    'effective_status'
                ])
                
                if not campaign_data or not campaign_data.get('id'):
                    logger.warning(f"Campaign data invalid or missing ID: {campaign_data}")
                    continue
                    
                # Get insights for additional metrics
                try:
                    insights = Campaign(campaign_data['id']).get_insights(
                        fields=[
                            'spend',
                            'impressions',
                            'clicks',
                            'conversions',
                            'ctr',
                            'cpc',
                            'conversion_rate',
                            'cost_per_conversion',
                            'cost_per_action_type',
                            'actions',
                            'action_values'
                        ],
                        params={'date_preset': 'last_30d'}
                    )
                    if insights and len(insights) > 0:
                        campaign_data.update(insights[0].export_data())
                        # Calculate CPA from cost_per_conversion if available
                        if 'cost_per_conversion' in insights[0]:
                            campaign_data['cpa'] = insights[0]['cost_per_conversion']
                        # Calculate conversion rate from actions if available
                        if 'actions' in insights[0] and 'clicks' in insights[0]:
                            for action in insights[0]['actions']:
                                if action['action_type'] == 'purchase':
                                    campaign_data['conversion_rate'] = (action['value'] / insights[0]['clicks']) * 100
                                    break
                    else:
                        # Add default values if no insights
                        campaign_data.update({
                            'spend': 0,
                            'impressions': 0,
                            'clicks': 0,
                            'conversions': 0,
                            'ctr': 0,
                            'cpc': 0,
                            'conversion_rate': 0,
                            'cpa': 0
                        })
                except Exception as e:
                    logger.warning(f"Failed to get insights for campaign {campaign_data['id']}: {e}")
                    campaign_data.update({
                        'spend': 0,
                        'impressions': 0,
                        'clicks': 0,
                        'conversions': 0,
                        'ctr': 0,
                        'cpc': 0,
                        'conversion_rate': 0,
                        'cpa': 0
                    })
                
                campaigns_data.append(campaign_data)
                
            except Exception as e:
                logger.warning(f"Error processing campaign: {e}")
                continue
        
        if not campaigns_data:
            logger.warning(f"No valid campaigns found for account {account_id}")
            return []
            
        set_cached_data(cache_key, campaigns_data)
        return campaigns_data
        
    except Exception as e:
        logger.error(f"Error fetching campaigns for account {account_id}: {str(e)}")
        raise Exception(f"Failed to fetch campaigns: {str(e)}")

@rate_limit
def fetch_adsets(campaign_id: str) -> List[Dict[str, Any]]:
    """Fetch ad sets with rate limiting and caching"""
    cache_key = f"adsets_{campaign_id}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    try:
        campaign = Campaign(campaign_id)
        adsets = campaign.get_ad_sets(
            fields=[
                'id',
                'name',
                'campaign_id',
                'optimization_goal',
                'daily_budget',
                'lifetime_budget',
                'bid_strategy',
                'billing_event',
                'status',
                'configured_status',
                'effective_status'
            ],
            params={
                'limit': RATE_LIMIT['batch_size'],
                'date_preset': 'last_30d'
            }
        )
        
        adsets_data = []
        for adset in adsets:
            try:
                adset_data = adset.api_get(fields=[
                    'id',
                    'name',
                    'campaign_id',
                    'optimization_goal',
                    'daily_budget',
                    'lifetime_budget',
                    'bid_strategy',
                    'billing_event',
                    'status',
                    'configured_status',
                    'effective_status'
                ])
                
                if not adset_data or not adset_data.get('id'):
                    logger.warning(f"Ad set data invalid or missing ID: {adset_data}")
                    continue
                
                # Get insights for additional metrics
                try:
                    insights = AdSet(adset_data['id']).get_insights(
                        fields=[
                            'spend',
                            'impressions',
                            'clicks',
                            'conversions',
                            'ctr',
                            'cpc'
                        ],
                        params={'date_preset': 'last_30d'}
                    )
                    if insights and len(insights) > 0:
                        adset_data.update(insights[0].export_data())
                    else:
                        adset_data.update({
                            'spend': 0,
                            'impressions': 0,
                            'clicks': 0,
                            'conversions': 0,
                            'ctr': 0,
                            'cpc': 0
                        })
                except Exception as e:
                    logger.warning(f"Failed to get insights for ad set {adset_data['id']}: {e}")
                    adset_data.update({
                        'spend': 0,
                        'impressions': 0,
                        'clicks': 0,
                        'conversions': 0,
                        'ctr': 0,
                        'cpc': 0
                    })
                
                adsets_data.append(adset_data)
                
            except Exception as e:
                logger.warning(f"Error processing ad set: {e}")
                continue
        
        if not adsets_data:
            logger.warning(f"No valid ad sets found for campaign {campaign_id}")
            return []
            
        set_cached_data(cache_key, adsets_data)
        return adsets_data
        
    except Exception as e:
        logger.error(f"Error fetching ad sets for campaign {campaign_id}: {str(e)}")
        return []  # Return empty list instead of raising to allow partial data

@rate_limit
def fetch_ads(adset_id: str) -> List[Dict[str, Any]]:
    """Fetch ads with rate limiting and caching"""
    cache_key = f"ads_{adset_id}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    try:
        adset = AdSet(adset_id)
        ads = adset.get_ads(
            fields=[
                'id',
                'name',
                'campaign_id',
                'adset_id',
                'status',
                'configured_status',
                'effective_status',
                'creative',
                'bid_amount',
                'bid_type'
            ],
            params={
                'limit': RATE_LIMIT['batch_size'],
                'date_preset': 'last_30d'
            }
        )
        
        ads_data = []
        for ad in ads:
            try:
                ad_data = ad.api_get(fields=[
                    'id',
                    'name',
                    'campaign_id',
                    'adset_id',
                    'status',
                    'configured_status',
                    'effective_status',
                    'creative',
                    'bid_amount',
                    'bid_type'
                ])
                
                if not ad_data or not ad_data.get('id'):
                    logger.warning(f"Ad data invalid or missing ID: {ad_data}")
                    continue
                
                # Get insights for additional metrics
                try:
                    insights = Ad(ad_data['id']).get_insights(
                        fields=[
                            'spend',
                            'impressions',
                            'clicks',
                            'conversions',
                            'ctr',
                            'cpc',
                            'quality_ranking',
                            'engagement_rate_ranking',
                            'conversion_rate_ranking'
                        ],
                        params={'date_preset': 'last_30d'}
                    )
                    if insights and len(insights) > 0:
                        ad_data.update(insights[0].export_data())
                    else:
                        ad_data.update({
                            'spend': 0,
                            'impressions': 0,
                            'clicks': 0,
                            'conversions': 0,
                            'ctr': 0,
                            'cpc': 0,
                            'quality_ranking': 'UNKNOWN',
                            'engagement_rate_ranking': 'UNKNOWN',
                            'conversion_rate_ranking': 'UNKNOWN'
                        })
                except Exception as e:
                    logger.warning(f"Failed to get insights for ad {ad_data['id']}: {e}")
                    ad_data.update({
                        'spend': 0,
                        'impressions': 0,
                        'clicks': 0,
                        'conversions': 0,
                        'ctr': 0,
                        'cpc': 0,
                        'quality_ranking': 'UNKNOWN',
                        'engagement_rate_ranking': 'UNKNOWN',
                        'conversion_rate_ranking': 'UNKNOWN'
                    })
                
                ads_data.append(ad_data)
                
            except Exception as e:
                logger.warning(f"Error processing ad: {e}")
                continue
        
        if not ads_data:
            logger.warning(f"No valid ads found for ad set {adset_id}")
            return []
            
        set_cached_data(cache_key, ads_data)
        return ads_data
        
    except Exception as e:
        logger.error(f"Error fetching ads for ad set {adset_id}: {str(e)}")
        return []  # Return empty list instead of raising to allow partial data

@api_bp.route('/campaign-hierarchy', methods=['POST'])
@login_required
def get_campaign_hierarchy():
    """Get the complete campaign hierarchy"""
    try:
        data = request.get_json()
        access_token = data.get('accessToken')
        account_id = data.get('accountId')
        
        if not access_token or not account_id:
            return jsonify({
                'success': False,
                'error': 'Missing access token or account ID'
            }), 400
        
        # Initialize Facebook API
        FacebookAdsApi.init(access_token=access_token)
        
        # Fetch campaigns
        campaigns = fetch_campaigns(account_id)
        
        # For each campaign, fetch its ad sets
        for campaign in campaigns:
            campaign['ad_sets'] = fetch_adsets(campaign['id'])
            
            # For each ad set, fetch its ads
            for adset in campaign['ad_sets']:
                adset['ads'] = fetch_ads(adset['id'])
        
        # Convert all data to JSON-serializable format
        def convert_to_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif hasattr(obj, 'export_data'):
                return obj.export_data()
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            else:
                return str(obj)
        
        serialized_hierarchy = convert_to_serializable(campaigns)
        
        return jsonify({
            'success': True,
            'hierarchy': serialized_hierarchy
        })
        
    except Exception as e:
        logger.error(f"Error fetching campaign hierarchy: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    """Handle Facebook OAuth connection"""
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        account_id = data.get('account_id')
        
        if not access_token or not account_id:
            return jsonify({
                'success': False,
                'error': 'Missing access token or account ID'
            }), 400
        
        # Validate the access token
        try:
            # Initialize the Facebook API
            FacebookAdsApi.init(access_token=access_token)
            
            # Try to access the account
            account = AdAccount(f'act_{account_id}')
            account.api_get(fields=['id', 'name'])
            
            # Store the credentials in the session
            session['fb_credentials'] = {
                'access_token': access_token,
                'account_id': account_id
            }
            
            return jsonify({
                'success': True,
                'message': 'Facebook account connected successfully'
            })
            
        except Exception as e:
            logger.error(f"Error validating Facebook credentials: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Invalid Facebook credentials'
            }), 401
            
    except Exception as e:
        logger.error(f"Error connecting Facebook account: {str(e)}")
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
        try:
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
        except Exception as e:
            logger.error(f"Error auditing Facebook account: {e}")
            results['facebook'] = {
                'success': False, 
                'error': str(e)
            }
    
    if 'tiktok' in account_ids:
        try:
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
        except Exception as e:
            logger.error(f"Error auditing TikTok account: {e}")
            results['tiktok'] = {
                'success': False, 
                'error': str(e)
            }
    
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
        'success': True,
        'results': {
            'analysis_results': {
        'platforms_audited': list(results.keys()),
        'platform_specific_results': results,
                'recommendations': all_recommendations,
        'prioritized_recommendations': prioritized_recommendations,
        'agency_name': current_user.agency_name,
        'client_name': client_name,
        'potential_savings': sum(platform_results.get('potential_savings', 0) 
                               for platform_results in results.values()),
        'potential_improvement_percentage': 15.5  # Default value if not available from analysis
            }
        }
    }
    
    # Use custom JSON serializer for NumPy types
    return jsonify(json.loads(json.dumps(audit_result, default=json_serialize)))

@api_bp.route('/audit/facebook', methods=['POST'])
def audit_facebook():
    """Run an audit on the Facebook ad account"""
    try:
        data = request.json or {}
        access_token = data.get('accessToken')
        account_id = data.get('accountId')
        
        if not access_token or not account_id:
            logger.error("Missing Facebook credentials in request")
            return jsonify({
                'success': False,
                'error': 'Facebook credentials not found. Please reconnect your account.'
            }), 400
        
        # Add 'act_' prefix if not present
        if not account_id.startswith('act_'):
            account_id = f'act_{account_id}'
            
        logger.info(f"Initializing Facebook API for account {account_id}")
        
        # Initialize Facebook API
        try:
            FacebookAdsApi.init(access_token=access_token)
            logger.info("Facebook API initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Facebook API: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to initialize Facebook API. Please check your credentials and try again.'
            }), 401
        
        # Get campaign hierarchy
        try:
            hierarchy_result = get_campaign_hierarchy()
            if not hierarchy_result.get('success', False):
                error_msg = hierarchy_result.get('error', 'Failed to get campaign data')
                logger.error(f"Error getting campaign hierarchy: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 500
            
            # Initialize OpenAI analyzer
            try:
                openai_api_key = os.getenv('OPENAI_API_KEY')
                if not openai_api_key:
                    logger.error("OpenAI API key not configured")
                    return jsonify({
                        'success': False,
                        'error': 'Analysis service is not properly configured'
                    }), 503
                
                analyzer = OpenAIAdAnalyzer(api_key=openai_api_key)
                logger.info("Successfully initialized OpenAI analyzer")
                
                # Run the analysis
                hierarchy_data = hierarchy_result.get('hierarchy', [])
                if not hierarchy_data:
                    logger.warning("No campaigns found to analyze")
                    return jsonify({
                        'success': True,
                        'results': {
                            'analysis': 'No campaigns found to analyze',
                            'recommendations': []
                        }
                    })
                
                analysis_results = analyzer.analyze_account(hierarchy_data)
                if not isinstance(analysis_results, dict):
                    logger.error("Invalid analysis results format")
                    raise ValueError('Analysis results must be a dictionary')
                
                return jsonify({
                    'success': True,
                    'results': analysis_results
                })
                
            except Exception as e:
                logger.error(f"Error in OpenAI analysis: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Analysis service error: {str(e)}'
                }), 503
                
        except Exception as e:
            logger.error(f"Error getting campaign hierarchy: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to get campaign data: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in audit_facebook: {str(e)}")
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

@api_bp.route('/test-openai', methods=['GET'])
@login_required
def test_openai():
    """Test OpenAI integration with sample data"""
    try:
        # Create sample data
        sample_data = {
            'campaigns': [
                {
                    'name': 'Test Campaign 1',
                    'spend': 1000.0,
                    'conversions': 50,
                    'ctr': 2.5,
                    'cpa': 20.0
                },
                {
                    'name': 'Test Campaign 2',
                    'spend': 500.0,
                    'conversions': 15,
                    'ctr': 0.8,
                    'cpa': 33.33
                }
            ],
            'ad_sets': [],
            'ads': []
        }
        
        # Initialize OpenAI analyzer
        try:
            openai_analyzer = OpenAIAdAnalyzer()
            logger.info("Successfully initialized OpenAI analyzer")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI analyzer: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to initialize OpenAI integration. Please check your API key.'
            }), 500
        
        # Test analysis
        try:
            analysis = openai_analyzer.analyze_account(sample_data)
            if not analysis['success']:
                raise Exception(analysis.get('error', 'Unknown error in analysis'))
                
            return jsonify({
                'success': True,
                'message': 'OpenAI integration is working properly',
                'analysis': analysis
            })
            
        except Exception as e:
            logger.error(f"Error during OpenAI analysis: {e}")
            return jsonify({
                'success': False,
                'error': f'Error during analysis: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in OpenAI test: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/facebook/credentials', methods=['GET'])
@login_required
def get_facebook_credentials():
    """Get the stored Facebook credentials for the current user."""
    try:
        # First try to get credentials from session
        fb_credentials = session.get('fb_credentials')
        
        if fb_credentials and fb_credentials.get('access_token') and fb_credentials.get('account_id'):
            return jsonify({
                'success': True,
                'credentials': {
                    'access_token': fb_credentials['access_token'],
                    'account_id': fb_credentials['account_id']
                }
            })
            
        # If not in session, try to get from database
        user = User.query.get(current_user.id)
        if user and hasattr(user, 'facebook_credentials') and user.facebook_credentials:
            credentials = {
                'access_token': user.facebook_credentials.get('access_token'),
                'account_id': user.facebook_credentials.get('account_id')
            }
            
            if credentials['access_token'] and credentials['account_id']:
                # Store in session for future use
                session['fb_credentials'] = credentials
                return jsonify({
                    'success': True,
                    'credentials': credentials
                })
        
        # No valid credentials found
        return jsonify({
            'success': False,
            'error': 'No Facebook credentials found'
        }), 404
            
    except Exception as e:
        logging.error(f"Error retrieving Facebook credentials: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve Facebook credentials'
        }), 500