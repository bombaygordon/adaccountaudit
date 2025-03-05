import logging
from datetime import datetime, timedelta
import json
import time
import random

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

def retry_with_backoff(max_retries=3, base_delay=5, max_delay=60):
    """
    Decorator that implements exponential backoff for functions that might hit rate limits.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        base_delay (int): Base delay in seconds between retries
        max_delay (int): Maximum delay in seconds between retries
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except FacebookRequestError as e:
                    # Add more robust rate limit detection
                    if e.api_error_code() == 17 or "User request limit reached" in str(e) or "too many calls" in str(e).lower():
                        if retries == max_retries:
                            logger.warning(f"Rate limit reached and max retries ({max_retries}) exceeded")
                            raise
                        
                        # Implement exponential backoff with jitter
                        delay = min(base_delay * (2 ** retries) + random.uniform(0, 1), max_delay)
                        logger.info(f"Rate limit hit, retrying in {delay:.2f} seconds (attempt {retries+1}/{max_retries})")
                        time.sleep(delay)
                        retries += 1
                    else:
                        # Re-raise if it's not a rate limit error
                        raise
        return wrapper
    return decorator

class AdPlatformConnector:
    def __init__(self, credentials):
        """
        Initialize connections to ad platforms.
        
        Args:
            credentials (dict): API keys and tokens for each platform
        """
        self.credentials = credentials
        self.connections = {}
        
    def connect_facebook(self, account_id: str) -> bool:
        """Connect to Facebook Ads API."""
        try:
            # Remove 'act_' prefix if it exists
            clean_account_id = account_id.replace('act_', '')
            self.account_id = clean_account_id  # Store without 'act_' prefix
            
            # Check if we have the access token
            if 'fb_access_token' not in self.credentials:
                logger.error("Missing Facebook access token")
                return False
            
            logger.info(f"Attempting to connect to Facebook with token: {self.credentials['fb_access_token'][:10]}...")
            
            # Verify the token is valid before proceeding
            api = FacebookAdsApi.init(access_token=self.credentials['fb_access_token'])
            # Test the connection with a simple API call
            AdAccount(f'act_{clean_account_id}').api_get(fields=['name'])
            
            # Store the API connection
            self.connections['facebook'] = api
            logger.info("Connected to Facebook Ads API using OAuth")
            return True
            
        except FacebookRequestError as e:
            logger.error(f"Facebook API error: {e.api_error_message()}")
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
                # Add a small delay before making API calls to help avoid rate limits
                time.sleep(1)
                
                logger.info(f"Fetching real Facebook data for account {account_id}")
                logger.info(f"Using access token starting with: {self.credentials['fb_access_token'][:15]}...")
                return self._fetch_facebook_data(account_id, start_date, end_date)
            
            except Exception as e:
                logger.error(f"Error fetching Facebook data: {e}", exc_info=True)
                logger.error(f"Error details: {str(e)}")
                raise
        elif platform == 'tiktok':
            raise NotImplementedError("TikTok data fetching not yet implemented")
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    @retry_with_backoff(max_retries=3, base_delay=5, max_delay=60)
    def _fetch_campaigns(self, account):
        """Fetch minimal campaign data with retry logic"""
        logger.info(f"Fetching campaigns for account {account.get_id()[4:]}")
        return account.get_campaigns(fields=[
            'id',
            'name',
            'status',
            'spend'
        ])
    
    @retry_with_backoff(max_retries=3, base_delay=5, max_delay=60)
    def _fetch_insights(self, account, start_date_str, end_date_str):
        """Fetch only essential insights metrics with retry logic"""
        logger.info(f"Fetching insights for account {account.get_id()[4:]}")
        return account.get_insights(
            params={
                'time_range': {
                    'since': start_date_str,
                    'until': end_date_str
                },
                'level': 'campaign',  # Get campaign-level data to reduce volume
                'time_increment': 1  # Daily breakdown
            },
            fields=[
                'campaign_id',
                'campaign_name',
                'spend',
                'impressions',
                'clicks',
                'ctr',
                'cpc',
                'actions',       # Needed for conversions
                'cost_per_action_type'  # Needed for cost per conversion
            ]
        )
    
    @retry_with_backoff(max_retries=3, base_delay=10, max_delay=120)
    def _fetch_facebook_data(self, account_id, start_date, end_date):
        """Fetch Facebook data with retry logic"""
        try:
            # Format dates for Facebook API
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"Fetching Facebook data from {start_date_str} to {end_date_str}")
            logger.info(f"Account ID: {account_id}")
            
            # Initialize the Ad Account object - add act_ prefix here
            account = AdAccount(f'act_{account_id}')
            
            # Fetch campaigns with detailed logging
            logger.info("Fetching campaigns...")
            campaigns = self._fetch_campaigns(account)
            if not campaigns:
                logger.error("No campaigns found - this indicates an issue with permissions or the account")
                raise ValueError("No campaigns found in the account. Please check permissions and account status.")
            
            campaigns_data = [campaign.export_all_data() for campaign in campaigns]
            logger.info(f"Successfully fetched {len(campaigns_data)} campaigns")
            
            # Add delay between API calls
            time.sleep(2)
            
            # Fetch insights with detailed logging
            logger.info("Fetching campaign insights...")
            insights = self._fetch_insights(account, start_date_str, end_date_str)
            if not insights:
                logger.error("No insights data found - this indicates an issue with the date range or data availability")
                raise ValueError("No insights data found. Please check the date range and account activity.")
            
            insights_data = [insight.export_all_data() for insight in insights]
            logger.info(f"Successfully fetched {len(insights_data)} insights records")
            
            # Process insights
            self._process_facebook_insights(insights_data)
            
            # Return the real data
            result = {
                'campaigns': campaigns_data,
                'insights': insights_data
            }
            
            logger.info(f"Successfully fetched real Facebook data with {len(campaigns_data)} campaigns and {len(insights_data)} insights")
            return result
            
        except FacebookRequestError as e:
            error_message = f"Facebook API error: {e.api_error_message()}"
            logger.error(error_message)
            logger.error(f"Error details: Request: {e.request_context}, Code: {e.api_error_code()}")
            raise
            
        except Exception as e:
            logger.error(f"Error fetching Facebook data: {e}", exc_info=True)
            raise
    
    def _process_facebook_insights(self, insights_data):
        """Process Facebook insights to extract only the specific metrics needed"""
        if not insights_data:
            logger.warning("No insights data to process")
            return
            
        logger.info(f"Processing {len(insights_data)} Facebook insights records")
        
        processed_count = 0
        for insight in insights_data:
            # Convert date string to a more standard format
            if 'date_start' in insight:
                insight['date'] = insight['date_start']
            
            # Extract conversion data
            if 'actions' in insight and isinstance(insight['actions'], list):
                # Extract conversions (purchase or complete_registration)
                conversions = next((
                    action.get('value', 0) 
                    for action in insight['actions'] 
                    if action.get('action_type') == 'purchase' or action.get('action_type') == 'complete_registration'
                ), 0)
                
                insight['conversions'] = float(conversions) if conversions else 0
                
                # Extract link clicks
                link_clicks = next((
                    action.get('value', 0) 
                    for action in insight['actions'] 
                    if action.get('action_type') == 'link_click'
                ), 0)
                
                insight['link_clicks'] = float(link_clicks) if link_clicks else 0
                
                # Keep the actions field as it might be needed for more detailed analysis
            
            # Extract cost per conversion
            if 'cost_per_action_type' in insight and isinstance(insight['cost_per_action_type'], list):
                cpa = next((
                    action.get('value', 0) 
                    for action in insight['cost_per_action_type'] 
                    if action.get('action_type') == 'purchase' or action.get('action_type') == 'complete_registration'
                ), 0)
                
                insight['cost_per_conversion'] = float(cpa) if cpa else 0
            
            # Clean up data types for the fields we're keeping
            for field in ['impressions', 'clicks', 'spend']:
                if field in insight:
                    insight[field] = float(insight[field]) if insight[field] else 0
            
            processed_count += 1
        
        logger.info(f"Processed {processed_count} insights records")
    
    def _get_mock_facebook_data(self, account_id, start_date, end_date):
        """Generate mock Facebook ad data with only the fields we need"""
        logger.warning(f"Using mock data for Facebook account {account_id}")
        return {
            'campaigns': [
                {
                    'id': '23456789012',
                    'name': 'Summer Sale',
                    'status': 'ACTIVE',
                    'spend': 1200.00
                },
                {
                    'id': '23456789013',
                    'name': 'Brand Awareness',
                    'status': 'ACTIVE',
                    'spend': 800.00
                }
            ],
            'insights': [
                {
                    'campaign_id': '23456789012',
                    'campaign_name': 'Summer Sale',
                    'impressions': 50000,
                    'clicks': 2500,
                    'spend': 1200.00,
                    'ctr': 5.0,
                    'cpc': 0.48,
                    'date': '2023-02-15',
                    'conversions': 35,
                    'link_clicks': 2500,
                    'cost_per_conversion': 34.29
                },
                {
                    'campaign_id': '23456789013',
                    'campaign_name': 'Brand Awareness',
                    'impressions': 100000,
                    'clicks': 3000,
                    'spend': 800.00,
                    'ctr': 3.0,
                    'cpc': 0.27,
                    'date': '2023-02-15',
                    'conversions': 20,
                    'link_clicks': 3000,
                    'cost_per_conversion': 40.00
                }
            ]
        }
    
    def _get_mock_tiktok_data(self, account_id, start_date, end_date):
        """Generate mock TikTok ad data with only the fields we need"""
        return {
            'campaigns': [
                {
                    'id': '6745891234',
                    'name': 'TikTok Product Launch',
                    'status': 'ACTIVE',
                    'spend': 950.00
                }
            ],
            'insights': [
                {
                    'campaign_id': '6745891234',
                    'campaign_name': 'TikTok Product Launch',
                    'impressions': 70000,
                    'clicks': 3500,
                    'spend': 950.00,
                    'ctr': 5.0,
                    'cpc': 0.27,
                    'date': '2023-02-15',
                    'conversions': 42,
                    'link_clicks': 3500,
                    'cost_per_conversion': 22.62
                }
            ]
        }