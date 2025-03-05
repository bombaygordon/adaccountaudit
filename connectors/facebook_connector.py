import logging
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from typing import Dict, List, Any
from datetime import datetime, timedelta

class FacebookConnector:
    """Connects to Facebook Ads API and fetches account data."""
    
    def __init__(self, access_token: str):
        """Initialize with Facebook access token."""
        self.access_token = access_token
        self.api = FacebookAdsApi.init(access_token=access_token)
        self.logger = logging.getLogger(__name__)

    def get_account_data(self, account_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Fetch comprehensive ad account data including all key metrics.
        
        Args:
            account_id: Facebook ad account ID
            days: Number of days of data to fetch (default: 30)
            
        Returns:
            Dictionary containing account data and metrics
        """
        try:
            self.logger.info(f"Fetching data for account {account_id}")
            
            # Initialize account
            account = AdAccount(f'act_{account_id}')
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            date_preset = f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
            
            # Define fields to fetch
            insight_fields = [
                'spend',
                'impressions',
                'clicks',
                'ctr',
                'cpc',
                'actions',
                'cost_per_action_type',
                'conversion_rate_ranking',
                'quality_ranking',
                'engagement_rate_ranking'
            ]
            
            # Fetch campaigns with insights
            campaigns = []
            for campaign in account.get_campaigns(fields=[
                'name',
                'objective',
                'status',
                'budget_remaining',
                'daily_budget',
                'lifetime_budget'
            ]):
                try:
                    # Get campaign insights
                    insights = campaign.get_insights(
                        fields=insight_fields,
                        params={
                            'time_range': {
                                'since': start_date.strftime('%Y-%m-%d'),
                                'until': end_date.strftime('%Y-%m-%d')
                            },
                            'level': 'campaign'
                        }
                    )
                    
                    if insights and len(insights) > 0:
                        insight = insights[0]
                        
                        # Extract conversion metrics from actions
                        conversions = 0
                        conversion_value = 0
                        if 'actions' in insight:
                            for action in insight['actions']:
                                if action['action_type'] in ['offsite_conversion', 'onsite_conversion']:
                                    conversions += int(action['value'])
                                    
                        # Calculate metrics
                        spend = float(insight.get('spend', 0))
                        clicks = int(insight.get('clicks', 0))
                        impressions = int(insight.get('impressions', 0))
                        
                        campaign_data = {
                            'id': campaign['id'],
                            'name': campaign['name'],
                            'objective': campaign['objective'],
                            'status': campaign['status'],
                            'budget_remaining': float(campaign.get('budget_remaining', 0)),
                            'daily_budget': float(campaign.get('daily_budget', 0)) if campaign.get('daily_budget') else None,
                            'lifetime_budget': float(campaign.get('lifetime_budget', 0)) if campaign.get('lifetime_budget') else None,
                            'spend': spend,
                            'impressions': impressions,
                            'clicks': clicks,
                            'ctr': float(insight.get('ctr', 0)) * 100,  # Convert to percentage
                            'cpc': float(insight.get('cpc', 0)) if clicks > 0 else 0,
                            'conversions': conversions,
                            'conversion_rate': (conversions / clicks * 100) if clicks > 0 else 0,
                            'cpa': spend / conversions if conversions > 0 else 0,
                            'quality_ranking': insight.get('quality_ranking'),
                            'conversion_ranking': insight.get('conversion_rate_ranking'),
                            'engagement_ranking': insight.get('engagement_rate_ranking')
                        }
                        campaigns.append(campaign_data)
                        
                except Exception as e:
                    self.logger.error(f"Error fetching insights for campaign {campaign['id']}: {str(e)}")
                    continue
            
            # Fetch ad sets
            ad_sets = []
            for ad_set in account.get_ad_sets(fields=[
                'name',
                'campaign_id',
                'targeting',
                'bid_amount',
                'budget_remaining',
                'daily_budget',
                'optimization_goal'
            ]):
                try:
                    # Get ad set insights
                    insights = ad_set.get_insights(
                        fields=insight_fields,
                        params={
                            'time_range': {
                                'since': start_date.strftime('%Y-%m-%d'),
                                'until': end_date.strftime('%Y-%m-%d')
                            },
                            'level': 'adset'
                        }
                    )
                    
                    if insights and len(insights) > 0:
                        insight = insights[0]
                        
                        # Calculate metrics similar to campaigns
                        conversions = 0
                        if 'actions' in insight:
                            for action in insight['actions']:
                                if action['action_type'] in ['offsite_conversion', 'onsite_conversion']:
                                    conversions += int(action['value'])
                        
                        spend = float(insight.get('spend', 0))
                        clicks = int(insight.get('clicks', 0))
                        impressions = int(insight.get('impressions', 0))
                        
                        ad_set_data = {
                            'id': ad_set['id'],
                            'name': ad_set['name'],
                            'campaign_id': ad_set['campaign_id'],
                            'optimization_goal': ad_set['optimization_goal'],
                            'targeting': ad_set['targeting'],
                            'bid_amount': float(ad_set.get('bid_amount', 0)),
                            'budget_remaining': float(ad_set.get('budget_remaining', 0)),
                            'daily_budget': float(ad_set.get('daily_budget', 0)) if ad_set.get('daily_budget') else None,
                            'spend': spend,
                            'impressions': impressions,
                            'clicks': clicks,
                            'ctr': float(insight.get('ctr', 0)) * 100,
                            'cpc': float(insight.get('cpc', 0)) if clicks > 0 else 0,
                            'conversions': conversions,
                            'conversion_rate': (conversions / clicks * 100) if clicks > 0 else 0,
                            'cpa': spend / conversions if conversions > 0 else 0
                        }
                        ad_sets.append(ad_set_data)
                        
                except Exception as e:
                    self.logger.error(f"Error fetching insights for ad set {ad_set['id']}: {str(e)}")
                    continue
            
            # Fetch ads
            ads = []
            for ad in account.get_ads(fields=[
                'name',
                'campaign_id',
                'adset_id',
                'creative',
                'status'
            ]):
                try:
                    # Get ad insights
                    insights = ad.get_insights(
                        fields=insight_fields,
                        params={
                            'time_range': {
                                'since': start_date.strftime('%Y-%m-%d'),
                                'until': end_date.strftime('%Y-%m-%d')
                            },
                            'level': 'ad'
                        }
                    )
                    
                    if insights and len(insights) > 0:
                        insight = insights[0]
                        
                        # Calculate metrics similar to campaigns and ad sets
                        conversions = 0
                        if 'actions' in insight:
                            for action in insight['actions']:
                                if action['action_type'] in ['offsite_conversion', 'onsite_conversion']:
                                    conversions += int(action['value'])
                        
                        spend = float(insight.get('spend', 0))
                        clicks = int(insight.get('clicks', 0))
                        impressions = int(insight.get('impressions', 0))
                        
                        ad_data = {
                            'id': ad['id'],
                            'name': ad['name'],
                            'campaign_id': ad['campaign_id'],
                            'adset_id': ad['adset_id'],
                            'status': ad['status'],
                            'creative': ad.get('creative'),
                            'spend': spend,
                            'impressions': impressions,
                            'clicks': clicks,
                            'ctr': float(insight.get('ctr', 0)) * 100,
                            'cpc': float(insight.get('cpc', 0)) if clicks > 0 else 0,
                            'conversions': conversions,
                            'conversion_rate': (conversions / clicks * 100) if clicks > 0 else 0,
                            'cpa': spend / conversions if conversions > 0 else 0,
                            'quality_ranking': insight.get('quality_ranking'),
                            'engagement_ranking': insight.get('engagement_rate_ranking')
                        }
                        ads.append(ad_data)
                        
                except Exception as e:
                    self.logger.error(f"Error fetching insights for ad {ad['id']}: {str(e)}")
                    continue
            
            return {
                'account_id': account_id,
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'campaigns': campaigns,
                'ad_sets': ad_sets,
                'ads': ads
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching account data: {str(e)}", exc_info=True)
            raise Exception(f"Failed to fetch Facebook account data: {str(e)}") 