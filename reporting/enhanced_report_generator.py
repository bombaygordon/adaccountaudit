import os
import pdfkit
import jinja2
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend which is non-interactive
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
import matplotlib.cm as cm
from datetime import datetime, timedelta
import logging
import pandas as pd
import json
from matplotlib.colors import LinearSegmentedColormap

class EnhancedReportGenerator:
    """
    Generate comprehensive, data-driven audit reports with advanced 
    visualizations from analysis results.
    """
    
    def __init__(self, report_dir='reports'):
        """
        Initialize the report generator.
        
        Args:
            report_dir (str): Directory to save generated reports
        """
        self.report_dir = report_dir
        self.logger = logging.getLogger(__name__)
        
        # Create reports directory if it doesn't exist
        os.makedirs(report_dir, exist_ok=True)
        
        # Set up custom colors
        self.color_palette = {
            'primary': '#ff6b35',  # Orange
            'secondary': '#2ec4b6',  # Teal
            'tertiary': '#6772e5',  # Purple
            'success': '#3ecf8e',  # Green
            'warning': '#f9a03f',  # Amber
            'danger': '#e73142',  # Red
            'neutral': '#4f566b',  # Dark gray
            'light': '#f5f5f5'     # Light gray
        }
        
        # Define custom gradient colormap for heatmaps
        self.gradient_cmap = LinearSegmentedColormap.from_list(
            'custom_gradient', 
            ['#f5f5f5', '#e6f2ff', '#99ccff', '#3399ff', '#0066cc']
        )
        
        # Platform-specific colors
        self.platform_colors = {
            'facebook': '#1877f2',  # Facebook blue
            'instagram': '#c32aa3',  # Instagram purple/pink
            'tiktok': '#000000',     # TikTok black
            'google': '#4285F4',     # Google blue
            'twitter': '#1DA1F2',    # Twitter blue
            'linkedin': '#0077B5',   # LinkedIn blue
            'pinterest': '#E60023',  # Pinterest red
            'snapchat': '#FFFC00',   # Snapchat yellow
            'youtube': '#FF0000'     # YouTube red
        }
    
    def generate_report(self, analysis_results, client_name, agency_name=None, 
                        filename=None, lookback_days=30, template_name='enhanced_report_template.html'):
        """
        Generate a comprehensive PDF report from analysis results.
        
        Args:
            analysis_results (dict): Results from enhanced analysis
            client_name (str): Name of the client
            agency_name (str, optional): Name of the agency
            filename (str, optional): Custom filename for the report
            lookback_days (int): Number of days in the analysis period
            template_name (str): HTML template filename
            
        Returns:
            str: Path to the generated PDF report
        """
        self.logger.info(f"Generating enhanced report for {client_name}")
        
        # Set default agency name if not provided
        agency_name = agency_name or "Your Agency"
        
        # Generate charts
        charts = self._generate_charts(analysis_results)
        
        # Prepare report data
        report_data = self._prepare_report_data(analysis_results, client_name, agency_name, lookback_days)
        
        # Add charts to report data
        report_data['charts'] = charts
        
        # Generate HTML content
        html_content = self._render_template(template_name, report_data)
        
        # Save HTML for debugging (optional)
        html_path = os.path.join(self.report_dir, f"{client_name.replace(' ', '_')}_report.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate PDF
        pdf_path = self._generate_pdf(html_content, filename, client_name)
        
        self.logger.info(f"Report generated successfully: {pdf_path}")
        
        return pdf_path
    
    def _prepare_report_data(self, results, client_name, agency_name, lookback_days):
        """
        Prepare data for the report template.
        
        Args:
            results (dict): Analysis results
            client_name (str): Name of the client
            agency_name (str): Name of the agency
            lookback_days (int): Number of days in the analysis period
            
        Returns:
            dict: Prepared report data
        """
        # Get date information
        report_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get platform information
        platform = results.get('platform', 'Facebook')
        
        # Format metrics
        account_overview = results.get('account_overview', {})
        
        total_spend = account_overview.get('total_spend', 0)
        total_impressions = account_overview.get('total_impressions', 0)
        total_clicks = account_overview.get('total_clicks', 0)
        total_conversions = account_overview.get('total_conversions', 0)
        
        # Format currency values
        formatted_metrics = {
            'total_spend': f"${total_spend:,.2f}",
            'total_impressions': f"{total_impressions:,}",
            'total_clicks': f"{total_clicks:,}",
            'total_conversions': f"{total_conversions:,}",
            'ctr': f"{account_overview.get('ctr', 0):.2f}%",
            'cpc': f"${account_overview.get('cpc', 0):.2f}",
            'cpm': f"${account_overview.get('cpm', 0):.2f}",
            'conversion_rate': f"{account_overview.get('conversion_rate', 0):.2f}%",
            'cpa': f"${account_overview.get('cpa', 0):.2f}",
            'roas': f"{account_overview.get('roas', 0):.2f}x"
        }
        
        # Format improvements and savings
        potential_savings = results.get('potential_savings', 0)
        improvement_percentage = results.get('potential_improvement_percentage', 0)
        
        # Get recommendations
        recommendations = results.get('recommendations', [])
        
        # Categorize recommendations
        categorized_recommendations = self._categorize_recommendations(recommendations)
        
        # Prepare report data
        report_data = {
            'client_name': client_name,
            'agency_name': agency_name,
            'report_date': report_date,
            'analysis_period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': lookback_days
            },
            'platform': platform,
            'account_overview': account_overview,
            'formatted_metrics': formatted_metrics,
            'potential_savings': f"${potential_savings:,.2f}",
            'potential_savings_raw': potential_savings,
            'improvement_percentage': f"{improvement_percentage:.1f}%",
            'improvement_percentage_raw': improvement_percentage,
            'recommendations': recommendations,
            'categorized_recommendations': categorized_recommendations,
            'total_recommendations': len(recommendations),
            'recommendations_by_severity': {
                'high': len([r for r in recommendations if r.get('severity') == 'high']),
                'medium': len([r for r in recommendations if r.get('severity') == 'medium']),
                'low': len([r for r in recommendations if r.get('severity') == 'low'])
            }
        }
        
        return report_data
    
    def _categorize_recommendations(self, recommendations):
        """
        Categorize recommendations by type.
        
        Args:
            recommendations (list): List of recommendations
            
        Returns:
            dict: Categorized recommendations
        """
        categories = {
            'budget_optimization': {
                'title': 'Budget Optimization',
                'icon': 'dollar-sign',
                'items': []
            },
            'audience_targeting': {
                'title': 'Audience Targeting',
                'icon': 'users',
                'items': []
            },
            'creative_performance': {
                'title': 'Creative Performance',
                'icon': 'image',
                'items': []
            },
            'ad_fatigue': {
                'title': 'Ad Fatigue',
                'icon': 'battery-low',
                'items': []
            }
        }
        
        # Categorize each recommendation
        for rec in recommendations:
            rec_type = rec.get('type', '')
            
            if any(term in rec_type for term in ['budget', 'cpa', 'cpc', 'allocation']):
                categories['budget_optimization']['items'].append(rec)
            elif any(term in rec_type for term in ['audience', 'targeting', 'segment']):
                categories['audience_targeting']['items'].append(rec)
            elif any(term in rec_type for term in ['creative', 'top_', 'bottom_']):
                categories['creative_performance']['items'].append(rec)
            elif 'fatigue' in rec_type:
                categories['ad_fatigue']['items'].append(rec)
            else:
                # Default to budget optimization for unknown types
                categories['budget_optimization']['items'].append(rec)
        
        # Only include categories that have recommendations
        categorized = {k: v for k, v in categories.items() if v['items']}
        
        return categorized
    
    def _generate_charts(self, results):
        """
        Generate all charts for the report.
        
        Args:
            results (dict): Analysis results
            
        Returns:
            dict: Chart images encoded as base64 strings
        """
        charts = {}
        
        try:
            # Generate savings distribution chart
            charts['savings_distribution'] = self._generate_savings_chart(results)
            
            # Generate performance comparison chart
            charts['performance_comparison'] = self._generate_performance_chart(results)
            
            # Generate audience insights chart if available
            audience_data = results.get('insights', {}).get('audience_targeting', {})
            if audience_data:
                charts['audience_insights'] = self._generate_audience_chart(audience_data)
            
            # Generate budget allocation chart
            budget_data = results.get('metrics', {}).get('budget_efficiency', {}).get('budget_distribution', {})
            if budget_data:
                charts['budget_allocation'] = self._generate_budget_chart(budget_data)
            
            # Generate recommendations by category chart
            recommendations = results.get('recommendations', [])
            if recommendations:
                charts['recommendations_by_category'] = self._generate_recommendations_chart(recommendations)
            
            # Generate performance improvement gauge
            improvement = results.get('potential_improvement_percentage', 0)
            charts['improvement_gauge'] = self._generate_gauge_chart(improvement)
            
        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")
        
        return charts
    
    def _generate_savings_chart(self, results):
        """
        Generate a chart showing the distribution of potential savings.
        
        Args:
            results (dict): Analysis results
            
        Returns:
            str: Chart image encoded as base64 string
        """
        # Get recommendations
        recommendations = results.get('recommendations', [])
        
        if not recommendations:
            return None
        
        # Group recommendations by category
        categories = {
            'Budget Allocation': 0,
            'Ad Fatigue': 0,
            'Audience Targeting': 0,
            'Creative Performance': 0
        }
        
        # Sum potential savings by category
        for rec in recommendations:
            rec_type = rec.get('type', '')
            savings = rec.get('potential_savings', 0)
            
            if any(term in rec_type for term in ['budget', 'cpa', 'cpc', 'allocation']):
                categories['Budget Allocation'] += savings
            elif any(term in rec_type for term in ['audience', 'targeting', 'segment']):
                categories['Audience Targeting'] += savings
            elif any(term in rec_type for term in ['creative', 'top_', 'bottom_']):
                categories['Creative Performance'] += savings
            elif 'fatigue' in rec_type:
                categories['Ad Fatigue'] += savings
        
        # Remove categories with no savings
        categories = {k: v for k, v in categories.items() if v > 0}
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Create bar chart
        bars = plt.bar(
            categories.keys(),
            categories.values(),
            color=[self.color_palette['primary'], self.color_palette['secondary'],
                  self.color_palette['tertiary'], self.color_palette['warning']]
        )
        
        # Add labels and formatting
        plt.title('Potential Savings by Category', fontsize=16, pad=20)
        plt.ylabel('Potential Savings ($)', fontsize=14)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.,
                height + 5,
                f'${height:.2f}',
                ha='center',
                va='bottom',
                fontsize=12
            )
        
        # Add styling
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.tight_layout()
        
        # Convert to base64 image
        return self._fig_to_base64(plt.gcf())
    
    def _generate_performance_chart(self, results):
        """
        Generate a chart comparing key performance metrics.
        
        Args:
            results (dict): Analysis results
            
        Returns:
            str: Chart image encoded as base64 string
        """
        # Get account overview metrics
        account_overview = results.get('account_overview', {})
        
        if not account_overview:
            return None
        
        # Get industry benchmarks (placeholder values)
        # In a real implementation, these would come from actual industry data
        benchmarks = {
            'ctr': 0.9,  # Industry average CTR %
            'cpc': 1.2,  # Industry average CPC $
            'conversion_rate': 2.5,  # Industry average conversion rate %
            'cpa': 30.0  # Industry average CPA $
        }
        
        # Calculate relative performance (account vs benchmark)
        # For CTR and conversion rate, higher is better
        # For CPC and CPA, lower is better
        ctr_index = (account_overview.get('ctr', 0) / benchmarks['ctr']) * 100
        conv_rate_index = (account_overview.get('conversion_rate', 0) / benchmarks['conversion_rate']) * 100
        cpc_index = (benchmarks['cpc'] / account_overview.get('cpc', benchmarks['cpc'])) * 100
        cpa_index = (benchmarks['cpa'] / account_overview.get('cpa', benchmarks['cpa'])) * 100
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Create bar chart
        categories = ['CTR', 'Conversion Rate', 'CPC', 'CPA']
        values = [ctr_index, conv_rate_index, cpc_index, cpa_index]
        
        # Use colors based on performance
        colors = []
        for value in values:
            if value >= 120:
                colors.append(self.color_palette['success'])
            elif value >= 80:
                colors.append(self.color_palette['primary'])
            else:
                colors.append(self.color_palette['danger'])
        
        bars = plt.bar(categories, values, color=colors)
        
        # Add benchmark line
        plt.axhline(y=100, color='gray', linestyle='--', alpha=0.7, label='Industry Benchmark')
        
        # Add labels and formatting
        plt.title('Performance vs. Industry Benchmarks', fontsize=16, pad=20)
        plt.ylabel('Performance Index (%)', fontsize=14)
        plt.ylim(0, max(200, max(values) * 1.2))  # Set reasonable y-axis limit
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.,
                height + 5,
                f'{height:.0f}%',
                ha='center',
                va='bottom',
                fontsize=12
            )
        
        # Add legend
        plt.legend(loc='best')
        
        # Add styling
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.tight_layout()
        
        # Convert to base64 image
        return self._fig_to_base64(plt.gcf())
    
    def _generate_audience_chart(self, audience_data):
        """
        Generate a chart visualizing audience insights.
        
        Args:
            audience_data (dict): Audience targeting analysis data
            
        Returns:
            str: Chart image encoded as base64 string
        """
        # Check if we have age segment data
        if 'age' not in audience_data:
            # Try gender data instead
            if 'gender' in audience_data:
                return self._generate_gender_chart(audience_data['gender'])
            return None
        
        # Extract age segment data
        age_data = audience_data['age']
        
        # Get segment metrics
        segment_metrics = age_data.get('segment_metrics', [])
        
        if not segment_metrics:
            return None
        
        # Create a DataFrame for easier manipulation
        df = pd.DataFrame(segment_metrics)
        
        # Check if we have conversion rate data
        has_conv_rate = 'conversion_rate' in df.columns
        
        # Sort by age group (assuming age values like '18-24', '25-34', etc.)
        if 'age' in df.columns:
            # Sort age groups naturally
            age_order = ['13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']
            df['age_order'] = df['age'].apply(lambda x: age_order.index(x) if x in age_order else 999)
            df = df.sort_values('age_order')
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Set up two y-axes for different metrics
        ax1 = plt.gca()
        ax2 = ax1.twinx()
        
        # Plot CTR as bars
        bars = ax1.bar(df['age'], df['ctr'], color=self.color_palette['primary'], alpha=0.7, label='CTR (%)')
        
        # Add conversion rate as line if available
        if has_conv_rate:
            line = ax2.plot(df['age'], df['conversion_rate'], 'o-', color=self.color_palette['tertiary'], 
                           linewidth=3, markersize=8, label='Conversion Rate (%)')
        
        # Add labels and formatting
        plt.title('Performance Metrics by Age Group', fontsize=16, pad=20)
        ax1.set_xlabel('Age Group', fontsize=14)
        ax1.set_ylabel('CTR (%)', fontsize=14, color=self.color_palette['primary'])
        
        if has_conv_rate:
            ax2.set_ylabel('Conversion Rate (%)', fontsize=14, color=self.color_palette['tertiary'])
            
            # Add combined legend
            lines, labels = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines + lines2, labels + labels2, loc='upper right')
        
        # Add styling
        ax1.grid(axis='y', linestyle='--', alpha=0.3)
        ax1.tick_params(axis='y', labelcolor=self.color_palette['primary'])
        if has_conv_rate:
            ax2.tick_params(axis='y', labelcolor=self.color_palette['tertiary'])
        
        # Adjust tick sizes
        plt.xticks(fontsize=12)
        ax1.tick_params(axis='y', labelsize=12)
        if has_conv_rate:
            ax2.tick_params(axis='y', labelsize=12)
        
        plt.tight_layout()
        
        # Convert to base64 image
        return self._fig_to_base64(plt.gcf())
    
    def _generate_gender_chart(self, gender_data):
        """
        Generate a chart visualizing gender-based performance.
        
        Args:
            gender_data (dict): Gender targeting analysis data
            
        Returns:
            str: Chart image encoded as base64 string
        """
        # Get segment metrics
        segment_metrics = gender_data.get('segment_metrics', [])
        
        if not segment_metrics:
            return None
        
        # Create a DataFrame for easier manipulation
        df = pd.DataFrame(segment_metrics)
        
        # Check if we have conversion rate data
        has_conv_rate = 'conversion_rate' in df.columns
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Plot CTR by gender as bar chart
        ax1.bar(df['gender'], df['ctr'], color=self.color_palette['primary'])
        ax1.set_title('CTR by Gender', fontsize=14)
        ax1.set_ylabel('CTR (%)', fontsize=12)
        ax1.set_ylim(0, df['ctr'].max() * 1.2)
        
        # Add value labels
        for i, ctr in enumerate(df['ctr']):
            ax1.text(i, ctr + (df['ctr'].max() * 0.05), f'{ctr:.2f}%', 
                    ha='center', va='bottom', fontsize=12)
        
        # Plot conversion rate by gender if available
        if has_conv_rate:
            ax2.bar(df['gender'], df['conversion_rate'], color=self.color_palette['tertiary'])
            ax2.set_title('Conversion Rate by Gender', fontsize=14)
            ax2.set_ylabel('Conversion Rate (%)', fontsize=12)
            ax2.set_ylim(0, df['conversion_rate'].max() * 1.2)
            
            # Add value labels
            for i, cr in enumerate(df['conversion_rate']):
                ax2.text(i, cr + (df['conversion_rate'].max() * 0.05), f'{cr:.2f}%', 
                        ha='center', va='bottom', fontsize=12)
        else:
            # If no conversion rate, plot CPC instead
            ax2.bar(df['gender'], df['cpc'], color=self.color_palette['secondary'])
            ax2.set_title('CPC by Gender', fontsize=14)
            ax2.set_ylabel('CPC ($)', fontsize=12)
            ax2.set_ylim(0, df['cpc'].max() * 1.2)
            
            # Add value labels
            for i, cpc in enumerate(df['cpc']):
                ax2.text(i, cpc + (df['cpc'].max() * 0.05), f'${cpc:.2f}', 
                        ha='center', va='bottom', fontsize=12)
        
        # Add styling
        ax1.grid(axis='y', linestyle='--', alpha=0.3)
        ax2.grid(axis='y', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        
        # Convert to base64 image
        return self._fig_to_base64(plt.gcf())
    
    def _generate_budget_chart(self, budget_data):
        """
        Generate a chart visualizing budget allocation.
        
        Args:
            budget_data (dict): Budget allocation data
            
        Returns:
            str: Chart image encoded as base64 string
        """
        # Get quartile data
        quartiles = budget_data.get('quartiles', {})
        
        if not quartiles:
            return None
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Create pie chart of spend distribution
        labels = ['Top 25% Performers', 'Mid-High Performers', 'Mid-Low Performers', 'Bottom 25% Performers']
        sizes = [
            quartiles.get('top_25', {}).get('spend_pct', 25),
            quartiles.get('mid_high', {}).get('spend_pct', 25),
            quartiles.get('mid_low', {}).get('spend_pct', 25),
            quartiles.get('bottom_25', {}).get('spend_pct', 25)
        ]
        
        colors = [
            self.color_palette['success'],
            self.color_palette['primary'],
            self.color_palette['warning'],
            self.color_palette['danger']
        ]
        
        # Explode the top performers slice
        explode = (0.1, 0, 0, 0)
        
        # Create pie chart
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
               shadow=True, startangle=90, textprops={'fontsize': 12})
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        plt.axis('equal')
        
        # Add title
        plt.title('Budget Allocation by Performance Quartile', fontsize=16, pad=20)
        
        plt.tight_layout()
        
        # Convert to base64 image
        return self._fig_to_base64(plt.gcf())
    
    def _generate_recommendations_chart(self, recommendations):
        """
        Generate a chart showing recommendations by category and severity.
        
        Args:
            recommendations (list): List of recommendations
            
        Returns:
            str: Chart image encoded as base64 string
        """
        # Count recommendations by category and severity
        categories = {
            'Budget': {'high': 0, 'medium': 0, 'low': 0},
            'Audience': {'high': 0, 'medium': 0, 'low': 0},
            'Creative': {'high': 0, 'medium': 0, 'low': 0},
            'Ad Fatigue': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        # Categorize recommendations
        for rec in recommendations:
            rec_type = rec.get('type', '')
            severity = rec.get('severity', 'medium')
            
            if any(term in rec_type for term in ['budget', 'cpa', 'cpc', 'allocation']):
                categories['Budget'][severity] += 1
            elif any(term in rec_type for term in ['audience', 'targeting', 'segment']):
                categories['Audience'][severity] += 1
            elif any(term in rec_type for term in ['creative', 'top_', 'bottom_']):
                categories['Creative'][severity] += 1
            elif 'fatigue' in rec_type:
                categories['Ad Fatigue'][severity] += 1
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Set up data for stacked bar chart
        category_names = list(categories.keys())
        high_counts = [categories[cat]['high'] for cat in category_names]
        medium_counts = [categories[cat]['medium'] for cat in category_names]
        low_counts = [categories[cat]['low'] for cat in category_names]
        
        # Create stacked bar chart
        bar_width = 0.5
        r = range(len(category_names))
        
        # Plot bars
        plt.bar(r, high_counts, color=self.color_palette['danger'], edgecolor='white',
               width=bar_width, label='High Priority')
        plt.bar(r, medium_counts, color=self.color_palette['warning'], edgecolor='white',
               width=bar_width, bottom=high_counts, label='Medium Priority')
        plt.bar(r, low_counts, color=self.color_palette['success'], edgecolor='white',
               width=bar_width, bottom=[high_counts[i] + medium_counts[i] for i in range(len(high_counts))],
               label='Low Priority')
        
        # Add labels and formatting
        plt.xlabel('Category', fontsize=14)
        plt.ylabel('Number of Recommendations', fontsize=14)
        plt.title('Recommendations by Category and Priority', fontsize=16, pad=20)
        plt.xticks(r, category_names, fontsize=12)
        plt.yticks(fontsize=12)
        
        # Add legend
        plt.legend(loc='upper right')
        
        # Add styling
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        
        # Add total count labels on top of stacks
        for i in range(len(category_names)):
            total = high_counts[i] + medium_counts[i] + low_counts[i]
            if total > 0:
                plt.text(i, total + 0.3, str(total), ha='center', va='bottom', fontsize=12)
        
        plt.tight_layout()
        
        # Convert to base64 image
        return self._fig_to_base64(plt.gcf())
    
    def _generate_gauge_chart(self, improvement_percentage):
        """
        Generate a gauge chart showing potential improvement percentage.
        
        Args:
            improvement_percentage (float): Potential improvement percentage
            
        Returns:
            str: Chart image encoded as base64 string
        """
        # Create figure
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, polar=True)
        
        # Define gauge parameters
        gauge_min = 0
        gauge_max = 50  # Max expected improvement percentage
        
        # Ensure value is within range
        value = min(max(improvement_percentage, gauge_min), gauge_max)
        
        # Calculate angle parameters
        angle_range = 180  # Semicircle
        start_angle = 180  # Bottom of semicircle
        
        # Convert value to angle
        angle = start_angle - (value / gauge_max * angle_range)
        angle_rad = np.radians(angle)
        
        # Create gauge background (colored arcs)
        # Define color zones
        zone_boundaries = [0, 10, 25, 50]  # Percentage boundaries
        zone_colors = [self.color_palette['light'], self.color_palette['secondary'], 
                     self.color_palette['primary'], self.color_palette['success']]
        
        # Draw colored arcs for each zone
        for i in range(len(zone_boundaries) - 1):
            zone_start = zone_boundaries[i]
            zone_end = zone_boundaries[i + 1]
            
            # Convert percentages to angles
            start_angle_zone = start_angle - (zone_start / gauge_max * angle_range)
            end_angle_zone = start_angle - (zone_end / gauge_max * angle_range)
            
            # Create colored arc
            arc = np.linspace(np.radians(start_angle_zone), np.radians(end_angle_zone), 100)
            ax.fill_between(arc, 0.7, 0.9, color=zone_colors[i], alpha=0.8)
        
        # Draw needle
        ax.plot([0, angle_rad], [0, 0.8], color='black', linewidth=3)
        
        # Add a center circle
        circle = plt.Circle((0, 0), 0.1, color='darkgray', transform=ax.transData._b)
        ax.add_artist(circle)
        
        # Add percentage text
        ax.text(0, 0.4, f"{value:.1f}%", ha='center', va='center', 
               fontsize=24, fontweight='bold')
        
        # Add "Potential Improvement" text
        ax.text(0, 0.2, "Potential Improvement", ha='center', va='center',
               fontsize=12)
        
        # Add tick labels
        for percent in [0, 10, 25, 50]:
            # Calculate angle for this percentage
            tick_angle = start_angle - (percent / gauge_max * angle_range)
            tick_angle_rad = np.radians(tick_angle)
            
            # Calculate text position
            text_x = 0.95 * np.cos(tick_angle_rad)
            text_y = 0.95 * np.sin(tick_angle_rad)
            
            # Add text
            ax.text(tick_angle_rad, 0.95, f"{percent}%", ha='center', va='center', 
                   fontsize=10, fontweight='bold')
        
        # Clean up the gauge
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('N')
        ax.set_thetagrids([])
        ax.set_rgrids([])
        ax.set_ylim(0, 1)
        ax.spines['polar'].set_visible(False)
        ax.grid(False)
        
        plt.tight_layout()
        
        # Convert to base64 image
        return self._fig_to_base64(plt.gcf())
    
    def _fig_to_base64(self, fig):
        """
        Convert a matplotlib figure to a base64 encoded string.
        
        Args:
            fig (Figure): Matplotlib figure
            
        Returns:
            str: Base64 encoded string
        """
        # Create a bytes buffer for the image
        buf = io.BytesIO()
        
        # Save the figure to the buffer
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        
        # Close the figure to free memory
        plt.close(fig)
        
        # Get the image data from the buffer and encode as base64
        buf.seek(0)
        img_data = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_data
    
    def _render_template(self, template_name, data):
        """
        Render HTML template with the provided data.
        
        Args:
            template_name (str): Name of the template file
            data (dict): Data to render in the template
            
        Returns:
            str: Rendered HTML content
        """
        # Set up template environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('reporting/templates'),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        env.filters['currency'] = lambda value: f"${float(value):,.2f}"
        env.filters['number'] = lambda value: f"{float(value):,}"
        env.filters['percentage'] = lambda value: f"{float(value):.2f}%"
        
        try:
            # Load template
            template = env.get_template(template_name)
            
            # Render template with data
            return template.render(**data)
        except jinja2.exceptions.TemplateNotFound:
            self.logger.error(f"Template '{template_name}' not found")
            
            # Use a basic fallback template
            fallback_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Ad Account Audit Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    h1 { color: #ff6b35; }
                </style>
            </head>
            <body>
                <h1>Ad Account Audit Report</h1>
                <h2>{{ client_name }}</h2>
                <p>Report Date: {{ report_date }}</p>
                <h3>Summary</h3>
                <p>Potential Savings: {{ potential_savings }}</p>
                <p>Improvement Percentage: {{ improvement_percentage }}</p>
            </body>
            </html>
            """
            fallback_template = jinja2.Template(fallback_html)
            return fallback_template.render(**data)
    
    def _generate_pdf(self, html_content, filename=None, client_name="Client"):
        """
        Generate PDF from HTML content.
        
        Args:
            html_content (str): HTML content to convert to PDF
            filename (str, optional): Custom filename for the PDF
            client_name (str): Client name for the default filename
            
        Returns:
            str: Path to the generated PDF file
        """
        # Generate filename if not provided
        if not filename:
            sanitized_name = client_name.replace(' ', '_').lower()
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"{sanitized_name}_audit_report_{date_str}.pdf"
        
        # Ensure filename has .pdf extension
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Define output path
        output_path = os.path.join(self.report_dir, filename)
        
        # Configure PDF options
        options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None
        }
        
        try:
            # Generate PDF using pdfkit (wkhtmltopdf wrapper)
            pdfkit.from_string(html_content, output_path, options=options)
            return output_path
        except Exception as e:
            self.logger.error(f"Error generating PDF: {e}")
            return None