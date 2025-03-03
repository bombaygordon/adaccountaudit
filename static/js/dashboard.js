// Check if data has the enhanced structure and extract the correct data
function extractAnalysisData(data) {
    // Check if this is the enhanced structure
    if (data.analysis_results) {
        return data.analysis_results;
    } else if (data.results && data.results.analysis_results) {
        return data.results.analysis_results;
    } else {
        // Fall back to the original structure
        return data.results || data;
    }
}

// Updated fetchAuditData function
async function fetchAuditData() {
    try {
        // Check if we have stored audit results from a real audit
        const storedAudit = sessionStorage.getItem('latest_audit');
        if (storedAudit) {
            const rawData = JSON.parse(storedAudit);
            const data = extractAnalysisData(rawData);
            updateDashboard(data);
            return;
        }
        
        // Otherwise fetch from the test endpoint
        const response = await fetch('/api/test-audit');
        const rawData = await response.json();
        
        // Extract analysis data
        const data = extractAnalysisData(rawData);
        
        // Update dashboard with the data
        updateDashboard(data);
    } catch (error) {
        console.error('Error fetching audit data:', error);
        showError('Failed to load audit data. Please try again later.');
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
    // Update summary metrics
    updateSummaryMetrics(data);
    
    // Update recommendations
    updateRecommendations(data.recommendations || []);
    
    // Initialize charts
    initCharts(data);
}

// Updated updateSummaryMetrics function
function updateSummaryMetrics(data) {
    // Update potential savings
    document.getElementById('potentialSavings').textContent = formatCurrency(data.potential_savings);
    
    // Update potential improvement
    document.getElementById('potentialImprovement').textContent = formatPercentage(data.potential_improvement_percentage);
    
    // Update recommendation count
    document.getElementById('recommendationCount').textContent = data.recommendations ? data.recommendations.length : 0;
    
    // Update platforms audited
    const platformsAudited = document.getElementById('platformsAudited');
    platformsAudited.textContent = data.platform ? capitalizeFirstLetter(data.platform) : 'Facebook (Mock Data)';
    
    // Update last audited time
    const lastAudited = new Date(data.timestamp);
    document.getElementById('lastAudited').textContent = formatDate(lastAudited);
    
    // Update gauge value
    document.getElementById('gaugeValue').textContent = formatPercentage(data.potential_improvement_percentage);
}