// api-response-handler.js
// This script adds error handling for API responses and ensures data is properly processed

document.addEventListener('DOMContentLoaded', function() {
    // Add this to the global scope to handle API responses
    window.handleApiResponse = async function(response) {
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            // Special handling for rate limits
            if (response.status === 429) {
                throw new Error(`Rate limit exceeded. Try again in ${errorData.retry_after || 5} minutes.`);
            }
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Check for API-level error
        if (result.success === false) {
            throw new Error(result.error || 'Unknown API error occurred');
        }
        
        return result;
    };
    
    // Initialize Facebook adapter if it doesn't exist
    if (!window.FacebookAdapter) {
        window.FacebookAdapter = {
            processFacebookData: function(data) {
                console.log("Facebook adapter not fully loaded, using basic processing");
                return {
                    success: true,
                    results: data.results || data
                };
            },
            generateSampleRecommendations: function() {
                return [{
                    type: 'general_recommendation',
                    severity: 'medium',
                    category: 'General',
                    title: 'Optimize Your Account',
                    recommendation: 'Consider optimizing your campaign structure and targeting to improve performance.',
                    potential_savings: 200.00,
                    action_items: ['Review campaign structure', 'Test new audiences', 'Optimize creative assets']
                }];
            }
        };
    }
    
    // Update the fetch function for campaign hierarchy
    const originalFetchHierarchy = window.fetchCampaignHierarchy;
    
    window.fetchCampaignHierarchy = async function(credentials) {
        try {
            showLoadingState();
            
            // Make sure we have credentials
            if (!credentials || !credentials.access_token || !credentials.account_id) {
                throw new Error('Missing Facebook credentials. Please reconnect your account.');
            }
            
            const response = await fetch('/api/campaign-hierarchy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    accessToken: credentials.access_token,
                    accountId: credentials.account_id
                })
            });
            
            const result = await window.handleApiResponse(response);
            
            // Process the data using the adapter if available
            if (window.FacebookAdapter) {
                const processedData = window.FacebookAdapter.processFacebookData(result);
                return processedData.success ? processedData.results : result;
            }
            
            return result;
        } catch (error) {
            console.error("Error fetching campaign hierarchy:", error);
            throw error;
        } finally {
            hideLoadingState();
        }
    };
    
    // Fix the extractAnalysisData function to handle hierarchy data properly
    const originalExtractAnalysisData = window.extractAnalysisData;
    
    if (typeof originalExtractAnalysisData === 'function') {
        window.extractAnalysisData = function(data) {
            console.log("Enhanced extractAnalysisData called with:", data);
            
            // First check if we have a FacebookAdapter
            if (window.FacebookAdapter) {
                // Check for campaign hierarchy data
                if (data.success === true && data.hierarchy) {
                    // Process using the adapter
                    const processedData = window.FacebookAdapter.processFacebookData(data);
                    if (processedData.success) {
                        return processedData.results;
                    }
                }
            }
            
            // Use the original function as fallback
            return originalExtractAnalysisData(data);
        };
    }
    
    // If on dashboard page, initialize the enhancement
    if (isDashboardPage()) {
        console.log("Initializing API response handler on dashboard page");
        
        // Check if we have Facebook credentials
        const fbCredentials = getSafeCredentials();
        if (fbCredentials) {
            // Make sure our FacebookAdapter is loaded
            if (window.FacebookAdapter) {
                console.log("Facebook adapter is loaded");
            } else {
                console.warn("Facebook adapter not loaded");
            }
        }
    }
    
    // Helper functions
    function isDashboardPage() {
        return document.getElementById('campaignHierarchy') !== null;
    }
    
    function getSafeCredentials() {
        try {
            const credString = sessionStorage.getItem('fb_credentials');
            if (!credString) return null;
            
            const creds = JSON.parse(credString);
            if (!creds.access_token || !creds.account_id) return null;
            
            return {
                access_token: creds.access_token,
                account_id: creds.account_id
            };
        } catch (e) {
            console.error('Error parsing stored credentials:', e);
            return null;
        }
    }
    
    function showLoadingState() {
        // Find or create loading indicator
        let loadingIndicator = document.getElementById('loadingIndicator');
        
        if (!loadingIndicator) {
            loadingIndicator = document.createElement('div');
            loadingIndicator.id = 'loadingIndicator';
            loadingIndicator.className = 'loading-overlay';
            loadingIndicator.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading data...</p>
            `;
            document.body.appendChild(loadingIndicator);
        }
        
        loadingIndicator.style.display = 'flex';
    }
    
    function hideLoadingState() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }
}); 