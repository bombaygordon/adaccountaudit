import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta

def detect_ad_fatigue(ad_daily_data, min_days=5, confidence_threshold=0.90):
    """
    Enhanced ad fatigue detection using statistical analysis and regression.
    
    Args:
        ad_daily_data (DataFrame): Daily ad performance data with columns:
            - date: Date of the data point
            - ad_id: Identifier for the ad
            - ad_name: Name of the ad
            - impressions: Number of impressions
            - clicks: Number of clicks
            - ctr: Click-through rate (percentage)
            - frequency: Average impression frequency
            - spend: Amount spent
            - conversions: Number of conversions (if available)
        min_days (int): Minimum number of days required for analysis
        confidence_threshold (float): Statistical confidence threshold (0-1)
        
    Returns:
        dict: Fatigue analysis results with metrics and confidence scores
    """
    results = {
        'is_fatigued': False,
        'confidence': 0,
        'metrics': {},
        'recommendation': None
    }
    
    # Check if we have enough data
    if ad_daily_data is None or len(ad_daily_data) < min_days:
        return results
    
    # Ensure data is sorted by date
    ad_daily_data = ad_daily_data.sort_values('date')
    
    # Extract key metrics
    dates = pd.to_datetime(ad_daily_data['date'])
    days_running = (dates.max() - dates.min()).days + 1
    
    # Skip if not enough days
    if days_running < min_days:
        return results
    
    # Get basic ad info
    ad_id = ad_daily_data['ad_id'].iloc[0]
    ad_name = ad_daily_data['ad_name'].iloc[0] if 'ad_name' in ad_daily_data.columns else f"Ad {ad_id}"
    
    # Calculate cumulative metrics
    ad_daily_data['day_number'] = (dates - dates.min()).dt.days
    
    # Create analysis metrics
    metrics = {}
    
    # 1. Linear regression on CTR over time
    if 'ctr' in ad_daily_data.columns:
        # Calculate linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            ad_daily_data['day_number'], 
            ad_daily_data['ctr']
        )
        
        # Store regression metrics
        metrics['ctr_regression'] = {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value**2,
            'p_value': p_value,
            'significant_decline': p_value < 0.1 and slope < 0
        }
        
        # Calculate percentage decline
        if days_running > 0 and intercept != 0:
            predicted_start = intercept
            predicted_end = intercept + (slope * days_running)
            pct_change = ((predicted_end - predicted_start) / predicted_start) * 100
            metrics['ctr_regression']['pct_change'] = pct_change
        
    # 2. Frequency vs. CTR correlation
    if 'frequency' in ad_daily_data.columns and 'ctr' in ad_daily_data.columns:
        # Calculate correlation
        corr = ad_daily_data['frequency'].corr(ad_daily_data['ctr'])
        metrics['frequency_ctr_correlation'] = corr
        
        # Negative correlation often indicates fatigue
        metrics['negative_frequency_correlation'] = corr < -0.3
    
    # 3. Conversion rate decay over time
    if 'conversions' in ad_daily_data.columns and 'clicks' in ad_daily_data.columns:
        # Calculate daily conversion rates
        ad_daily_data['conv_rate'] = (ad_daily_data['conversions'] / ad_daily_data['clicks']) * 100
        
        # Regression on conversion rate
        if not ad_daily_data['conv_rate'].isna().all():
            # Remove NaN values
            conv_data = ad_daily_data.dropna(subset=['conv_rate'])
            
            if len(conv_data) >= min_days:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    conv_data['day_number'], 
                    conv_data['conv_rate']
                )
                
                metrics['conversion_regression'] = {
                    'slope': slope,
                    'p_value': p_value,
                    'significant_decline': p_value < 0.1 and slope < 0
                }
    
    # 4. CPC increase over time
    if 'clicks' in ad_daily_data.columns and 'spend' in ad_daily_data.columns:
        # Calculate CPC
        ad_daily_data['cpc'] = ad_daily_data['spend'] / ad_daily_data['clicks']
        
        # Regression on CPC
        cpc_data = ad_daily_data.dropna(subset=['cpc'])
        if len(cpc_data) >= min_days:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                cpc_data['day_number'], 
                cpc_data['cpc']
            )
            
            metrics['cpc_regression'] = {
                'slope': slope,
                'p_value': p_value,
                'significant_increase': p_value < 0.1 and slope > 0
            }
    
    # 5. Calculate Moving Averages and Acceleration
    if 'ctr' in ad_daily_data.columns and len(ad_daily_data) >= min_days + 2:
        # Calculate 3-day moving average
        ad_daily_data['ctr_ma3'] = ad_daily_data['ctr'].rolling(window=3, min_periods=1).mean()
        
        # Calculate rate of change in the moving average (acceleration)
        ad_daily_data['ctr_ma3_change'] = ad_daily_data['ctr_ma3'].diff()
        
        # Check if recent changes are negative
        recent_changes = ad_daily_data['ctr_ma3_change'].tail(3).mean()
        metrics['recent_ctr_velocity'] = recent_changes
        metrics['accelerating_decline'] = recent_changes < 0
    
    # Store all metrics
    results['metrics'] = metrics
    
    # Determine if ad is fatigued based on multiple signals
    fatigue_signals = 0
    max_signals = 0
    
    # CTR decline signal
    if 'ctr_regression' in metrics:
        max_signals += 1
        if metrics['ctr_regression'].get('significant_decline', False):
            fatigue_signals += 1
    
    # Negative frequency correlation signal
    if 'negative_frequency_correlation' in metrics:
        max_signals += 1
        if metrics['negative_frequency_correlation']:
            fatigue_signals += 1
    
    # Conversion rate decline signal
    if 'conversion_regression' in metrics:
        max_signals += 1
        if metrics['conversion_regression'].get('significant_decline', False):
            fatigue_signals += 1
    
    # CPC increase signal
    if 'cpc_regression' in metrics:
        max_signals += 1
        if metrics['cpc_regression'].get('significant_increase', False):
            fatigue_signals += 1
    
    # Accelerating decline signal
    if 'accelerating_decline' in metrics:
        max_signals += 1
        if metrics['accelerating_decline']:
            fatigue_signals += 1
    
    # Calculate confidence based on signals
    signal_confidence = fatigue_signals / max_signals if max_signals > 0 else 0
    
    # Adjust for the number of days (more days = more confident)
    day_factor = min(1.0, days_running / 14)  # Max factor at 14 days
    
    # Overall confidence calculation
    confidence = signal_confidence * day_factor
    
    # Determine if ad is fatigued based on confidence threshold
    results['is_fatigued'] = confidence >= confidence_threshold
    results['confidence'] = confidence
    results['days_running'] = days_running
    
    # Generate recommendation if fatigued
    if results['is_fatigued']:
        severity = "severe" if confidence > 0.8 else "moderate"
        
        # Find which metric has declined the most
        decline_pct = metrics.get('ctr_regression', {}).get('pct_change', 0)
        
        recommendation = (
            f"{severity.capitalize()} ad fatigue detected for '{ad_name}' after {days_running} days "
            f"with {confidence:.0%} confidence. "
        )
        
        if decline_pct < 0:
            recommendation += f"CTR has declined approximately {abs(decline_pct):.1f}%. "
        
        if confidence > 0.8:
            recommendation += "Recommend pausing this ad and replacing with fresh creative."
        else:
            recommendation += "Consider refreshing the creative or adjusting audience targeting."
            
        results['recommendation'] = recommendation
        results['severity'] = severity
    
    return results


def batch_fatigue_analysis(ads_df, min_impressions=1000):
    """
    Analyze a batch of ads for fatigue.
    
    Args:
        ads_df (DataFrame): DataFrame with daily ad performance data
        min_impressions (int): Minimum impressions for an ad to be analyzed
        
    Returns:
        list: List of fatigued ads with analysis results
    """
    if ads_df.empty:
        return []
    
    # Group by ad_id to get total impressions
    ad_totals = ads_df.groupby('ad_id').agg({
        'impressions': 'sum',
        'ad_name': 'first'
    }).reset_index()
    
    # Filter for ads with minimum impressions
    qualified_ads = ad_totals[ad_totals['impressions'] >= min_impressions]['ad_id'].tolist()
    
    fatigued_ads = []
    
    # Analyze each qualified ad
    for ad_id in qualified_ads:
        ad_data = ads_df[ads_df['ad_id'] == ad_id].copy()
        
        # Run fatigue detection
        fatigue_result = detect_ad_fatigue(ad_data)
        
        # If fatigued, add to results
        if fatigue_result['is_fatigued']:
            result = {
                'ad_id': ad_id,
                'ad_name': ad_data['ad_name'].iloc[0] if 'ad_name' in ad_data.columns else f"Ad {ad_id}",
                'days_running': fatigue_result['days_running'],
                'confidence': fatigue_result['confidence'],
                'metrics': fatigue_result['metrics'],
                'recommendation': fatigue_result['recommendation'],
                'severity': fatigue_result.get('severity', 'medium')
            }
            fatigued_ads.append(result)
    
    # Sort by confidence (highest first)
    fatigued_ads.sort(key=lambda x: x['confidence'], reverse=True)
    
    return fatigued_ads