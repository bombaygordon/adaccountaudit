import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_performance_metrics(processed_data, platform):
    """
    Calculate key performance metrics for the platform.
    
    Args:
        processed_data (dict): Processed platform data
        platform (str): Platform name
        
    Returns:
        dict: Performance metrics
    """
    metrics = {}
    
    # Use the master dataset if available, otherwise use insights
    df = processed_data.get('master', processed_data.get('insights', pd.DataFrame()))
    
    if df.empty:
        return metrics
    
    # Calculate core metrics
    metrics['spend'] = df['spend'].sum() if 'spend' in df.columns else 0
    metrics['impressions'] = df['impressions'].sum() if 'impressions' in df.columns else 0
    metrics['clicks'] = df['clicks'].sum() if 'clicks' in df.columns else 0
    
    # Calculate conversions (platform specific)
    if platform in ['facebook', 'instagram']:
        metrics['conversions'] = df['purchases'].sum() if 'purchases' in df.columns else 0
    elif platform == 'tiktok':
        metrics['conversions'] = df['conversions'].sum() if 'conversions' in df.columns else 0
    else:
        metrics['conversions'] = 0
    
    # Calculate revenue (if available)
    if 'revenue' in df.columns:
        metrics['revenue'] = df['revenue'].sum()
    elif 'conversion_value' in df.columns:
        metrics['revenue'] = df['conversion_value'].sum()
    else:
        # Estimate revenue using average order value if available
        aov = 50  # Default average order value
        metrics['revenue'] = metrics['conversions'] * aov
    
    # Calculate derived metrics
    if metrics['impressions'] > 0:
        metrics['ctr'] = (metrics['clicks'] / metrics['impressions']) * 100
        metrics['cpm'] = (metrics['spend'] / metrics['impressions']) * 1000
    else:
        metrics['ctr'] = 0
        metrics['cpm'] = 0
    
    if metrics['clicks'] > 0:
        metrics['cpc'] = metrics['spend'] / metrics['clicks']
        
        if metrics['conversions'] > 0:
            metrics['conversion_rate'] = (metrics['conversions'] / metrics['clicks']) * 100
        else:
            metrics['conversion_rate'] = 0
    else:
        metrics['cpc'] = 0
        metrics['conversion_rate'] = 0
    
    if metrics['conversions'] > 0:
        metrics['cpa'] = metrics['spend'] / metrics['conversions']
    else:
        metrics['cpa'] = 0
    
    if metrics['spend'] > 0 and metrics['revenue'] > 0:
        metrics['roas'] = metrics['revenue'] / metrics['spend']
    else:
        metrics['roas'] = 0
    
    # Calculate segment-specific metrics if available
    if 'age' in df.columns or 'gender' in df.columns or 'device' in df.columns:
        metrics['segments'] = calculate_segment_metrics(df)
    
    return metrics

def calculate_segment_metrics(df):
    """
    Calculate metrics for different segments (age, gender, device, etc.)
    
    Args:
        df (DataFrame): Insights data
        
    Returns:
        dict: Segment metrics
    """
    segment_metrics = {}
    
    # Age segments
    if 'age' in df.columns:
        age_metrics = df.groupby('age').agg({
            'spend': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'purchases': 'sum' if 'purchases' in df.columns else 'count'
        }).reset_index()
        
        # Calculate derived metrics for each age group
        age_metrics['ctr'] = (age_metrics['clicks'] / age_metrics['impressions']) * 100
        age_metrics['cpc'] = age_metrics['spend'] / age_metrics['clicks']
        age_metrics['conversion_rate'] = (age_metrics['purchases'] / age_metrics['clicks']) * 100
        age_metrics['cpa'] = age_metrics['spend'] / age_metrics['purchases']
        
        # Replace infinities with 0
        age_metrics = age_metrics.replace([np.inf, -np.inf], 0)
        
        segment_metrics['age'] = age_metrics.to_dict('records')
    
    # Gender segments
    if 'gender' in df.columns:
        gender_metrics = df.groupby('gender').agg({
            'spend': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'purchases': 'sum' if 'purchases' in df.columns else 'count'
        }).reset_index()
        
        # Calculate derived metrics for each gender
        gender_metrics['ctr'] = (gender_metrics['clicks'] / gender_metrics['impressions']) * 100
        gender_metrics['cpc'] = gender_metrics['spend'] / gender_metrics['clicks']
        gender_metrics['conversion_rate'] = (gender_metrics['purchases'] / gender_metrics['clicks']) * 100
        gender_metrics['cpa'] = gender_metrics['spend'] / gender_metrics['purchases']
        
        # Replace infinities with 0
        gender_metrics = gender_metrics.replace([np.inf, -np.inf], 0)
        
        segment_metrics['gender'] = gender_metrics.to_dict('records')
    
    # Device segments
    if 'device' in df.columns:
        device_metrics = df.groupby('device').agg({
            'spend': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'purchases': 'sum' if 'purchases' in df.columns else 'count'
        }).reset_index()
        
        # Calculate derived metrics for each device
        device_metrics['ctr'] = (device_metrics['clicks'] / device_metrics['impressions']) * 100
        device_metrics['cpc'] = device_metrics['spend'] / device_metrics['clicks']
        device_metrics['conversion_rate'] = (device_metrics['purchases'] / device_metrics['clicks']) * 100
        device_metrics['cpa'] = device_metrics['spend'] / device_metrics['purchases']
        
        # Replace infinities with 0
        device_metrics = device_metrics.replace([np.inf, -np.inf], 0)
        
        segment_metrics['device'] = device_metrics.to_dict('records')
    
    return segment_metrics

def identify_kpi_trends(processed_data, platform, lookback_days):
    """
    Identify trends in key performance indicators over time.
    
    Args:
        processed_data (dict): Processed platform data
        platform (str): Platform name
        lookback_days (int): Number of days to analyze
        
    Returns:
        dict: Trend analysis results
    """
    trends = {}
    
    # Use the master dataset if available, otherwise use insights
    df = processed_data.get('master', processed_data.get('insights', pd.DataFrame()))
    
    if df.empty or 'date' not in df.columns:
        return trends
    
    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by date
    daily_metrics = df.groupby('date').agg({
        'spend': 'sum',
        'impressions': 'sum',
        'clicks': 'sum',
        'purchases': 'sum' if 'purchases' in df.columns else 'count'
    }).reset_index()
    
    # Calculate daily derived metrics
    daily_metrics['ctr'] = (daily_metrics['clicks'] / daily_metrics['impressions']) * 100
    daily_metrics['cpc'] = daily_metrics['spend'] / daily_metrics['clicks']
    daily_metrics['conversion_rate'] = (daily_metrics['purchases'] / daily_metrics['clicks']) * 100
    daily_metrics['cpa'] = daily_metrics['spend'] / daily_metrics['purchases']
    
    # Replace infinities with NaN for rolling calculations
    daily_metrics = daily_metrics.replace([np.inf, -np.inf], np.nan)
    
    # Sort by date
    daily_metrics = daily_metrics.sort_values('date')
    
    # Calculate 7-day rolling averages
    for metric in ['ctr', 'cpc', 'conversion_rate', 'cpa']:
        daily_metrics[f'{metric}_7d_avg'] = daily_metrics[metric].rolling(7, min_periods=1).mean()
    
    # Analyze trends (comparing first half to second half of period)
    if len(daily_metrics) >= 14:  # Need at least 14 days for meaningful trend
        half_point = len(daily_metrics) // 2
        first_half = daily_metrics.iloc[:half_point]
        second_half = daily_metrics.iloc[half_point:]
        
        for metric in ['ctr', 'cpc', 'conversion_rate', 'cpa']:
            first_half_avg = first_half[metric].mean()
            second_half_avg = second_half[metric].mean()
            
            if not (np.isnan(first_half_avg) or np.isnan(second_half_avg) or first_half_avg == 0):
                percent_change = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                
                # Determine if trend is positive or negative (depends on metric)
                if metric in ['ctr', 'conversion_rate']:
                    is_improving = percent_change > 0
                else:  # cpc, cpa - lower is better
                    is_improving = percent_change < 0
                
                trends[metric] = {
                    'first_half_avg': first_half_avg,
                    'second_half_avg': second_half_avg,
                    'percent_change': percent_change,
                    'is_improving': is_improving
                }
    
    # Add daily metrics to trends
    trends['daily_metrics'] = daily_metrics.to_dict('records')
    
    return trends