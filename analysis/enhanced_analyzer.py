import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import the enhanced analysis components
from processing.enhanced_fatigue_detection import detect_ad_fatigue, batch_fatigue_analysis
from processing.audience_targeting_analyzer import AudienceTargetingAnalyzer
from processing.budget_optimizer import BudgetOptimizer

class EnhancedAdAccountAnalyzer:
    """
    Comprehensive ad account analyzer that integrates multiple advanced analysis
    algorithms to generate high-quality optimization insights.
    """
    
    def __init__(self, lookback_days=30):
        """
        Initialize the enhanced analyzer.
        
        Args:
            lookback_days (int): Number of days to analyze
        """
        self.lookback_days = lookback_days
        self.logger = logging.getLogger(__name__)
        
        # Initialize component analyzers
        self.audience_analyzer = AudienceTargetingAnalyzer(min_segment_size=100)
        self.budget_optimizer = BudgetOptimizer(min_campaign_spend=50, min_adset_spend=20)
    
    def analyze(self, account_data, platform='facebook'):
        """
        Run a comprehensive analysis of the ad account data.
        
        Args:
            account_data (dict): Raw ad account data from the API connector
            platform (str): Ad platform name ('facebook', 'tiktok', etc.)
            
        Returns:
            dict: Comprehensive analysis results and recommendations
        """
        self.logger.info(f"Starting enhanced analysis for {platform} ad account")
        
        # Process and prepare data
        processed_data = self._process_data(account_data, platform)
        
        # Initialize results structure
        results = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'account_overview': {},
            'insights': {},
            'recommendations': [],
            'metrics': {},
            'potential_savings': 0,
            'potential_improvement_percentage': 0
        }
        
        # Analyze account overview
        results['account_overview'] = self._analyze_account_overview(processed_data)
        
        # Run budget optimization analysis
        budget_results = self._analyze_budget_efficiency(processed_data)
        if budget_results:
            results['insights']['budget_efficiency'] = budget_results.get('efficiency_metrics', {})
            results['recommendations'].extend(budget_results.get('recommendations', []))
            results['metrics']['budget_efficiency'] = self._extract_budget_metrics(budget_results)
        
        # Run audience targeting analysis
        audience_results = self._analyze_audience_targeting(processed_data)
        if audience_results:
            results['insights']['audience_targeting'] = audience_results.get('segments', {})
            results['recommendations'].extend(audience_results.get('recommendations', []))
            results['metrics']['audience_targeting'] = self._extract_audience_metrics(audience_results)
        
        # Run ad fatigue analysis
        fatigue_results = self._analyze_ad_fatigue(processed_data)
        if fatigue_results:
            results['insights']['ad_fatigue'] = fatigue_results.get('fatigued_ads', [])
            results['recommendations'].extend(fatigue_results.get('recommendations', []))
            results['metrics']['ad_fatigue'] = self._extract_fatigue_metrics(fatigue_results)
        
        # Run creative performance analysis
        creative_results = self._analyze_creative_performance(processed_data)
        if creative_results:
            results['insights']['creative_performance'] = creative_results
            results['recommendations'].extend(creative_results.get('recommendations', []))
            results['metrics']['creative_performance'] = self._extract_creative_metrics(creative_results)
        
        # Prioritize all recommendations
        results['recommendations'] = self._prioritize_recommendations(results['recommendations'])
        
        # Calculate overall potential savings
        results['potential_savings'] = sum(rec.get('potential_savings', 0) for rec in results['recommendations'])
        
        # Calculate potential improvement percentage
        results['potential_improvement_percentage'] = self._calculate_improvement_potential(
            results['recommendations'], results['account_overview'].get('total_spend', 0))
        
        self.logger.info(f"Enhanced analysis complete with {len(results['recommendations'])} recommendations")
        
        return results
    
    def _process_data(self, account_data, platform):
        """
        Process raw account data into analyzable DataFrame format.
        
        Args:
            account_data (dict): Raw account data from API connector
            platform (str): Platform name
            
        Returns:
            dict: Processed data ready for analysis
        """
        processed_data = {
            'platform': platform,
            'campaigns': None,
            'ad_sets': None,
            'ads': None,
            'insights': None,
            'daily_insights': None
        }
        
        # Extract raw data based on platform
        if platform == 'facebook' or platform == 'instagram':
            campaigns = account_data.get('campaigns', [])
            ad_sets = account_data.get('ad_sets', [])
            ads = account_data.get('ads', [])
            insights = account_data.get('insights', [])
        elif platform == 'tiktok':
            # Map TikTok data structure to our standard format
            campaigns = account_data.get('campaigns', [])
            ad_sets = account_data.get('ad_groups', [])  # TikTok calls them ad groups
            ads = account_data.get('ads', [])
            insights = account_data.get('insights', [])
        else:
            # Generic extraction for other platforms
            campaigns = account_data.get('campaigns', [])
            ad_sets = account_data.get('ad_sets', []) or account_data.get('ad_groups', [])
            ads = account_data.get('ads', [])
            insights = account_data.get('insights', [])
        
        # Convert to pandas DataFrames
        processed_data['campaigns'] = pd.DataFrame(campaigns) if campaigns else pd.DataFrame()
        processed_data['ad_sets'] = pd.DataFrame(ad_sets) if ad_sets else pd.DataFrame()
        processed_data['ads'] = pd.DataFrame(ads) if ads else pd.DataFrame()
        
        # Process insights data
        if insights:
            insights_df = pd.DataFrame(insights)
            
            # Convert date strings to datetime
            if 'date' in insights_df.columns:
                insights_df['date'] = pd.to_datetime(insights_df['date'])
            elif 'date_start' in insights_df.columns:
                insights_df['date'] = pd.to_datetime(insights_df['date_start'])
            
            # Create a daily insights copy if we have date information
            if 'date' in insights_df.columns:
                processed_data['daily_insights'] = insights_df.copy()
                
                # Create aggregated insights (removing date breakdown)
                if platform == 'facebook' or platform == 'instagram':
                    group_cols = ['campaign_id', 'campaign_name', 'adset_id', 'adset_name', 'ad_id', 'ad_name']
                elif platform == 'tiktok':
                    group_cols = ['campaign_id', 'campaign_name', 'ad_group_id', 'ad_group_name', 'ad_id', 'ad_name']
                else:
                    # Try to determine grouping columns dynamically
                    group_cols = [col for col in insights_df.columns if 
                                 col.endswith('_id') or col.endswith('_name')]
                
                # Keep only existing columns
                group_cols = [col for col in group_cols if col in insights_df.columns]
                
                if group_cols:
                    # Aggregate metrics
                    agg_dict = {}
                    for col in insights_df.columns:
                        if col in group_cols or col == 'date':
                            continue
                        
                        # Try to determine if the column is numeric
                        try:
                            insights_df[col] = pd.to_numeric(insights_df[col])
                            agg_dict[col] = 'sum'
                        except:
                            agg_dict[col] = 'first'
                    
                    # Aggregate by group columns
                    agg_insights = insights_df.groupby(group_cols).agg(agg_dict).reset_index()
                    processed_data['insights'] = agg_insights
                else:
                    processed_data['insights'] = insights_df
            else:
                processed_data['insights'] = insights_df
                processed_data['daily_insights'] = None
        
        # Clean up and standardize column names
        self._standardize_columns(processed_data)
        
        return processed_data
    
    def _standardize_columns(self, processed_data):
        """
        Standardize column names across different platforms.
        
        Args:
            processed_data (dict): Dictionary of DataFrames to standardize
        """
        # Map of platform-specific column names to standard names
        column_mapping = {
            'tiktok': {
                'ad_group_id': 'adset_id',
                'ad_group_name': 'adset_name',
                'total_conversions': 'conversions',
                'conversion_value': 'revenue'
            }
        }
        
        platform = processed_data['platform']
        if platform in column_mapping:
            mapping = column_mapping[platform]
            
            # Apply mapping to each DataFrame
            for key, df in processed_data.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    # Rename columns based on mapping
                    df.rename(columns=mapping, inplace=True)
        
        # Ensure consistent data types
        for key, df in processed_data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Convert numeric columns to numeric types
                numeric_cols = ['impressions', 'clicks', 'spend', 'conversions', 'purchases', 
                                'revenue', 'ctr', 'cpc', 'cpm', 'cpa']
                
                for col in numeric_cols:
                    if col in df.columns:
                        try:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        except:
                            pass
    
    def _analyze_account_overview(self, processed_data):
        """
        Generate account-level performance overview.
        
        Args:
            processed_data (dict): Processed account data
            
        Returns:
            dict: Account overview metrics
        """
        insights_df = processed_data.get('insights')
        if insights_df is None or insights_df.empty:
            return {}
        
        # Initialize overview
        overview = {
            'total_spend': 0,
            'total_impressions': 0,
            'total_clicks': 0,
            'total_conversions': 0,
            'total_revenue': 0,
            'ctr': 0,
            'cpc': 0,
            'cpm': 0,
            'conversion_rate': 0,
            'cpa': 0,
            'roas': 0
        }
        
        # Calculate totals
        if 'spend' in insights_df.columns:
            overview['total_spend'] = insights_df['spend'].sum()
        
        if 'impressions' in insights_df.columns:
            overview['total_impressions'] = insights_df['impressions'].sum()
        
        if 'clicks' in insights_df.columns:
            overview['total_clicks'] = insights_df['clicks'].sum()
        
        # Check for conversions (different platforms may use different column names)
        for col in ['conversions', 'purchases', 'total_conversions']:
            if col in insights_df.columns:
                overview['total_conversions'] += insights_df[col].sum()
        
        # Check for revenue (different platforms may use different column names)
        for col in ['revenue', 'conversion_value', 'purchase_value']:
            if col in insights_df.columns:
                overview['total_revenue'] += insights_df[col].sum()
        
        # Calculate derived metrics
        if overview['total_impressions'] > 0:
            overview['ctr'] = (overview['total_clicks'] / overview['total_impressions']) * 100
            overview['cpm'] = (overview['total_spend'] / overview['total_impressions']) * 1000
        
        if overview['total_clicks'] > 0:
            overview['cpc'] = overview['total_spend'] / overview['total_clicks']
            if overview['total_conversions'] > 0:
                overview['conversion_rate'] = (overview['total_conversions'] / overview['total_clicks']) * 100
        
        if overview['total_conversions'] > 0:
            overview['cpa'] = overview['total_spend'] / overview['total_conversions']
        
        if overview['total_spend'] > 0 and overview['total_revenue'] > 0:
            overview['roas'] = overview['total_revenue'] / overview['total_spend']
        
        # Add campaign and ad set counts
        campaigns_df = processed_data.get('campaigns')
        ad_sets_df = processed_data.get('ad_sets')
        ads_df = processed_data.get('ads')
        
        if campaigns_df is not None and not campaigns_df.empty:
            # Get active campaign count
            if 'status' in campaigns_df.columns:
                overview['active_campaigns'] = campaigns_df[campaigns_df['status'].isin(['ACTIVE', 'active'])].shape[0]
            overview['total_campaigns'] = campaigns_df.shape[0]
        
        if ad_sets_df is not None and not ad_sets_df.empty:
            # Get active ad set count
            if 'status' in ad_sets_df.columns:
                overview['active_ad_sets'] = ad_sets_df[ad_sets_df['status'].isin(['ACTIVE', 'active'])].shape[0]
            overview['total_ad_sets'] = ad_sets_df.shape[0]
        
        if ads_df is not None and not ads_df.empty:
            # Get active ad count
            if 'status' in ads_df.columns:
                overview['active_ads'] = ads_df[ads_df['status'].isin(['ACTIVE', 'active'])].shape[0]
            overview['total_ads'] = ads_df.shape[0]
        
        return overview
    
    def _analyze_budget_efficiency(self, processed_data):
        """
        Analyze budget efficiency using the BudgetOptimizer.
        
        Args:
            processed_data (dict): Processed account data
            
        Returns:
            dict: Budget efficiency analysis results
        """
        # Extract needed dataframes
        campaigns_df = processed_data.get('campaigns')
        ad_sets_df = processed_data.get('ad_sets')
        ads_df = processed_data.get('ads')
        insights_df = processed_data.get('insights')
        
        if campaigns_df is None or campaigns_df.empty or insights_df is None or insights_df.empty:
            self.logger.warning("Insufficient data for budget efficiency analysis")
            return None
        
        try:
            # Run budget optimization analysis
            budget_analysis = self.budget_optimizer.analyze(
                campaigns_df, ad_sets_df, ads_df, insights_df)
            return budget_analysis
        except Exception as e:
            self.logger.error(f"Error in budget efficiency analysis: {e}")
            return None
    
    def _analyze_audience_targeting(self, processed_data):
        """
        Analyze audience targeting using the AudienceTargetingAnalyzer.
        
        Args:
            processed_data (dict): Processed account data
            
        Returns:
            dict: Audience targeting analysis results
        """
        insights_df = processed_data.get('insights')
        
        if insights_df is None or insights_df.empty:
            self.logger.warning("Insufficient data for audience targeting analysis")
            return None
        
        # Check if we have segment breakdowns
        segment_columns = ['age', 'gender', 'device', 'platform', 'placement', 
                          'country', 'region', 'device_platform']
        
        if not any(col in insights_df.columns for col in segment_columns):
            self.logger.warning("No segment breakdowns found for audience analysis")
            return None
        
        try:
            # Run audience targeting analysis
            audience_analysis = self.audience_analyzer.analyze(insights_df)
            return audience_analysis
        except Exception as e:
            self.logger.error(f"Error in audience targeting analysis: {e}")
            return None
    
    def _analyze_ad_fatigue(self, processed_data):
        """
        Analyze ad fatigue using enhanced fatigue detection.
        
        Args:
            processed_data (dict): Processed account data
            
        Returns:
            dict: Ad fatigue analysis results
        """
        daily_insights = processed_data.get('daily_insights')
        
        if daily_insights is None or daily_insights.empty or 'date' not in daily_insights.columns:
            self.logger.warning("Insufficient data for ad fatigue analysis")
            return None
        
        # Check if we have the minimum required fields
        required_cols = ['ad_id', 'impressions', 'clicks']
        if not all(col in daily_insights.columns for col in required_cols):
            self.logger.warning(f"Missing required columns for ad fatigue analysis: {required_cols}")
            return None
        
        try:
            # Run batch fatigue analysis
            fatigued_ads = batch_fatigue_analysis(daily_insights, min_impressions=1000)
            
            # Extract recommendations
            recommendations = []
            for ad in fatigued_ads:
                recommendations.append({
                    'type': 'ad_fatigue',
                    'ad_id': ad['ad_id'],
                    'ad_name': ad['ad_name'],
                    'days_running': ad['days_running'],
                    'confidence': ad['confidence'],
                    'severity': ad['severity'],
                    'potential_savings': self._estimate_fatigue_savings(ad),
                    'recommendation': ad['recommendation']
                })
            
            return {
                'fatigued_ads': fatigued_ads,
                'recommendations': recommendations
            }
        except Exception as e:
            self.logger.error(f"Error in ad fatigue analysis: {e}")
            return None
    
    def _analyze_creative_performance(self, processed_data):
        """
        Analyze creative performance to identify top and bottom performers.
        
        Args:
            processed_data (dict): Processed account data
            
        Returns:
            dict: Creative performance analysis results
        """
        insights_df = processed_data.get('insights')
        ads_df = processed_data.get('ads')
        
        if insights_df is None or insights_df.empty:
            self.logger.warning("Insufficient data for creative performance analysis")
            return None
        
        # Check if we have ad-level data
        if 'ad_id' not in insights_df.columns:
            self.logger.warning("No ad-level data found for creative analysis")
            return None
        
        try:
            # Group by ad
            ad_metrics = insights_df.groupby('ad_id').agg({
                'ad_name': 'first',
                'impressions': 'sum',
                'clicks': 'sum',
                'spend': 'sum'
            }).reset_index()
            
            # Add conversion metrics if available
            conversion_cols = [col for col in ['conversions', 'purchases'] if col in insights_df.columns]
            if conversion_cols:
                for col in conversion_cols:
                    conversion_data = insights_df.groupby('ad_id')[col].sum().reset_index()
                    ad_metrics = ad_metrics.merge(conversion_data, on='ad_id', how='left')
            
            # Filter for ads with minimum data
            min_impressions = 1000
            ad_metrics = ad_metrics[ad_metrics['impressions'] >= min_impressions]
            
            if ad_metrics.empty:
                return None
            
            # Calculate performance metrics
            ad_metrics['ctr'] = (ad_metrics['clicks'] / ad_metrics['impressions']) * 100
            ad_metrics['cpc'] = ad_metrics['spend'] / ad_metrics['clicks']
            
            # Add conversion metrics if available
            if conversion_cols:
                # Use first available conversion column
                conv_col = conversion_cols[0]
                ad_metrics['conversion_rate'] = (ad_metrics[conv_col] / ad_metrics['clicks']) * 100
                ad_metrics['cpa'] = ad_metrics['spend'] / ad_metrics[conv_col]
            
            # Clean up infinity and NaN values
            ad_metrics = ad_metrics.replace([np.inf, -np.inf], np.nan)
            
            # Identify top and bottom performers
            results = {
                'total_ads_analyzed': len(ad_metrics),
                'top_performers': [],
                'bottom_performers': [],
                'recommendations': []
            }
            
            # Identify top performers by CTR
            top_ctr = ad_metrics.nlargest(3, 'ctr')
            results['top_performers'].extend([{
                'ad_id': row['ad_id'],
                'ad_name': row['ad_name'],
                'impressions': row['impressions'],
                'clicks': row['clicks'],
                'ctr': row['ctr'],
                'metric': 'ctr'
            } for _, row in top_ctr.iterrows()])
            
            # Identify bottom performers by CTR
            bottom_ctr = ad_metrics.nsmallest(3, 'ctr')
            results['bottom_performers'].extend([{
                'ad_id': row['ad_id'],
                'ad_name': row['ad_name'],
                'impressions': row['impressions'],
                'clicks': row['clicks'],
                'ctr': row['ctr'],
                'metric': 'ctr'
            } for _, row in bottom_ctr.iterrows()])
            
            # Add conversion-based analysis if available
            if conversion_cols:
                # Filter ads with minimum conversions
                conv_metrics = ad_metrics.dropna(subset=['conversion_rate'])
                
                if not conv_metrics.empty:
                    # Top performers by conversion rate
                    top_cr = conv_metrics.nlargest(3, 'conversion_rate')
                    results['top_performers'].extend([{
                        'ad_id': row['ad_id'],
                        'ad_name': row['ad_name'],
                        'clicks': row['clicks'],
                        'conversions': row[conversion_cols[0]],
                        'conversion_rate': row['conversion_rate'],
                        'metric': 'conversion_rate'
                    } for _, row in top_cr.iterrows()])
                    
                    # Bottom performers by conversion rate
                    bottom_cr = conv_metrics.nsmallest(3, 'conversion_rate')
                    results['bottom_performers'].extend([{
                        'ad_id': row['ad_id'],
                        'ad_name': row['ad_name'],
                        'clicks': row['clicks'],
                        'conversions': row[conversion_cols[0]],
                        'conversion_rate': row['conversion_rate'],
                        'metric': 'conversion_rate'
                    } for _, row in bottom_cr.iterrows()])
            
            # Generate recommendations
            # Recommendation for scaling top performers
            if 'conversion_rate' in ad_metrics.columns:
                best_ad = ad_metrics.nlargest(1, 'conversion_rate').iloc[0]
                top_recommendation = {
                    'type': 'top_creative_scaling',
                    'ad_id': best_ad['ad_id'],
                    'ad_name': best_ad['ad_name'],
                    'conversion_rate': best_ad['conversion_rate'],
                    'ctr': best_ad['ctr'],
                    'severity': 'low',  # This is a positive recommendation
                    'potential_savings': 0,
                    'recommendation': (
                        f"Scale budget for top-performing ad '{best_ad['ad_name']}' with exceptional "
                        f"conversion rate of {best_ad['conversion_rate']:.2f}% and CTR of {best_ad['ctr']:.2f}%. "
                        f"Consider creating similar ads based on this winning creative."
                    )
                }
                results['recommendations'].append(top_recommendation)
            else:
                best_ad = ad_metrics.nlargest(1, 'ctr').iloc[0]
                top_recommendation = {
                    'type': 'top_creative_scaling',
                    'ad_id': best_ad['ad_id'],
                    'ad_name': best_ad['ad_name'],
                    'ctr': best_ad['ctr'],
                    'severity': 'low',  # This is a positive recommendation
                    'potential_savings': 0,
                    'recommendation': (
                        f"Scale budget for top-performing ad '{best_ad['ad_name']}' with exceptional "
                        f"CTR of {best_ad['ctr']:.2f}%. Consider creating similar ads based on this winning creative."
                    )
                }
                results['recommendations'].append(top_recommendation)
            
            # Recommendation for pausing bottom performers
            if 'conversion_rate' in ad_metrics.columns:
                worst_ads = ad_metrics[ad_metrics['spend'] > 50].nsmallest(2, 'conversion_rate')
                
                for _, ad in worst_ads.iterrows():
                    if pd.isna(ad['conversion_rate']) or ad['conversion_rate'] < best_ad['conversion_rate'] * 0.3:
                        potential_savings = ad['spend'] * 0.9  # 90% of spend on this ad
                        bottom_recommendation = {
                            'type': 'bottom_creative_pausing',
                            'ad_id': ad['ad_id'],
                            'ad_name': ad['ad_name'],
                            'conversion_rate': ad['conversion_rate'] if not pd.isna(ad['conversion_rate']) else 0,
                            'ctr': ad['ctr'],
                            'severity': 'medium',
                            'potential_savings': potential_savings,
                            'recommendation': (
                                f"Consider pausing underperforming ad '{ad['ad_name']}' with "
                                f"low conversion rate of {ad['conversion_rate']:.2f}% compared to "
                                f"top performer at {best_ad['conversion_rate']:.2f}%. "
                                f"Reallocate budget to better-performing creatives."
                            )
                        }
                        results['recommendations'].append(bottom_recommendation)
            else:
                worst_ads = ad_metrics[ad_metrics['spend'] > 50].nsmallest(2, 'ctr')
                
                for _, ad in worst_ads.iterrows():
                    if ad['ctr'] < best_ad['ctr'] * 0.3:
                        potential_savings = ad['spend'] * 0.9  # 90% of spend on this ad
                        bottom_recommendation = {
                            'type': 'bottom_creative_pausing',
                            'ad_id': ad['ad_id'],
                            'ad_name': ad['ad_name'],
                            'ctr': ad['ctr'],
                            'severity': 'medium',
                            'potential_savings': potential_savings,
                            'recommendation': (
                                f"Consider pausing underperforming ad '{ad['ad_name']}' with "
                                f"low CTR of {ad['ctr']:.2f}% compared to top performer "
                                f"at {best_ad['ctr']:.2f}%. Reallocate budget to better-performing creatives."
                            )
                        }
                        results['recommendations'].append(bottom_recommendation)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in creative performance analysis: {e}")
            return None
    
    def _prioritize_recommendations(self, recommendations):
        """
        Prioritize recommendations based on potential impact and severity.
        
        Args:
            recommendations (list): List of recommendation objects
            
        Returns:
            list: Prioritized recommendations
        """
        if not recommendations:
            return []
        
        # Define type priority scores (higher = more important)
        type_priority = {
            'budget_allocation_imbalance': 100,
            'campaign_budget_inefficiency': 90,
            'adset_budget_inefficiency': 80,
            'ad_fatigue': 70,
            'cross_segment_conversion_rate_optimization': 65,
            'cross_segment_cpa_optimization': 65,
            'age_conversion_rate_optimization': 60,
            'gender_conversion_rate_optimization': 60,
            'device_conversion_rate_optimization': 55,
            'ad_performance_inefficiency': 50,
            'bottom_creative_pausing': 45,
            'top_creative_scaling': 40,
            'ctr_trend': 30,
            'cpa_trend': 35
        }
        
        # Define severity multipliers
        severity_multiplier = {
            'high': 1.5,
            'medium': 1.0,
            'low': 0.5
        }
        
        # Calculate priority score for each recommendation
        for rec in recommendations:
            # Base priority from type
            base_priority = type_priority.get(rec.get('type', ''), 50)
            
            # Adjust by severity
            severity = rec.get('severity', 'medium')
            multiplier = severity_multiplier.get(severity, 1.0)
            
            # Adjust by potential savings
            savings = rec.get('potential_savings', 0)
            savings_factor = min(savings / 100, 2.0)  # Cap at 2x multiplier
            
            # Calculate final priority score
            priority_score = base_priority * multiplier * (1 + savings_factor)
            
            # Add priority score to recommendation
            rec['priority_score'] = priority_score
        
        # Sort by priority score (descending)
        prioritized = sorted(recommendations, key=lambda x: x.get('priority_score', 0), reverse=True)
        
        return prioritized
    
    def _estimate_fatigue_savings(self, fatigue_data):
        """
        Estimate potential savings from addressing ad fatigue.
        
        Args:
            fatigue_data (dict): Ad fatigue analysis for a single ad
            
        Returns:
            float: Estimated potential savings
        """
        # Get spend data if available
        if 'spend' in fatigue_data:
            spend = fatigue_data['spend']
        else:
            # Default to moderate value if spend not available
            spend = 100
        
        # Adjust based on severity and confidence
        severity = fatigue_data.get('severity', 'medium')
        confidence = fatigue_data.get('confidence', 0.5)
        
        if severity == 'severe':
            # For severe fatigue, we recommend pausing (90% savings)
            savings_rate = 0.9
        else:
            # For moderate fatigue, we recommend reducing spend (50% savings)
            savings_rate = 0.5
        
        # Adjust by confidence
        adjusted_rate = savings_rate * confidence
        
        return spend * adjusted_rate
    
    def _extract_budget_metrics(self, budget_results):
        """
        Extract key metrics from budget analysis results.
        
        Args:
            budget_results (dict): Budget optimization results
            
        Returns:
            dict: Key budget metrics
        """
        metrics = {
            'estimated_savings': budget_results.get('estimated_savings', 0),
            'inefficient_entities': 0
        }
        
        # Count inefficient entities
        recommendations = budget_results.get('recommendations', [])
        entity_counts = {
            'campaign': 0,
            'adset': 0,
            'ad': 0
        }
        
        for rec in recommendations:
            rec_type = rec.get('type', '')
            if 'campaign' in rec_type:
                entity_counts['campaign'] += 1
            elif 'adset' in rec_type:
                entity_counts['adset'] += 1
            elif 'ad' in rec_type:
                entity_counts['ad'] += 1
        
        metrics['inefficient_entities'] = sum(entity_counts.values())
        metrics['entity_counts'] = entity_counts
        
        # Add budget distribution if available
        distribution = budget_results.get('budget_distribution', {})
        if 'quartiles' in distribution:
            metrics['budget_distribution'] = distribution
        
        return metrics
    
    def _extract_audience_metrics(self, audience_results):
        """
        Extract key metrics from audience analysis results.
        
        Args:
            audience_results (dict): Audience targeting results
            
        Returns:
            dict: Key audience metrics
        """
        metrics = {
            'segments_analyzed': 0,
            'significant_findings': 0
        }
        
        # Count segments analyzed
        segments = audience_results.get('segments', {})
        metrics['segments_analyzed'] = len(segments)
        
        # Count significant findings
        for segment_type, segment_data in segments.items():
            if segment_data.get('significant_findings', False):
                metrics['significant_findings'] += 1
        
        # Add recommendation count
        metrics['recommendation_count'] = len(audience_results.get('recommendations', []))
        
        return metrics
    
    def _extract_fatigue_metrics(self, fatigue_results):
        """
        Extract key metrics from ad fatigue analysis results.
        
        Args:
            fatigue_results (dict): Ad fatigue results
            
        Returns:
            dict: Key fatigue metrics
        """
        metrics = {
            'fatigued_ads_count': 0,
            'avg_confidence': 0,
            'severe_fatigue_count': 0,
            'moderate_fatigue_count': 0
        }
        
        fatigued_ads = fatigue_results.get('fatigued_ads', [])
        metrics['fatigued_ads_count'] = len(fatigued_ads)
        
        if fatigued_ads:
            # Calculate average confidence
            confidences = [ad.get('confidence', 0) for ad in fatigued_ads]
            metrics['avg_confidence'] = sum(confidences) / len(confidences)
            
            # Count by severity
            for ad in fatigued_ads:
                severity = ad.get('severity', 'medium')
                if severity == 'severe':
                    metrics['severe_fatigue_count'] += 1
                else:
                    metrics['moderate_fatigue_count'] += 1
        
        return metrics
    
    def _extract_creative_metrics(self, creative_results):
        """
        Extract key metrics from creative performance analysis results.
        
        Args:
            creative_results (dict): Creative performance results
            
        Returns:
            dict: Key creative metrics
        """
        metrics = {
            'ads_analyzed': creative_results.get('total_ads_analyzed', 0),
            'top_performers_count': len(creative_results.get('top_performers', [])),
            'bottom_performers_count': len(creative_results.get('bottom_performers', []))
        }
        
        # Extract performance gap metrics
        top_performers = creative_results.get('top_performers', [])
        bottom_performers = creative_results.get('bottom_performers', [])
        
        if top_performers and bottom_performers:
            # Find CTR gap
            top_ctr = next((ad['ctr'] for ad in top_performers if ad['metric'] == 'ctr'), None)
            bottom_ctr = next((ad['ctr'] for ad in bottom_performers if ad['metric'] == 'ctr'), None)
            
            if top_ctr is not None and bottom_ctr is not None and bottom_ctr > 0:
                metrics['ctr_gap_pct'] = ((top_ctr - bottom_ctr) / bottom_ctr) * 100
            
            # Find conversion rate gap if available
            top_cr = next((ad['conversion_rate'] for ad in top_performers if ad['metric'] == 'conversion_rate'), None)
            bottom_cr = next((ad['conversion_rate'] for ad in bottom_performers if ad['metric'] == 'conversion_rate'), None)
            
            if top_cr is not None and bottom_cr is not None and bottom_cr > 0:
                metrics['conversion_rate_gap_pct'] = ((top_cr - bottom_cr) / bottom_cr) * 100
        
        return metrics
    
    def _calculate_improvement_potential(self, recommendations, total_spend):
        """
        Calculate potential performance improvement percentage.
        
        Args:
            recommendations (list): List of recommendations
            total_spend (float): Total account spend
            
        Returns:
            float: Potential improvement percentage
        """
        if not recommendations or total_spend <= 0:
            return 0
        
        # Base improvement based on recommendations
        base_improvement = 0
        
        # Weight recommendations by severity and type
        for rec in recommendations:
            severity = rec.get('severity', 'medium')
            rec_type = rec.get('type', '')
            
            # Calculate impact contribution
            impact = 0
            
            if severity == 'high':
                impact = 2.0
            elif severity == 'medium':
                impact = 1.0
            elif severity == 'low':
                impact = 0.5
            
            # Adjust based on recommendation type
            if 'budget' in rec_type or 'allocation' in rec_type:
                # Budget optimization has direct impact
                impact *= 1.2
            elif 'audience' in rec_type or 'segment' in rec_type:
                # Audience targeting is generally high impact
                impact *= 1.1
            elif 'fatigue' in rec_type:
                # Ad fatigue has moderate impact
                impact *= 0.9
            
            # Add to base improvement
            base_improvement += impact
        
        # Scale based on number of recommendations
        # Each recommendation contributes less as the total goes up
        scaling_factor = min(1.0, 10 / len(recommendations))
        scaled_improvement = base_improvement * scaling_factor
        
        # Normalize to percentage (capping at 50%)
        improvement_percentage = min(scaled_improvement * 2.5, 50.0)
        
        return improvement_percentage