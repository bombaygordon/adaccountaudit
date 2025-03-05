// Add this at the top of the file
let mainContentElement = null;

// Function to ensure main content container exists
function ensureMainContent() {
    if (!mainContentElement) {
        mainContentElement = document.querySelector('.main-content');
        if (!mainContentElement) {
            // Create main content if it doesn't exist
            mainContentElement = document.createElement('div');
            mainContentElement.className = 'main-content';
            const container = document.querySelector('.container');
            if (container) {
                container.insertBefore(mainContentElement, container.firstChild);
            } else {
                // Create container if it doesn't exist
                const newContainer = document.createElement('div');
                newContainer.className = 'container';
                document.body.appendChild(newContainer);
                newContainer.appendChild(mainContentElement);
            }
        }
    }
    return mainContentElement;
}

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

// Updated fetchAuditData function
async function fetchAuditData() {
    try {
        console.log("Starting fetchAuditData function");
        
        // Get Facebook credentials from session storage
        const fbCredentials = JSON.parse(sessionStorage.getItem('fb_credentials') || '{}');
        console.log("Retrieved credentials:", {
            hasAccessToken: !!fbCredentials.access_token,
            hasAccountId: !!fbCredentials.account_id,
            accountId: fbCredentials.account_id
        });
        
        if (!fbCredentials.access_token || !fbCredentials.account_id) {
            console.error("Facebook credentials not found");
            showError("Facebook credentials not found. Please reconnect your account.");
            return;
        }
        
        // Show loading state
        showLoadingState();
        hideError(); // Hide any existing errors
        
        // Fetch data for the connected account
        const response = await fetch('/api/audit/facebook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                access_token: fbCredentials.access_token,
                account_id: fbCredentials.account_id,
                days_lookback: 30
            })
        });
        
        console.log("API Response status:", response.status);
        
        if (!response.ok) {
            if (response.status === 401) {
                // Clear invalid credentials and redirect
                sessionStorage.removeItem('fb_credentials');
                sessionStorage.removeItem('facebook_response');
                window.location.href = '/connect/facebook';
                return;
            }
            
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log("Facebook API response:", result);
        
        if (result.success === false) {
            throw new Error(result.error || 'Unknown error occurred');
        }
        
        // Hide loading state and error messages
        hideLoadingState();
        hideError();
        
        // Extract and process the data
        const data = extractAnalysisData(result);
        console.log("Extracted data for dashboard:", data);
        
        // Update the dashboard with the data
        updateDashboard(data);
        
        // Store the latest audit results
        sessionStorage.setItem('latest_audit', JSON.stringify(result));
        
    } catch (error) {
        console.error('Error fetching audit data:', error);
        handleApiError(error);
        showError(error.message || "An error occurred while fetching your data. Please try again.");
        hideLoadingState();
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

// Function to update the dashboard with audit data
function updateDashboard(data) {
    console.log('Raw dashboard data:', data);
    
    if (!data || typeof data !== 'object') {
        console.error('Invalid data received:', data);
        showError("Invalid data received from the server");
        return;
    }
    
    // Ensure all necessary containers exist
    ensureChartContainers();
    
    // Extract analysis results
    const analysisResults = data.analysis_results || {};
    console.log('Analysis results:', analysisResults);
    
    // Update recommendations
    const recommendations = analysisResults.recommendations || [];
    console.log('Updating recommendations:', recommendations);
    updateRecommendations(recommendations);
    
    // Update metrics
    const metrics = {
        totalSpend: analysisResults.account_overview?.total_spend || 0,
        ctr: analysisResults.metrics?.average_ctr || 0,
        cpc: analysisResults.metrics?.average_cpc || 0,
        cpm: analysisResults.metrics?.average_cpm || 0,
        conversionRate: analysisResults.metrics?.average_conversion_rate || 0,
        roas: analysisResults.metrics?.roas || 0
    };
    console.log('Updating metrics with:', metrics);
    updateMetrics(metrics);
    
    // Update account overview charts
    if (analysisResults.account_overview) {
        console.log('Updating charts with:', analysisResults.account_overview);
        // Ensure chart containers exist again before updating charts
        ensureChartContainers();
        updateCharts(analysisResults.account_overview);
    }
    
    // Update summary stats
    updateSummaryMetrics(data);
    
    // Update potential savings and improvement percentage
    const potentialSavingsElement = document.getElementById('potentialSavings');
    const improvementPercentageElement = document.getElementById('improvementPercentage');
    
    if (potentialSavingsElement) {
        potentialSavingsElement.textContent = formatCurrency(data.potential_savings || 0);
    }
    
    if (improvementPercentageElement) {
        improvementPercentageElement.textContent = formatPercentage(data.potential_improvement_percentage || 0);
    }
}

// Function to update metrics section
function updateMetrics(metrics) {
    console.log('Updating metrics with values:', metrics);
    
    const metricsMap = {
        'totalSpend': { id: 'metric-totalSpend', format: (val) => `$${parseFloat(val).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` },
        'ctr': { id: 'metric-ctr', format: (val) => `${(parseFloat(val) * 100).toFixed(2)}%` },
        'cpc': { id: 'metric-cpc', format: (val) => `$${parseFloat(val).toFixed(2)}` },
        'cpm': { id: 'metric-cpm', format: (val) => `$${parseFloat(val).toFixed(2)}` },
        'conversionRate': { id: 'metric-conversionRate', format: (val) => `${(parseFloat(val) * 100).toFixed(2)}%` },
        'roas': { id: 'metric-roas', format: (val) => parseFloat(val).toFixed(2) }
    };
    
    Object.entries(metrics).forEach(([key, value]) => {
        const metricConfig = metricsMap[key];
        if (metricConfig) {
            const element = document.getElementById(metricConfig.id);
            if (element) {
                const formattedValue = metricConfig.format(value);
                console.log(`Updating ${key} with value:`, value, 'formatted as:', formattedValue);
                element.textContent = formattedValue;
            } else {
                console.warn(`Element not found for metric: ${key} (id: ${metricConfig.id})`);
            }
        }
    });
}

// Function to update connection status indicators
function updateConnectionStatus() {
    // Update Facebook connection status
    const fbConnectionStatus = document.getElementById('fbConnectionStatus');
    const fbCredentials = JSON.parse(sessionStorage.getItem('fb_credentials') || '{}');
    
    console.log("Checking Facebook credentials in updateConnectionStatus:", fbCredentials);
    
    if (fbConnectionStatus && fbCredentials.access_token && fbCredentials.account_id) {
        fbConnectionStatus.textContent = `Connected (Account ID: ${fbCredentials.account_id})`;
        fbConnectionStatus.classList.add('text-success');
        
        // Update the connect button to show "Re-connect" instead
        const fbConnectBtn = document.querySelector('.card-body a[href*="connect_facebook"]');
        if (fbConnectBtn) {
            fbConnectBtn.textContent = 'Re-connect';
            fbConnectBtn.classList.remove('btn-outline-primary');
            fbConnectBtn.classList.add('btn-outline-secondary');
        }
        
        // Since we have valid credentials, trigger data fetch
        fetchAuditData().catch(error => {
            console.error('Error fetching audit data:', error);
            showError('Failed to fetch audit data. Please try again.');
        });
    } else {
        if (fbConnectionStatus) {
            fbConnectionStatus.textContent = 'Not connected';
            fbConnectionStatus.classList.remove('text-success');
            fbConnectionStatus.classList.add('text-warning');
        }
        
        // Show connection warning
        showError('Facebook credentials not found. Please connect your account.');
        
        // Update connect button to primary state
        const fbConnectBtn = document.querySelector('.card-body a[href*="connect_facebook"]');
        if (fbConnectBtn) {
            fbConnectBtn.textContent = 'Connect Account';
            fbConnectBtn.classList.remove('btn-outline-secondary');
            fbConnectBtn.classList.add('btn-outline-primary');
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
    console.log("Starting updateRecommendations with:", recommendations);
    
    // First, ensure we have a container structure
    function ensureContainer() {
        // Try to find the app container first
        let appContainer = document.querySelector('#app');
        if (!appContainer) {
            console.log("Creating app container");
            appContainer = document.createElement('div');
            appContainer.id = 'app';
            document.body.appendChild(appContainer);
        }

        // Create or find the container element
        let container = document.querySelector('.container');
        if (!container) {
            console.log("Creating container");
            container = document.createElement('div');
            container.className = 'container';
            appContainer.appendChild(container);
        }

        // Create or find main content area
        let mainContent = document.querySelector('.main-content');
        if (!mainContent) {
            console.log("Creating main content area");
            mainContent = document.createElement('div');
            mainContent.className = 'main-content';
            container.appendChild(mainContent);
        }

        return mainContent;
    }

    // Ensure we have the basic container structure
    const mainContent = ensureContainer();

    // Create or find recommendations section
    let recommendationsSection = document.getElementById('recommendationsSection');
    if (!recommendationsSection) {
        console.log("Creating recommendations section");
        recommendationsSection = document.createElement('section');
        recommendationsSection.id = 'recommendationsSection';
        recommendationsSection.className = 'mb-4';
        mainContent.appendChild(recommendationsSection);
    }

    // Create or find recommendations container
    let recommendationsContainer = document.getElementById('recommendationsContainer');
    if (!recommendationsContainer) {
        console.log("Creating recommendations container");
        recommendationsContainer = document.createElement('div');
        recommendationsContainer.id = 'recommendationsContainer';
        recommendationsContainer.className = 'card mb-4';
        recommendationsSection.appendChild(recommendationsContainer);
    }

    // Create or find card header
    let cardHeader = recommendationsContainer.querySelector('.card-header');
    if (!cardHeader) {
        cardHeader = document.createElement('div');
        cardHeader.className = 'card-header';
        cardHeader.innerHTML = '<h5 class="card-title mb-0">Priority Recommendations</h5>';
        recommendationsContainer.appendChild(cardHeader);
    }

    // Create or find card body
    let cardBody = recommendationsContainer.querySelector('.card-body');
    if (!cardBody) {
        cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        recommendationsContainer.appendChild(cardBody);
    }

    // Create or find recommendations list
    let recommendationsList = document.getElementById('recommendationsList');
    if (!recommendationsList) {
        console.log("Creating recommendations list");
        recommendationsList = document.createElement('div');
        recommendationsList.id = 'recommendationsList';
        cardBody.appendChild(recommendationsList);
    }

    // Show appropriate message based on recommendations
    if (!recommendations || recommendations.length === 0) {
        recommendationsList.innerHTML = `
            <div class="alert alert-info">
                <h5 class="alert-heading">No Recommendations Available</h5>
                <p class="mb-0">We encountered an issue connecting to our analysis service. Here's what you can try:</p>
                <ul class="mt-2 mb-0">
                    <li>Check your internet connection</li>
                    <li>Refresh the page and try again</li>
                    <li>If the problem persists, try reconnecting your Facebook account</li>
                </ul>
            </div>
        `;
        return;
    }

    let html = '';
    recommendations.forEach(rec => {
        const severityClass = getSeverityClass(rec.severity);
        const severityBadge = getSeverityBadge(rec.severity);
        
        html += `
            <div class="card mb-3 ${severityClass}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h5 class="card-title mb-0">${rec.category || 'Optimization Opportunity'}</h5>
                        ${severityBadge}
                    </div>
                    <p class="card-text">${rec.recommendation}</p>
                    ${rec.action_items ? getActionItemsHtml(rec.action_items) : ''}
                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <div class="small text-muted">
                            ${getMetricsImpactHtml(rec.metrics_impact)}
                        </div>
                        <div class="text-success">
                            <strong>Potential Savings: ${formatCurrency(rec.potential_savings)}</strong>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    recommendationsList.innerHTML = html;
}

// Helper function to get severity class
function getSeverityClass(severity) {
    switch (severity?.toLowerCase()) {
        case 'high':
            return 'border-danger';
        case 'medium':
            return 'border-warning';
        case 'low':
            return 'border-success';
        default:
            return 'border-secondary';
    }
}

// Helper function to get severity badge
function getSeverityBadge(severity) {
    const label = severity?.toLowerCase() === 'high' ? 'High Priority' :
                 severity?.toLowerCase() === 'medium' ? 'Medium Priority' :
                 severity?.toLowerCase() === 'low' ? 'Low Priority' : 'Normal Priority';
    
    const badgeClass = severity?.toLowerCase() === 'high' ? 'bg-danger' :
                      severity?.toLowerCase() === 'medium' ? 'bg-warning' :
                      severity?.toLowerCase() === 'low' ? 'bg-info' : 'bg-secondary';
    
    return `<span class="badge ${badgeClass}">${label}</span>`;
}

// Helper function to format action items
function getActionItemsHtml(actionItems) {
    if (!actionItems || !actionItems.length) return '';
    
    return `
        <div class="mt-3">
            <strong>Action Items:</strong>
            <ul class="mb-0">
                ${actionItems.map(item => `<li>${item}</li>`).join('')}
            </ul>
        </div>
    `;
}

// Helper function to format metrics impact
function getMetricsImpactHtml(metricsImpact) {
    if (!metricsImpact) return '';
    
    const impacts = [];
    if (metricsImpact.roas_improvement > 0) impacts.push(`ROAS +${metricsImpact.roas_improvement.toFixed(1)}%`);
    if (metricsImpact.ctr_improvement > 0) impacts.push(`CTR +${metricsImpact.ctr_improvement.toFixed(1)}%`);
    if (metricsImpact.cpc_reduction > 0) impacts.push(`CPC -${metricsImpact.cpc_reduction.toFixed(1)}%`);
    if (metricsImpact.cpa_reduction > 0) impacts.push(`CPA -${metricsImpact.cpa_reduction.toFixed(1)}%`);
    
    return impacts.length ? `Expected Impact: ${impacts.join(' | ')}` : '';
}

// Helper function to initialize charts
function initCharts(data) {
    // Performance Gauge Chart
    initPerformanceGauge(data.potential_improvement_percentage || 0);
    
    // Campaign Performance Chart
    initCampaignChart(data);
}

// Function to initialize performance gauge
function initPerformanceGauge(value) {
    const gaugeCanvas = document.getElementById('performanceGauge');
    if (!gaugeCanvas) {
        console.warn('Performance gauge canvas not found');
        return;
    }
    
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
    }
    
    // Clear any existing chart
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

// Function to initialize campaign chart
function initCampaignChart(data) {
    const chartCanvas = document.getElementById('campaignChart');
    if (!chartCanvas) {
        console.warn('Campaign chart canvas not found');
        return;
    }
    
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
    }
    
    // Clear any existing chart
    if (window.campaignChart && typeof window.campaignChart.destroy === 'function') {
        window.campaignChart.destroy();
    }
    
    // Get campaign data
    let labels = [];
    let values = [];
    
    console.log("Campaign chart data input:", data);
    
    // Check cached Facebook audit data first
    const cachedAudit = JSON.parse(sessionStorage.getItem('latest_audit') || '{}');
    
    // Try to extract campaign data from different potential locations
    let campaignData = [];
    
    // Check in the cached audit result
    if (cachedAudit.analysis_results && cachedAudit.analysis_results.insights && 
        cachedAudit.analysis_results.insights.budget_efficiency && 
        cachedAudit.analysis_results.insights.budget_efficiency.campaigns) {
        campaignData = cachedAudit.analysis_results.insights.budget_efficiency.campaigns;
    } 
    // Check in the current data
    else if (data && data.insights && data.insights.budget_efficiency && data.insights.budget_efficiency.campaigns) {
        campaignData = data.insights.budget_efficiency.campaigns;
    }
    // Check for direct campaign data in the account overview
    else if (data && data.total_campaigns) {
        // Create mock campaign data based on total spend and campaign count
        const totalSpend = data.total_spend || 0;
        const campaignCount = data.total_campaigns || 5;
        const averageSpend = totalSpend / campaignCount;
        
        // Generate campaign data with some variation
        for (let i = 0; i < campaignCount; i++) {
            const variation = 0.8 + Math.random() * 0.4; // Random variation between 80% and 120%
            campaignData.push({
                name: `Campaign ${i + 1}`,
                spend: averageSpend * variation
            });
        }
    }
    
    // If we have campaign data, process it
    if (campaignData && campaignData.length > 0) {
        // Sort campaigns by spend in descending order
        campaignData.sort((a, b) => (b.spend || 0) - (a.spend || 0));
        
        // Take top 5 campaigns
        campaignData.slice(0, 5).forEach(campaign => {
            labels.push(campaign.name || 'Unnamed Campaign');
            values.push(campaign.spend || 0);
        });
    } 
    else {
        // Fallback to sample data if no real data found
        console.warn("No campaign data found, using sample data");
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
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Spend: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        },
                        title: {
                            display: true,
                            text: 'Campaign Spend'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Campaign Names'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating campaign chart:', error);
    }
}

// Function to ensure chart containers exist
function ensureChartContainers() {
    // Create or find the charts section
    let chartsSection = document.getElementById('chartsSection');
    if (!chartsSection) {
        chartsSection = document.createElement('section');
        chartsSection.id = 'chartsSection';
        chartsSection.className = 'row mb-4';
        
        // Add to main content
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.insertBefore(chartsSection, mainContent.firstChild);
        }
    }
    
    // Create performance gauge container if it doesn't exist
    let gaugeContainer = document.getElementById('gaugeContainer');
    if (!gaugeContainer) {
        gaugeContainer = document.createElement('div');
        gaugeContainer.id = 'gaugeContainer';
        gaugeContainer.className = 'col-md-6 mb-4';
        gaugeContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Performance Gauge</h5>
                </div>
                <div class="card-body">
                    <canvas id="performanceGauge"></canvas>
                </div>
            </div>
        `;
        chartsSection.appendChild(gaugeContainer);
    }
    
    // Create campaign chart container if it doesn't exist
    let campaignChartContainer = document.getElementById('campaignChartContainer');
    if (!campaignChartContainer) {
        campaignChartContainer = document.createElement('div');
        campaignChartContainer.id = 'campaignChartContainer';
        campaignChartContainer.className = 'col-md-6 mb-4';
        campaignChartContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Campaign Performance</h5>
                </div>
                <div class="card-body">
                    <canvas id="campaignChart"></canvas>
                </div>
            </div>
        `;
        chartsSection.appendChild(campaignChartContainer);
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

// Function to handle API errors
function handleApiError(error) {
    console.error('API Error:', error);
    
    let errorMessage = 'An error occurred while processing your request.';
    
    if (error.message) {
        if (error.message.includes('OpenAI API key not configured')) {
            errorMessage = 'The OpenAI API key is not configured. Please contact support.';
        } else if (error.message.includes('Failed to initialize OpenAI analyzer')) {
            errorMessage = 'The OpenAI API key is invalid. Please check your API key configuration.';
        } else if (error.message.includes('OpenAI analysis failed')) {
            errorMessage = 'The analysis service encountered an error. Please try again later.';
        } else if (error.message.includes('Invalid OAuth access token')) {
            errorMessage = 'Your Facebook connection has expired. Please reconnect your account.';
        } else if (error.message.includes('User request limit reached')) {
            errorMessage = 'Facebook API rate limit reached. Please try again in a few minutes.';
        } else if (error.message.includes('HTTP error! status: 503')) {
            errorMessage = 'The analysis service is temporarily unavailable. Please try again in a few minutes.';
        } else if (error.message.includes('HTTP error! status: 500')) {
            errorMessage = 'Server error occurred. Please try again later.';
        } else if (error.message.includes('HTTP error! status: 404')) {
            errorMessage = 'Resource not found. Please check your account ID.';
        } else {
            errorMessage = error.message;
        }
    }
    
    showError(errorMessage);
}

// Updated error handling functions
function showError(message) {
    ensureMainContent();
    const errorDiv = document.getElementById('errorAlert') || createErrorDiv();
    errorDiv.innerHTML = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    errorDiv.style.display = 'block';
}

function createErrorDiv() {
    const mainContent = ensureMainContent();
    let errorDiv = document.getElementById('errorAlert');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'errorAlert';
        mainContent.insertBefore(errorDiv, mainContent.firstChild);
    }
    return errorDiv;
}

function hideError() {
    const errorDiv = document.getElementById('errorAlert');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// Updated loading state functions
function showLoadingState() {
    ensureMainContent();
    hideError();
    const loadingDiv = document.getElementById('loadingIndicator') || createLoadingDiv();
    loadingDiv.style.display = 'block';
}

function createLoadingDiv() {
    const mainContent = ensureMainContent();
    let loadingDiv = document.getElementById('loadingIndicator');
    if (!loadingDiv) {
        loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingIndicator';
        loadingDiv.className = 'text-center mt-3';
        loadingDiv.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading data...</p>
        `;
        mainContent.insertBefore(loadingDiv, mainContent.firstChild);
    }
    return loadingDiv;
}

function hideLoadingState() {
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

// Function to check Facebook connection status
function checkFacebookConnection() {
    const fbCredentials = JSON.parse(sessionStorage.getItem('fb_credentials') || '{}');
    
    // Log the actual credential values for debugging
    console.log("Raw Facebook credentials:", fbCredentials);
    console.log("Checking Facebook credentials:", {
        hasAccessToken: !!fbCredentials.access_token,
        hasAccountId: !!fbCredentials.account_id,
        accountId: fbCredentials.account_id
    });

    const connectionStatus = document.getElementById('connectionStatus');
    const runAuditBtn = document.getElementById('runAuditBtn');

    if (fbCredentials && fbCredentials.access_token && fbCredentials.account_id) {
        // Update connection status to show success
        if (connectionStatus) {
            connectionStatus.className = 'alert alert-success';
            connectionStatus.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>Connected to Facebook Ads</strong>
                        <br>
                        <small>Account ID: ${fbCredentials.account_id}</small>
                    </div>
                    <a href="/connect/facebook" class="btn btn-outline-success btn-sm">Re-connect</a>
                </div>
            `;
        }
        
        // Enable the run audit button and trigger data fetch
        if (runAuditBtn) {
            runAuditBtn.disabled = false;
            
            // Add click event listener if not already added
            if (!runAuditBtn.hasAttribute('data-listener-added')) {
                runAuditBtn.addEventListener('click', async () => {
                    try {
                        showLoadingState();
                        await fetchAuditData();
                        hideLoadingState();
                    } catch (error) {
                        console.error('Error during audit:', error);
                        showError(error.message || 'An error occurred while running the audit');
                        hideLoadingState();
                    }
                });
                runAuditBtn.setAttribute('data-listener-added', 'true');
            }
        }
        
        // Automatically fetch data if we have credentials
        fetchAuditData().catch(error => {
            console.error('Error fetching initial audit data:', error);
            showError('Failed to fetch audit data. Please try again.');
        });
    } else {
        // Update connection status to show warning
        if (connectionStatus) {
            connectionStatus.className = 'alert alert-warning';
            connectionStatus.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>Not connected to Facebook Ads</strong>
                        <br>
                        <small>Please connect your account to run an audit</small>
                    </div>
                    <a href="/connect/facebook" class="btn btn-primary btn-sm">Connect Account</a>
                </div>
            `;
        }
        
        // Disable the run audit button
        if (runAuditBtn) {
            runAuditBtn.disabled = true;
        }
        
        showError('Facebook credentials not found. Please connect your account.');
    }
}

// Add this function at the top of the file
async function initializeFacebookCredentials() {
    try {
        // Check if we're returning from Facebook OAuth
        const urlParams = new URLSearchParams(window.location.search);
        const fbConnected = urlParams.get('fb_connected');
        
        if (fbConnected === 'true') {
            console.log('Detected successful Facebook connection');
        }
        
        // Try to fetch stored credentials
        const response = await fetch('/api/facebook/credentials', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            if (response.status === 404) {
                console.log('No Facebook credentials found');
                updateConnectionStatus(false);
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (!data.success || !data.credentials) {
            console.log('No valid credentials in response');
            updateConnectionStatus(false);
            return null;
        }

        const { access_token, account_id } = data.credentials;
        
        if (!access_token || !account_id) {
            console.log('Incomplete credentials received');
            updateConnectionStatus(false);
            return null;
        }

        console.log('Successfully retrieved Facebook credentials');
        
        // Store credentials in sessionStorage
        const credentials = { access_token, account_id };
        sessionStorage.setItem('fb_credentials', JSON.stringify(credentials));
        
        // Update UI and fetch data
        updateConnectionStatus(true);
        return credentials;

    } catch (error) {
        console.error('Error fetching credentials:', error);
        showError('Failed to retrieve Facebook credentials. Please try reconnecting your account.');
        updateConnectionStatus(false);
        return null;
    }
}

function updateConnectionStatus(isConnected) {
    const runAuditBtn = document.getElementById('runAuditBtn');
    const connectFbLink = document.getElementById('connectFbLink');
    
    if (isConnected) {
        // Get stored credentials
        const fbCredentials = JSON.parse(sessionStorage.getItem('fb_credentials') || '{}');
        const hasAccessToken = !!fbCredentials.access_token;
        const hasAccountId = !!fbCredentials.account_id;
        
        console.log('Connection status:', { hasAccessToken, hasAccountId });
        
        if (hasAccessToken && hasAccountId) {
            if (runAuditBtn) {
                runAuditBtn.disabled = false;
                runAuditBtn.title = 'Run Facebook Ads Audit';
            }
            if (connectFbLink) {
                connectFbLink.textContent = 'Reconnect Facebook Account';
                connectFbLink.classList.remove('btn-primary');
                connectFbLink.classList.add('btn-outline-secondary');
            }
            hideError();
            return true;
        }
    }
    
    // Not connected or missing credentials
    if (runAuditBtn) {
        runAuditBtn.disabled = true;
        runAuditBtn.title = 'Please connect your Facebook account first';
    }
    if (connectFbLink) {
        connectFbLink.textContent = 'Connect Facebook Account';
        connectFbLink.classList.remove('btn-outline-secondary');
        connectFbLink.classList.add('btn-primary');
    }
    return false;
}

// Update the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', async function() {
    console.log("DOM fully loaded");
    
    // Ensure main content exists
    ensureMainContent();
    
    // Initialize Facebook credentials if needed
    await initializeFacebookCredentials();
    
    // Update client dropdown if it exists
    updateClientDropdown();
    
    // Check Facebook connection
    checkFacebookConnection();
    
    // Then fetch audit data if connected
    const fbCredentials = JSON.parse(sessionStorage.getItem('fb_credentials') || '{}');
    if (fbCredentials.access_token && fbCredentials.account_id) {
        fetchAuditData();
    }
    
    // Add event listeners for time filter dropdowns
    document.querySelectorAll('.time-filter').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const period = this.getAttribute('data-period');
            if (period) {
                document.getElementById('selectedPeriod').textContent = `Last ${period} Days`;
            }
        });
    });
    
    // Add event listener for export button
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
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

// Function to update charts with account overview data
function updateCharts(accountOverview) {
    console.log('Updating charts with account overview:', accountOverview);
    
    try {
        // Ensure chart containers exist
        ensureChartContainers();
        
        // Update Performance Gauge
        const improvementPercentage = accountOverview.potential_improvement || 15.5; // Default fallback
        initPerformanceGauge(improvementPercentage);
        
        // Update Campaign Chart
        initCampaignChart(accountOverview);
        
        // Update Account Overview Stats
        updateAccountOverviewStats(accountOverview);
    } catch (error) {
        console.error('Error updating charts:', error);
    }
}

// Function to update account overview statistics
function updateAccountOverviewStats(accountOverview) {
    const stats = {
        'totalCampaigns': { id: 'stat-totalCampaigns', value: accountOverview.total_campaigns || 0 },
        'activeCampaigns': { id: 'stat-activeCampaigns', value: accountOverview.active_campaigns || 0 },
        'totalSpend': { 
            id: 'stat-totalSpend', 
            value: accountOverview.total_spend || 0,
            format: (val) => formatCurrency(val)
        }
    };
    
    Object.entries(stats).forEach(([key, config]) => {
        const element = document.getElementById(config.id);
        if (element) {
            const value = config.format ? config.format(config.value) : config.value;
            element.textContent = value;
        }
    });
}
