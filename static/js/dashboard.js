// Dashboard JavaScript

// Initialize the dashboard when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Fetch audit data
    fetchAuditData();
    
    // Fetch client list for the logged-in user
    fetchClientList();
    
    // Set up event listeners
    setupEventListeners();
    
    // Check Facebook connection
    checkFacebookConnection();
});

// Fetch audit data from the API
async function fetchAuditData() {
    try {
        // Check if we have stored audit results from a real audit
        const storedAudit = sessionStorage.getItem('latest_audit');
        if (storedAudit) {
            const data = JSON.parse(storedAudit);
            updateDashboard(data);
            return;
        }
        
        // Otherwise fetch from the test endpoint
        const response = await fetch('/data');
        const data = await response.json();
        
        // Update dashboard with the data
        updateDashboard(data);
    } catch (error) {
        console.error('Error fetching audit data:', error);
        showError('Failed to load audit data. Please try again later.');
    }
}

// Fetch client list for the current user
async function fetchClientList() {
    try {
        const response = await fetch('/api/clients');
        const data = await response.json();
        
        if (data.success && data.clients) {
            updateClientDropdown(data.clients);
        }
    } catch (error) {
        console.error('Error fetching client list:', error);
    }
}

// Check for Facebook connection
function checkFacebookConnection() {
    const fbCredentials = sessionStorage.getItem('fb_credentials');
    const fbConnectionStatus = document.getElementById('fbConnectionStatus');
    
    if (fbCredentials) {
        fbConnectionStatus.textContent = 'Connected';
        fbConnectionStatus.classList.add('text-success');
        
        // Update connect button to say "Manage" instead
        const connectButton = fbConnectionStatus.nextElementSibling;
        if (connectButton) {
            connectButton.textContent = 'Manage';
        }
    }
}

// Update client dropdown with client list
function updateClientDropdown(clients) {
    const clientSelect = document.getElementById('clientSelect');
    
    if (clientSelect) {
        // Clear existing options
        clientSelect.innerHTML = '<option value="">Select a client</option>';
        
        // Add clients to dropdown
        clients.forEach(client => {
            const option = document.createElement('option');
            option.value = client.id;
            option.textContent = client.name;
            clientSelect.appendChild(option);
        });
    }
}

// Update dashboard with audit data
function updateDashboard(data) {
    // Update summary metrics
    updateSummaryMetrics(data);
    
    // Update recommendations
    updateRecommendations(data.prioritized_recommendations);
    
    // Initialize charts
    initCharts(data);
}

// Update summary metrics
function updateSummaryMetrics(data) {
    // Update potential savings
    document.getElementById('potentialSavings').textContent = formatCurrency(data.potential_savings);
    
    // Update potential improvement
    document.getElementById('potentialImprovement').textContent = formatPercentage(data.potential_improvement_percentage);
    
    // Update recommendation count
    document.getElementById('recommendationCount').textContent = data.prioritized_recommendations ? data.prioritized_recommendations.length : 0;
    
    // Update platforms audited
    const platformsAudited = document.getElementById('platformsAudited');
    platformsAudited.textContent = data.platform ? capitalizeFirstLetter(data.platform) : 'Facebook (Mock Data)';
    
    // Update last audited time
    const lastAudited = new Date(data.timestamp);
    document.getElementById('lastAudited').textContent = formatDate(lastAudited);
    
    // Update gauge value
    document.getElementById('gaugeValue').textContent = formatPercentage(data.potential_improvement_percentage);
}

// Update recommendations list
function updateRecommendations(recommendations) {
    const recommendationsList = document.getElementById('recommendationsList');
    recommendationsList.innerHTML = '';
    
    if (recommendations && recommendations.length > 0) {
        recommendations.forEach(rec => {
            // Determine recommendation type icon and color
            let icon = 'lightbulb';
            let category = 'General';
            
            if (rec.type && rec.type.includes('cpc') || rec.type.includes('cpa')) {
                icon = 'dollar-sign';
                category = 'Budget Efficiency';
            } else if (rec.type && rec.type.includes('target')) {
                icon = 'users';
                category = 'Audience Targeting';
            } else if (rec.type && rec.type.includes('creative') || rec.type.includes('fatigue')) {
                icon = 'paint-brush';
                category = 'Creative Performance';
            } else if (rec.type && rec.type.includes('ctr')) {
                icon = 'activity';
                category = 'Performance';
            }
            
            const recommendationItem = document.createElement('div');
            recommendationItem.className = 'recommendation-card';
            recommendationItem.innerHTML = `
                <div class="d-flex align-items-start mb-2">
                    <div class="me-2">
                        <i class="fas fa-${icon} text-primary"></i>
                    </div>
                    <div>
                        <div class="recommendation-title">${category}</div>
                        <div class="recommendation-text">${rec.recommendation}</div>
                    </div>
                </div>
                <div class="d-flex justify-content-end">
                    <span class="platform-badge ${rec.platform || 'facebook'}">${capitalizeFirstLetter(rec.platform || 'facebook')}</span>
                </div>
            `;
            
            recommendationsList.appendChild(recommendationItem);
        });
    } else {
        recommendationsList.innerHTML = '<div class="text-center py-4">No recommendations found.</div>';
    }
}

// Initialize charts
function initCharts(data) {
    // Performance gauge chart
    const improvementPercentage = data.potential_improvement_percentage;
    initGaugeChart(improvementPercentage);
    
    // Campaign performance chart
    initCampaignChart(data);
}

// Initialize gauge chart for performance improvement
function initGaugeChart(percentage) {
    const gaugeElement = document.getElementById('performanceGauge');
    
    // Create a gauge chart showing the performance improvement potential
    const gauge = new Chart(gaugeElement, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [percentage, 100 - percentage],
                backgroundColor: [
                    '#ff6b35',
                    '#f5f5f5'
                ],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '80%',
            rotation: Math.PI,
            circumference: Math.PI,
            tooltips: {
                enabled: false
            },
            hover: {
                mode: null
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Initialize campaign performance chart
function initCampaignChart(data) {
    // Try to get real data if available
    let chartData = {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [
            {
                label: 'Clicks',
                data: [120, 190, 300, 250],
                borderColor: '#ff6b35',
                backgroundColor: 'rgba(255, 107, 53, 0.1)',
                tension: 0.4,
                fill: true
            },
            {
                label: 'Impressions',
                data: [1000, 1200, 1500, 1300],
                borderColor: '#36a2eb',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                tension: 0.4,
                fill: true
            }
        ]
    };
    
    // If we have real trend data, use it
    if (data.metrics && data.metrics.trends && data.metrics.trends.daily_metrics) {
        const dailyMetrics = data.metrics.trends.daily_metrics;
        
        // Group by week
        const weeks = {};
        dailyMetrics.forEach(metric => {
            const date = new Date(metric.date);
            const weekNum = Math.floor(date.getDate() / 7) + 1;
            
            if (!weeks[weekNum]) {
                weeks[weekNum] = {
                    clicks: 0,
                    impressions: 0
                };
            }
            
            weeks[weekNum].clicks += metric.clicks || 0;
            weeks[weekNum].impressions += metric.impressions || 0;
        });
        
        // Format for chart
        const labels = Object.keys(weeks).map(week => `Week ${week}`);
        const clicksData = Object.values(weeks).map(week => week.clicks);
        const impressionsData = Object.values(weeks).map(week => week.impressions);
        
        if (labels.length > 0) {
            chartData = {
                labels: labels,
                datasets: [
                    {
                        label: 'Clicks',
                        data: clicksData,
                        borderColor: '#ff6b35',
                        backgroundColor: 'rgba(255, 107, 53, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Impressions',
                        data: impressionsData,
                        borderColor: '#36a2eb',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.4,
                        fill: true,
                        yAxisID: 'y1'
                    }
                ]
            };
        }
    }
    
    const ctx = document.getElementById('campaignChart').getContext('2d');
    const campaignChart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Clicks'
                    }
                },
                y1: {
                    beginAtZero: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Impressions'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Generate PDF report
function generateReport() {
    // Get selected client ID from dropdown
    const clientSelect = document.getElementById('clientSelect');
    const clientId = clientSelect ? clientSelect.value : null;
    
    if (clientSelect && !clientId) {
        alert('Please select a client for the report');
        return;
    }
    
    // Show loading spinner
    document.getElementById('exportBtn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
    document.getElementById('exportBtn').disabled = true;
    
    // Prepare request data
    const requestData = {
        client_id: clientId,
        client_name: clientId ? null : 'Demo Client'
    };
    
    // Call the API to generate report
    fetch('/api/generate-report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reset button
            document.getElementById('exportBtn').innerHTML = '<i class="fas fa-file-export me-2"></i>Export Report';
            document.getElementById('exportBtn').disabled = false;
            
            // Download the report
            window.location.href = data.download_url;
            
            // Show success message
            alert('Report generated successfully for ' + (data.client_name || 'Demo Client'));
        } else {
            throw new Error(data.error || 'Failed to generate report');
        }
    })
    .catch(error => {
        console.error('Error generating report:', error);
        
        // Reset button
        document.getElementById('exportBtn').innerHTML = '<i class="fas fa-file-export me-2"></i>Export Report';
        document.getElementById('exportBtn').disabled = false;
        
        // Show error message
        alert('Failed to generate report. Please try again.');
    });
}

// Set up event listeners
function setupEventListeners() {
    // Time period filters
    const timeFilters = document.querySelectorAll('.time-filter');
    timeFilters.forEach(filter => {
        filter.addEventListener('click', function(e) {
            e.preventDefault();
            const period = this.dataset.period;
            document.getElementById('selectedPeriod').textContent = this.textContent;
            // In a real app, this would trigger a data refresh for the selected period
        });
    });
    
    // Export button
    document.getElementById('exportBtn').addEventListener('click', function() {
        generateReport();
    });
    
    // Client filter change
    const clientSelect = document.getElementById('clientSelect');
    if (clientSelect) {
        clientSelect.addEventListener('change', function() {
            // In a real app, this would refresh data for the selected client
            // For now, we'll just update the client name display
            const selectedOption = clientSelect.options[clientSelect.selectedIndex];
            if (selectedOption.value) {
                console.log(`Selected client: ${selectedOption.text} (ID: ${selectedOption.value})`);
                // Here you would fetch client-specific data
            }
        });
    }
}

// Utility functions
function formatCurrency(value) {
    return '$' + parseFloat(value).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatPercentage(value) {
    return parseFloat(value).toFixed(1) + '%';
}

function formatDate(date) {
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function showError(message) {
    // Create an error alert
    const errorAlert = document.createElement('div');
    errorAlert.className = 'alert alert-danger alert-dismissible fade show';
    errorAlert.role = 'alert';
    errorAlert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to the top of the main content
    const mainContent = document.querySelector('.container');
    mainContent.insertBefore(errorAlert, mainContent.firstChild);
}