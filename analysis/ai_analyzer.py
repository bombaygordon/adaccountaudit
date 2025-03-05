import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from openai import OpenAI

class AIAdAnalyzer:
    """
    Analyzes Facebook ad account data using OpenAI to generate intelligent recommendations.
    """
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the analyzer with OpenAI API key."""
        self.openai_analyzer = OpenAIAdAnalyzer(api_key=openai_api_key)
        self.logger = logging.getLogger(__name__)

    def analyze_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for analyzing account data.
        Uses OpenAI to generate recommendations based on account performance.
        """
        try:
            self.logger.info("Starting account analysis")
            
            # Preprocess the data
            processed_data = self._preprocess_data(data)
            
            # Use OpenAI to analyze the data and generate recommendations
            analysis_results = self.openai_analyzer.analyze_account(processed_data)
            
            if not analysis_results.get('success'):
                self.logger.error("OpenAI analysis failed")
                return {
                    'success': False,
                    'error': analysis_results.get('error', 'Unknown error in OpenAI analysis')
                }
            
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'analysis_results': analysis_results['analysis_results']
            }
            
        except Exception as e:
            self.logger.error(f"Error in account analysis: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess raw account data for analysis.
        Converts data frames to lists of dictionaries and ensures consistent format.
        """
        processed = {}
        
        # Convert DataFrames to lists of dictionaries if needed
        for key in ['campaigns', 'ad_sets', 'ads', 'insights']:
            if key in data:
                if hasattr(data[key], 'to_dict'):
                    processed[key] = data[key].to_dict('records')
                else:
                    processed[key] = data[key]
        
        # If we have insights data, merge relevant metrics into campaigns
        if 'insights' in processed and 'campaigns' in processed:
            campaign_metrics = {}
            
            # Aggregate metrics by campaign
            for insight in processed['insights']:
                campaign_id = insight.get('campaign_id')
                if campaign_id:
                    if campaign_id not in campaign_metrics:
                        campaign_metrics[campaign_id] = {
                            'impressions': 0,
                            'clicks': 0,
                            'spend': 0.0,
                            'conversions': 0,
                            'cost_per_conversion': 0.0
                        }
                    
                    metrics = campaign_metrics[campaign_id]
                    metrics['impressions'] += insight.get('impressions', 0)
                    metrics['clicks'] += insight.get('clicks', 0)
                    metrics['spend'] += float(insight.get('spend', 0))
                    metrics['conversions'] += insight.get('conversions', 0)
                    
                    # Update cost per conversion
                    if metrics['conversions'] > 0:
                        metrics['cost_per_conversion'] = metrics['spend'] / metrics['conversions']
            
            # Merge metrics into campaigns
            for campaign in processed['campaigns']:
                campaign_id = campaign.get('id')
                if campaign_id in campaign_metrics:
                    campaign.update(campaign_metrics[campaign_id])
        
        return processed
    
    def _analyze_campaigns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze campaign performance and identify issues."""
        campaigns = data.get('campaigns', [])
        if not campaigns:
            return {}
        
        analysis = {
            'underperforming': [],
            'high_potential': [],
            'optimization_opportunities': []
        }
        
        # Convert to DataFrame if it's a list of dictionaries
        if isinstance(campaigns, list):
            campaigns_df = pd.DataFrame(campaigns)
        elif isinstance(campaigns, pd.DataFrame):
            campaigns_df = campaigns
        else:
            self.logger.warning("Campaigns data is not in a supported format")
            return analysis
        
        # Identify underperforming campaigns
        if 'ctr' in campaigns_df.columns:
            underperforming = campaigns_df[campaigns_df['ctr'] < self.performance_thresholds['ctr']]
            analysis['underperforming'] = underperforming.to_dict('records')
        
        # Identify high-potential campaigns
        if 'roas' in campaigns_df.columns:
            high_potential = campaigns_df[campaigns_df['roas'] > self.performance_thresholds['roas']]
            analysis['high_potential'] = high_potential.to_dict('records')
        
        return analysis
    
    def _analyze_audiences(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience performance and saturation."""
        ad_sets = data.get('ad_sets', [])
        if not ad_sets:
            return {}
            
        analysis = {
            'saturated_audiences': [],
            'best_performing_interests': [],
            'audience_size_issues': []
        }
        
        # Convert to DataFrame if it's a list of dictionaries
        if isinstance(ad_sets, list):
            ad_sets_df = pd.DataFrame(ad_sets)
        elif isinstance(ad_sets, pd.DataFrame):
            ad_sets_df = ad_sets
        else:
            self.logger.warning("Ad sets data is not in a supported format")
            return analysis
        
        # Check for audience saturation
        if 'frequency' in ad_sets_df.columns:
            saturated = ad_sets_df[ad_sets_df['frequency'] > self.performance_thresholds['frequency']]
            analysis['saturated_audiences'] = saturated.to_dict('records')
            
        return analysis
    
    def _analyze_creatives(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze creative performance and identify winning/losing ads."""
        ads = data.get('ads', [])
        if not ads:
            return {}
        
        analysis = {
            'top_performing_ads': [],
            'underperforming_ads': [],
            'creative_fatigue': []
        }
        
        # Convert to DataFrame if it's a list of dictionaries
        if isinstance(ads, list):
            ads_df = pd.DataFrame(ads)
        elif isinstance(ads, pd.DataFrame):
            ads_df = ads
        else:
            self.logger.warning("Ads data is not in a supported format")
            return analysis
        
        # Identify top performing ads
        if 'ctr' in ads_df.columns:
            top_ads = ads_df.nlargest(5, 'ctr')
            analysis['top_performing_ads'] = top_ads.to_dict('records')
        
        return analysis
    
    def _analyze_budget_allocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze budget allocation and spending efficiency."""
        campaigns = data.get('campaigns', pd.DataFrame())
        insights = data.get('insights', pd.DataFrame())
        
        if campaigns.empty or insights.empty:
            return {}
            
        analysis = {
            'overspending_campaigns': [],
            'underspending_campaigns': [],
            'budget_recommendations': []
        }
        
        # Merge campaign data with insights
        if not insights.empty and 'campaign_id' in insights.columns:
            campaign_metrics = insights.groupby('campaign_id').agg({
                'spend': 'sum',
                'cost_per_conversion': 'mean',
                'conversions': 'sum'
            }).reset_index()
            
            # Calculate average cost per conversion across all campaigns
            avg_cpc = campaign_metrics['cost_per_conversion'].mean()
            
            # Find campaigns with significantly higher cost per conversion
            threshold = avg_cpc * 1.3  # 30% higher than average
            overspending = campaign_metrics[campaign_metrics['cost_per_conversion'] > threshold]
            
            # Add campaign names
            if not campaigns.empty and 'id' in campaigns.columns:
                campaigns_dict = campaigns.set_index('id')[['name']].to_dict('index')
                for _, row in overspending.iterrows():
                    campaign_info = campaigns_dict.get(row['campaign_id'], {})
                    analysis['overspending_campaigns'].append({
                        'id': row['campaign_id'],
                        'name': campaign_info.get('name', 'Unknown Campaign'),
                        'spend': float(row['spend']),
                        'cost_per_conversion': float(row['cost_per_conversion']),
                        'avg_cost_per_conversion': float(avg_cpc),
                        'difference_percentage': float((row['cost_per_conversion'] - avg_cpc) / avg_cpc * 100)
                    })
            
        return analysis
    
    def _generate_campaign_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on campaign analysis."""
        recommendations = []
        
        # Process underperforming campaigns
        for campaign in analysis.get('underperforming', []):
            recommendations.append({
                'type': 'campaign_performance',
                'severity': 'high',
                'campaign_name': campaign.get('name'),
                'recommendation': f"Campaign '{campaign.get('name')}' is underperforming with a CTR of {campaign.get('ctr', 0):.2f}%",
                'action_items': [
                    "Review targeting settings",
                    "Check ad creative performance",
                    "Optimize bid strategy"
                ],
                'potential_savings': campaign.get('spend', 0) * 0.3  # Estimate 30% potential savings
            })
            
        return recommendations
    
    def _generate_audience_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on audience analysis."""
        recommendations = []
        
        # Process saturated audiences
        for audience in analysis.get('saturated_audiences', []):
            recommendations.append({
                'type': 'audience_fatigue',
                'severity': 'medium',
                'adset_name': audience.get('name'),
                'recommendation': f"Audience fatigue detected in ad set '{audience.get('name')}' with frequency {audience.get('frequency', 0):.1f}",
                'action_items': [
                    "Refresh creative content",
                    "Expand audience targeting",
                    "Consider creating a new lookalike audience"
                ],
                'potential_savings': audience.get('spend', 0) * 0.2  # Estimate 20% potential savings
            })
            
        return recommendations
    
    def _generate_creative_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on creative analysis."""
        recommendations = []
        
        # Process underperforming ads
        for ad in analysis.get('underperforming_ads', []):
            recommendations.append({
                'type': 'creative_performance',
                'severity': 'medium',
                'ad_name': ad.get('name'),
                'recommendation': f"Ad '{ad.get('name')}' is underperforming with low engagement rates",
                'action_items': [
                    "Test new creative variations",
                    "Review ad copy and call-to-action",
                    "Consider pausing or replacing the ad"
                ],
                'potential_savings': ad.get('spend', 0) * 0.25  # Estimate 25% potential savings
            })
            
        return recommendations
    
    def _generate_budget_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on budget analysis."""
        recommendations = []
        
        # Process overspending campaigns
        for campaign in analysis.get('overspending_campaigns', []):
            diff_pct = campaign.get('difference_percentage', 0)
            recommendations.append({
                'type': 'budget_optimization',
                'severity': 'high' if diff_pct > 50 else 'medium',
                'campaign_name': campaign.get('name'),
                'recommendation': (
                    f"Campaign '{campaign.get('name')}' has {diff_pct:.1f}% higher cost per conversion "
                    f"(${campaign.get('cost_per_conversion', 0):.2f} vs. average ${campaign.get('avg_cost_per_conversion', 0):.2f})"
                ),
                'action_items': [
                    "Review campaign targeting settings",
                    "Analyze ad creative performance",
                    "Consider reducing daily budget",
                    "Optimize bidding strategy"
                ],
                'potential_savings': campaign.get('spend', 0) * min(0.5, diff_pct / 100)  # Cap at 50% potential savings
            })
            
        return recommendations
    
    def _calculate_potential_savings(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate total potential savings from all recommendations."""
        return sum(rec.get('potential_savings', 0) for rec in recommendations)
    
    def _calculate_improvement_potential(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate overall improvement percentage potential."""
        # Simple calculation - could be made more sophisticated
        high_severity = len([r for r in recommendations if r.get('severity') == 'high'])
        medium_severity = len([r for r in recommendations if r.get('severity') == 'medium'])
        
        # Weight high severity more than medium
        return min(100, (high_severity * 15 + medium_severity * 7))  # Cap at 100% 