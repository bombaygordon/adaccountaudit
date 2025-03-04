import logging
from datetime import datetime, timedelta
import json

# Import Facebook Business SDK
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.exceptions import FacebookRequestError

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdPlatformConnector:
    def __init__(self, credentials):
        """
        Initialize connections to ad platforms.
        
        Args:
            credentials (dict): API keys and tokens for each platform
        """
        self.credentials = credentials
        self.connections = {}
        
    def connect_facebook(self):
        """Establish connection to Facebook/Instagram Ads API using OAuth"""
        try:
            # Check if we have the access token
            if 'fb_access_token' not in self.credentials:
                logger.error("Missing Facebook access token")
                return False
            
            logger.info(f"Attempting to connect to Facebook with token: {self.credentials['fb_access_token'][:10]}...")
            
            # Initialize the Facebook Ads API with just the access token
            api = FacebookAdsApi.init(
                access_token=self.credentials['fb_access_token']
            )
            
            # Store the API connection
            self.connections['facebook'] = api
            logger.info("Connected to Facebook Ads API using OAuth")
            return True
            
        except FacebookRequestError as e:
            error_message = f"Facebook API error: {e.api_error_message()}"
            logger.error(error_message)
            return False
        except Exception as e:
            logger.error(f"Facebook connection error: {e}")
            return False
    
    def connect_tiktok(self):
        """Establish connection to TikTok Ads API"""
        try:
            # In a real implementation, you would use the TikTok API client library
            # For now, we'll just simulate a connection
            logger.info("Connected to TikTok Ads API")
            self.connections['tiktok'] = True
            return True
        except Exception as e:
            logger.error(f"TikTok connection error: {e}")
            return False
    
    def fetch_account_data(self, platform, account_id, days_lookback=30):
        """
        Fetch ad account performance data.
        
        Args:
            platform (str): 'facebook' or 'tiktok'
            account_id (str): Platform-specific account ID
            days_lookback (int): Number of days of historical data to retrieve
            
        Returns:
            dict: Raw account data including campaigns, ad sets, ads, and metrics
        """
        logger.info(f"Fetching {platform} data for account {account_id}, {days_lookback} days lookback")
        
        if platform not in self.connections:
            logger.error(f"Not connected to {platform}")
            raise ValueError(f"Not connected to {platform}")
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_lookback)
        
        if platform == 'facebook':
            try:
                logger.info(f"Attempting to fetch real Facebook data for account {account_id}")
                logger.info(f"Using access token starting with: {self.credentials['fb_access_token'][:15]}...")
                real_data = self._fetch_facebook_data(account_id, start_date, end_date)
                
                # Improved verification of real data
                has_real_data = (
                    real_data and 
                    'campaigns' in real_data and 
                    len(real_data['campaigns']) > 0 and
                    'insights' in real_data and 
                    len(real_data['insights']) > 0
                )
                
                if has_real_data:
                    logger.info(f"Successfully fetched real Facebook data: {len(real_data['campaigns'])} campaigns, {len(real_data['insights'])} insights")
                    return real_data
                else:
                    logger.warning("Real Facebook data fetch returned empty or incomplete results")
                    logger.warning(f"Data structure returned: {json.dumps(real_data, default=str)[:500]}...")
                    
                    # For debugging purposes, if we have partial data, let's return that instead of mock data
                    if real_data and ('campaigns' in real_data or 'insights' in real_data):
                        logger.info("Returning partial real data for debugging")
                        return real_data
                    
                    logger.warning("Falling back to mock data due to empty/missing data")
                    return self._get_mock_facebook_data(account_id, start_date, end_date)
            except Exception as e:
                logger.error(f"Error fetching Facebook data: {e}", exc_info=True)
                logger.warning(f"Error details: {str(e)}")
                logger.info("Falling back to mock data due to error")
                return self._get_mock_facebook_data(account_id, start_date, end_date)
        elif platform == 'tiktok':
            return self._get_mock_tiktok_data(account_id, start_date, end_date)
    
    def _fetch_facebook_data(self, account_id, start_date, end_date):
        """Fetch real data from Facebook Ads API"""
        try:
            # Format dates for Facebook API
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"Fetching Facebook data from {start_date_str} to {end_date_str}")
            logger.info(f"Account ID: {account_id}")
            
            # Initialize the Ad Account object
            account = AdAccount(f'act_{account_id}')
            
            # Fetch campaigns
            logger.info(f"Fetching campaigns for account {account_id}")
            campaigns = account.get_campaigns(fields=[
                'id',
                'name',
                'objective',
                'status',
                'daily_budget',
                'lifetime_budget',
                'start_time',
                'stop_time',
                'spend',
                'buying_type',
                'bid_strategy',
                'created_time',
                'updated_time'
            ])
            
            # Check if we got campaigns data
            if not campaigns:
                logger.warning("No campaigns found for this account")
            else:
                logger.info(f"Found {len(campaigns)} campaigns")
            
            # Fetch ad sets
            logger.info(f"Fetching ad sets for account {account_id}")
            ad_sets = account.get_ad_sets(fields=[
                'id',
                'name',
                'campaign_id',
                'status',
                'daily_budget',
                'lifetime_budget',
                'targeting',
                'bid_amount',
                'optimization_goal',
                'billing_event',
                'created_time',
                'updated_time'
            ])
            
            if not ad_sets:
                logger.warning("No ad sets found for this account")
            else:
                logger.info(f"Found {len(ad_sets)} ad sets")
            
            # Fetch ads
            logger.info(f"Fetching ads for account {account_id}")
            ads = account.get_ads(fields=[
                'id',
                'name',
                'adset_id',
                'campaign_id',
                'status',
                'creative',
                'created_time',
                'updated_time'
            ])
            
            if not ads:
                logger.warning("No ads found for this account")
            else:
                logger.info(f"Found {len(ads)} ads")
            
            # Fetch insights data
            logger.info(f"Fetching insights for account {account_id}")
            insights = account.get_insights(
                params={
                    'time_range': {
                        'since': start_date_str,
                        'until': end_date_str
                    },
                    'time_increment': 1,  # Daily breakdown
                    'level': 'ad',
                    'breakdowns': ['age', 'gender', 'device_platform']
                },
                fields=[
                    'date_start',
                    'campaign_id',
                    'campaign_name',
                    'adset_id',
                    'adset_name',
                    'ad_id',
                    'ad_name',
                    'impressions',
                    'clicks',
                    'spend',
                    'reach',
                    'frequency',
                    'cpc',
                    'cpm',
                    'ctr',
                    'unique_clicks',
                    'actions',
                    'action_values',
                    'cost_per_action_type',
                    'video_p25_watched_actions',
                    'video_p50_watched_actions',
                    'video_p75_watched_actions',
                    'video_p100_watched_actions'
                ]
            )
            
            if not insights:
                logger.warning("No insights data found for this account")
            else:
                logger.info(f"Found {len(insights)} insights records")
            
            # Log the counts of fetched objects for debugging
            logger.info(f"Fetched {len(campaigns)} campaigns, {len(ad_sets)} ad sets, {len(ads)} ads, {len(insights)} insights")
            
            # Process and convert to dictionaries for consistency
            campaigns_data = [campaign.export_all_data() for campaign in campaigns]
            ad_sets_data = [ad_set.export_all_data() for ad_set in ad_sets]
            ads_data = [ad.export_all_data() for ad in ads]
            insights_data = [insight.export_all_data() for insight in insights]
            
            # Log sample data for debugging
            if campaigns_data:
                logger.info(f"Sample campaign data: {json.dumps(campaigns_data[0], default=str)[:500]}")
            if insights_data:
                logger.info(f"Sample insight data: {json.dumps(insights_data[0], default=str)[:500]}")
            
            # Process insights data to extract purchase actions
            self._process_facebook_insights(insights_data)
            
            # Return the structured data
            result = {
                'campaigns': campaigns_data,
                'ad_sets': ad_sets_data,
                'ads': ads_data,
                'insights': insights_data
            }
            
            logger.info(f"Returning real Facebook data with {len(campaigns_data)} campaigns, {len(insights_data)} insights")
            return result
            
        except FacebookRequestError as e:
            error_message = f"Facebook API error while fetching data: {e.api_error_message()}"
            logger.error(error_message)
            logger.error(f"Error details: Request: {e.request_context}, Code: {e.api_error_code()}")
            raise
            
        except Exception as e:
            logger.error(f"Error fetching Facebook data: {e}", exc_info=True)
            raise
    
    def _process_facebook_insights(self, insights_data):
        """Process Facebook insights to extract actions and make data more usable"""
        if not insights_data:
            logger.warning("No insights data to process")
            return
            
        logger.info(f"Processing {len(insights_data)} Facebook insights records")
        
        processed_count = 0
        for insight in insights_data:
            # Convert date string to a more standard format
            if 'date_start' in insight:
                insight['date'] = insight['date_start']
            
            # Extract purchase actions
            if 'actions' in insight and isinstance(insight['actions'], list):
                # Extract purchase conversions
                purchases = next((
                    action.get('value', 0) 
                    for action in insight['actions'] 
                    if action.get('action_type') == 'purchase'
                ), 0)
                
                insight['purchases'] = float(purchases) if purchases else 0
                
                # Extract other important actions
                for action_type in ['link_click', 'page_engagement', 'video_view']:
                    value = next((
                        action.get('value', 0) 
                        for action in insight['actions'] 
                        if action.get('action_type') == action_type
                    ), 0)
                    
                    insight[f'{action_type}s'] = float(value) if value else 0
            
            # Extract action values (revenue)
            if 'action_values' in insight and isinstance(insight['action_values'], list):
                purchase_value = next((
                    action.get('value', 0) 
                    for action in insight['action_values'] 
                    if action.get('action_type') == 'purchase'
                ), 0)
                
                insight['revenue'] = float(purchase_value) if purchase_value else 0
            
            # Clean up data types
            for field in ['impressions', 'clicks', 'spend', 'reach']:
                if field in insight:
                    insight[field] = float(insight[field]) if insight[field] else 0
            
            processed_count += 1
        
        logger.info(f"Processed {processed_count} insights records")
    
    def _get_mock_facebook_data(self, account_id, start_date, end_date):
        """Generate mock Facebook ad data for development"""
        logger.warning(f"Using mock data for Facebook account {account_id}")
        return {
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
    
    def _get_mock_tiktok_data(self, account_id, start_date, end_date):
        """Generate mock TikTok ad data for development"""
        return {
            'campaigns': [
                {
                    'id': '6745891234',
                    'name': 'TikTok Product Launch',
                    'objective': 'CONVERSIONS',
                    'status': 'ACTIVE',
                    'budget': 40.00,
                    'spend': 950.00
                }
            ],
            'ad_groups': [
                {
                    'id': '7856234598',
                    'name': 'Teen Audience',
                    'campaign_id': '6745891234',
                    'status': 'ACTIVE',
                    'budget': 40.00
                }
            ],
            'ads': [
                {
                    'id': '8967452301',
                    'name': 'Dance Challenge',
                    'ad_group_id': '7856234598',
                    'status': 'ACTIVE'
                }
            ],
            'insights': [
                {
                    'campaign_id': '6745891234',
                    'campaign_name': 'TikTok Product Launch',
                    'ad_group_id': '7856234598',
                    'ad_group_name': 'Teen Audience',
                    'ad_id': '8967452301',
                    'ad_name': 'Dance Challenge',
                    'impressions': 70000,
                    'clicks': 3500,
                    'spend': 950.00,
                    'ctr': 5.0,
                    'frequency': 3.1,
                    'reach': 22500,
                    'date': '2023-02-15',
                    'conversions': 42
                }
            ]
        }