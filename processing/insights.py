import numpy as np

def generate_insights(processed_data, metrics, platform):
    """
    Generate platform-specific insights and recommendations.
    
    Args:
        processed_data (dict): Processed platform data
        metrics (dict): Performance metrics
        platform (str): Platform name
        
    Returns:
        dict: Insights and recommendations
    """
    insights = {
        'recommendations': [],
        'areas_of_improvement': [],
        'strengths': []
    }
    
    # Generate budget efficiency insights
    budget_insights = analyze_budget_efficiency(processed_data, metrics, platform)
    if budget_insights:
        insights['budget_efficiency'] = budget_insights
        insights['recommendations'].extend(budget_insights.get('recommendations', []))
    
    # Generate audience insights
    audience_insights = analyze_audience_targeting(processed_data, metrics, platform)
    if audience_insights:
        insights['audience_targeting'] = audience_insights
        insights['recommendations'].extend(audience_insights.get('recommendations', []))
    
    # Generate ad fatigue insights
    fatigue_insights = analyze_ad_fatigue(processed_data, metrics, platform)
    if fatigue_insights:
        insights['ad_fatigue'] = fatigue_insights
        insights['recommendations'].extend(fatigue_insights.get('recommendations', []))
    
    # Generate creative performance insights
    creative_insights = analyze_creative_performance(processed_data, metrics, platform)
    if creative_insights:
        insights['creative_performance'] = creative_insights
        insights['recommendations'].extend(creative_insights.get('recommendations', []))
    
    # Analyze trends
    if 'trends' in metrics:
        trend_insights = analyze_trends(metrics['trends'], platform)
        if trend_insights:
            insights['trends'] = trend_insights
            insights['recommendations'].extend(trend_insights.get('recommendations', []))
    
    # Estimate potential savings
    potential_savings = estimate_potential_savings(insights)
    insights['potential_savings'] = potential_savings
    
    # Estimate potential improvement
    potential_improvement = estimate_potential_improvement(insights, metrics)
    insights['potential_improvement'] = potential_improvement
    
    return insights

def analyze_budget_efficiency(processed_data, metrics, platform):
    """Analyze budget efficiency and identify savings opportunities"""
    insights = {
        'recommendations': []
    }
    
    # Use the master dataset if available
    df = processed_data.get('master', processed_data.get('insights', None))
    if df is None or df.empty:
        return insights
    
    # Identify high-CPA campaigns
    if 'campaign_name' in df.columns and 'campaign_id' in df.columns:
        campaign_metrics = df.groupby(['campaign_id', 'campaign_name']).agg({
            'spend': 'sum',
            'clicks': 'sum',
            'impressions': 'sum',
            'purchases': 'sum' if 'purchases' in df.columns else 'count'
        }).reset_index()
        
        # Calculate CPA for each campaign
        campaign_metrics['cpa'] = campaign_metrics['spend'] / campaign_metrics['purchases']
        campaign_metrics = campaign_metrics.replace([np.inf, -np.inf], np.nan)
        
        # Get average CPA
        avg_cpa = campaign_metrics['cpa'].mean()
        
        # Find campaigns with high CPA (>50% above average)
        high_cpa_campaigns = campaign_metrics[campaign_metrics['cpa'] > avg_cpa * 1.5]
        high_cpa_campaigns = high_cpa_campaigns.dropna(subset=['cpa']).sort_values('cpa', ascending=False)
        
        insights['inefficient_campaigns'] = high_cpa_campaigns.to_dict('records')
        
        # Generate recommendations for high CPA campaigns
        for _, campaign in high_cpa_campaigns.iterrows():
            insights['recommendations'].append({
                'type': 'high_cpa',
                'platform': platform,
                'campaign_id': campaign['campaign_id'],
                'campaign_name': campaign['campaign_name'],
                'current_cpa': campaign['cpa'],
                'avg_cpa': avg_cpa,
                'severity': 'high' if campaign['cpa'] > avg_cpa * 2 else 'medium',
                'potential_savings': campaign['spend'] * 0.3,  # Estimate 30% savings
                'recommendation': f"Consider reducing budget or revising creative for campaign '{campaign['campaign_name']}' as its CPA (${campaign['cpa']:.2f}) is significantly higher than average (${avg_cpa:.2f})."
            })
    
    # Identify campaigns with budget but low impressions
    if 'campaign_name' in df.columns and 'campaign_id' in df.columns:
        avg_impressions = campaign_metrics['impressions'].mean()
        
        low_impression_campaigns = campaign_metrics[
            (campaign_metrics['spend'] > 0) & 
            (campaign_metrics['impressions'] < avg_impressions * 0.5)
        ]
        
        insights['low_reach_campaigns'] = low_impression_campaigns.to_dict('records')
        
        # Generate recommendations for low impression campaigns
        for _, campaign in low_impression_campaigns.iterrows():
            insights['recommendations'].append({
                'type': 'low_reach',
                'platform': platform,
                'campaign_id': campaign['campaign_id'],
                'campaign_name': campaign['campaign_name'],
                'spend': campaign['spend'],
                'impressions': campaign['impressions'],
                'avg_impressions': avg_impressions,
                'severity': 'medium',
                'potential_savings': campaign['spend'] * 0.2,  # Estimate 20% savings
                'recommendation': f"Campaign '{campaign['campaign_name']}' has spent ${campaign['spend']:.2f} but received only {campaign['impressions']} impressions (50% below average). Consider reviewing targeting or creative quality."
            })
    
    return insights

def analyze_audience_targeting(processed_data, metrics, platform):
    """Analyze audience targeting effectiveness"""
    insights = {
        'recommendations': []
    }
    
    # Check if we have segment metrics
    if 'segments' not in metrics:
        return insights
    
    segments = metrics['segments']
    
    # Analyze age segments if available
    if 'age' in segments:
        age_metrics = segments['age']
        
        # Find best and worst performing age groups by conversion rate
        if len(age_metrics) > 1:
            age_metrics_valid = [m for m in age_metrics if not np.isnan(m.get('conversion_rate', np.nan))]
            
            if age_metrics_valid:
                best_age = max(age_metrics_valid, key=lambda x: x['conversion_rate'])
                worst_age = min(age_metrics_valid, key=lambda x: x['conversion_rate'])
                
                # Check if there's a significant difference (>50%)
                if worst_age['conversion_rate'] * 1.5 < best_age['conversion_rate']:
                    insights['recommendations'].append({
                        'type': 'age_targeting',
                        'platform': platform,
                        'best_segment': best_age['age'],
                        'best_conversion_rate': best_age['conversion_rate'],
                        'worst_segment': worst_age['age'],
                        'worst_conversion_rate': worst_age['conversion_rate'],
                        'severity': 'medium',
                        'potential_savings': worst_age['spend'] * 0.5,  # Estimate reallocating 50% of spend
                        'recommendation': f"Consider reducing budget for age group '{worst_age['age']}' which has a conversion rate of {worst_age['conversion_rate']:.2f}% compared to {best_age['conversion_rate']:.2f}% for '{best_age['age']}'."
                    })
    
    # Analyze gender segments if available
    if 'gender' in segments:
        gender_metrics = segments['gender']
        
        # Find best and worst performing genders by conversion rate
        if len(gender_metrics) > 1:
            gender_metrics_valid = [m for m in gender_metrics if not np.isnan(m.get('conversion_rate', np.nan))]
            
            if gender_metrics_valid:
                best_gender = max(gender_metrics_valid, key=lambda x: x['conversion_rate'])
                worst_gender = min(gender_metrics_valid, key=lambda x: x['conversion_rate'])
                
                # Check if there's a significant difference (>50%)
                if worst_gender['conversion_rate'] * 1.5 < best_gender['conversion_rate']:
                    insights['recommendations'].append({
                        'type': 'gender_targeting',
                        'platform': platform,
                        'best_segment': best_gender['gender'],
                        'best_conversion_rate': best_gender['conversion_rate'],
                        'worst_segment': worst_gender['gender'],
                        'worst_conversion_rate': worst_gender['conversion_rate'],
                        'severity': 'medium',
                        'potential_savings': worst_gender['spend'] * 0.5,  # Estimate reallocating 50% of spend
                        'recommendation': f"Gender '{worst_gender['gender']}' significantly underperforms with a conversion rate of {worst_gender['conversion_rate']:.2f}% vs {best_gender['conversion_rate']:.2f}% for '{best_gender['gender']}'. Consider rebalancing budget allocation."
                    })
    
    # Analyze device segments if available
    if 'device' in segments:
        device_metrics = segments['device']
        
        # Find best and worst performing devices by conversion rate
        if len(device_metrics) > 1:
            device_metrics_valid = [m for m in device_metrics if not np.isnan(m.get('conversion_rate', np.nan))]
            
            if device_metrics_valid:
                best_device = max(device_metrics_valid, key=lambda x: x['conversion_rate'])
                worst_device = min(device_metrics_valid, key=lambda x: x['conversion_rate'])
                
                # Check if there's a significant difference (>50%)
                if worst_device['conversion_rate'] * 1.5 < best_device['conversion_rate']:
                    insights['recommendations'].append({
                        'type': 'device_targeting',
                        'platform': platform,
                        'best_segment': best_device['device'],
                        'best_conversion_rate': best_device['conversion_rate'],
                        'worst_segment': worst_device['device'],
                        'worst_conversion_rate': worst_device['conversion_rate'],
                        'severity': 'medium',
                        'potential_savings': worst_device['spend'] * 0.4,  # Estimate reallocating 40% of spend
                        'recommendation': f"Device type '{worst_device['device']}' has poor performance with a conversion rate of {worst_device['conversion_rate']:.2f}% compared to {best_device['conversion_rate']:.2f}% for '{best_device['device']}'. Consider optimizing creative for this device or adjusting device targeting."
                    })
    
    return insights

def analyze_ad_fatigue(processed_data, metrics, platform):
    """Analyze ad performance over time to identify fatigue"""
    insights = {
        'recommendations': []
    }
    
    # Check if we have trends data
    if 'trends' not in metrics:
        return insights
    
    # Get daily metrics
    daily_metrics = metrics['trends'].get('daily_metrics', [])
    if not daily_metrics:
        return insights
    
    # Use the master dataset if available
    df = processed_data.get('master', processed_data.get('insights', None))
    if df is None or df.empty:
        return insights
    
    # Check if we have ad-level data
    if 'ad_id' in df.columns and 'ad_name' in df.columns and 'date' in df.columns:
        # Group by ad and date
        ad_daily = df.groupby(['ad_id', 'ad_name', 'date']).agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'frequency': 'mean'
        }).reset_index()
        
        # Calculate CTR
        ad_daily['ctr'] = (ad_daily['clicks'] / ad_daily['impressions']) * 100
        
        # Sort by date
        ad_daily = ad_daily.sort_values(['ad_id', 'date'])
        
        # Identify ads running for more than 5 days
        ad_counts = ad_daily.groupby('ad_id').size()
        long_running_ads = ad_counts[ad_counts > 5].index
        
        # Analyze fatigue signals for long-running ads
        fatigued_ads = []
        
        for ad_id in long_running_ads:
            ad_data = ad_daily[ad_daily['ad_id'] == ad_id]
            
            if len(ad_data) >= 6:  # Need at least 6 days for comparison
                # Get first half and second half data
                half_point = len(ad_data) // 2
                first_half = ad_data.iloc[:half_point]
                second_half = ad_data.iloc[half_point:]
                
                # Calculate averages
                first_half_ctr = first_half['ctr'].mean()
                second_half_ctr = second_half['ctr'].mean()
                
                first_half_frequency = first_half['frequency'].mean()
                second_half_frequency = second_half['frequency'].mean()
                
                # Check for fatigue signals: declining CTR and increasing frequency
                if second_half_ctr < first_half_ctr * 0.8 and second_half_frequency > first_half_frequency * 1.2:
                    ad_name = ad_data['ad_name'].iloc[0]
                    days_running = len(ad_data)
                    ctr_decline = ((second_half_ctr - first_half_ctr) / first_half_ctr) * 100
                    frequency_increase = ((second_half_frequency - first_half_frequency) / first_half_frequency) * 100
                    
                    fatigued_ad = {
                        'ad_id': ad_id,
                        'ad_name': ad_name,
                        'days_running': days_running,
                        'ctr_decline': ctr_decline,
                        'frequency_increase': frequency_increase,
                        'first_half_ctr': first_half_ctr,
                        'second_half_ctr': second_half_ctr,
                        'first_half_frequency': first_half_frequency,
                        'second_half_frequency': second_half_frequency,
                        'severity': 'high' if second_half_ctr < first_half_ctr * 0.6 else 'medium'
                    }
                    
                    fatigued_ads.append(fatigued_ad)
                    
                    # Add recommendation
                    severity_word = 'severe' if fatigued_ad['severity'] == 'high' else 'moderate'
                    insights['recommendations'].append({
                        'type': 'ad_fatigue',
                        'platform': platform,
                        'ad_id': ad_id,
                        'ad_name': ad_name,
                        'days_running': days_running,
                        'ctr_decline': abs(ctr_decline),
                        'frequency_increase': frequency_increase,
                        'severity': fatigued_ad['severity'],
                        'potential_savings': 0,  # Ad fatigue is about performance improvement, not direct savings
                        'recommendation': f"{severity_word.capitalize()} fatigue detected in ad '{ad_name}' after {days_running} days with CTR declining by {abs(ctr_decline):.1f}% while frequency increased by {frequency_increase:.1f}%. {'Pause and replace with fresh creative.' if fatigued_ad['severity'] == 'high' else 'Consider refreshing creative or adjusting targeting.'}"
                    })
        
        insights['fatigued_ads'] = fatigued_ads
    
    return insights

def analyze_creative_performance(processed_data, metrics, platform):
    """Analyze creative performance and identify top/bottom performers"""
    insights = {
        'recommendations': []
    }
    
    # Use the master dataset if available
    df = processed_data.get('master', processed_data.get('insights', None))
    if df is None or df.empty:
        return insights
    
    # Check if we have creative-level data
    creative_id_field = 'creative_id' if 'creative_id' in df.columns else ('ad_id' if 'ad_id' in df.columns else None)
    creative_name_field = 'creative_name' if 'creative_name' in df.columns else ('ad_name' if 'ad_name' in df.columns else None)
    
    if creative_id_field and creative_name_field:
        # Group by creative
        creative_metrics = df.groupby([creative_id_field, creative_name_field]).agg({
            'spend': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'purchases': 'sum' if 'purchases' in df.columns else 'count'
        }).reset_index()
        
        # Calculate performance metrics
        creative_metrics['ctr'] = (creative_metrics['clicks'] / creative_metrics['impressions']) * 100
        creative_metrics['conversion_rate'] = (creative_metrics['purchases'] / creative_metrics['clicks']) * 100
        creative_metrics['cpa'] = creative_metrics['spend'] / creative_metrics['purchases']
        
        # Replace infinities with NaN
        creative_metrics = creative_metrics.replace([np.inf, -np.inf], np.nan)
        
        # Exclude creatives with insufficient data
        valid_creatives = creative_metrics[
            (creative_metrics['impressions'] >= 1000) & 
            (creative_metrics['clicks'] >= 10)
        ].dropna(subset=['conversion_rate']).copy()
        
        if not valid_creatives.empty and len(valid_creatives) >= 2:
            # Find top and bottom performers by conversion rate
            top_creatives = valid_creatives.nlargest(3, 'conversion_rate')
            bottom_creatives = valid_creatives.nsmallest(3, 'conversion_rate')
            
            # Store top and bottom performers
            insights['top_creatives'] = top_creatives.to_dict('records')
            insights['bottom_creatives'] = bottom_creatives.to_dict('records')
            
            # Generate recommendations for top performers
            for _, creative in top_creatives.head(1).iterrows():
                insights['recommendations'].append({
                    'type': 'top_creative',
                    'platform': platform,
                    'creative_id': creative[creative_id_field],
                    'creative_name': creative[creative_name_field],
                    'conversion_rate': creative['conversion_rate'],
                    'ctr': creative['ctr'],
                    'severity': 'low',  # This is a positive insight
                    'potential_savings': 0,  # This is about improvement, not savings
                    'recommendation': f"Scale budget for top-performing ad '{creative[creative_name_field]}' with exceptional conversion rate of {creative['conversion_rate']:.2f}% and CTR of {creative['ctr']:.2f}%."
                })
            
            # Generate recommendations for bottom performers with significant difference
            top_cr = top_creatives['conversion_rate'].iloc[0]
            for _, creative in bottom_creatives.head(1).iterrows():
                if creative['conversion_rate'] < top_cr * 0.3:  # Less than 30% of top performer
                    insights['recommendations'].append({
                        'type': 'bottom_creative',
                        'platform': platform,
                        'creative_id': creative[creative_id_field],
                        'creative_name': creative[creative_name_field],
                        'conversion_rate': creative['conversion_rate'],
                        'ctr': creative['ctr'],
                        'top_conversion_rate': top_cr,
                        'severity': 'medium',
                        'potential_savings': creative['spend'] * 0.7,  # Reallocate 70% of spend
                        'recommendation': f"Consider pausing underperforming ad '{creative[creative_name_field]}' with low conversion rate of {creative['conversion_rate']:.2f}% compared to top performer at {top_cr:.2f}%."
                    })
    
    return insights

def analyze_trends(trends, platform):
    """Analyze metric trends over time"""
    insights = {
        'recommendations': []
    }
    
    # Check if we have trend data for key metrics
    for metric in ['ctr', 'conversion_rate', 'cpa', 'cpc']:
        if metric in trends:
            metric_trend = trends[metric]
            percent_change = metric_trend.get('percent_change', 0)
            is_improving = metric_trend.get('is_improving', False)
            
            # Generate insights for significant changes (>15%)
            if abs(percent_change) > 15:
                # Format the trend direction and recommendation based on the metric
                if metric in ['ctr', 'conversion_rate']:
                    direction = 'increased' if percent_change > 0 else 'decreased'
                    sentiment = 'positive' if percent_change > 0 else 'negative'
                else:  # cpa, cpc - lower is better
                    direction = 'decreased' if percent_change < 0 else 'increased'
                    sentiment = 'positive' if percent_change < 0 else 'negative'
                
                # Add to insights
                insights[f'{metric}_trend'] = {
                    'percent_change': percent_change,
                    'direction': direction,
                    'sentiment': sentiment,
                    'is_improving': is_improving
                }
                
                # Generate recommendation for negative trends only
                if sentiment == 'negative' and abs(percent_change) > 25:
                    metric_name = metric.upper()
                    
                    if metric in ['ctr', 'conversion_rate']:
                        insights['recommendations'].append({
                            'type': f'{metric}_trend',
                            'platform': platform,
                            'percent_change': abs(percent_change),
                            'severity': 'medium' if abs(percent_change) > 35 else 'low',
                            'potential_savings': 0,  # Trend insights are about performance, not direct savings
                            'recommendation': f"{metric_name} has declined by {abs(percent_change):.1f}% over the analysis period. Consider refreshing creatives and reviewing audience targeting."
                        })
                    else:  # cpa, cpc
                        insights['recommendations'].append({
                            'type': f'{metric}_trend',
                            'platform': platform,
                            'percent_change': abs(percent_change),
                            'severity': 'medium' if abs(percent_change) > 35 else 'low',
                            'potential_savings': 0,  # Difficult to estimate without more data
                            'recommendation': f"{metric_name} has increased by {abs(percent_change):.1f}% over the analysis period. Evaluate bidding strategy and audience quality."
                        })
    
    return insights

def estimate_potential_savings(insights):
    """Estimate total potential savings from all insights"""
    total_savings = 0
    
    # Sum up potential savings from all recommendations
    for rec in insights.get('recommendations', []):
        total_savings += rec.get('potential_savings', 0)
    
    return total_savings

def estimate_potential_improvement(insights, metrics):
    """Estimate potential performance improvement percentage"""
    # Start with a baseline improvement estimate based on recommendations
    baseline_improvement = 0
    high_severity_count = 0
    medium_severity_count = 0
    
    for rec in insights.get('recommendations', []):
        severity = rec.get('severity', 'low')
        if severity == 'high':
            high_severity_count += 1
        elif severity == 'medium':
            medium_severity_count += 1
    
    # More high severity issues = more improvement potential
    if high_severity_count > 0:
        baseline_improvement += high_severity_count * 5  # 5% per high severity issue
    
    if medium_severity_count > 0:
        baseline_improvement += medium_severity_count * 2  # 2% per medium severity issue
    
    # Cap at reasonable levels
    baseline_improvement = min(baseline_improvement, 50)
    
    return baseline_improvement

def prioritize_recommendations(recommendations):
    """
    Prioritize recommendations based on potential impact and severity.
    
    Args:
        recommendations (list): List of recommendation dictionaries
        
    Returns:
        list: Prioritized list of recommendations
    """
    # Assign priority scores to each recommendation
    for rec in recommendations:
        severity = rec.get('severity', 'low')
        potential_savings = rec.get('potential_savings', 0)
        
        # Base score on severity
        if severity == 'high':
            priority_score = 100
        elif severity == 'medium':
            priority_score = 50
        else:
            priority_score = 10
        
        # Adjust score based on potential savings
        if potential_savings > 0:
            # More savings = higher priority
            priority_score += min(potential_savings / 10, 100)  # Cap at 100 additional points
        
        # Adjust score based on recommendation type
        rec_type = rec.get('type', '')
        
        # Budget-related recommendations get priority boost
        if any(budget_term in rec_type for budget_term in ['cpa', 'budget', 'spend', 'cost']):
            priority_score += 20
        
        # Creative performance gets secondary priority
        elif any(creative_term in rec_type for creative_term in ['creative', 'ad_', 'fatigue']):
            priority_score += 10
        
        rec['priority_score'] = priority_score
    
    # Sort by priority score (descending)
    prioritized = sorted(recommendations, key=lambda x: x.get('priority_score', 0), reverse=True)
    
    return prioritized