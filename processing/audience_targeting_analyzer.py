import pandas as pd
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)

class AudienceTargetingAnalyzer:
    """
    Advanced audience targeting analysis using statistical methods to identify
    significant performance differences across audience segments.
    """
    
    def __init__(self, min_segment_size=100, confidence_level=0.95):
        """
        Initialize the audience targeting analyzer.
        
        Args:
            min_segment_size (int): Minimum number of impressions for a segment to be analyzed
            confidence_level (float): Statistical confidence level for significance testing
        """
        self.min_segment_size = min_segment_size
        self.confidence_level = confidence_level
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, insights_df):
        """
        Analyze audience targeting performance across different segments.
        
        Args:
            insights_df (DataFrame): Ad insights data with segment breakdowns
            
        Returns:
            dict: Analysis results with segment insights and recommendations
        """
        if insights_df.empty:
            return {'recommendations': [], 'segments': {}}
        
        results = {
            'recommendations': [],
            'segments': {}
        }
        
        # Analyze each type of segmentation if data is available
        segment_types = self._identify_segment_columns(insights_df)
        
        self.logger.info(f"Analyzing audience segments: {segment_types}")
        
        # Preprocess data
        processed_df = self._preprocess_data(insights_df)
        
        # Analyze each segment type
        for segment_type in segment_types:
            segment_results = self._analyze_segment_type(
                processed_df, segment_type)
            
            if segment_results:
                results['segments'][segment_type] = segment_results
                
                # Add recommendations if there are significant findings
                if segment_results.get('significant_findings', False):
                    recommendations = self._generate_recommendations(
                        segment_type, segment_results)
                    results['recommendations'].extend(recommendations)
        
        # Cross-segment analysis (e.g., age + gender combinations)
        if len(segment_types) >= 2 and 'age' in segment_types and 'gender' in segment_types:
            cross_segment_results = self._analyze_cross_segments(
                processed_df, ['age', 'gender'])
                
            if cross_segment_results:
                results['segments']['age_gender'] = cross_segment_results
                
                # Add cross-segment recommendations
                if cross_segment_results.get('significant_findings', False):
                    recommendations = self._generate_cross_segment_recommendations(
                        cross_segment_results)
                    results['recommendations'].extend(recommendations)
        
        return results
    
    def _identify_segment_columns(self, df):
        """
        Identify segment breakdown columns in the dataset.
        
        Args:
            df (DataFrame): The insights data
            
        Returns:
            list: List of segment column names
        """
        potential_segments = ['age', 'gender', 'device', 'platform', 'placement', 'region', 
                              'country', 'device_platform']
        
        # Find which potential segments are in the dataframe
        available_segments = [col for col in potential_segments if col in df.columns]
        
        # Verify segments have multiple values
        valid_segments = []
        for segment in available_segments:
            unique_values = df[segment].nunique()
            if unique_values > 1:
                valid_segments.append(segment)
        
        return valid_segments
    
    def _preprocess_data(self, df):
        """
        Preprocess the insights data for analysis.
        
        Args:
            df (DataFrame): Raw insights data
            
        Returns:
            DataFrame: Processed data
        """
        # Create a copy to avoid modifying the original
        processed_df = df.copy()
        
        # Calculate metrics that might not exist
        if 'ctr' not in processed_df.columns and 'clicks' in processed_df.columns and 'impressions' in processed_df.columns:
            processed_df['ctr'] = (processed_df['clicks'] / processed_df['impressions']) * 100
        
        if 'conversion_rate' not in processed_df.columns:
            # Check for different names of conversion columns
            conv_col = None
            for col in ['conversions', 'purchases', 'total_conversions']:
                if col in processed_df.columns:
                    conv_col = col
                    break
            
            if conv_col and 'clicks' in processed_df.columns:
                processed_df['conversion_rate'] = (processed_df[conv_col] / processed_df['clicks']) * 100
        
        if 'cpa' not in processed_df.columns:
            # Check for conversion column
            conv_col = None
            for col in ['conversions', 'purchases', 'total_conversions']:
                if col in processed_df.columns:
                    conv_col = col
                    break
            
            if conv_col and 'spend' in processed_df.columns:
                # Avoid division by zero
                processed_df['cpa'] = processed_df['spend'] / processed_df[conv_col].replace(0, np.nan)
        
        if 'cpc' not in processed_df.columns and 'spend' in processed_df.columns and 'clicks' in processed_df.columns:
            processed_df['cpc'] = processed_df['spend'] / processed_df['clicks'].replace(0, np.nan)
        
        # Handle missing values and convert data types
        numeric_cols = ['impressions', 'clicks', 'spend', 'ctr', 'conversion_rate', 'cpc', 'cpa']
        for col in numeric_cols:
            if col in processed_df.columns:
                processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
        
        return processed_df
    
    def _analyze_segment_type(self, df, segment_type):
        """
        Analyze performance differences across a specific segment type.
        
        Args:
            df (DataFrame): Processed insights data
            segment_type (str): Segment column name (e.g., 'age', 'gender')
            
        Returns:
            dict: Segment analysis results
        """
        # Group by segment
        segment_metrics = df.groupby(segment_type).agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'spend': 'sum'
        }).reset_index()
        
        # Filter for minimum segment size
        segment_metrics = segment_metrics[segment_metrics['impressions'] >= self.min_segment_size]
        
        if segment_metrics.empty or len(segment_metrics) < 2:
            return None  # Not enough data for comparison
        
        # Calculate derived metrics
        segment_metrics['ctr'] = (segment_metrics['clicks'] / segment_metrics['impressions']) * 100
        
        # Check for conversion data
        conv_col = None
        for col in ['conversions', 'purchases', 'total_conversions']:
            if col in df.columns:
                conv_col = col
                break
        
        if conv_col:
            # Add conversion metrics
            conversion_agg = df.groupby(segment_type)[conv_col].sum().reset_index()
            segment_metrics = segment_metrics.merge(conversion_agg, on=segment_type)
            
            # Calculate conversion rate and CPA
            segment_metrics['conversion_rate'] = (segment_metrics[conv_col] / segment_metrics['clicks']) * 100
            segment_metrics['cpa'] = segment_metrics['spend'] / segment_metrics[conv_col].replace(0, np.nan)
        
        # Calculate CPM and CPC
        segment_metrics['cpm'] = (segment_metrics['spend'] / segment_metrics['impressions']) * 1000
        segment_metrics['cpc'] = segment_metrics['spend'] / segment_metrics['clicks']
        
        # Calculate relative performance metrics
        avg_ctr = segment_metrics['clicks'].sum() / segment_metrics['impressions'].sum() * 100
        segment_metrics['ctr_index'] = segment_metrics['ctr'] / avg_ctr * 100
        
        if conv_col:
            avg_conv_rate = segment_metrics[conv_col].sum() / segment_metrics['clicks'].sum() * 100
            segment_metrics['conversion_rate_index'] = segment_metrics['conversion_rate'] / avg_conv_rate * 100
            
            avg_cpa = segment_metrics['spend'].sum() / segment_metrics[conv_col].sum()
            segment_metrics['cpa_index'] = avg_cpa / segment_metrics['cpa'].replace(0, np.nan) * 100
        
        # Statistical significance testing
        segment_stats = self._calculate_segment_significance(df, segment_type, segment_metrics)
        
        # Identify best and worst performers
        performance_metrics = ['ctr', 'conversion_rate', 'cpa'] if conv_col else ['ctr']
        best_worst = self._identify_best_worst_segments(segment_metrics, performance_metrics)
        
        # Format results
        results = {
            'segment_metrics': segment_metrics.to_dict('records'),
            'segment_stats': segment_stats,
            'best_worst': best_worst,
            'significant_findings': any(stat['is_significant'] for stat in segment_stats),
            'metrics_analyzed': performance_metrics
        }
        
        return results
    
    def _calculate_segment_significance(self, df, segment_type, segment_metrics):
        """
        Calculate statistical significance of performance differences between segments.
        
        Args:
            df (DataFrame): Original insights data
            segment_type (str): Segment column name
            segment_metrics (DataFrame): Aggregated segment metrics
            
        Returns:
            list: Statistical significance results
        """
        segment_stats = []
        
        # Get overall average metrics for reference
        overall_ctr = df['clicks'].sum() / df['impressions'].sum() * 100
        
        # Check if we have conversion data
        has_conversion_data = any(col in df.columns for col in ['conversions', 'purchases', 'total_conversions'])
        
        # Perform z-test for each segment against overall average
        for _, segment in segment_metrics.iterrows():
            segment_value = segment[segment_type]
            
            # CTR significance test
            segment_ctr = segment['ctr']
            segment_impressions = segment['impressions']
            segment_clicks = segment['clicks']
            
            # Calculate standard error and z-score for CTR
            # Using normal approximation to binomial
            se_ctr = np.sqrt((overall_ctr/100 * (1 - overall_ctr/100)) / segment_impressions)
            if se_ctr > 0:
                z_score_ctr = (segment_ctr - overall_ctr) / (se_ctr * 100)
                p_value_ctr = 2 * (1 - stats.norm.cdf(abs(z_score_ctr)))  # Two-tailed test
            else:
                z_score_ctr = 0
                p_value_ctr = 1
            
            # Determine if statistically significant
            is_significant_ctr = p_value_ctr < (1 - self.confidence_level)
            
            stat_result = {
                'segment_type': segment_type,
                'segment_value': segment_value,
                'metric': 'ctr',
                'segment_metric': segment_ctr,
                'overall_metric': overall_ctr,
                'difference_pct': ((segment_ctr - overall_ctr) / overall_ctr) * 100,
                'z_score': z_score_ctr,
                'p_value': p_value_ctr,
                'is_significant': is_significant_ctr
            }
            segment_stats.append(stat_result)
            
            # Conversion rate significance test if data is available
            if has_conversion_data:
                conv_col = next((col for col in ['conversions', 'purchases', 'total_conversions'] 
                               if col in df.columns), None)
                if conv_col and 'conversion_rate' in segment:
                    # Get overall conversion rate
                    overall_conv_rate = df[conv_col].sum() / df['clicks'].sum() * 100
                    
                    segment_conv_rate = segment['conversion_rate']
                    segment_conversions = segment[conv_col]
                    
                    # Calculate standard error and z-score for conversion rate
                    if segment_clicks > 0:
                        se_conv = np.sqrt((overall_conv_rate/100 * (1 - overall_conv_rate/100)) / segment_clicks)
                        if se_conv > 0:
                            z_score_conv = (segment_conv_rate - overall_conv_rate) / (se_conv * 100)
                            p_value_conv = 2 * (1 - stats.norm.cdf(abs(z_score_conv)))
                        else:
                            z_score_conv = 0
                            p_value_conv = 1
                        
                        # Determine if statistically significant
                        is_significant_conv = p_value_conv < (1 - self.confidence_level)
                        
                        conv_stat_result = {
                            'segment_type': segment_type,
                            'segment_value': segment_value,
                            'metric': 'conversion_rate',
                            'segment_metric': segment_conv_rate,
                            'overall_metric': overall_conv_rate,
                            'difference_pct': ((segment_conv_rate - overall_conv_rate) / overall_conv_rate) * 100,
                            'z_score': z_score_conv,
                            'p_value': p_value_conv,
                            'is_significant': is_significant_conv
                        }
                        segment_stats.append(conv_stat_result)
        
        return segment_stats
    
    def _identify_best_worst_segments(self, segment_metrics, metrics):
        """
        Identify best and worst performing segments for each metric.
        
        Args:
            segment_metrics (DataFrame): Segment performance metrics
            metrics (list): List of metrics to analyze
            
        Returns:
            dict: Best and worst performers for each metric
        """
        best_worst = {}
        
        for metric in metrics:
            if metric not in segment_metrics.columns:
                continue
                
            # For CTR and conversion_rate, higher is better
            if metric in ['ctr', 'conversion_rate']:
                best = segment_metrics.nlargest(1, metric)
                worst = segment_metrics.nsmallest(1, metric)
            # For CPA, lower is better
            elif metric == 'cpa':
                # Filter out zero values and infinities
                valid_segments = segment_metrics[segment_metrics[metric] > 0]
                if valid_segments.empty:
                    continue
                best = valid_segments.nsmallest(1, metric)
                worst = valid_segments.nlargest(1, metric)
            else:
                continue
            
            segment_type = segment_metrics.columns[0]  # First column should be the segment type
            
            best_worst[metric] = {
                'best': {
                    'segment': best[segment_type].iloc[0],
                    'value': best[metric].iloc[0],
                    'spend': best['spend'].iloc[0],
                    'impressions': best['impressions'].iloc[0]
                },
                'worst': {
                    'segment': worst[segment_type].iloc[0],
                    'value': worst[metric].iloc[0],
                    'spend': worst['spend'].iloc[0],
                    'impressions': worst['impressions'].iloc[0]
                },
                'difference_pct': abs((best[metric].iloc[0] - worst[metric].iloc[0]) / worst[metric].iloc[0] * 100)
                if worst[metric].iloc[0] != 0 else float('inf')
            }
        
        return best_worst
    
    def _analyze_cross_segments(self, df, segment_types):
        """
        Analyze performance across combined segments (e.g., age + gender).
        
        Args:
            df (DataFrame): Processed insights data
            segment_types (list): List of segment columns to combine
            
        Returns:
            dict: Cross-segment analysis results
        """
        if not all(segment in df.columns for segment in segment_types):
            return None
        
        # Group by multiple segment dimensions
        cross_segment_metrics = df.groupby(segment_types).agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'spend': 'sum'
        }).reset_index()
        
        # Filter for minimum segment size
        cross_segment_metrics = cross_segment_metrics[
            cross_segment_metrics['impressions'] >= self.min_segment_size]
        
        if cross_segment_metrics.empty or len(cross_segment_metrics) < 2:
            return None  # Not enough data
        
        # Calculate derived metrics
        cross_segment_metrics['ctr'] = (cross_segment_metrics['clicks'] / 
                                       cross_segment_metrics['impressions']) * 100
        
        # Check for conversion data
        conv_col = None
        for col in ['conversions', 'purchases', 'total_conversions']:
            if col in df.columns:
                conv_col = col
                break
        
        if conv_col:
            # Add conversion metrics
            conversion_agg = df.groupby(segment_types)[conv_col].sum().reset_index()
            cross_segment_metrics = cross_segment_metrics.merge(conversion_agg, on=segment_types)
            
            # Calculate conversion rate and CPA
            cross_segment_metrics['conversion_rate'] = (
                cross_segment_metrics[conv_col] / cross_segment_metrics['clicks']) * 100
            cross_segment_metrics['cpa'] = (
                cross_segment_metrics['spend'] / cross_segment_metrics[conv_col].replace(0, np.nan))
        
        # Identify top and bottom performers
        performance_metrics = ['ctr', 'conversion_rate'] if conv_col else ['ctr']
        
        results = {
            'cross_segment_metrics': cross_segment_metrics.to_dict('records'),
            'significant_findings': False,
            'top_segments': {},
            'bottom_segments': {}
        }
        
        # Find top and bottom segments
        for metric in performance_metrics:
            if metric not in cross_segment_metrics.columns:
                continue
                
            # Sort and get top/bottom segments
            if metric in ['ctr', 'conversion_rate']:
                top_segments = cross_segment_metrics.nlargest(3, metric)
                bottom_segments = cross_segment_metrics.nsmallest(3, metric)
            elif metric == 'cpa':
                valid_segments = cross_segment_metrics[cross_segment_metrics[metric] > 0]
                if valid_segments.empty:
                    continue
                top_segments = valid_segments.nsmallest(3, metric)
                bottom_segments = valid_segments.nlargest(3, metric)
                
            # Store top and bottom segments
            results['top_segments'][metric] = top_segments.to_dict('records')
            results['bottom_segments'][metric] = bottom_segments.to_dict('records')
            
            # Calculate percent difference between best and worst
            if not top_segments.empty and not bottom_segments.empty:
                best_value = top_segments[metric].iloc[0]
                worst_value = bottom_segments[metric].iloc[0]
                
                if worst_value != 0:
                    diff_pct = abs((best_value - worst_value) / worst_value * 100)
                    
                    # Mark as significant if the difference is substantial
                    if diff_pct > 50:  # 50% difference threshold
                        results['significant_findings'] = True
        
        return results
    
    def _generate_recommendations(self, segment_type, segment_results):
        """
        Generate actionable recommendations based on segment analysis.
        
        Args:
            segment_type (str): Type of segment analyzed (e.g., 'age', 'gender')
            segment_results (dict): Results of segment analysis
            
        Returns:
            list: Recommendations based on analysis
        """
        recommendations = []
        
        if not segment_results.get('significant_findings', False):
            return recommendations
        
        # Get best and worst performers
        best_worst = segment_results.get('best_worst', {})
        
        for metric, results in best_worst.items():
            # Skip if difference is too small
            if results.get('difference_pct', 0) < 30:  # Require at least 30% difference
                continue
            
            best_segment = results['best']['segment']
            worst_segment = results['worst']['segment']
            best_value = results['best']['value']
            worst_value = results['worst']['value']
            difference_pct = results['difference_pct']
            
            # Format metric value based on metric type
            if metric == 'ctr' or metric == 'conversion_rate':
                best_formatted = f"{best_value:.2f}%"
                worst_formatted = f"{worst_value:.2f}%"
            elif metric == 'cpa':
                best_formatted = f"${best_value:.2f}"
                worst_formatted = f"${worst_value:.2f}"
            else:
                best_formatted = f"{best_value:.2f}"
                worst_formatted = f"{worst_value:.2f}"
            
            # Tailor recommendation based on metric
            recommendation_text = ""
            action = ""
            severity = "medium"
            
            if metric == 'ctr':
                recommendation_text = (
                    f"The {segment_type} segment '{best_segment}' has a CTR of {best_formatted}, "
                    f"which is {difference_pct:.1f}% higher than '{worst_segment}' at {worst_formatted}."
                )
                
                if difference_pct > 100:  # More than double the performance
                    severity = "high"
                    action = (
                        f"Consider reallocating budget from '{worst_segment}' to '{best_segment}' "
                        f"or creating specific creatives for the underperforming segment."
                    )
                else:
                    action = (
                        f"Test different ad creatives for the '{worst_segment}' segment to improve engagement."
                    )
                    
            elif metric == 'conversion_rate':
                recommendation_text = (
                    f"The {segment_type} segment '{best_segment}' has a conversion rate of {best_formatted}, "
                    f"which is {difference_pct:.1f}% higher than '{worst_segment}' at {worst_formatted}."
                )
                
                if difference_pct > 100:  # More than double the performance
                    severity = "high"
                    action = (
                        f"Significantly increase budget allocation to the '{best_segment}' segment "
                        f"and consider creating a separate campaign specifically for this audience."
                    )
                else:
                    action = (
                        f"Review landing page and conversion funnel for the '{worst_segment}' segment "
                        f"to identify and address potential friction points."
                    )
                    
            elif metric == 'cpa':
                recommendation_text = (
                    f"The {segment_type} segment '{best_segment}' has a CPA of {best_formatted}, "
                    f"which is {difference_pct:.1f}% lower than '{worst_segment}' at {worst_formatted}."
                )
                
                if difference_pct > 100:  # More than double the efficiency
                    severity = "high"
                    action = (
                        f"Reduce budget for the '{worst_segment}' segment and reallocate to '{best_segment}' "
                        f"to improve overall campaign efficiency."
                    )
                else:
                    action = (
                        f"Review bidding strategy and targeting settings for the '{worst_segment}' segment "
                        f"to improve cost efficiency."
                    )
            
            # Create recommendation object
            recommendation = {
                'type': f"{segment_type}_{metric}_optimization",
                'segment_type': segment_type,
                'best_segment': best_segment,
                'worst_segment': worst_segment,
                'metric': metric,
                'best_value': best_value,
                'worst_value': worst_value,
                'difference_pct': difference_pct,
                'recommendation': f"{recommendation_text} {action}",
                'severity': severity,
                'potential_savings': self._estimate_potential_savings(
                    results['worst']['spend'], difference_pct)
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_cross_segment_recommendations(self, cross_segment_results):
        """
        Generate actionable recommendations based on cross-segment analysis.
        
        Args:
            cross_segment_results (dict): Results of cross-segment analysis
            
        Returns:
            list: Recommendations for cross-segment optimizations
        """
        recommendations = []
        
        if not cross_segment_results.get('significant_findings', False):
            return recommendations
        
        for metric in ['ctr', 'conversion_rate', 'cpa']:
            top_segments = cross_segment_results.get('top_segments', {}).get(metric, [])
            bottom_segments = cross_segment_results.get('bottom_segments', {}).get(metric, [])
            
            if not top_segments or not bottom_segments:
                continue
            
            # Get best and worst performers
            best_segment = top_segments[0]
            worst_segment = bottom_segments[0]
            
            # Construct segment description (e.g., "Women 25-34")
            segment_keys = list(best_segment.keys())[:2]  # Get the first two segment columns
            best_desc = " ".join(str(best_segment[key]) for key in segment_keys)
            worst_desc = " ".join(str(worst_segment[key]) for key in segment_keys)
            
            # Format metric values
            if metric == 'ctr' or metric == 'conversion_rate':
                best_formatted = f"{best_segment[metric]:.2f}%"
                worst_formatted = f"{worst_segment[metric]:.2f}%"
                
                if worst_segment[metric] != 0:
                    diff_pct = abs((best_segment[metric] - worst_segment[metric]) / worst_segment[metric] * 100)
                else:
                    diff_pct = 100  # Default if worst is zero
                    
            elif metric == 'cpa':
                best_formatted = f"${best_segment[metric]:.2f}"
                worst_formatted = f"${worst_segment[metric]:.2f}"
                
                if worst_segment[metric] != 0:
                    diff_pct = abs((best_segment[metric] - worst_segment[metric]) / worst_segment[metric] * 100)
                else:
                    diff_pct = 100  # Default if worst is zero
            else:
                continue  # Skip unknown metrics
            
            # Skip if difference is too small
            if diff_pct < 50:
                continue
                
            # Create recommendation based on metric
            recommendation_text = ""
            action = ""
            severity = "medium"
            
            if metric == 'ctr':
                recommendation_text = (
                    f"The '{best_desc}' audience has a CTR of {best_formatted}, "
                    f"which is {diff_pct:.1f}% higher than '{worst_desc}' at {worst_formatted}."
                )
                
                if diff_pct > 100:
                    severity = "high"
                    action = (
                        f"Create a separate campaign targeting the '{best_desc}' audience with "
                        f"increased budget allocation. Consider revising creative strategy for '{worst_desc}'."
                    )
                else:
                    action = (
                        f"Test different messaging for the '{worst_desc}' audience to improve engagement."
                    )
                    
            elif metric == 'conversion_rate':
                recommendation_text = (
                    f"The '{best_desc}' audience has a conversion rate of {best_formatted}, "
                    f"which is {diff_pct:.1f}% higher than '{worst_desc}' at {worst_formatted}."
                )
                
                if diff_pct > 100:
                    severity = "high"
                    action = (
                        f"Significantly increase budget to the '{best_desc}' audience and create "
                        f"conversion-optimized campaigns specifically for this segment."
                    )
                else:
                    action = (
                        f"Review the conversion path for '{worst_desc}' audience to identify "
                        f"potential issues in messaging, landing page, or offer relevance."
                    )
                    
            elif metric == 'cpa':
                recommendation_text = (
                    f"The '{best_desc}' audience has a CPA of {best_formatted}, "
                    f"which is {diff_pct:.1f}% lower than '{worst_desc}' at {worst_formatted}."
                )
                
                if diff_pct > 100:
                    severity = "high"
                    action = (
                        f"Reduce budget for the '{worst_desc}' audience and reallocate to '{best_desc}' "
                        f"to improve overall campaign efficiency."
                    )
                else:
                    action = (
                        f"Review bidding strategy and refine targeting for the '{worst_desc}' audience."
                    )
            
            # Create recommendation object
            recommendation = {
                'type': f"cross_segment_{metric}_optimization",
                'segment_description': f"combined_{segment_keys[0]}_{segment_keys[1]}",
                'best_segment': best_desc,
                'worst_segment': worst_desc,
                'metric': metric,
                'best_value': best_segment[metric],
                'worst_value': worst_segment[metric],
                'difference_pct': diff_pct,
                'recommendation': f"{recommendation_text} {action}",
                'severity': severity,
                'potential_savings': self._estimate_potential_savings(
                    worst_segment['spend'], diff_pct)
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _estimate_potential_savings(self, spend, difference_pct):
        """
        Estimate potential savings from optimization.
        
        Args:
            spend (float): Current spend on underperforming segment
            difference_pct (float): Performance difference percentage
            
        Returns:
            float: Estimated potential savings
        """
        # Conservative estimate: 
        # For small differences (<50%), savings potential is lower
        # For large differences (>100%), savings potential is higher
        if difference_pct < 50:
            savings_factor = 0.15  # 15% of spend
        elif difference_pct < 100:
            savings_factor = 0.25  # 25% of spend
        else:
            savings_factor = 0.4   # 40% of spend
        
        return spend * savings_factor