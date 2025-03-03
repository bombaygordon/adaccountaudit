import pandas as pd
import numpy as np
from scipy import stats
import logging
from datetime import datetime, timedelta
import math

class BudgetOptimizer:
    """
    Advanced budget optimization engine that identifies inefficient spend 
    and provides data-driven recommendations for budget reallocation.
    """
    
    def __init__(self, min_campaign_spend=100, min_adset_spend=50, 
                 min_data_threshold=1000, confidence_level=0.90):
        """
        Initialize the budget optimizer with threshold settings.
        
        Args:
            min_campaign_spend (float): Minimum campaign spend to analyze ($)
            min_adset_spend (float): Minimum ad set spend to analyze ($)
            min_data_threshold (int): Minimum impressions for statistical significance
            confidence_level (float): Statistical confidence level (0-1)
        """
        self.min_campaign_spend = min_campaign_spend
        self.min_adset_spend = min_adset_spend
        self.min_data_threshold = min_data_threshold
        self.confidence_level = confidence_level
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, campaigns_df, ad_sets_df, ads_df, insights_df):
        """
        Analyze budget efficiency across campaigns, ad sets, and ads.
        
        Args:
            campaigns_df (DataFrame): Campaign data
            ad_sets_df (DataFrame): Ad set data
            ads_df (DataFrame): Ad data
            insights_df (DataFrame): Performance insights data
            
        Returns:
            dict: Budget optimization analysis and recommendations
        """
        results = {
            'recommendations': [],
            'efficiency_metrics': {},
            'budget_distribution': {},
            'estimated_savings': 0
        }
        
        # Clean and prepare data
        prepared_data = self._prepare_data(campaigns_df, ad_sets_df, ads_df, insights_df)
        if not prepared_data:
            return results
        
        # Analyze at campaign level
        campaign_results = self._analyze_campaigns(prepared_data['campaigns'])
        if campaign_results:
            results['efficiency_metrics']['campaigns'] = campaign_results['metrics']
            results['recommendations'].extend(campaign_results['recommendations'])
        
        # Analyze at ad set level
        adset_results = self._analyze_adsets(prepared_data['ad_sets'])
        if adset_results:
            results['efficiency_metrics']['ad_sets'] = adset_results['metrics']
            results['recommendations'].extend(adset_results['recommendations'])
        
        # Analyze at ad level
        ad_results = self._analyze_ads(prepared_data['ads'])
        if ad_results:
            results['efficiency_metrics']['ads'] = ad_results['metrics']
            results['recommendations'].extend(ad_results['recommendations'])
        
        # Analyze budget allocation efficiency
        budget_results = self._analyze_budget_allocation(prepared_data)
        if budget_results:
            results['budget_distribution'] = budget_results['distribution']
            results['recommendations'].extend(budget_results['recommendations'])
        
        # Calculate total estimated savings
        total_savings = sum(rec.get('potential_savings', 0) for rec in results['recommendations'])
        results['estimated_savings'] = total_savings
        
        # Sort recommendations by potential impact
        results['recommendations'] = sorted(
            results['recommendations'], 
            key=lambda x: x.get('potential_savings', 0), 
            reverse=True
        )
        
        return results
    
    def _prepare_data(self, campaigns_df, ad_sets_df, ads_df, insights_df):
        """
        Clean and prepare data for analysis.
        
        Args:
            campaigns_df (DataFrame): Campaign data
            ad_sets_df (DataFrame): Ad set data
            ads_df (DataFrame): Ad data
            insights_df (DataFrame): Performance insights data
            
        Returns:
            dict: Prepared DataFrames for analysis
        """
        # Check for required data
        if (campaigns_df is None or campaigns_df.empty or 
            insights_df is None or insights_df.empty):
            self.logger.warning("Missing required campaign or insights data for budget analysis")
            return None
        
        # Convert to DataFrame if needed
        campaigns_df = pd.DataFrame(campaigns_df) if not isinstance(campaigns_df, pd.DataFrame) else campaigns_df
        ad_sets_df = pd.DataFrame(ad_sets_df) if not isinstance(ad_sets_df, pd.DataFrame) else ad_sets_df
        ads_df = pd.DataFrame(ads_df) if not isinstance(ads_df, pd.DataFrame) else ads_df
        insights_df = pd.DataFrame(insights_df) if not isinstance(insights_df, pd.DataFrame) else insights_df
        
        # Make sure we have campaign IDs
        if 'id' not in campaigns_df.columns and 'campaign_id' not in campaigns_df.columns:
            self.logger.warning("Campaign data missing required ID fields")
            return None
        
        # Rename columns for consistency if needed
        if 'id' in campaigns_df.columns and 'campaign_id' not in campaigns_df.columns:
            campaigns_df['campaign_id'] = campaigns_df['id']
        
        # Ensure we have insights for campaigns
        if 'campaign_id' not in insights_df.columns:
            self.logger.warning("Insights data missing required campaign_id field")
            return None
        
        # Ensure numeric data types
        numeric_cols = ['spend', 'impressions', 'clicks', 'conversions', 'purchases']
        for col in numeric_cols:
            if col in insights_df.columns:
                insights_df[col] = pd.to_numeric(insights_df[col], errors='coerce').fillna(0)
        
        # Add conversion column if it doesn't exist but purchases does
        if 'conversions' not in insights_df.columns and 'purchases' in insights_df.columns:
            insights_df['conversions'] = insights_df['purchases']
        
        # Prepare campaign-level data
        campaign_insights = insights_df.groupby('campaign_id').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'spend': 'sum',
            'conversions': 'sum' if 'conversions' in insights_df.columns else 'count'
        }).reset_index()
        
        # Calculate campaign-level metrics
        campaign_insights['ctr'] = (campaign_insights['clicks'] / campaign_insights['impressions']) * 100
        campaign_insights['cpm'] = (campaign_insights['spend'] / campaign_insights['impressions']) * 1000
        campaign_insights['cpc'] = campaign_insights['spend'] / campaign_insights['clicks']
        campaign_insights['conversion_rate'] = (campaign_insights['conversions'] / campaign_insights['clicks']) * 100
        campaign_insights['cpa'] = campaign_insights['spend'] / campaign_insights['conversions']
        
        # Clean up infinity and NaN values
        campaign_insights = campaign_insights.replace([np.inf, -np.inf], np.nan)
        
        # Merge with campaign data
        campaigns = campaigns_df.merge(
            campaign_insights, 
            left_on='campaign_id', 
            right_on='campaign_id', 
            how='inner'
        )
        
        # Filter campaigns by minimum spend
        campaigns = campaigns[campaigns['spend'] >= self.min_campaign_spend]
        
        prepared_data = {
            'campaigns': campaigns,
            'insights': insights_df
        }
        
        # Prepare ad set-level data if available
        if not ad_sets_df.empty and 'adset_id' in insights_df.columns:
            # Rename columns for consistency if needed
            if 'id' in ad_sets_df.columns and 'adset_id' not in ad_sets_df.columns:
                ad_sets_df['adset_id'] = ad_sets_df['id']
            
            # Aggregate insights at ad set level
            adset_insights = insights_df.groupby('adset_id').agg({
                'campaign_id': 'first',
                'impressions': 'sum',
                'clicks': 'sum',
                'spend': 'sum',
                'conversions': 'sum' if 'conversions' in insights_df.columns else 'count'
            }).reset_index()
            
            # Calculate ad set-level metrics
            adset_insights['ctr'] = (adset_insights['clicks'] / adset_insights['impressions']) * 100
            adset_insights['cpm'] = (adset_insights['spend'] / adset_insights['impressions']) * 1000
            adset_insights['cpc'] = adset_insights['spend'] / adset_insights['clicks']
            adset_insights['conversion_rate'] = (adset_insights['conversions'] / adset_insights['clicks']) * 100
            adset_insights['cpa'] = adset_insights['spend'] / adset_insights['conversions']
            
            # Clean up infinity and NaN values
            adset_insights = adset_insights.replace([np.inf, -np.inf], np.nan)
            
            # Merge with ad set data
            ad_sets = ad_sets_df.merge(
                adset_insights, 
                left_on='adset_id', 
                right_on='adset_id', 
                how='inner'
            )
            
            # Filter ad sets by minimum spend
            ad_sets = ad_sets[ad_sets['spend'] >= self.min_adset_spend]
            
            prepared_data['ad_sets'] = ad_sets
        else:
            prepared_data['ad_sets'] = pd.DataFrame()
        
        # Prepare ad-level data if available
        if not ads_df.empty and 'ad_id' in insights_df.columns:
            # Rename columns for consistency if needed
            if 'id' in ads_df.columns and 'ad_id' not in ads_df.columns:
                ads_df['ad_id'] = ads_df['id']
            
            # Aggregate insights at ad level
            ad_insights = insights_df.groupby('ad_id').agg({
                'campaign_id': 'first',
                'adset_id': 'first' if 'adset_id' in insights_df.columns else None,
                'impressions': 'sum',
                'clicks': 'sum',
                'spend': 'sum',
                'conversions': 'sum' if 'conversions' in insights_df.columns else 'count'
            }).reset_index()
            
            # Remove any None columns
            ad_insights = ad_insights.loc[:, ad_insights.columns.notna()]
            
            # Calculate ad-level metrics
            ad_insights['ctr'] = (ad_insights['clicks'] / ad_insights['impressions']) * 100
            ad_insights['cpm'] = (ad_insights['spend'] / ad_insights['impressions']) * 1000
            ad_insights['cpc'] = ad_insights['spend'] / ad_insights['clicks']
            ad_insights['conversion_rate'] = (ad_insights['conversions'] / ad_insights['clicks']) * 100
            ad_insights['cpa'] = ad_insights['spend'] / ad_insights['conversions']
            
            # Clean up infinity and NaN values
            ad_insights = ad_insights.replace([np.inf, -np.inf], np.nan)
            
            # Merge with ad data
            ads = ads_df.merge(
                ad_insights, 
                left_on='ad_id', 
                right_on='ad_id', 
                how='inner'
            )
            
            prepared_data['ads'] = ads
        else:
            prepared_data['ads'] = pd.DataFrame()
        
        return prepared_data
    
    def _analyze_campaigns(self, campaigns_df):
        """
        Analyze campaign-level budget efficiency.
        
        Args:
            campaigns_df (DataFrame): Campaign data with performance metrics
            
        Returns:
            dict: Campaign efficiency analysis and recommendations
        """
        if campaigns_df.empty:
            return None
        
        results = {
            'metrics': [],
            'recommendations': []
        }
        
        # Calculate average performance metrics
        avg_metrics = {
            'ctr': campaigns_df['ctr'].mean(),
            'cpm': campaigns_df['cpm'].mean(),
            'cpc': campaigns_df['cpc'].mean(),
            'conversion_rate': campaigns_df['conversion_rate'].mean() if 'conversion_rate' in campaigns_df.columns else None,
            'cpa': campaigns_df['cpa'].mean() if 'cpa' in campaigns_df.columns else None
        }
        
        # Analyze each campaign
        for _, campaign in campaigns_df.iterrows():
            # Skip campaigns with insufficient data
            if campaign['impressions'] < self.min_data_threshold:
                continue
            
            campaign_id = campaign['campaign_id']
            campaign_name = campaign.get('name', f"Campaign {campaign_id}")
            
            # Calculate efficiency metrics
            efficiency_metrics = {
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'spend': campaign['spend'],
                'impressions': campaign['impressions'],
                'clicks': campaign['clicks'],
                'conversions': campaign['conversions'] if 'conversions' in campaign else 0,
                'ctr': campaign['ctr'],
                'cpm': campaign['cpm'],
                'cpc': campaign['cpc'],
                'ctr_index': (campaign['ctr'] / avg_metrics['ctr']) * 100 if avg_metrics['ctr'] > 0 else 0,
                'cpm_index': (avg_metrics['cpm'] / campaign['cpm']) * 100 if campaign['cpm'] > 0 else 0,
                'cpc_index': (avg_metrics['cpc'] / campaign['cpc']) * 100 if campaign['cpc'] > 0 else 0
            }
            
            # Add conversion metrics if available
            if 'conversion_rate' in campaign and avg_metrics['conversion_rate'] is not None:
                efficiency_metrics['conversion_rate'] = campaign['conversion_rate']
                efficiency_metrics['cpa'] = campaign['cpa'] if 'cpa' in campaign else None
                
                if avg_metrics['conversion_rate'] > 0:
                    efficiency_metrics['conversion_rate_index'] = (campaign['conversion_rate'] / avg_metrics['conversion_rate']) * 100
                else:
                    efficiency_metrics['conversion_rate_index'] = 0
                    
                if 'cpa' in campaign and avg_metrics['cpa'] is not None and campaign['cpa'] > 0:
                    efficiency_metrics['cpa_index'] = (avg_metrics['cpa'] / campaign['cpa']) * 100
                else:
                    efficiency_metrics['cpa_index'] = 0
            
            # Calculate overall efficiency score (0-100)
            efficiency_score = self._calculate_efficiency_score(efficiency_metrics)
            efficiency_metrics['efficiency_score'] = efficiency_score
            
            # Add to metrics
            results['metrics'].append(efficiency_metrics)
            
            # Generate recommendations for inefficient campaigns
            if efficiency_score < 40:  # Very inefficient
                severity = "high"
                potential_savings = campaign['spend'] * 0.3  # 30% of spend
                
                # Determine main issue
                main_issue = self._identify_main_issue(efficiency_metrics)
                
                recommendation = {
                    'type': 'campaign_budget_inefficiency',
                    'campaign_id': campaign_id,
                    'campaign_name': campaign_name,
                    'efficiency_score': efficiency_score,
                    'main_issue': main_issue,
                    'severity': severity,
                    'potential_savings': potential_savings,
                    'recommendation': (
                        f"Campaign '{campaign_name}' is highly inefficient (score: {efficiency_score:.0f}/100) "
                        f"with {main_issue}. Consider reducing budget by 30% and reallocating to better-performing campaigns."
                    )
                }
                results['recommendations'].append(recommendation)
                
            elif efficiency_score < 60:  # Moderately inefficient
                severity = "medium"
                potential_savings = campaign['spend'] * 0.15  # 15% of spend
                
                # Determine main issue
                main_issue = self._identify_main_issue(efficiency_metrics)
                
                recommendation = {
                    'type': 'campaign_budget_inefficiency',
                    'campaign_id': campaign_id,
                    'campaign_name': campaign_name,
                    'efficiency_score': efficiency_score,
                    'main_issue': main_issue,
                    'severity': severity,
                    'potential_savings': potential_savings,
                    'recommendation': (
                        f"Campaign '{campaign_name}' is performing below average (score: {efficiency_score:.0f}/100) "
                        f"with {main_issue}. Consider reducing budget by 15% or optimizing targeting."
                    )
                }
                results['recommendations'].append(recommendation)
        
        return results
    
    def _analyze_adsets(self, ad_sets_df):
        """
        Analyze ad set-level budget efficiency.
        
        Args:
            ad_sets_df (DataFrame): Ad set data with performance metrics
            
        Returns:
            dict: Ad set efficiency analysis and recommendations
        """
        if ad_sets_df.empty:
            return None
        
        results = {
            'metrics': [],
            'recommendations': []
        }
        
        # Group by campaign to compare ad sets within the same campaign
        campaign_groups = ad_sets_df.groupby('campaign_id')
        
        for campaign_id, campaign_adsets in campaign_groups:
            # Skip campaigns with only one ad set
            if len(campaign_adsets) < 2:
                continue
            
            campaign_name = campaign_adsets['campaign_name'].iloc[0] if 'campaign_name' in campaign_adsets.columns else f"Campaign {campaign_id}"
            
            # Calculate average metrics for this campaign
            avg_metrics = {
                'ctr': campaign_adsets['ctr'].mean(),
                'cpm': campaign_adsets['cpm'].mean(),
                'cpc': campaign_adsets['cpc'].mean(),
                'conversion_rate': campaign_adsets['conversion_rate'].mean() if 'conversion_rate' in campaign_adsets.columns else None,
                'cpa': campaign_adsets['cpa'].mean() if 'cpa' in campaign_adsets.columns else None
            }
            
            # Calculate relative performance for each ad set
            for _, adset in campaign_adsets.iterrows():
                # Skip ad sets with insufficient data
                if adset['impressions'] < self.min_data_threshold / 2:  # Lower threshold for ad sets
                    continue
                
                adset_id = adset['adset_id']
                adset_name = adset.get('name', f"Ad Set {adset_id}")
                
                # Calculate efficiency metrics
                efficiency_metrics = {
                    'campaign_id': campaign_id,
                    'campaign_name': campaign_name,
                    'adset_id': adset_id,
                    'adset_name': adset_name,
                    'spend': adset['spend'],
                    'impressions': adset['impressions'],
                    'clicks': adset['clicks'],
                    'conversions': adset['conversions'] if 'conversions' in adset else 0,
                    'ctr': adset['ctr'],
                    'cpm': adset['cpm'],
                    'cpc': adset['cpc'],
                    'ctr_index': (adset['ctr'] / avg_metrics['ctr']) * 100 if avg_metrics['ctr'] > 0 else 0,
                    'cpm_index': (avg_metrics['cpm'] / adset['cpm']) * 100 if adset['cpm'] > 0 else 0,
                    'cpc_index': (avg_metrics['cpc'] / adset['cpc']) * 100 if adset['cpc'] > 0 else 0
                }
                
                # Add conversion metrics if available
                if 'conversion_rate' in adset and avg_metrics['conversion_rate'] is not None:
                    efficiency_metrics['conversion_rate'] = adset['conversion_rate']
                    efficiency_metrics['cpa'] = adset['cpa'] if 'cpa' in adset else None
                    
                    if avg_metrics['conversion_rate'] > 0:
                        efficiency_metrics['conversion_rate_index'] = (adset['conversion_rate'] / avg_metrics['conversion_rate']) * 100
                    else:
                        efficiency_metrics['conversion_rate_index'] = 0
                        
                    if 'cpa' in adset and avg_metrics['cpa'] is not None and adset['cpa'] > 0:
                        efficiency_metrics['cpa_index'] = (avg_metrics['cpa'] / adset['cpa']) * 100
                    else:
                        efficiency_metrics['cpa_index'] = 0
                
                # Calculate overall efficiency score (0-100)
                efficiency_score = self._calculate_efficiency_score(efficiency_metrics)
                efficiency_metrics['efficiency_score'] = efficiency_score
                
                # Add to metrics
                results['metrics'].append(efficiency_metrics)
                
                # Generate recommendations for inefficient ad sets
                if efficiency_score < 30:  # Very inefficient
                    severity = "high"
                    potential_savings = adset['spend'] * 0.5  # 50% of spend could be reallocated
                    
                    # Determine main issue
                    main_issue = self._identify_main_issue(efficiency_metrics)
                    
                    recommendation = {
                        'type': 'adset_budget_inefficiency',
                        'campaign_id': campaign_id,
                        'campaign_name': campaign_name,
                        'adset_id': adset_id,
                        'adset_name': adset_name,
                        'efficiency_score': efficiency_score,
                        'main_issue': main_issue,
                        'severity': severity,
                        'potential_savings': potential_savings,
                        'recommendation': (
                            f"Ad set '{adset_name}' in campaign '{campaign_name}' is performing very poorly "
                            f"(score: {efficiency_score:.0f}/100) with {main_issue}. Consider pausing this ad set "
                            f"and reallocating its budget to better-performing ad sets in this campaign."
                        )
                    }
                    results['recommendations'].append(recommendation)
                    
                elif efficiency_score < 50:  # Moderately inefficient
                    severity = "medium"
                    potential_savings = adset['spend'] * 0.25  # 25% of spend
                    
                    # Determine main issue
                    main_issue = self._identify_main_issue(efficiency_metrics)
                    
                    recommendation = {
                        'type': 'adset_budget_inefficiency',
                        'campaign_id': campaign_id,
                        'campaign_name': campaign_name,
                        'adset_id': adset_id,
                        'adset_name': adset_name,
                        'efficiency_score': efficiency_score,
                        'main_issue': main_issue,
                        'severity': severity,
                        'potential_savings': potential_savings,
                        'recommendation': (
                            f"Ad set '{adset_name}' in campaign '{campaign_name}' is underperforming "
                            f"(score: {efficiency_score:.0f}/100) with {main_issue}. Consider reducing its budget "
                            f"by 25% or refining its audience targeting."
                        )
                    }
                    results['recommendations'].append(recommendation)
        
        return results
    
    def _analyze_ads(self, ads_df):
        """
        Analyze ad-level performance efficiency.
        
        Args:
            ads_df (DataFrame): Ad data with performance metrics
            
        Returns:
            dict: Ad efficiency analysis and recommendations
        """
        if ads_df.empty:
            return None
        
        results = {
            'metrics': [],
            'recommendations': []
        }
        
        # Group by ad set to compare ads within the same ad set
        if 'adset_id' in ads_df.columns:
            group_col = 'adset_id'
            group_name_col = 'adset_name'
        else:
            # Fall back to campaign grouping if ad set info not available
            group_col = 'campaign_id'
            group_name_col = 'campaign_name'
        
        group_by = ads_df.groupby(group_col)
        
        for group_id, group_ads in group_by:
            # Skip groups with only one ad
            if len(group_ads) < 2:
                continue
            
            group_name = group_ads[group_name_col].iloc[0] if group_name_col in group_ads.columns else f"Group {group_id}"
            
            # Calculate average metrics for this group
            avg_metrics = {
                'ctr': group_ads['ctr'].mean(),
                'cpm': group_ads['cpm'].mean(),
                'cpc': group_ads['cpc'].mean(),
                'conversion_rate': group_ads['conversion_rate'].mean() if 'conversion_rate' in group_ads.columns else None,
                'cpa': group_ads['cpa'].mean() if 'cpa' in group_ads.columns else None
            }
            
            # Find the best performing ad in this group (by conversion rate or CTR)
            if 'conversion_rate' in group_ads.columns and not group_ads['conversion_rate'].isna().all():
                best_ad_idx = group_ads['conversion_rate'].idxmax()
            else:
                best_ad_idx = group_ads['ctr'].idxmax()
                
            best_ad = group_ads.loc[best_ad_idx]
            best_ad_id = best_ad['ad_id']
            best_ad_name = best_ad.get('name', f"Ad {best_ad_id}")
            
            # Calculate relative performance for each ad
            for _, ad in group_ads.iterrows():
                # Skip ads with insufficient data
                if ad['impressions'] < self.min_data_threshold / 4:  # Even lower threshold for ads
                    continue
                
                ad_id = ad['ad_id']
                ad_name = ad.get('name', f"Ad {ad_id}")
                
                # Calculate efficiency metrics relative to group average
                efficiency_metrics = {
                    'group_id': group_id,
                    'group_name': group_name,
                    'ad_id': ad_id,
                    'ad_name': ad_name,
                    'spend': ad['spend'],
                    'impressions': ad['impressions'],
                    'clicks': ad['clicks'],
                    'conversions': ad['conversions'] if 'conversions' in ad else 0,
                    'ctr': ad['ctr'],
                    'cpm': ad['cpm'],
                    'cpc': ad['cpc'],
                    'ctr_index': (ad['ctr'] / avg_metrics['ctr']) * 100 if avg_metrics['ctr'] > 0 else 0,
                    'cpm_index': (avg_metrics['cpm'] / ad['cpm']) * 100 if ad['cpm'] > 0 else 0,
                    'cpc_index': (avg_metrics['cpc'] / ad['cpc']) * 100 if ad['cpc'] > 0 else 0
                }
                
                # Add conversion metrics if available
                if 'conversion_rate' in ad and avg_metrics['conversion_rate'] is not None:
                    efficiency_metrics['conversion_rate'] = ad['conversion_rate']
                    efficiency_metrics['cpa'] = ad['cpa'] if 'cpa' in ad else None
                    
                    if avg_metrics['conversion_rate'] > 0:
                        efficiency_metrics['conversion_rate_index'] = (ad['conversion_rate'] / avg_metrics['conversion_rate']) * 100
                    else:
                        efficiency_metrics['conversion_rate_index'] = 0
                        
                    if 'cpa' in ad and avg_metrics['cpa'] is not None and ad['cpa'] > 0:
                        efficiency_metrics['cpa_index'] = (avg_metrics['cpa'] / ad['cpa']) * 100
                    else:
                        efficiency_metrics['cpa_index'] = 0
                
                # Calculate overall efficiency score (0-100)
                efficiency_score = self._calculate_efficiency_score(efficiency_metrics)
                efficiency_metrics['efficiency_score'] = efficiency_score
                
                # Calculate comparison to best performing ad
                if 'conversion_rate' in ad and 'conversion_rate' in best_ad:
                    best_cr = best_ad['conversion_rate']
                    ad_cr = ad['conversion_rate']
                    if best_cr > 0 and ad_cr > 0:
                        cr_vs_best = (ad_cr / best_cr) * 100
                    else:
                        cr_vs_best = 0
                    efficiency_metrics['conversion_rate_vs_best'] = cr_vs_best
                
                # Add to metrics
                results['metrics'].append(efficiency_metrics)
                
                # Skip recommendations for the best performing ad
                if ad_id == best_ad_id:
                    continue
                
                # Generate recommendations for inefficient ads
                if efficiency_score < 30 and ad['spend'] >= self.min_adset_spend / 4:
                    severity = "high"
                    potential_savings = ad['spend'] * 0.9  # 90% of spend could be saved
                    
                    recommendation = {
                        'type': 'ad_performance_inefficiency',
                        'group_id': group_id,
                        'group_name': group_name,
                        'ad_id': ad_id,
                        'ad_name': ad_name,
                        'best_ad_id': best_ad_id,
                        'best_ad_name': best_ad_name,
                        'efficiency_score': efficiency_score,
                        'severity': severity,
                        'potential_savings': potential_savings,
                        'recommendation': (
                            f"Ad '{ad_name}' in {group_name_col} '{group_name}' is performing very poorly "
                            f"(score: {efficiency_score:.0f}/100). Pause this ad and reallocate its impressions "
                            f"to the better-performing ad '{best_ad_name}'."
                        )
                    }
                    results['recommendations'].append(recommendation)
                    
                elif efficiency_score < 50 and ad['spend'] >= self.min_adset_spend / 4:
                    severity = "medium"
                    potential_savings = ad['spend'] * 0.5  # 50% of spend
                    
                    recommendation = {
                        'type': 'ad_performance_inefficiency',
                        'group_id': group_id,
                        'group_name': group_name,
                        'ad_id': ad_id,
                        'ad_name': ad_name,
                        'best_ad_id': best_ad_id,
                        'best_ad_name': best_ad_name,
                        'efficiency_score': efficiency_score,
                        'severity': severity,
                        'potential_savings': potential_savings,
                        'recommendation': (
                            f"Ad '{ad_name}' in {group_name_col} '{group_name}' is significantly underperforming "
                            f"(score: {efficiency_score:.0f}/100). Consider reducing its budget and testing new creative "
                            f"variations based on the better-performing ad '{best_ad_name}'."
                        )
                    }
                    results['recommendations'].append(recommendation)
        
        return results
    
    def _analyze_budget_allocation(self, data):
        """
        Analyze budget allocation efficiency across the account.
        
        Args:
            data (dict): Prepared data including campaigns, ad sets, and ads
            
        Returns:
            dict: Budget allocation analysis and recommendations
        """
        results = {
            'distribution': {},
            'recommendations': []
        }
        
        campaigns_df = data['campaigns']
        if campaigns_df.empty:
            return results
        
        # Calculate total account spend
        total_spend = campaigns_df['spend'].sum()
        if total_spend == 0:
            return results
        
        # Calculate spend distribution by performance
        campaigns_df['spend_pct'] = (campaigns_df['spend'] / total_spend) * 100
        
        # Sort campaigns by efficiency (using CPA, conversion rate or CTR)
        if 'cpa' in campaigns_df.columns and not campaigns_df['cpa'].isna().all():
            # For CPA, lower is better so sort ascending
            campaigns_df = campaigns_df.sort_values('cpa')
            perf_metric = 'cpa'
            better_is_lower = True
        elif 'conversion_rate' in campaigns_df.columns and not campaigns_df['conversion_rate'].isna().all():
            # For conversion rate, higher is better so sort descending
            campaigns_df = campaigns_df.sort_values('conversion_rate', ascending=False)
            perf_metric = 'conversion_rate'
            better_is_lower = False
        else:
            # Fallback to CTR
            campaigns_df = campaigns_df.sort_values('ctr', ascending=False)
            perf_metric = 'ctr'
            better_is_lower = False
        
        # Calculate cumulative spend percentage
        campaigns_df['cumulative_spend_pct'] = campaigns_df['spend_pct'].cumsum()
        
        # Split into quartiles
        quartile_spend = {}
        
        # Top 25% of campaigns by performance
        top_25 = campaigns_df[campaigns_df['cumulative_spend_pct'] <= 25]
        quartile_spend['top_25'] = {
            'spend': top_25['spend'].sum(),
            'spend_pct': (top_25['spend'].sum() / total_spend) * 100,
            'campaign_count': len(top_25)
        }
        
        # Mid-high 25-50% of campaigns
        mid_high = campaigns_df[(campaigns_df['cumulative_spend_pct'] > 25) & 
                               (campaigns_df['cumulative_spend_pct'] <= 50)]
        quartile_spend['mid_high'] = {
            'spend': mid_high['spend'].sum(),
            'spend_pct': (mid_high['spend'].sum() / total_spend) * 100,
            'campaign_count': len(mid_high)
        }
        
        # Mid-low 50-75% of campaigns
        mid_low = campaigns_df[(campaigns_df['cumulative_spend_pct'] > 50) & 
                              (campaigns_df['cumulative_spend_pct'] <= 75)]
        quartile_spend['mid_low'] = {
            'spend': mid_low['spend'].sum(),
            'spend_pct': (mid_low['spend'].sum() / total_spend) * 100,
            'campaign_count': len(mid_low)
        }
        
        # Bottom 25% of campaigns
        bottom_25 = campaigns_df[campaigns_df['cumulative_spend_pct'] > 75]
        quartile_spend['bottom_25'] = {
            'spend': bottom_25['spend'].sum(),
            'spend_pct': (bottom_25['spend'].sum() / total_spend) * 100,
            'campaign_count': len(bottom_25)
        }
        
        results['distribution'] = {
            'total_spend': total_spend,
            'performance_metric': perf_metric,
            'quartiles': quartile_spend
        }
        
        # Check for allocation inefficiency
        bottom_spend_pct = quartile_spend['bottom_25']['spend_pct']
        top_spend_pct = quartile_spend['top_25']['spend_pct']
        
        if bottom_spend_pct > top_spend_pct * 1.5:
            # Significant overspend on bottom performers
            severity = "high"
            potential_savings = bottom_25['spend'].sum() * 0.5  # 50% of bottom quartile spend
            
            if better_is_lower:
                metric_desc = f"highest {perf_metric}"
            else:
                metric_desc = f"lowest {perf_metric}"
            
            recommendation = {
                'type': 'budget_allocation_imbalance',
                'performance_metric': perf_metric,
                'bottom_spend_pct': bottom_spend_pct,
                'top_spend_pct': top_spend_pct,
                'severity': severity,
                'potential_savings': potential_savings,
                'recommendation': (
                    f"Budget allocation is inefficient with {bottom_spend_pct:.1f}% of spend on the worst-performing campaigns "
                    f"(with {metric_desc}) versus only {top_spend_pct:.1f}% on the best-performing campaigns. "
                    f"Consider reallocating at least 50% of the budget from the bottom quartile campaigns to the top performers."
                )
            }
            results['recommendations'].append(recommendation)
            
        elif bottom_spend_pct > top_spend_pct * 1.2:
            # Moderate overspend on bottom performers
            severity = "medium"
            potential_savings = bottom_25['spend'].sum() * 0.3  # 30% of bottom quartile spend
            
            if better_is_lower:
                metric_desc = f"higher {perf_metric}"
            else:
                metric_desc = f"lower {perf_metric}"
            
            recommendation = {
                'type': 'budget_allocation_imbalance',
                'performance_metric': perf_metric,
                'bottom_spend_pct': bottom_spend_pct,
                'top_spend_pct': top_spend_pct,
                'severity': severity,
                'potential_savings': potential_savings,
                'recommendation': (
                    f"Budget allocation could be improved with {bottom_spend_pct:.1f}% of spend on lower-performing campaigns "
                    f"versus {top_spend_pct:.1f}% on the top performers. Consider shifting 30% of budget from the bottom quartile "
                    f"campaigns to those with {metric_desc}."
                )
            }
            results['recommendations'].append(recommendation)
        
        return results
    
    def _calculate_efficiency_score(self, metrics):
        """
        Calculate an overall efficiency score from 0-100.
        
        Args:
            metrics (dict): Performance metrics for the entity
            
        Returns:
            float: Efficiency score (0-100)
        """
        # Weights for different metrics
        weights = {
            'ctr_index': 0.15,
            'cpm_index': 0.15,
            'cpc_index': 0.2,
            'conversion_rate_index': 0.25,
            'cpa_index': 0.25
        }
        
        # Start with base score
        score = 50.0
        weight_sum = 0
        
        # Add weighted components
        for metric, weight in weights.items():
            if metric in metrics and not pd.isna(metrics[metric]) and metrics[metric] > 0:
                # For indices, 100 is the baseline (average performance)
                # We want to reward above average and penalize below average
                metric_score = metrics[metric]
                
                # Cap extreme values to avoid oversized impact
                if metric_score > 200:
                    metric_score = 200
                    
                # Convert to 0-100 scale
                if metric == 'cpa_index':
                    # For CPA, lower is better, so the score is already properly scaled
                    pass
                else:
                    # For other metrics, higher is better, but we want 100 to be baseline
                    metric_score = (metric_score / 2) + 50
                
                score += (metric_score - 50) * weight
                weight_sum += weight
        
        # If we didn't have enough metrics, adjust the base score
        if weight_sum < 0.5:
            # Not enough data for a reliable score, revert closer to baseline
            score = score * (weight_sum * 2) + 50 * (1 - (weight_sum * 2))
        
        # Ensure score is within 0-100 range
        score = max(0, min(100, score))
        
        return score
    
    def _identify_main_issue(self, metrics):
        """
        Identify the main performance issue for an entity.
        
        Args:
            metrics (dict): Performance metrics
            
        Returns:
            str: Description of the main issue
        """
        issues = []
        
        # Check CTR
        if 'ctr_index' in metrics and metrics['ctr_index'] < 70:
            issues.append(f"low CTR ({metrics['ctr']:.2f}% vs. average)")
        
        # Check CPM
        if 'cpm_index' in metrics and metrics['cpm_index'] < 70:
            issues.append(f"high CPM (${metrics['cpm']:.2f} vs. average)")
        
        # Check CPC
        if 'cpc_index' in metrics and metrics['cpc_index'] < 70:
            issues.append(f"high CPC (${metrics['cpc']:.2f} vs. average)")
        
        # Check conversion rate
        if 'conversion_rate_index' in metrics and metrics['conversion_rate_index'] < 70:
            issues.append(f"low conversion rate ({metrics['conversion_rate']:.2f}% vs. average)")
        
        # Check CPA
        if 'cpa_index' in metrics and metrics['cpa_index'] < 70:
            issues.append(f"high CPA (${metrics['cpa']:.2f} vs. average)")
        
        if not issues:
            return "overall performance below average"
        elif len(issues) == 1:
            return issues[0]
        else:
            # Return the first two issues
            return f"{issues[0]} and {issues[1]}"