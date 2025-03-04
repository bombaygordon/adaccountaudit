import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import numpy as np

# Import our enhanced components
from analysis.enhanced_analyzer import EnhancedAdAccountAnalyzer
from reporting.enhanced_report_generator import EnhancedReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('enhanced_audit.log')
    ]
)
logger = logging.getLogger('enhanced_audit')

# Custom JSON serializer for handling NumPy types
def json_serialize(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (datetime, np.datetime64)):
        return obj.isoformat()
    return obj

class EnhancedAdAccountAudit:
    """
    Main integration module for enhanced ad account auditing.
    Coordinates data flow between connector, analyzer, and report generator.
    """
    
    def __init__(self, reports_dir='reports', cache_dir='cache'):
        """
        Initialize the enhanced audit system.
        
        Args:
            reports_dir (str): Directory to save generated reports
            cache_dir (str): Directory to cache analysis results
        """
        self.reports_dir = reports_dir
        self.cache_dir = cache_dir
        
        # Ensure directories exist
        os.makedirs(reports_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize components
        self.analyzer = EnhancedAdAccountAnalyzer()
        self.report_generator = EnhancedReportGenerator(reports_dir)
        
        self.logger = logging.getLogger('enhanced_audit.integration')
    
    def run_audit(self, account_data, platform='facebook', client_name=None, 
                 agency_name=None, generate_report=True, cache_results=True):
        """
        Run a complete enhanced audit process from data to final report.
        
        Args:
            account_data (dict): Raw ad account data
            platform (str): Platform name ('facebook', 'tiktok', etc.)
            client_name (str, optional): Name of the client
            agency_name (str, optional): Name of the agency
            generate_report (bool): Whether to generate a PDF report
            cache_results (bool): Whether to cache analysis results
            
        Returns:
            dict: Complete audit results including analysis and report path
        """
        # Set default client name if not provided
        if not client_name:
            client_name = f"{platform.capitalize()} Ad Account"
        
        # Set default agency name if not provided
        if not agency_name:
            agency_name = "AI Ad Account Auditor"
        
        self.logger.info(f"Starting enhanced audit for {client_name} on {platform}")
        
        try:
            # Validate account_data structure before analysis
            if not isinstance(account_data, dict):
                raise ValueError(f"Invalid account data format: expected dict, got {type(account_data)}")
                
            # Check that required keys are present
            for key in ['campaigns', 'insights']:
                if key not in account_data:
                    self.logger.warning(f"Missing key '{key}' in account data, adding empty list")
                    account_data[key] = []
                    
            # Verify insights is a list and has items
            if not isinstance(account_data['insights'], list):
                self.logger.error(f"Invalid insights format: expected list, got {type(account_data['insights'])}")
                account_data['insights'] = []
            
            # Run enhanced analysis
            self.logger.info(f"Running analysis on {platform} data")
            analysis_results = self.analyzer.analyze(account_data, platform)
            
            # Cache results if enabled
            if cache_results:
                self._cache_analysis_results(analysis_results, client_name, platform)
            
            # Generate report if enabled
            report_path = None
            if generate_report:
                self.logger.info(f"Generating report for {client_name}")
                try:
                    report_path = self.report_generator.generate_report(
                        analysis_results, 
                        client_name, 
                        agency_name
                    )
                except Exception as report_error:
                    self.logger.error(f"Error generating report: {report_error}", exc_info=True)
                    # Continue without report instead of failing the whole audit
            
            # Prepare audit result
            audit_result = {
                'timestamp': datetime.now().isoformat(),
                'client_name': client_name,
                'agency_name': agency_name,
                'platform': platform,
                'analysis_results': analysis_results,
                'report_path': report_path,
                'success': True
            }
            
            self.logger.info(f"Audit completed successfully for {client_name}")
            
            return audit_result
            
        except Exception as e:
            self.logger.error(f"Error running audit: {e}", exc_info=True)
            
            # Return error result
            return {
                'timestamp': datetime.now().isoformat(),
                'client_name': client_name,
                'platform': platform,
                'success': False,
                'error': str(e)
            }
    
    # Alias for backwards compatibility
    analyze = run_audit
    
    def _cache_analysis_results(self, analysis_results, client_name, platform):
        """
        Cache analysis results to file.
        
        Args:
            analysis_results (dict): Analysis results
            client_name (str): Client name
            platform (str): Platform name
        """
        try:
            # Create cache filename
            sanitized_name = client_name.replace(' ', '_').lower()
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"{sanitized_name}_{platform}_{date_str}.json"
            
            # Define cache path
            cache_path = os.path.join(self.cache_dir, filename)
            
            # Save to JSON file with custom serialization for NumPy types
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, indent=2, default=json_serialize)
                
            self.logger.info(f"Analysis results cached to {cache_path}")
            
        except Exception as e:
            self.logger.error(f"Error caching analysis results: {e}")
    
    def load_cached_analysis(self, client_name, platform=None, days_lookback=30):
        """
        Load the most recent cached analysis results for a client.
        
        Args:
            client_name (str): Client name
            platform (str, optional): Platform name filter
            days_lookback (int): Max days to look back for cached results
            
        Returns:
            dict: Cached analysis results or None if not found
        """
        try:
            # Sanitize client name for filename matching
            sanitized_name = client_name.replace(' ', '_').lower()
            
            # Get cache directory contents
            cache_dir = Path(self.cache_dir)
            cache_files = list(cache_dir.glob(f"{sanitized_name}_*.json"))
            
            # Filter by platform if specified
            if platform:
                cache_files = [f for f in cache_files if f.name.split('_')[1] == platform]
            
            if not cache_files:
                return None
            
            # Sort by modification time (newest first)
            cache_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Load the most recent file
            with open(cache_files[0], 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
            self.logger.info(f"Loaded cached analysis from {cache_files[0]}")
            
            return cached_data
            
        except Exception as e:
            self.logger.error(f"Error loading cached analysis: {e}")
            return None
    
    def generate_report_from_cache(self, client_name, agency_name=None, platform=None):
        """
        Generate a report from cached analysis results.
        
        Args:
            client_name (str): Client name
            agency_name (str, optional): Agency name
            platform (str, optional): Platform name filter
            
        Returns:
            str: Path to the generated report or None if failed
        """
        try:
            # Load cached analysis
            cached_analysis = self.load_cached_analysis(client_name, platform)
            
            if not cached_analysis:
                self.logger.error(f"No cached analysis found for {client_name}")
                return None
            
            # Generate report
            report_path = self.report_generator.generate_report(
                cached_analysis,
                client_name,
                agency_name
            )
            
            return report_path
            
        except Exception as e:
            self.logger.error(f"Error generating report from cache: {e}")
            return None