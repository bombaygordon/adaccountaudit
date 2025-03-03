def calculate_metrics(insights):
    """
    Calculate additional performance metrics from raw insights data.
    
    Args:
        insights (list): List of insight data points
        
    Returns:
        dict: Aggregated metrics and calculated KPIs
    """
    if not insights:
        return {}
        
    # Initialize metrics
    total_spend = 0
    total_impressions = 0
    total_clicks = 0
    total_conversions = 0
    
    # Aggregate data
    for insight in insights:
        total_spend += insight.get('spend', 0)
        total_impressions += insight.get('impressions', 0)
        total_clicks += insight.get('clicks', 0)
        
        # For conversions, check 'actions' field which might contain different conversion types
        actions = insight.get('actions', [])
        for action in actions:
            if action.get('action_type') == 'purchase':
                total_conversions += action.get('value', 0)
    
    # Calculate derived metrics
    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
    cpa = (total_spend / total_conversions) if total_conversions > 0 else 0
    
    return {
        'total_spend': total_spend,
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'total_conversions': total_conversions,
        'ctr': ctr,
        'cpc': cpc,
        'cpa': cpa
    }

def format_currency(value, currency='USD', decimals=2):
    """Format a numeric value as currency string"""
    return f"{currency} {value:.{decimals}f}"