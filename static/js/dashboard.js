// Check if data has the enhanced structure and extract the correct data
function extractAnalysisData(data) {
    console.log("Extracting analysis data from:", data);
    
    // Check if this is the enhanced structure
    if (data.analysis_results) {
        return data.analysis_results;
    } else if (data.results && data.results.analysis_results) {
        return data.results.analysis_results;
    } else if (data.prioritized_recommendations || data.recommendations) {
        // If we have recommendations directly at the top level
        return data;
    } else {
        // Fall back to the original structure
        return data.results || data;
    }
}

// Updated fetchAuditData function with better error handling
// Add this at the beginning of the fetchAuditData function
// Updated fetchAuditData function with error fixed
async function fetchAuditData() {
    try {
        console.log("Starting fetchAuditData function");
        
        // Properly define fbCredentials first before using it
        const fbCredentials = JSON.parse(sessionStorage.getItem('fb_credentials') || '{}');
        console.log("Facebook credentials being used:", fbCredentials);
        
        if (fbCredentials.fb_access_token && fbCredentials.fb_account_id) {
            console.log("Found Facebook credentials, fetching data...");
            // Fetch data for the connected account
            const response = await fetch('/api/audit/facebook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    access_token: fbCredentials.fb_access_token,
                    account_id: fbCredentials.fb_account_id,
                    days_lookback: 30
                })
            });
            
            const result = await response.json();
            console.log("Facebook API response:", result);
            
            if (result.success) {
                // Update sessionStorage with the latest audit
                sessionStorage.setItem('latest_audit', JSON.stringify(result));
                
                // Extract data and update dashboard
                const data = extractAnalysisData(result);
                updateDashboard(data);
                return;
            } else {
                console.warn("API call failed:", result.error);
            }
        }
        
        // Rest of the function remains the same...
        
        // If we don't have credentials or the API call failed, fall back to test data
        console.log("No Facebook credentials found or API call failed, using test data");
        const response = await fetch('/api/test-audit');
        console.log("Test audit API response status:", response.status);
        
        if (!response.ok) {
            throw new Error(`API responded with status: ${response.status}`);
        }
        
        const rawData = await response.json();
        console.log("Raw data from API:", rawData);
        
        // Extract data properly
        const data = extractAnalysisData(rawData);
        console.log("Extracted data:", data);
        
        // Update dashboard with the data
        if (data) {
            updateDashboard(data);
        } else {
            console.error("No valid data found in API response");
            showError("Failed to load audit data: No valid data found");
        }
    } catch (error) {
        console.error('Error fetching audit data:', error);
        // Try to update with minimal mock data so at least something shows
        updateDashboardWithMockData();
    }
}

// Fallback function for when data fetching fails
function updateDashboardWithMockData() {
    console.log("Using mock data as fallback");
    const mockData = {
        potential_savings: 450.75,
        potential_improvement_percentage: 15.5,
        recommendations: [
            {
                type: "budget_efficiency",
                severity: "high",
                recommendation: "Test recommendation for budget efficiency",
                potential_savings: 250.0
            },
            {
                type: "audience_targeting",
                severity: "medium",
                recommendation: "Test recommendation for audience targeting",
                potential_savings: 125.0
            },
            {
                type: "creative_performance",
                severity: "low",
                recommendation: "Test recommendation for creative performance",
                potential_savings: 75.0
            }
        ],
        timestamp: new Date().toISOString(),
        platform: "facebook"
    };
    
    try {
        updateDashboard(mockData);
    } catch (error) {
        console.error("Error even with mock data:", error);
    }
}

// Updated function to handle Facebook audit response
function processFacebookAuditResponse(result) {
    if (result.success) {
        // Extract the correct data structure
        const data = extractAnalysisData(result);
        
        // Store audit results in session storage
        sessionStorage.setItem('latest_audit', JSON.stringify(result));
        
        // Show success message
        auditStatusTitle.textContent = 'Audit Complete';
        auditStatusMessage.innerHTML = `
            <div class="alert alert-success">
                <h5 class="alert-heading">Audit completed successfully!</h5>
                <p>Your Facebook Ads account has been analyzed and insights are ready.</p>
                <hr>
                <p class="mb-0">Click "View Results" to see the audit findings.</p>
            </div>
        `;
        viewResultsBtn.style.display = 'block';
    } else {
        // Show error message
        auditStatusTitle.textContent = 'Audit Failed';
        auditStatusMessage.innerHTML = `
            <div class="alert alert-danger">
                <h5 class="alert-heading">Audit failed</h5>
                <p>${result.error || 'An error occurred while running the audit.'}</p>
            </div>
        `;
        viewResultsBtn.style.display = 'none';
    }
}

// Updated updateDashboard function
function updateDashboard(data) {
    // Store full data for reference
    window.currentDashboardData = data;
    
    console.log("Updating dashboard with data:", data);
    
    // Update summary metrics
    updateSummaryMetrics(data);
    
    // Update recommendations
    updateRecommendations(data.recommendations || []);
    
    // Initialize charts
    initCharts(data);
    
    // Update connection status indicators
    updateConnectionStatus();
}

// Function to update connection status indicators
function updateConnectionStatus() {
    // Update Facebook connection status
    const fbConnectionStatus = document.getElementById('fbConnectionStatus');
    const fbCredentials = JSON.parse(sessionStorage.getItem('fb_credentials') || '{}');
    
    if (fbConnectionStatus && fbCredentials.fb_access_token && fbCredentials.fb_account_id) {
        fbConnectionStatus.textContent = `Connected (Account ID: ${fbCredentials.fb_account_id})`;
        fbConnectionStatus.classList.add('text-success');
        
        // Update the connect button to show "Re-connect" instead
        const fbConnectBtn = document.querySelector('.card-body a[href*="connect_facebook"]');
        if (fbConnectBtn) {
            fbConnectBtn.textContent = 'Re-connect';
            fbConnectBtn.classList.remove('btn-outline-primary');
            fbConnectBtn.classList.add('btn-outline-secondary');
        }
    }
}

// Updated updateSummaryMetrics function
function updateSummaryMetrics(data) {
    console.log("Updating summary metrics with:", data);
    
    // Update potential savings
    const potentialSavings = document.getElementById('potentialSavings');
    if (potentialSavings) {
        potentialSavings.textContent = formatCurrency(data.potential_savings);
    }
    
    // Update potential improvement
    const potentialImprovement = document.getElementById('potentialImprovement');
    if (potentialImprovement) {
        potentialImprovement.textContent = formatPercentage(data.potential_improvement_percentage);
    }
    
    // Update recommendation count
    const recommendationCount = document.getElementById('recommendationCount');
    if (recommendationCount) {
        recommendationCount.textContent = data.recommendations ? data.recommendations.length : 0;
    }
    
    // Update platforms audited
    const platformsAudited = document.getElementById('platformsAudited');
    if (platformsAudited) {
        platformsAudited.textContent = data.platform ? capitalizeFirstLetter(data.platform) : 'Facebook (Mock Data)';
    }
    
    // Update last audited time
    const lastAudited = document.getElementById('lastAudited');
    if (lastAudited) {
        const timestamp = new Date(data.timestamp);
        lastAudited.textContent = formatDate(timestamp);
    }
    
    // Update gauge value
    const gaugeValue = document.getElementById('gaugeValue');
    if (gaugeValue) {
        gaugeValue.textContent = formatPercentage(data.potential_improvement_percentage);
    }
}

// Update recommendations function
function updateRecommendations(recommendations) {
    const recommendationsList = document.getElementById('recommendationsList');
    if (!recommendationsList) {
        console.error("recommendationsList element not found");
        return;
    }
    
    console.log("Updating recommendations with:", recommendations);
    
    if (recommendations && recommendations.length > 0) {
        let html = '';
        // Display top 5 recommendations
        recommendations.slice(0, 5).forEach(rec => {
            let severityClass = '';
            if (rec.severity === 'high') {
                severityClass = 'border-danger';
            } else if (rec.severity === 'medium') {
                severityClass = 'border-warning';
            } else {
                severityClass = 'border-success';
            }
            
            html += `
                <div class="recommendation-card ${severityClass} mb-3">
                    <div class="recommendation-title fw-bold">${getRecommendationTitle(rec)}</div>
                    <div class="recommendation-text mt-2">${rec.recommendation}</div>
                    ${rec.potential_savings ? `<div class="text-success fw-bold mt-2">Potential Savings: ${formatCurrency(rec.potential_savings)}</div>` : ''}
                </div>
            `;
        });
        
        recommendationsList.innerHTML = html;
    } else {
        // Check if we should use prioritized_recommendations instead
        const data = window.currentDashboardData;
        if (data && data.prioritized_recommendations && data.prioritized_recommendations.length > 0) {
            console.log("Using prioritized_recommendations instead");
            updateRecommendations(data.prioritized_recommendations);
            return;
        }
        
        recommendationsList.innerHTML = `
            <div class="alert alert-info">
                <p class="mb-0">No recommendations available. This could be because the account is performing well or because this is test data.</p>
                <p class="mb-0 mt-2">Connect a real ad account to get personalized recommendations.</p>
            </div>
        `;
    }
}

// Helper function to get a readable title for a recommendation
function getRecommendationTitle(rec) {
    if (rec.campaign_name) {
        return `Campaign: ${rec.campaign_name}`;
    } else if (rec.adset_name) {
        return `Ad Set: ${rec.adset_name}`;
    } else if (rec.ad_name) {
        return `Ad: ${rec.ad_name}`;
    } else if (rec.type) {
        // Format the type for display
        return rec.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    return 'Optimization Recommendation';
}

// Helper function to initialize charts
function initCharts(data) {
    // Performance Gauge Chart
    initPerformanceGauge(data.potential_improvement_percentage || 0);
    
    // Campaign Performance Chart
    initCampaignChart(data);
}

// Initialize Performance Gauge
function initPerformanceGauge(value) {
    const gaugeCanvas = document.getElementById('performanceGauge');
    if (!gaugeCanvas) return;
    
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
    }
    
    // Clear any existing chart - fixed to check if destroy function exists
    if (window.gaugeChart && typeof window.gaugeChart.destroy === 'function') {
        window.gaugeChart.destroy();
    }
    
    try {
        // Create new chart
        window.gaugeChart = new Chart(gaugeCanvas, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [value, 100 - value],
                    backgroundColor: [
                        '#ff6b35',
                        '#f5f5f5'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                circumference: 180,
                rotation: 270,
                cutout: '75%',
                plugins: {
                    tooltip: {
                        enabled: false
                    },
                    legend: {
                        display: false
                    }
                },
                responsive: true,
                maintainAspectRatio: true
            }
        });
    } catch (error) {
        console.error('Error creating gauge chart:', error);
    }
}

// Initialize Campaign Performance Chart
function initCampaignChart(data) {
    const chartCanvas = document.getElementById('campaignChart');
    if (!chartCanvas) return;
    
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
    }
    
    // Clear any existing chart
    if (window.campaignChart && typeof window.campaignChart.destroy === 'function') {
        window.campaignChart.destroy();
    }
    
    // Get campaign data if available
    let labels = [];
    let values = [];
    
    console.log("Data structure for chart:", data); // Debug log to see the actual structure
    
    // Try to extract campaign performance data from different possible data structures
    if (data.insights && Array.isArray(data.insights)) {
        // New structure - the insights array contains campaign data directly
        const campaignData = data.insights;
        
        // Create a map to combine insights by campaign
        const campaignMap = new Map();
        
        // Aggregate insights by campaign_id
        campaignData.forEach(insight => {
            if (!insight.campaign_id || !insight.campaign_name) return;
            
            if (!campaignMap.has(insight.campaign_id)) {
                campaignMap.set(insight.campaign_id, {
                    campaign_id: insight.campaign_id,
                    campaign_name: insight.campaign_name,
                    spend: 0
                });
            }
            
            // Add spend for this insight to the campaign total
            const campaign = campaignMap.get(insight.campaign_id);
            campaign.spend += parseFloat(insight.spend || 0);
        });
        
        // Convert map to array and sort by spend
        const aggregatedCampaigns = Array.from(campaignMap.values())
            .sort((a, b) => b.spend - a.spend);
        
        // Get top 5 campaigns
        aggregatedCampaigns.slice(0, 5).forEach(campaign => {
            labels.push(campaign.campaign_name || 'Campaign');
            values.push(campaign.spend || 0);
        });
    } 
    // Also try the old structure as fallback
    else if (data.insights && data.insights.campaigns) {
        const campaignData = data.insights.campaigns;
        // Sort by spend
        campaignData.sort((a, b) => (b.spend || 0) - (a.spend || 0));
        
        // Get top 5 campaigns
        campaignData.slice(0, 5).forEach(campaign => {
            labels.push(campaign.name || campaign.campaign_name || 'Campaign');
            values.push(campaign.spend || 0);
        });
    } 
    // If data is in a completely different format, check for the campaigns array directly
    else if (data.campaigns && Array.isArray(data.campaigns)) {
        const campaignData = data.campaigns;
        // Sort by spend if available
        if (campaignData[0] && 'spend' in campaignData[0]) {
            campaignData.sort((a, b) => (b.spend || 0) - (a.spend || 0));
        }
        
        // Get top 5 campaigns
        campaignData.slice(0, 5).forEach(campaign => {
            labels.push(campaign.name || 'Campaign');
            values.push(campaign.spend || 0);
        });
    } 
    else {
        // Sample data if no campaign data is available
        console.log("Using sample data for chart - no matching data structure found");
        labels = ['Campaign 1', 'Campaign 2', 'Campaign 3', 'Campaign 4', 'Campaign 5'];
        values = [1200, 800, 600, 400, 200];
    }
    
    // Create new chart
    try {
        window.campaignChart = new Chart(chartCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Spend ($)',
                    data: values,
                    backgroundColor: '#ff6b35',
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating campaign chart:', error);
    }
}

// Utility Functions
function formatCurrency(value) {
    return '$' + parseFloat(value || 0).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

function formatPercentage(value) {
    return parseFloat(value || 0).toFixed(1) + '%';
}

function formatDate(date) {
    if (!(date instanceof Date) || isNaN(date)) {
        return 'Unknown';
    }
    return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function capitalizeFirstLetter(string) {
    if (!string) return '';
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function showError(message) {
    console.error(message);
    // Show error message to user
    // Could use a toast notification or alert
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded");
    
    // Update client dropdown if it exists
    updateClientDropdown();
    
    // Fetch audit data
    fetchAuditData();
    
    // Add event listeners for time filter dropdowns
    document.querySelectorAll('.time-filter').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const period = this.getAttribute('data-period');
            if (period) {
                document.getElementById('selectedPeriod').textContent = `Last ${period} Days`;
                // Re-fetch data with new period
                // This would be implemented in a full version
            }
        });
    });
    
    // Add event listener for export button
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            // Implement report export functionality
            generateReport();
        });
    }
});

// Update client dropdown function
function updateClientDropdown() {
    const clientSelect = document.getElementById('clientSelect');
    if (!clientSelect) return;
    
    // Fetch clients from API
    fetch('/api/clients')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.clients) {
                clientSelect.innerHTML = '<option value="">Select a client</option>';
                data.clients.forEach(client => {
                    const option = document.createElement('option');
                    option.value = client.id;
                    option.textContent = client.name;
                    clientSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching clients:', error);
        });
}

// Generate report function
function generateReport() {
    // Get client ID if selected
    const clientSelect = document.getElementById('clientSelect');
    const clientId = clientSelect ? clientSelect.value : null;
    
    // Call API to generate report
    fetch('/api/generate-report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            client_id: clientId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.download_url) {
            // Open download link in new tab
            window.open(data.download_url, '_blank');
        } else {
            alert('Failed to generate report: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error generating report:', error);
        alert('Error generating report. Please try again.');
    });
}