import logging
from enhanced_audit import EnhancedAdAccountAudit

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_enhanced_audit')

def test_enhanced_audit():
    """Test the enhanced audit system with mock data"""
    logger.info("Starting enhanced audit test")
    
    # Create simple mock data directly
    mock_data = {
        'campaigns': [
            {
                'id': '23456789012',
                'name': 'Summer Sale',
                'objective': 'CONVERSIONS',
                'status': 'ACTIVE',
                'daily_budget': 50.00,
                'spend': 1200.00
            },
            {
                'id': '23456789013',
                'name': 'Brand Awareness',
                'objective': 'BRAND_AWARENESS',
                'status': 'ACTIVE',
                'daily_budget': 30.00,
                'spend': 800.00
            }
        ],
        'ad_sets': [
            {
                'id': '34567890123',
                'name': 'US Women 25-45',
                'campaign_id': '23456789012',
                'targeting': {'age_min': 25, 'age_max': 45, 'genders': [1]},
                'status': 'ACTIVE',
                'daily_budget': 25.00
            }
        ],
        'ads': [
            {
                'id': '45678901234',
                'name': 'Product Demo Video',
                'adset_id': '34567890123',
                'status': 'ACTIVE'
            }
        ],
        'insights': [
            {
                'campaign_id': '23456789012',
                'campaign_name': 'Summer Sale',
                'adset_id': '34567890123',
                'adset_name': 'US Women 25-45',
                'ad_id': '45678901234',
                'ad_name': 'Product Demo Video',
                'impressions': 50000,
                'clicks': 2500,
                'spend': 1200.00,
                'ctr': 5.0,
                'frequency': 2.4,
                'reach': 20000,
                'date': '2023-02-15',
                'age': '25-34',
                'gender': 'female',
                'device': 'mobile',
                'purchases': 35
            }
        ]
    }
    
    # Initialize enhanced audit
    try:
        enhanced_audit = EnhancedAdAccountAudit()
        
        # Run audit
        logger.info("Running enhanced audit")
        result = enhanced_audit.run_audit(
            mock_data,
            platform='facebook',
            client_name='Test Client',
            agency_name='Test Agency',
            generate_report=False  # Skip report generation for testing
        )
        
        # Print summary
        if result.get('success', False):
            logger.info("Audit completed successfully")
            analysis_results = result.get('analysis_results', {})
            logger.info(f"Potential savings: ${analysis_results.get('potential_savings', 0):.2f}")
            logger.info(f"Improvement percentage: {analysis_results.get('potential_improvement_percentage', 0):.1f}%")
            if 'recommendations' in analysis_results:
                logger.info(f"Recommendations: {len(analysis_results['recommendations'])}")
            logger.info(f"Report path: {result.get('report_path', 'None')}")
        else:
            logger.error(f"Audit failed: {result.get('error', 'Unknown error')}")
        
        return result
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    test_enhanced_audit()