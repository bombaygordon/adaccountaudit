// Add this at the top of the file
let mainContentElement = null;

// Helper function to check if we're on a specific page
function isPageWithId(elementId) {
    return document.getElementById(elementId) !== null;
}

// Function to check if we're on the dashboard page
function isDashboardPage() {
    // Check for elements that only exist on the dashboard
    return isPageWithId('recommendationsContainer') || 
           isPageWithId('platformsAudited') ||
           document.querySelector('.dashboard-content') !== null;
}

// Improved version of getElement that doesn't log warnings on certain pages
function getElement(id, logWarning = true) {
    const element = document.getElementById(id);
    if (!element && logWarning) {
        // Only log warnings if we're on a page where the element should exist
        if (
            (id === 'runAuditBtn' && isDashboardPage()) ||
            (id === 'errorAlert' && isDashboardPage()) ||
            (id === 'loadingIndicator' && isDashboardPage())
        ) {
            console.warn(`Element with id "${id}" not found in the DOM`);
        }
    }
    return element;
}

// Updated ensureMainContent function
function ensureMainContent() {
    // Try to find existing main content
    let mainContentElement = document.querySelector('.main-content');
    
    // If it doesn't exist, find the appropriate container to add it to
    if (!mainContentElement) {
        // Look for existing container
        const container = document.querySelector('.container');
        if (!container) {
            console.error('No container found in the page structure');
            return null;
        }
        
        // Create main content element
            mainContentElement = document.createElement('div');
            mainContentElement.className = 'main-content';
        
        // Add it to the existing container
        container.appendChild(mainContentElement);
        console.log('Added main content to existing container');
    }
    
    return mainContentElement;
}

// Updated ensureContainer function
function ensureContainer() {
    // Just return the existing main content
    return document.querySelector('.main-content');
}

// Update showError function
function showError(message) {
    let errorDiv = getElement('errorAlert', false);
    
    if (!errorDiv && isDashboardPage()) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'errorAlert';
        errorDiv.className = 'alert alert-danger';
        
        // Find dashboard content area
        const dashboardContent = document.querySelector('.dashboard-content');
        if (dashboardContent) {
            dashboardContent.insertBefore(errorDiv, dashboardContent.firstChild);
        }
    }
    
    if (errorDiv) {
        errorDiv.innerHTML = message;
        errorDiv.style.display = 'block';
    } else {
        console.error("Error:", message);
    }
}

function hideError() {
    const errorDiv = getElement('errorAlert', false);
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

function showLoadingState() {
    hideError();
    
    let loadingDiv = getElement('loadingIndicator', false);
    
    if (!loadingDiv && isDashboardPage()) {
        loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingIndicator';
        loadingDiv.className = 'text-center mt-3';
        loadingDiv.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading data...</p>
        `;
        
        // Find dashboard content area
        const dashboardContent = document.querySelector('.dashboard-content');
        if (dashboardContent) {
            dashboardContent.insertBefore(loadingDiv, dashboardContent.firstChild);
        }
    }
    
    if (loadingDiv) {
        loadingDiv.style.display = 'block';
    }
}

function hideLoadingState() {
    const loadingDiv = getElement('loadingIndicator', false);
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

// Updated extractAnalysisData function with direct data processing
function extractAnalysisData(data) {
    console.log("Extracting analysis data from:", data);
    
    // Validate the data structure
    if (!data || !data.hierarchy || !Array.isArray(data.hierarchy)) {
        console.error("Invalid data structure:", data);
        throw new Error('Invalid data structure received from API');
    }
    
    // Process the data directly without relying on external modules
      return {
        campaigns: data.hierarchy,
        account_overview: calculateAccountOverview(data.hierarchy),
        insights: extractInsights(data.hierarchy)
    };
}

// Helper function to calculate account overview
function calculateAccountOverview(campaigns) {
    const overview = {
        total_spend: 0,
        total_impressions: 0,
        total_clicks: 0,
        total_conversions: 0,
        active_campaigns: 0
    };
    
    campaigns.forEach(campaign => {
        if (campaign.status === 'ACTIVE') {
            overview.active_campaigns++;
        }
        overview.total_spend += parseFloat(campaign.spend || 0);
        overview.total_impressions += parseInt(campaign.impressions || 0);
        overview.total_clicks += parseInt(campaign.clicks || 0);
        overview.total_conversions += parseInt(campaign.conversions || 0);
    });
    
    // Calculate derived metrics
    overview.ctr = overview.total_impressions > 0 ? (overview.total_clicks / overview.total_impressions) * 100 : 0;
    overview.cpc = overview.total_clicks > 0 ? overview.total_spend / overview.total_clicks : 0;
    overview.cpm = overview.total_impressions > 0 ? (overview.total_spend / overview.total_impressions) * 1000 : 0;
    overview.conversion_rate = overview.total_clicks > 0 ? (overview.total_conversions / overview.total_clicks) * 100 : 0;
    overview.cpa = overview.total_conversions > 0 ? overview.total_spend / overview.total_conversions : 0;
    
    return overview;
}

// Helper function to extract insights
function extractInsights(campaigns) {
    return campaigns.map(campaign => ({
        campaign_id: campaign.id,
        campaign_name: campaign.name,
        spend: parseFloat(campaign.spend || 0),
        impressions: parseInt(campaign.impressions || 0),
        clicks: parseInt(campaign.clicks || 0),
        conversions: parseInt(campaign.conversions || 0),
        ctr: parseFloat(campaign.ctr || 0),
        cpc: parseFloat(campaign.cpc || 0),
        level: 'campaign'
    }));
}

// Updated fetchAuditData function to better handle the Facebook data
async function fetchAuditData() {
    try {
        console.log("Starting fetchAuditData function");
        
    // Get Facebook credentials from session storage
    const fbCredentials = getSafeCredentials();
    console.log("Retrieved credentials:", {
      hasAccessToken: !!fbCredentials?.access_token,
      hasAccountId: !!fbCredentials?.account_id,
      accountId: fbCredentials?.account_id
    });
    
    if (!fbCredentials) {
      console.error("Facebook credentials not found");
      showError("Facebook credentials not found. Please reconnect your account.");
      return;
    }
    
    // Show loading state
    showLoadingState();
    hideError(); // Hide any existing errors
    
        // First, try to get campaign hierarchy data
      const hierarchyResponse = await fetch('/api/campaign-hierarchy', {
                method: 'POST',
                headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',  // Prevent caching
                'Pragma': 'no-cache'
                },
                body: JSON.stringify({
          accessToken: fbCredentials.access_token,
          accountId: fbCredentials.account_id
                })
            });
            
      console.log("Campaign hierarchy response status:", hierarchyResponse.status);
      
        if (!hierarchyResponse.ok) {
            throw new Error(`HTTP error! status: ${hierarchyResponse.status}`);
        }
        
        const hierarchyData = await hierarchyResponse.json();
        console.log("Campaign hierarchy data:", hierarchyData);
        
        if (!hierarchyData.success) {
            throw new Error(hierarchyData.error || 'Failed to fetch campaign data');
        }
        
          // Process and update dashboard with hierarchy data
          const processedData = extractAnalysisData(hierarchyData);
        if (!processedData || !processedData.account_overview) {
            throw new Error('Invalid data structure received from API');
        }
        
        updateDashboard(processedData);
        
    } catch (error) {
        console.error("Error in fetchAuditData:", error);
        showError(`Failed to fetch campaign data: ${error.message}`);
        
        // Don't fall back to sample data immediately
        if (error.message.includes('rate limit') || error.message.includes('429')) {
            showError('Rate limit reached. Please try again in a few minutes.');
        } else if (error.message.includes('auth') || error.message.includes('401')) {
            showError('Authentication failed. Please reconnect your Facebook account.');
        } else {
            showError(`Error fetching data: ${error.message}`);
        }
    } finally {
    hideLoadingState();
  }
}

// Updated updateDashboard function to handle the data structure
function updateDashboard(data) {
  console.log("Updating dashboard with data:", data);
  
  if (!data || typeof data !== 'object') {
    console.error('Invalid data received:', data);
    showError("Invalid data received from the server");
    return;
  }
  
  // Update recommendations section
  if (data.recommendations || data.prioritized_recommendations) {
    const recommendations = data.recommendations || data.prioritized_recommendations || [];
    updateRecommendations(recommendations);
  } else {
    // If no recommendations are provided, generate some sample ones
    const sampleRecommendations = window.FacebookAdapter.generateSampleRecommendations(data);
    updateRecommendations(sampleRecommendations);
  }
  
  // Update metrics
  if (data.metrics || data.account_overview) {
    const metrics = data.metrics || {};
    const accountOverview = data.account_overview || {};
    
    // Combine the data
    const combinedMetrics = {
      totalSpend: accountOverview.total_spend || metrics.total_spend || 0,
      totalImpressions: accountOverview.total_impressions || metrics.total_impressions || 0,
      totalClicks: accountOverview.total_clicks || metrics.total_clicks || 0,
      totalConversions: accountOverview.total_conversions || metrics.total_conversions || 0,
      ctr: accountOverview.ctr || metrics.ctr || 0,
      cpc: accountOverview.cpc || metrics.cpc || 0,
      cpa: accountOverview.cpa || metrics.cpa || 0,
      conversionRate: accountOverview.conversion_rate || metrics.conversion_rate || 0,
      roas: accountOverview.roas || metrics.roas || 0
    };
    
    updateMetrics(combinedMetrics);
  }
  
  // Update potential savings
  const potentialSavings = getElement('potentialSavings', false);
  if (potentialSavings) {
    // Default to $750 if not provided
    potentialSavings.textContent = formatCurrency(data.potential_savings || 750);
  }
  
  // Update potential improvement percentage
  const potentialImprovement = getElement('potentialImprovement', false);
  if (potentialImprovement) {
    // Default to 15.5% if not provided
    potentialImprovement.textContent = formatPercentage(data.potential_improvement_percentage || 15.5);
  }
  
  // Initialize or update charts
  try {
    initCharts(data);
  } catch (e) {
    console.warn("Error initializing charts:", e);
  }
  
  // Update summary metrics
  updateSummaryMetrics(data);
}

// Function to update metrics section
function updateMetrics(metrics) {
    console.log('Updating metrics with values:', metrics);
    
    const metricsMap = {
        'totalSpend': { 
            id: 'metric-totalSpend', 
            format: (val) => `$${Number(val || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` 
        },
        'ctr': { 
            id: 'metric-ctr', 
            format: (val) => `${(Number(val || 0) * 100).toFixed(2)}%` 
        },
        'cpc': { 
            id: 'metric-cpc', 
            format: (val) => `$${Number(val || 0).toFixed(2)}` 
        },
        'cpm': { 
            id: 'metric-cpm', 
            format: (val) => `$${Number(val || 0).toFixed(2)}` 
        },
        'conversionRate': { 
            id: 'metric-conversionRate', 
            format: (val) => `${(Number(val || 0) * 100).toFixed(2)}%` 
        },
        'roas': { 
            id: 'metric-roas', 
            format: (val) => Number(val || 0).toFixed(2) 
        }
    };
    
    Object.entries(metrics).forEach(([key, value]) => {
        const metricConfig = metricsMap[key];
        if (metricConfig) {
            const element = document.getElementById(metricConfig.id);
            if (element) {
                try {
                    const formattedValue = metricConfig.format(value);
                    console.log(`Updating ${key} with value:`, value, 'formatted as:', formattedValue);
                    element.textContent = formattedValue;
                } catch (error) {
                    console.error(`Error formatting ${key}:`, error);
                    element.textContent = '0.00';
                }
            } else {
                console.warn(`Element not found for metric: ${key} (id: ${metricConfig.id})`);
            }
        }
    });
}

// Updated function to handle connection status
function updateConnectionStatus(isConnected) {
    if (!isDashboardPage()) {
        return; // Don't update connection status on non-dashboard pages
    }
    
    const runAuditBtn = getElement('runAuditBtn', false);
    const connectFbLink = getElement('connectFbLink', false);
    const fbConnectionStatus = getElement('fbConnectionStatus', false);
    
    if (isConnected) {
        // Get stored credentials
        const fbCredentials = getSafeCredentials();
        const hasAccessToken = !!fbCredentials?.access_token;
        const hasAccountId = !!fbCredentials?.account_id;
        
        console.log('Connection status:', { hasAccessToken, hasAccountId, accountId: fbCredentials?.account_id });
        
        if (hasAccessToken && hasAccountId) {
            if (runAuditBtn) {
                runAuditBtn.disabled = false;
                runAuditBtn.title = 'Run Facebook Ads Audit';
            }
            
            if (connectFbLink) {
                connectFbLink.textContent = 'Re-connect Facebook';
                connectFbLink.classList.remove('btn-primary');
                connectFbLink.classList.add('btn-outline-secondary');
            }
            
            if (fbConnectionStatus) {
                fbConnectionStatus.textContent = `Connected (Account ID: ${fbCredentials.account_id})`;
        fbConnectionStatus.classList.add('text-success');
            }
            
            hideError();
            return true;
        }
    }
    
    // Not connected
    if (runAuditBtn) {
        runAuditBtn.disabled = true;
        runAuditBtn.title = 'Please connect your Facebook account first';
    }
    
    if (connectFbLink) {
        connectFbLink.textContent = 'Connect Facebook Account';
        connectFbLink.classList.remove('btn-outline-secondary');
        connectFbLink.classList.add('btn-primary');
    }
    
    if (fbConnectionStatus) {
        fbConnectionStatus.textContent = 'Not connected';
        fbConnectionStatus.classList.remove('text-success');
    }
    
    return false;
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

// Updated initCampaignChart function to handle missing spend values
async function initCampaignChart(data) {
    console.log('Initializing campaign chart with data:', data);
    
    try {
        // Find the dashboard content area
        const dashboardContent = document.querySelector('.dashboard-content');
        if (!dashboardContent) {
            console.error('Dashboard content area not found');
            return;
        }
        
        // Create charts section if it doesn't exist
        let chartsSection = document.getElementById('chartsSection');
        if (!chartsSection) {
            chartsSection = document.createElement('div');
            chartsSection.id = 'chartsSection';
            chartsSection.className = 'row mb-4';
            dashboardContent.insertBefore(chartsSection, dashboardContent.firstChild);
        }
        
        // Process campaign data if available
        const campaignData = data?.campaigns || await fetchCampaignData();
        if (!campaignData || !Array.isArray(campaignData)) {
            console.warn('No valid campaign data found');
            return;
        }
        
        // Detailed campaign data debugging
        console.log('Campaign data sample:', campaignData.slice(0, 2));
        if (campaignData[0]) {
            console.log('First campaign raw data:', JSON.stringify(campaignData[0], null, 2));
        }
        
        // Process campaigns with Facebook API data handling
        const processedCampaigns = campaignData
            .map(campaign => {
                // Extract spend from Facebook API data structure
                let spendValue = 0;
                
                // Try to get spend from insights first (most reliable)
                if (campaign.insights && Array.isArray(campaign.insights) && campaign.insights.length > 0) {
                    const insight = campaign.insights[0];
                    spendValue = parseFloat(insight.spend || insight.amount_spent || 0);
                }
                
                // If no spend in insights, try other locations
                if (!spendValue) {
                    spendValue = parseFloat(
                        campaign.spend || 
                        campaign.amount_spent || 
                        campaign.lifetime_spend || 
                        campaign.daily_spend ||
                        campaign.budget?.amount ||
                        0
                    );
                }
                
                // Log spend extraction for debugging
                console.debug('Campaign spend extraction:', {
                    campaignId: campaign.id,
                    name: campaign.name,
                    spendValue,
                    rawData: {
                        spend: campaign.spend,
                        amount_spent: campaign.amount_spent,
                        lifetime_spend: campaign.lifetime_spend,
                        daily_spend: campaign.daily_spend,
                        insights: campaign.insights?.[0],
                        budget: campaign.budget
                    }
                });
                
                // Extract other metrics
                const impressions = parseInt(
                    campaign.insights?.[0]?.impressions || 
                    campaign.impressions || 
                    0
                );
                
                const clicks = parseInt(
                    campaign.insights?.[0]?.clicks || 
                    campaign.clicks || 
                    0
                );
                
                return {
                    name: campaign.name || `Campaign ${campaign.id}`,
                    spend: spendValue,
                    impressions: impressions,
                    clicks: clicks,
                    debug: {
                        originalSpend: campaign.spend,
                        amountSpent: campaign.amount_spent,
                        lifetimeSpend: campaign.lifetime_spend,
                        dailySpend: campaign.daily_spend,
                        insightsSpend: campaign.insights?.[0]?.spend,
                        budgetAmount: campaign.budget?.amount,
                        finalSpend: spendValue,
                        currency: campaign.account_currency || 'USD'
                    }
                };
            })
            .filter(campaign => {
                // Only filter out campaigns with zero spend if we're not using mock data
                if (campaign.spend <= 0) {
                    console.debug('Filtered out campaign with zero spend:', {
                        name: campaign.name,
                        debug: campaign.debug
                    });
                    return false;
                }
                return true;
            })
            .sort((a, b) => b.spend - a.spend)
            .slice(0, 7);
        
        // Log processed campaigns
        console.log('Processed campaigns for chart:', processedCampaigns);
        
        // Create chart data
        const chartData = {
            labels: processedCampaigns.map(c => c.name),
            datasets: [{
                label: 'Campaign Spend ($)',
                data: processedCampaigns.map(c => c.spend),
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        };
        
        // Create or update campaign chart container
        let campaignChartContainer = document.getElementById('campaignChartContainer');
        if (!campaignChartContainer) {
            campaignChartContainer = document.createElement('div');
            campaignChartContainer.id = 'campaignChartContainer';
            campaignChartContainer.className = 'col-md-12 mb-4';
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
        
        // Add note about data source
        const cardBody = campaignChartContainer.querySelector('.card-body');
        let noteElement = document.getElementById('data-source-note');
        if (!noteElement) {
            noteElement = document.createElement('div');
            noteElement.id = 'data-source-note';
            noteElement.className = 'small text-muted mt-2';
            noteElement.innerHTML = '<i class="fas fa-info-circle"></i> Data from Facebook Ads API';
            cardBody.appendChild(noteElement);
        }
        
        // Update performance metrics with the processed data
        updatePerformanceMetrics(processedCampaigns);
        
    } catch (error) {
        console.error('Error initializing campaign chart:', error);
        showError('Failed to initialize campaign chart: ' + error.message);
    }
}

// New function to update performance metrics
function updatePerformanceMetrics(campaigns) {
    const totalSpend = campaigns.reduce((sum, campaign) => sum + campaign.spend, 0);
    const totalImpressions = campaigns.reduce((sum, campaign) => sum + campaign.impressions, 0);
    const totalClicks = campaigns.reduce((sum, campaign) => sum + campaign.clicks, 0);
    
    const metrics = {
        totalSpend,
        ctr: totalImpressions > 0 ? (totalClicks / totalImpressions) * 100 : 0,
        cpc: totalClicks > 0 ? totalSpend / totalClicks : 0,
        cpm: totalImpressions > 0 ? (totalSpend / totalImpressions) * 1000 : 0
    };
    
    updateMetrics(metrics);
}

// Updated createChartsSection function
function createChartsSection() {
    // Find the dashboard content area
    const dashboardContent = document.querySelector('.dashboard-content');
    if (!dashboardContent) {
        console.error('Dashboard content area not found');
        return null;
    }
    
    // Remove any existing performance overview cards
    const performanceOverviewCards = dashboardContent.querySelectorAll('.card.mb-4');
    performanceOverviewCards.forEach(card => {
        const header = card.querySelector('.card-header h5.mb-0');
        if (header && header.textContent === 'Performance Overview') {
            card.remove();
        }
    });
    
    // Remove any existing campaign chart and spend overview chart
    const campaignChart = document.getElementById('campaignChart');
    if (campaignChart) {
        const cardContainer = campaignChart.closest('.card');
        if (cardContainer) {
            cardContainer.remove();
        }
    }
    
    const spendOverviewChart = document.getElementById('spendOverviewChart');
    if (spendOverviewChart) {
        const cardContainer = spendOverviewChart.closest('.card');
        if (cardContainer) {
            cardContainer.remove();
        }
    }
    
    let chartsSection = document.getElementById('chartsSection');
    if (!chartsSection) {
        chartsSection = document.createElement('div');
        chartsSection.id = 'chartsSection';
        chartsSection.className = 'row mb-4';
        
        // Insert at the beginning of dashboard content
        if (dashboardContent.firstChild) {
            dashboardContent.insertBefore(chartsSection, dashboardContent.firstChild);
        } else {
            dashboardContent.appendChild(chartsSection);
        }
    }
    
    return chartsSection;
}

function showChartEmptyState(chartId) {
    const canvas = document.getElementById(chartId);
    const emptyState = document.getElementById(`${chartId}-empty-state`);
    
    if (canvas) {
        canvas.style.display = 'none';
    }
    
    if (emptyState) {
        emptyState.style.display = 'flex';
    }
}

// Update ensureChartContainers function
function ensureChartContainers() {
    // Find the dashboard content area
    const dashboardContent = document.querySelector('.dashboard-content');
    if (!dashboardContent) {
        console.error('Dashboard content area not found');
        return;
    }
    
    // Remove any existing performance overview section
    const performanceOverviewCards = dashboardContent.querySelectorAll('.card.mb-4');
    performanceOverviewCards.forEach(card => {
        const header = card.querySelector('.card-header h5.mb-0');
        if (header && header.textContent === 'Performance Overview') {
            card.remove();
        }
    });
    
    // Remove any existing campaign chart and spend overview chart
    const campaignChart = document.getElementById('campaignChart');
    if (campaignChart) {
        const cardContainer = campaignChart.closest('.card');
        if (cardContainer) {
            cardContainer.remove();
        }
    }
    
    const spendOverviewChart = document.getElementById('spendOverviewChart');
    if (spendOverviewChart) {
        const cardContainer = spendOverviewChart.closest('.card');
        if (cardContainer) {
            cardContainer.remove();
        }
    }
    
    // Create or find the charts section
    let chartsSection = document.getElementById('chartsSection');
    if (!chartsSection) {
        chartsSection = document.createElement('section');
        chartsSection.id = 'chartsSection';
        chartsSection.className = 'row mb-4';
        dashboardContent.insertBefore(chartsSection, dashboardContent.firstChild);
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

// Improved error handling function
function handleApiError(error) {
    console.error('API Error:', error);
    
    // Default error message
    let errorMessage = 'An error occurred while processing your request.';
    let errorType = 'unknown';
    let shouldRetry = false;
    let shouldReconnect = false;
    
    // Helper function to determine if error is a network error
    const isNetworkError = (err) => {
        return err instanceof TypeError && 
               (err.message.includes('Failed to fetch') || 
                err.message.includes('NetworkError') ||
                err.message.includes('Network request failed'));
    };
    
    // Helper function to determine if error is a timeout
    const isTimeoutError = (err) => {
        return err.message.includes('timeout') || 
               err.message.includes('Request timed out') ||
               err.message.includes('AbortError');
    };
    
    // Helper function to determine if error is a rate limit
    const isRateLimitError = (err) => {
        return err.message.includes('rate limit') || 
               err.message.includes('User request limit reached') ||
               err.message.includes('Too Many Requests') ||
               err.message.includes('429');
    };
    
    // Helper function to determine if error is an authentication error
    const isAuthError = (err) => {
        return err.message.includes('Invalid OAuth access token') ||
               err.message.includes('Unauthorized') ||
               err.message.includes('401') ||
               err.message.includes('authentication failed');
    };
    
    // Helper function to determine if error is a server error
    const isServerError = (err) => {
        return err.message.includes('500') ||
               err.message.includes('Internal Server Error') ||
               err.message.includes('Service Unavailable') ||
               err.message.includes('503');
    };
    
    // Helper function to determine if error is a resource not found error
    const isNotFoundError = (err) => {
        return err.message.includes('404') ||
               err.message.includes('Not Found') ||
               err.message.includes('Resource not found');
    };
    
    // Helper function to determine if error is a validation error
    const isValidationError = (err) => {
        return err.message.includes('400') ||
               err.message.includes('Bad Request') ||
               err.message.includes('validation failed') ||
               err.message.includes('invalid input');
    };
    
    // Helper function to determine if error is an OpenAI-specific error
    const isOpenAIError = (err) => {
        return err.message.includes('OpenAI') ||
               err.message.includes('GPT') ||
               err.message.includes('model');
    };
    
    // Helper function to determine if error is a Facebook-specific error
    const isFacebookError = (err) => {
        return err.message.includes('Facebook') ||
               err.message.includes('OAuth') ||
               err.message.includes('access token');
    };
    
    if (error) {
        // Network errors
        if (isNetworkError(error)) {
            errorMessage = 'Unable to connect to the server. Please check your internet connection and try again.';
            errorType = 'network';
            shouldRetry = true;
        }
        // Timeout errors
        else if (isTimeoutError(error)) {
            errorMessage = 'The request took too long to complete. Please try again.';
            errorType = 'timeout';
            shouldRetry = true;
        }
        // Rate limit errors
        else if (isRateLimitError(error)) {
            errorMessage = 'Too many requests. Please wait a few minutes before trying again.';
            errorType = 'rate_limit';
            shouldRetry = true;
        }
        // Authentication errors
        else if (isAuthError(error)) {
            errorMessage = 'Your session has expired. Please reconnect your Facebook account.';
            errorType = 'auth';
            shouldReconnect = true;
        }
        // Server errors
        else if (isServerError(error)) {
            errorMessage = 'The server is experiencing issues. Please try again in a few minutes.';
            errorType = 'server';
            shouldRetry = true;
        }
        // Resource not found errors
        else if (isNotFoundError(error)) {
            errorMessage = 'The requested resource could not be found. Please check your account ID and try again.';
            errorType = 'not_found';
        }
        // Validation errors
        else if (isValidationError(error)) {
            errorMessage = 'Invalid input provided. Please check your settings and try again.';
            errorType = 'validation';
        }
        // OpenAI-specific errors
        else if (isOpenAIError(error)) {
            if (error.message.includes('API key not configured')) {
                errorMessage = 'The OpenAI API key is not configured. Please contact support.';
            } else if (error.message.includes('API key is invalid')) {
                errorMessage = 'The OpenAI API key is invalid. Please check your API key configuration.';
            } else if (error.message.includes('analysis failed')) {
                errorMessage = 'The analysis service encountered an error. Please try again later.';
            } else {
                errorMessage = 'An error occurred with the analysis service. Please try again later.';
            }
            errorType = 'openai';
        }
        // Facebook-specific errors
        else if (isFacebookError(error)) {
            if (error.message.includes('Invalid OAuth access token')) {
                errorMessage = 'Your Facebook connection has expired. Please reconnect your account.';
                shouldReconnect = true;
            } else if (error.message.includes('permissions')) {
                errorMessage = 'Insufficient permissions to access Facebook data. Please reconnect with the required permissions.';
                shouldReconnect = true;
            } else {
                errorMessage = 'An error occurred while accessing Facebook data. Please try again.';
            }
            errorType = 'facebook';
        }
        // Fallback to error message if available
        else if (error.message) {
            errorMessage = error.message;
        }
    }
    
    // Log the categorized error
    console.error('Categorized API Error:', {
        type: errorType,
        message: errorMessage,
        shouldRetry,
        shouldReconnect,
        originalError: error
    });
    
    // Show the error message
    showError(errorMessage);
    
    // Handle reconnection if needed
    if (shouldReconnect) {
        // Clear invalid credentials
        sessionStorage.removeItem('fb_credentials');
        sessionStorage.removeItem('facebook_response');
        
        // Redirect to Facebook connection page after a short delay
        setTimeout(() => {
            window.location.href = '/connect/facebook';
        }, 3000);
    }
    
    // Return error details for potential retry logic
    return {
        type: errorType,
        message: errorMessage,
        shouldRetry,
        shouldReconnect,
        originalError: error
    };
}

// Updated initializeFacebookCredentials function
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

// Updated getSafeCredentials function
function getSafeCredentials() {
    try {
        const credentials = JSON.parse(sessionStorage.getItem('fb_credentials') || '{}');
        if (!credentials.access_token || !credentials.account_id) {
            console.warn('Incomplete Facebook credentials found');
            return null;
        }
        return credentials;
    } catch (error) {
        console.error('Error parsing Facebook credentials:', error);
        return null;
    }
}

// Updated checkFacebookConnection function
function checkFacebookConnection() {
    const fbCredentials = getSafeCredentials();
    console.log('Checking Facebook credentials:', {
        hasAccessToken: !!fbCredentials?.access_token,
        hasAccountId: !!fbCredentials?.account_id,
        accountId: fbCredentials?.account_id
    });
    
    return !!fbCredentials;
}

// Function to fetch campaign data
async function fetchCampaignData() {
    try {
        const fbCredentials = JSON.parse(sessionStorage.getItem('fb_credentials') || '{}');
        
        if (!fbCredentials.access_token || !fbCredentials.account_id) {
            console.error('Facebook credentials not found');
            return null;
        }

        const response = await fetch('/api/campaign-hierarchy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                accessToken: fbCredentials.access_token,
                accountId: fbCredentials.account_id
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Raw campaign data:', data);

        if (!data.success || !data.hierarchy) {
            console.error('Invalid campaign data structure:', data);
            return null;
        }

        return data.hierarchy;
    } catch (error) {
        console.error('Error fetching campaign data:', error);
        return null;
    }
}

// Updated initializeCharts function
async function initializeCharts() {
    console.log("Starting charts initialization");
    
    try {
        // Find the dashboard content area
        const dashboardContent = document.querySelector('.dashboard-content');
        if (!dashboardContent) {
            console.error('Dashboard content area not found. Make sure you are on the dashboard page.');
            return;
        }
        
        // Create charts section if it doesn't exist
        let chartsSection = document.getElementById('chartsSection');
        if (!chartsSection) {
            chartsSection = document.createElement('div');
            chartsSection.id = 'chartsSection';
            chartsSection.className = 'row mb-4';
            dashboardContent.insertBefore(chartsSection, dashboardContent.firstChild);
        }
        
        // Initialize campaign chart with empty data first
        await initCampaignChart({});
        
        console.log("Charts initialization complete");
    } catch (error) {
        console.error('Error initializing charts:', error);
        showError('Error initializing dashboard components');
    }
}

// Updated DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', async function() {
    console.log("DOM fully loaded");
    
    try {
        // Check if we're on the dashboard page
        if (isDashboardPage()) {
            console.log("Dashboard page detected, initializing dashboard components");
    
    // Update client dropdown if it exists
            if (document.getElementById('clientSelect')) {
    updateClientDropdown();
            }
            
            // Initialize Facebook credentials and check connection
            await initializeFacebookCredentials();
            const isConnected = checkFacebookConnection();
            console.log('Facebook connection status:', isConnected);
            
            if (isConnected) {
                // Initialize charts and fetch data
                await initializeCharts();
                await fetchAuditData();
            } else {
                showError('Please connect your Facebook account to view campaign data');
            }
        } else {
            console.log("Not on dashboard page, skipping dashboard initialization");
        }
    
        // Add event listeners
        setupEventListeners();
        
    } catch (error) {
        console.error("Error during initialization:", error);
        showError("An error occurred while initializing the dashboard");
    }
});

// Helper function to setup event listeners
function setupEventListeners() {
    // Time filter listeners
    document.querySelectorAll('.time-filter').forEach(item => {
            if (item) {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const period = this.getAttribute('data-period');
                    const selectedPeriod = document.getElementById('selectedPeriod');
                    if (period && selectedPeriod) {
                        selectedPeriod.textContent = `Last ${period} Days`;
                        console.log(`Time filter updated to ${period} days`);
                    }
                });
            }
    });
    
    // Export button listener
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
            exportBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log("Export button clicked");
            generateReport();
        });
        }
        
    // Refresh button listener
    const refreshBtn = document.getElementById('refresh-data');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async function() {
            try {
                refreshBtn.disabled = true;
                refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
                
                await initCampaignChart();
                showToast('success', 'Data refreshed successfully');
    } catch (error) {
                console.error('Error refreshing data:', error);
                showToast('error', 'Failed to refresh data. Please try again.');
            } finally {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync"></i> Refresh Data';
            }
        });
    }
}

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

function showToast(type, message) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Trigger reflow
    toast.offsetHeight;
    
    // Add show class
    toast.classList.add('show');
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
