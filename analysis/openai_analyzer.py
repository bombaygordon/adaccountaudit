import os
from openai import OpenAI
from typing import Dict, List, Any
import logging
from datetime import datetime
import re
import json
import time

logger = logging.getLogger(__name__)

class OpenAIAdAnalyzer:
    """
    Analyzes Facebook ad data using OpenAI's GPT models to generate
    intelligent recommendations and insights.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the analyzer with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        # Log the first few characters of the API key for debugging
        logger.info(f"Using OpenAI API key starting with: {self.api_key[:8]}...")
        
        # Initialize OpenAI client with timeout and retry settings
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=30.0,  # 30 second timeout
            max_retries=3  # Retry failed requests up to 3 times
        )
        
        # Log which API endpoint we're using
        logger.info(f"Using API endpoint: {self.client.base_url}")

    def _calculate_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key performance metrics from raw data."""
        campaigns = data.get('campaigns', [])
        ad_sets = data.get('ad_sets', [])
        ads = data.get('ads', [])
        
        account_metrics = {
            'total_spend': 0.0,
            'total_impressions': 0,
            'total_clicks': 0,
            'total_conversions': 0,
            'average_ctr': 0.0,
            'average_cpc': 0.0,
            'average_conversion_rate': 0.0,
            'average_cpa': 0.0,
            'best_performing_campaigns': [],
            'underperforming_campaigns': []
        }
        
        # Calculate account-level metrics
        for campaign in campaigns:
            spend = float(campaign.get('spend', 0))
            impressions = int(campaign.get('impressions', 0))
            clicks = int(campaign.get('clicks', 0))
            conversions = int(campaign.get('conversions', 0))
            
            account_metrics['total_spend'] += spend
            account_metrics['total_impressions'] += impressions
            account_metrics['total_clicks'] += clicks
            account_metrics['total_conversions'] += conversions
            
            # Calculate campaign performance metrics
            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            cpc = spend / clicks if clicks > 0 else 0
            conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
            cpa = spend / conversions if conversions > 0 else 0
            
            campaign_metrics = {
                'name': campaign.get('name', ''),
                'spend': spend,
                'impressions': impressions,
                'clicks': clicks,
                'conversions': conversions,
                'ctr': ctr,
                'cpc': cpc,
                'conversion_rate': conversion_rate,
                'cpa': cpa
            }
            
            # Classify campaign performance
            if conversion_rate > 2.0 and ctr > 1.0:
                account_metrics['best_performing_campaigns'].append(campaign_metrics)
            elif (conversion_rate < 1.0 or ctr < 0.5) and spend > 100:
                account_metrics['underperforming_campaigns'].append(campaign_metrics)
        
        # Calculate averages
        if len(campaigns) > 0:
            account_metrics['average_ctr'] = (account_metrics['total_clicks'] / account_metrics['total_impressions'] * 100) if account_metrics['total_impressions'] > 0 else 0
            account_metrics['average_cpc'] = account_metrics['total_spend'] / account_metrics['total_clicks'] if account_metrics['total_clicks'] > 0 else 0
            account_metrics['average_conversion_rate'] = (account_metrics['total_conversions'] / account_metrics['total_clicks'] * 100) if account_metrics['total_clicks'] > 0 else 0
            account_metrics['average_cpa'] = account_metrics['total_spend'] / account_metrics['total_conversions'] if account_metrics['total_conversions'] > 0 else 0
        
        return account_metrics

    def _format_ad_data(self, data: Dict[str, Any]) -> str:
        """Format ad account data for AI analysis."""
        campaigns = data.get('campaigns', [])
        ad_sets = data.get('ad_sets', [])
        ads = data.get('ads', [])
        
        prompt = "Here is the raw Facebook Ads account data with full conversion tracking:\n\n"
        
        # Add account-level summary
        total_spend = sum(float(campaign.get('spend', 0)) for campaign in campaigns)
        total_impressions = sum(int(campaign.get('impressions', 0)) for campaign in campaigns)
        total_clicks = sum(int(campaign.get('clicks', 0)) for campaign in campaigns)
        total_conversions = sum(int(campaign.get('conversions', 0)) for campaign in campaigns)
        
        # Calculate funnel metrics
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        cpa = (total_spend / total_conversions) if total_conversions > 0 else 0
        
        prompt += f"""Account Overview and Conversion Funnel:
Total Spend: ${total_spend:,.2f}
Total Impressions: {total_impressions:,}
Total Clicks: {total_clicks:,}
Total Purchases (Conversions): {total_conversions:,}

Funnel Metrics:
Click-Through Rate (CTR): {ctr:.2f}%
Cost per Click (CPC): ${cpc:.2f}
Purchase Conversion Rate: {conversion_rate:.2f}%
Cost per Purchase: ${cpa:.2f}

Campaign Performance (with conversion data):\n"""
        
        # Add campaign data with enhanced conversion metrics
        for campaign in campaigns:
            spend = float(campaign.get('spend', 0))
            impressions = int(campaign.get('impressions', 0))
            clicks = int(campaign.get('clicks', 0))
            conversions = int(campaign.get('conversions', 0))
            
            # Calculate campaign-specific metrics
            campaign_ctr = (clicks / impressions * 100) if impressions > 0 else 0
            campaign_cvr = (conversions / clicks * 100) if clicks > 0 else 0
            campaign_cpc = spend / clicks if clicks > 0 else 0
            campaign_cpa = spend / conversions if conversions > 0 else 0
            
            prompt += f"""
Campaign: {campaign.get('name', 'Unnamed Campaign')}
Status: {campaign.get('status', 'Unknown')}
Objective: {campaign.get('objective', 'Unknown')}
Daily Budget: ${float(campaign.get('daily_budget', 0)):.2f}

Performance Metrics:
Spend: ${spend:.2f}
Impressions: {impressions:,}
Clicks: {clicks:,}
Purchases: {conversions:,}

Conversion Metrics:
CTR: {campaign_ctr:.2f}%
CPC: ${campaign_cpc:.2f}
Purchase Conversion Rate: {campaign_cvr:.2f}%
Cost per Purchase: ${campaign_cpa:.2f}

Rankings:
Quality Ranking: {campaign.get('quality_ranking', 'Unknown')}
Engagement Ranking: {campaign.get('engagement_ranking', 'Unknown')}
"""

        # Add ad set data with conversion focus
        if ad_sets:
            prompt += "\nAd Set Performance (with conversion data):\n"
            for ad_set in ad_sets:
                spend = float(ad_set.get('spend', 0))
                impressions = int(ad_set.get('impressions', 0))
                clicks = int(ad_set.get('clicks', 0))
                conversions = int(ad_set.get('conversions', 0))
                
                # Calculate ad set metrics
                ad_set_ctr = (clicks / impressions * 100) if impressions > 0 else 0
                ad_set_cvr = (conversions / clicks * 100) if clicks > 0 else 0
                ad_set_cpc = spend / clicks if clicks > 0 else 0
                ad_set_cpa = spend / conversions if conversions > 0 else 0
                
                prompt += f"""
Ad Set: {ad_set.get('name', 'Unnamed Ad Set')}
Campaign: {next((c.get('name', 'Unknown') for c in campaigns if c.get('id') == ad_set.get('campaign_id')), 'Unknown')}
Optimization Goal: {ad_set.get('optimization_goal', 'Unknown')}
Daily Budget: ${float(ad_set.get('daily_budget', 0)):.2f}

Performance & Conversion Data:
Spend: ${spend:.2f}
Impressions: {impressions:,}
Clicks: {clicks:,}
Purchases: {conversions:,}
CTR: {ad_set_ctr:.2f}%
CPC: ${ad_set_cpc:.2f}
Purchase Conversion Rate: {ad_set_cvr:.2f}%
Cost per Purchase: ${ad_set_cpa:.2f}
"""

        # Add ad-level data with conversion focus
        if ads:
            prompt += "\nAd Performance (with conversion data):\n"
            for ad in ads:
                spend = float(ad.get('spend', 0))
                impressions = int(ad.get('impressions', 0))
                clicks = int(ad.get('clicks', 0))
                conversions = int(ad.get('conversions', 0))
                
                # Calculate ad metrics
                ad_ctr = (clicks / impressions * 100) if impressions > 0 else 0
                ad_cvr = (conversions / clicks * 100) if clicks > 0 else 0
                ad_cpc = spend / clicks if clicks > 0 else 0
                ad_cpa = spend / conversions if conversions > 0 else 0
                
                prompt += f"""
Ad: {ad.get('name', 'Unnamed Ad')}
Campaign: {next((c.get('name', 'Unknown') for c in campaigns if c.get('id') == ad.get('campaign_id')), 'Unknown')}
Ad Set: {next((a.get('name', 'Unknown') for a in ad_sets if a.get('id') == ad.get('adset_id')), 'Unknown')}
Status: {ad.get('status', 'Unknown')}

Performance & Conversion Data:
Spend: ${spend:.2f}
Impressions: {impressions:,}
Clicks: {clicks:,}
Purchases: {conversions:,}
CTR: {ad_ctr:.2f}%
CPC: ${ad_cpc:.2f}
Purchase Conversion Rate: {ad_cvr:.2f}%
Cost per Purchase: ${ad_cpa:.2f}

Rankings:
Quality Ranking: {ad.get('quality_ranking', 'Unknown')}
Engagement Ranking: {ad.get('engagement_ranking', 'Unknown')}
"""

        prompt += "\nAnalyze this data focusing on the full conversion funnel from impressions to purchases. For each recommendation, include:\n"
        prompt += "1. Current conversion metrics and performance\n"
        prompt += "2. Specific opportunities for improvement\n"
        prompt += "3. How to optimize for better conversion rates\n"
        prompt += "4. Expected impact on ROAS and conversion metrics\n"
        prompt += "\nFocus on identifying:\n"
        prompt += "- Campaigns, ad sets, and ads with strong purchase performance\n"
        prompt += "- Opportunities to improve conversion rates\n"
        prompt += "- Budget optimization based on ROAS\n"
        prompt += "- Creative and audience optimizations to drive more purchases\n"
        prompt += "- Cost efficiency opportunities (CPC, CPA)\n"
        prompt += "- Scaling opportunities for high-converting campaigns\n"

        return prompt

    def analyze_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Facebook ad account data using OpenAI's GPT model."""
        try:
            logger.info("Starting OpenAI analysis of ad account data")
            
            # Format the data for analysis
            formatted_data = self._format_ad_data(account_data)
            
            # Create the analysis prompt
            prompt = self._create_analysis_prompt(formatted_data)
            
            # Make the API call with retry logic
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    # Test connection before making the actual request
                    try:
                        self.client.models.list()
                    except Exception as conn_error:
                        logger.error(f"OpenAI API connection test failed: {str(conn_error)}")
                        if attempt == max_retries - 1:
                            return {
                                'success': False,
                                'error': 'Failed to connect to OpenAI API. Please check your internet connection and API key.'
                            }
                        time.sleep(retry_delay)
                        continue
                    
                    response = self.client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an expert digital marketing analyst specializing in Facebook Ads optimization."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=3000
                    )
                    
                    # Process the response
                    analysis = self._process_response(response)
                    logger.info("Successfully completed OpenAI analysis")
                    return analysis
                    
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        logger.error(f"OpenAI API error after {max_retries} attempts: {str(e)}")
                        return {
                            'success': False,
                            'error': f'OpenAI analysis failed: {str(e)}'
                        }
                    logger.warning(f"OpenAI API attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {str(e)}")
            return {
                'success': False,
                'error': f'OpenAI analysis failed: {str(e)}'
            }

    def _create_analysis_prompt(self, data: str) -> str:
        """Create the prompt for the OpenAI analysis"""
        try:
            # The data parameter is already a formatted string
            prompt = f"""Analyze this Facebook Ads account data and provide recommendations for optimization:

{data}

Please provide:
1. Overall account performance assessment
2. Specific recommendations for improvement
3. Potential cost savings opportunities
4. Priority action items
5. Expected impact of implementing recommendations

Format the response as a JSON object with the following structure:
{{
    "success": true,
    "analysis_results": {{
        "recommendations": [
            {{
                "category": "string",
                "recommendation": "string",
                "severity": "high|medium|low",
                "action_items": ["string"],
                "metrics_impact": {{
                    "roas_improvement": number,
                    "ctr_improvement": number,
                    "cpc_reduction": number,
                    "cpa_reduction": number
                }},
                "potential_savings": number
            }}
        ],
        "metrics": {{
            "ctr": number,
            "cpc": number,
            "cpm": number,
            "conversion_rate": number,
            "roas": number
        }}
    }}
}}"""
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error creating analysis prompt: {str(e)}")
            raise

    def _process_response(self, response):
        """Process the OpenAI API response"""
        try:
            # Extract the analysis from the response
            analysis_text = response.choices[0].message.content
            
            # Parse the JSON response
            analysis = json.loads(analysis_text)
            
            # Validate the response structure
            if not analysis.get('success'):
                raise ValueError("Analysis response indicates failure")
                
            if not analysis.get('analysis_results'):
                raise ValueError("Missing analysis results in response")
                
            return analysis
            
        except Exception as e:
            logger.error(f"Error processing OpenAI response: {str(e)}")
            raise

    def _structure_recommendations(self, ai_response: str) -> List[Dict[str, Any]]:
        """Convert AI response into structured recommendations."""
        recommendations = []
        self.logger.debug(f"Starting to parse AI response: {ai_response}")
        
        # Split response into sections by numbered items
        sections = re.split(r'\n\d+\.', ai_response)
        if sections and not sections[0].strip():  # Remove empty first section if exists
            sections = sections[1:]
            
        self.logger.debug(f"Split into {len(sections)} sections")
        
        for section in sections:
            if not section.strip():
                continue
                
            try:
                # Extract main recommendation and action items
                lines = [line.strip() for line in section.split('\n') if line.strip()]
                if not lines:
                    continue
                    
                title = lines[0].strip()
                current_rec = None
                action_items = []
                
                for line in lines[1:]:
                    if line.startswith('-'):
                        if current_rec:  # Save previous recommendation if exists
                            recommendations.append(current_rec)
                        
                        # Start new recommendation
                        rec_text = line.lstrip('- ').strip()
                        
                        # Extract impact percentages
                        impact_match = re.search(r'(?:by|to)\s+(\d+(?:\.\d+)?)%', rec_text)
                        impact_value = float(impact_match.group(1)) if impact_match else 15.0
                        
                        metrics_impact = {
                            'roas_improvement': impact_value if 'ROAS' in rec_text else 0.0,
                            'ctr_improvement': impact_value if 'CTR' in rec_text else 0.0,
                            'cpc_reduction': impact_value if 'CPC' in rec_text else 0.0,
                            'cpa_reduction': impact_value if 'CPA' in rec_text or 'cost per conversion' in rec_text.lower() else 0.0
                        }
                        
                        # If no specific metric mentioned, assign to most relevant based on context
                        if all(v == 0.0 for v in metrics_impact.values()):
                            if 'cost' in rec_text.lower():
                                metrics_impact['cpa_reduction'] = impact_value
                            elif 'click' in rec_text.lower():
                                metrics_impact['ctr_improvement'] = impact_value
                            else:
                                metrics_impact['roas_improvement'] = impact_value
                        
                        severity = 'high' if impact_value >= 20 or \
                                 any(word in rec_text.lower() for word in ['critical', 'significant', 'immediate', 'urgent']) \
                                 else 'medium'
                        
                        current_rec = {
                            'type': 'performance_improvement',
                            'category': title,
                            'recommendation': rec_text,
                            'severity': severity,
                            'action_items': [],
                            'metrics_impact': metrics_impact,
                            'potential_savings': impact_value * 2.0  # Estimate potential savings
                        }
                    elif line.startswith('  -') and current_rec:
                        action_item = line.lstrip(' -').strip()
                        if action_item:
                            current_rec['action_items'].append(action_item)
                
                # Add the last recommendation
                if current_rec:
                    recommendations.append(current_rec)
                    
            except Exception as e:
                self.logger.error(f"Error processing section: {str(e)}", exc_info=True)
                continue
        
        self.logger.debug(f"Final recommendations: {recommendations}")
        
        # Sort recommendations by severity and potential impact
        recommendations.sort(
            key=lambda x: (
                2 if x['severity'] == 'high' else 1,
                sum(x['metrics_impact'].values())
            ),
            reverse=True
        )
        
        return recommendations
    
    def _parse_impact(self, impact_text: str) -> Dict[str, float]:
        """Parse impact estimates from AI response."""
        impact = {}
        try:
            if 'ROAS:' in impact_text:
                impact['roas_improvement'] = float(impact_text.split('ROAS:')[1].split('%')[0].strip())
            if 'CTR:' in impact_text:
                impact['ctr_improvement'] = float(impact_text.split('CTR:')[1].split('%')[0].strip())
            if 'CPC:' in impact_text:
                impact['cpc_reduction'] = float(impact_text.split('CPC:')[1].split('%')[0].strip())
            if 'CPA:' in impact_text:
                impact['cpa_reduction'] = float(impact_text.split('CPA:')[1].split('%')[0].strip())
        except:
            pass
        return impact 