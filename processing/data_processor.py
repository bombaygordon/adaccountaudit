import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from processing.metrics import calculate_performance_metrics, identify_kpi_trends
from processing.insights import generate_insights, prioritize_recommendations

logger = logging.getLogger(__name__)

class AdDataProcessor:
    """
    Advanced data processing engine for ad account data analysis.
    Processes raw data from multiple platforms and generates insights.
    """
    
    def __init__(self, platform_data, lookback_days=30):
        """
        Initialize processor with platform-specific data.
        
        Args:
            platform_data (dict): Dictionary mapping platform names to their data
            lookback_days (int): Number of days of historical data being analyzed
        """
        self.platform_data = platform_data
        self.lookback_days = lookback_days
        self.processed_data = {}
        self.metrics = {}
        self.insights = {}
        
    def process_all_platforms(self):
        """Process data from all available platforms"""
        for platform, data in self.platform_data.items():
            try:
                logger.info(f"Processing data for platform: {platform}")
                processed = self.process_platform_data(platform, data)
                self.processed_data[platform] = processed
                
                # Calculate platform-specific metrics
                self.metrics[platform] = calculate_performance_metrics(processed, platform)
                
                # Identify trends
                trends = identify_kpi_trends(processed, platform, self.lookback_days)
                self.metrics[platform]['trends'] = trends
                
                # Generate platform-specific insights
                self.insights[platform] = generate_insights(
                    processed, 
                    self.metrics[platform], 
                    platform
                )
                
            except Exception as e:
                logger.error(f"Error processing {platform} data: {str(e)}")
                self.processed_data[platform] = None
                self.metrics[platform] = {}
                self.insights[platform] = {
                    'recommendations': [],
                    'error': str(e)
                }
        
        # Generate cross-platform insights if multiple platforms
        if len(self.platform_data) > 1:
            self._generate_cross_platform_insights()
            
        return self.processed_data
    
    def process_platform_data(self, platform, data):
        """
        Process raw platform data into analyzable format.
        
        Args:
            platform (str): Platform name ('facebook', 'tiktok', etc.)
            data (dict): Raw platform data
            
        Returns:
            dict: Processed data with DataFrames for different entities
        """
        processed = {}
        
        # Handle platform-specific data structures
        if platform == 'facebook' or platform == 'instagram':
            processed = self._process_facebook_data(data)
        elif platform == 'tiktok':
            processed = self._process_tiktok_data(data)
        else:
            # Generic processing for other platforms
            for entity_type, entities in data.items():
                processed[entity_type] = pd.DataFrame(entities)
                
        # Add platform identifier to processed data
        processed['platform'] = platform
                
        return processed
    
    def _process_facebook_data(self, data):
        """Process Facebook/Instagram specific data structure"""
        processed = {}
        
        # Convert each entity to DataFrame
        for entity_type in ['campaigns', 'ad_sets', 'ads', 'insights']:
            if entity_type in data and data[entity_type]:
                df = pd.DataFrame(data[entity_type])
                
                # Handle special fields
                if entity_type == 'insights':
                    # Convert date strings to datetime
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                    
                    # Extract actions (conversions, etc.)
                    if 'actions' in df.columns:
                        # This is complex in real FB data, simplified here
                        df['purchases'] = df['actions'].apply(
                            lambda x: sum(a.get('value', 0) for a in x if a.get('action_type') == 'purchase')
                            if isinstance(x, list) else 0
                        )
                
                processed[entity_type] = df
        
        # Join insights with campaign, ad set, and ad data if available
        if 'insights' in processed and not processed['insights'].empty:
            insights_df = processed['insights']
            
            # Join with campaigns
            if 'campaigns' in processed and not processed['campaigns'].empty:
                if 'campaign_id' in insights_df.columns and 'id' in processed['campaigns'].columns:
                    campaigns_df = processed['campaigns']
                    insights_df = pd.merge(
                        insights_df, 
                        campaigns_df,
                        left_on='campaign_id',
                        right_on='id',
                        how='left',
                        suffixes=('', '_campaign')
                    )
            
            # Join with ad sets
            if 'ad_sets' in processed and not processed['ad_sets'].empty:
                if 'adset_id' in insights_df.columns and 'id' in processed['ad_sets'].columns:
                    ad_sets_df = processed['ad_sets']
                    insights_df = pd.merge(
                        insights_df, 
                        ad_sets_df,
                        left_on='adset_id',
                        right_on='id',
                        how='left',
                        suffixes=('', '_adset')
                    )
            
            # Join with ads
            if 'ads' in processed and not processed['ads'].empty:
                if 'ad_id' in insights_df.columns and 'id' in processed['ads'].columns:
                    ads_df = processed['ads']
                    insights_df = pd.merge(
                        insights_df, 
                        ads_df,
                        left_on='ad_id',
                        right_on='id',
                        how='left',
                        suffixes=('', '_ad')
                    )
            
            # Update insights with joined data
            processed['insights'] = insights_df
            
            # Create a master dataset with all joined data
            processed['master'] = insights_df
        
        return processed
    
    def _process_tiktok_data(self, data):
        """Process TikTok specific data structure"""
        processed = {}
        
        # Convert each entity to DataFrame
        for entity_type in ['campaigns', 'ad_groups', 'ads', 'insights']:
            if entity_type in data and data[entity_type]:
                df = pd.DataFrame(data[entity_type])
                
                # Handle TikTok-specific data structures
                if entity_type == 'insights':
                    # Convert date strings to datetime
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                
                processed[entity_type] = df
        
        # Join insights with campaign, ad group, and ad data
        if 'insights' in processed and not processed['insights'].empty:
            insights_df = processed['insights']
            
            # Join with campaigns
            if 'campaigns' in processed and not processed['campaigns'].empty:
                if 'campaign_id' in insights_df.columns and 'id' in processed['campaigns'].columns:
                    campaigns_df = processed['campaigns']
                    insights_df = pd.merge(
                        insights_df, 
                        campaigns_df,
                        left_on='campaign_id',
                        right_on='id',
                        how='left',
                        suffixes=('', '_campaign')
                    )
            
            # Join with ad groups
            if 'ad_groups' in processed and not processed['ad_groups'].empty:
                if 'ad_group_id' in insights_df.columns and 'id' in processed['ad_groups'].columns:
                    ad_groups_df = processed['ad_groups']
                    insights_df = pd.merge(
                        insights_df, 
                        ad_groups_df,
                        left_on='ad_group_id',
                        right_on='id',
                        how='left',
                        suffixes=('', '_adgroup')
                    )
            
            # Join with ads
            if 'ads' in processed and not processed['ads'].empty:
                if 'ad_id' in insights_df.columns and 'id' in processed['ads'].columns:
                    ads_df = processed['ads']
                    insights_df = pd.merge(
                        insights_df, 
                        ads_df,
                        left_on='ad_id',
                        right_on='id',
                        how='left',
                        suffixes=('', '_ad')
                    )
            
            # Update insights with joined data
            processed['insights'] = insights_df
            
            # Create a master dataset with all joined data
            processed['master'] = insights_df
        
        return processed
    
    def _generate_cross_platform_insights(self):
        """Generate insights by comparing metrics across platforms"""
        if len(self.metrics) < 2:
            return
        
        # Create cross-platform comparison metrics
        cross_platform_metrics = {}
        cross_platform_insights = []
        
        # Compare CPA, CTR, etc. across platforms
        for metric in ['ctr', 'cpc', 'cpm', 'conversion_rate', 'roas']:
            platform_values = {}
            
            for platform, metrics in self.metrics.items():
                if metric in metrics:
                    platform_values[platform] = metrics[metric]
            
            if len(platform_values) > 1:
                # Find best and worst performing platforms for this metric
                best_platform = max(platform_values.items(), key=lambda x: x[1])
                worst_platform = min(platform_values.items(), key=lambda x: x[1])
                
                # Calculate the difference
                difference_pct = ((best_platform[1] - worst_platform[1]) / worst_platform[1]) * 100 if worst_platform[1] != 0 else 0
                
                # Store the comparison
                cross_platform_metrics[metric] = {
                    'best_platform': best_platform[0],
                    'best_value': best_platform[1],
                    'worst_platform': worst_platform[0],
                    'worst_value': worst_platform[1],
                    'difference_pct': difference_pct
                }
                
                # Generate insight if difference is significant (>20%)
                if difference_pct > 20:
                    metric_name = metric.upper()
                    insight = {
                        'type': 'cross_platform_comparison',
                        'metric': metric,
                        'best_platform': best_platform[0],
                        'worst_platform': worst_platform[0],
                        'difference_pct': difference_pct,
                        'recommendation': f"Consider reallocating budget from {worst_platform[0]} to {best_platform[0]} where {metric_name} is {difference_pct:.1f}% better."
                    }
                    cross_platform_insights.append(insight)
        
        # Add to overall insights
        self.insights['cross_platform'] = {
            'metrics': cross_platform_metrics,
            'recommendations': cross_platform_insights
        }
    
    def get_all_recommendations(self):
        """
        Get prioritized recommendations across all platforms.
        
        Returns:
            list: Prioritized list of recommendation dictionaries
        """
        all_recommendations = []
        
        # Collect recommendations from each platform
        for platform, platform_insights in self.insights.items():
            if 'recommendations' in platform_insights:
                platform_recs = platform_insights['recommendations']
                
                # Add platform to each recommendation
                for rec in platform_recs:
                    if 'platform' not in rec:
                        rec['platform'] = platform
                
                all_recommendations.extend(platform_recs)
        
        # Prioritize recommendations
        prioritized_recommendations = prioritize_recommendations(all_recommendations)
        
        return prioritized_recommendations
    
    def get_overall_metrics(self):
        """
        Get aggregated metrics across all platforms.
        
        Returns:
            dict: Aggregated performance metrics
        """
        overall_metrics = {
            'spend': 0,
            'impressions': 0,
            'clicks': 0,
            'conversions': 0,
            'revenue': 0
        }
        
        # Sum up core metrics across platforms
        for platform, metrics in self.metrics.items():
            for key in overall_metrics:
                if key in metrics:
                    overall_metrics[key] += metrics[key]
        
        # Calculate derived metrics
        if overall_metrics['impressions'] > 0:
            overall_metrics['ctr'] = (overall_metrics['clicks'] / overall_metrics['impressions']) * 100
        
        if overall_metrics['clicks'] > 0:
            overall_metrics['cpc'] = overall_metrics['spend'] / overall_metrics['clicks']
            
            if overall_metrics['conversions'] > 0:
                overall_metrics['conversion_rate'] = (overall_metrics['conversions'] / overall_metrics['clicks']) * 100
                overall_metrics['cpa'] = overall_metrics['spend'] / overall_metrics['conversions']
        
        if overall_metrics['spend'] > 0 and overall_metrics['revenue'] > 0:
            overall_metrics['roas'] = overall_metrics['revenue'] / overall_metrics['spend']
        
        return overall_metrics
    
    def estimate_savings_potential(self):
        """
        Estimate potential savings based on identified inefficiencies.
        
        Returns:
            float: Estimated monthly savings in dollars
        """
        total_potential_savings = 0
        
        # Sum up savings potential across platforms
        for platform, insights in self.insights.items():
            if 'potential_savings' in insights:
                total_potential_savings += insights['potential_savings']
        
        return total_potential_savings
    
    def estimate_improvement_potential(self):
        """
        Estimate potential performance improvement percentage.
        
        Returns:
            float: Estimated performance improvement percentage
        """
        # Calculate weighted average of improvement potentials
        total_spend = 0
        weighted_improvement = 0
        
        for platform, metrics in self.metrics.items():
            if 'spend' in metrics and platform in self.insights:
                platform_spend = metrics['spend']
                total_spend += platform_spend
                
                if 'potential_improvement' in self.insights[platform]:
                    platform_improvement = self.insights[platform]['potential_improvement']
                    weighted_improvement += platform_spend * platform_improvement
        
        # Calculate weighted average
        if total_spend > 0:
            return weighted_improvement / total_spend
        else:
            return 0