import os
import pdfkit
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import matplotlib.pyplot as plt
import io
import base64
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, audit_results, client_name, agency_name=None):
        """
        Initialize report generator with audit results.
        
        Args:
            audit_results (dict): Complete audit results 
            client_name (str): Name of the client
            agency_name (str, optional): Name of the agency
        """
        self.audit_results = audit_results
        self.client_name = client_name
        self.agency_name = agency_name or "Your Agency"
        self.report_date = datetime.now().strftime("%Y-%m-%d")
        self.charts = {}
        
    def _generate_charts(self):
        """Generate charts for the report"""
        try:
            # Generate potential savings chart
            self._generate_savings_chart()
            
            # Generate audience performance chart
            self._generate_audience_chart()
            
            # Generate platform comparison chart
            self._generate_platform_chart()
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
    
    def _generate_savings_chart(self):
        """Generate potential savings chart"""
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Simplified data for demonstration
        categories = ['Budget Inefficiencies', 'Ad Fatigue', 'Audience Targeting']
        values = [
            self.audit_results.get('potential_savings', 0) * 0.6,  # 60% from budget
            self.audit_results.get('potential_savings', 0) * 0.2,  # 20% from fatigue
            self.audit_results.get('potential_savings', 0) * 0.2   # 20% from targeting
        ]
        
        # Create bar chart
        ax.bar(categories, values, color=['#ff6b35', '#f9a03f', '#2ec4b6'])
        
        # Add labels and title
        ax.set_ylabel('Potential Savings ($)')
        ax.set_title('Potential Savings by Category')
        
        # Rotate x labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Tight layout
        plt.tight_layout()
        
        # Save chart to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        self.charts['savings'] = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
    
    def _generate_audience_chart(self):
        """Generate audience performance chart"""
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Mock audience data
        age_groups = ['18-24', '25-34', '35-44', '45-54', '55+']
        ctr_values = [1.8, 3.2, 2.5, 1.4, 0.9]
        
        # Create bar chart
        ax.bar(age_groups, ctr_values, color='#ff6b35')
        
        # Add labels and title
        ax.set_ylabel('CTR (%)')
        ax.set_title('Click-Through Rate by Age Group')
        
        # Save chart to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        self.charts['audience'] = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
    
    def _generate_platform_chart(self):
        """Generate platform comparison chart"""
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Mock platform data
        platforms = ['Facebook', 'Instagram', 'TikTok']
        cpa_values = [12.50, 15.75, 9.80]
        
        # Create bar chart
        ax.bar(platforms, cpa_values, color=['#1877f2', '#c32aa3', '#000000'])
        
        # Add labels and title
        ax.set_ylabel('Cost per Acquisition ($)')
        ax.set_title('CPA Comparison Across Platforms')
        
        # Save chart to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        self.charts['platform'] = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
    
    def generate_html_report(self):
        """Generate HTML report"""
        try:
            # Generate charts
            self._generate_charts()
            
            # Set up Jinja2 environment
            env = Environment(loader=FileSystemLoader('reporting/templates'))
            template = env.get_template('report_template.html')
            
            # Compile recommendations
            recommendations = self.audit_results.get('prioritized_recommendations', [])
            
            # Render template
            html_content = template.render(
                client_name=self.client_name,
                agency_name=self.agency_name,
                report_date=self.report_date,
                potential_savings=self.audit_results.get('potential_savings', 0),
                potential_improvement=self.audit_results.get('potential_improvement_percentage', 0),
                recommendations=recommendations,
                charts=self.charts
            )
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            raise
    
    def generate_pdf_report(self, output_path=None):
        """Generate PDF report and save to file"""
        try:
            # Generate HTML report
            html_content = self.generate_html_report()
            
            # Determine output path
            if output_path is None:
                reports_dir = os.path.join(os.getcwd(), 'reports')
                os.makedirs(reports_dir, exist_ok=True)
                
                filename = f"{self.client_name.replace(' ', '_')}_{self.report_date}.pdf"
                output_path = os.path.join(reports_dir, filename)
            
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
            
            # Generate