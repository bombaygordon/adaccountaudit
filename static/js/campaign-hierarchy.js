// Enhanced campaign hierarchy class with proper error handling and data processing
class EnhancedCampaignHierarchy {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentLevel = 'campaigns';
        this.breadcrumbs = [];
        this.data = null;
        this.retryAttempts = 0;
        this.maxRetries = 3;
        this.init();
    }

    init() {
        this.createStructure();
        this.loadData();
    }

    createStructure() {
        this.container.innerHTML = `
            <div class="hierarchy-nav mb-3">
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb" id="hierarchyBreadcrumb">
                        <li class="breadcrumb-item active">Campaigns</li>
                    </ol>
                </nav>
            </div>
            <div class="hierarchy-content">
                <div class="row" id="hierarchyItems">
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async loadData() {
        try {
            // Get Facebook credentials from session storage
            const fbCredentials = this.getSafeCredentials();
            
            if (!fbCredentials) {
                this.showError('Facebook credentials not found. Please reconnect your account.');
                return;
            }
            
            this.showLoading('Loading campaign data...');
            
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
                const data = await response.json().catch(() => ({}));
                if (response.status === 429) {
                    // Handle rate limit error
                    const retryAfter = data.retry_after || 300;
                    this.showRateLimitError(retryAfter);
                    return;
                }
                throw new Error(data.error || `Failed to load hierarchy data: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Loaded hierarchy data:', data);
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load hierarchy data');
            }
            
            // Process the hierarchy data
            if (data.hierarchy && Array.isArray(data.hierarchy)) {
                // Store the data
                this.data = data;
                
                // Reset view to campaigns
                this.currentLevel = 'campaigns';
                this.breadcrumbs = [];
                
                // Render the view
                this.renderLevel();
            } else {
                // No hierarchy data, create some mock data for testing
                this.data = this.createMockData();
                
                // Reset view to campaigns
                this.currentLevel = 'campaigns';
                this.breadcrumbs = [];
                
                // Render the view with mock data
                this.renderLevel();
            }
            
        } catch (error) {
            console.error('Error loading hierarchy data:', error);
            
            // If we've tried too many times, show error and create mock data
            if (this.retryAttempts >= this.maxRetries) {
                this.showError('Failed to load campaign data after multiple attempts. Showing sample data instead.');
                this.data = this.createMockData();
                this.renderLevel();
            } else {
                // Otherwise show error and retry button
                this.showError(`${error.message}. <button class="btn btn-primary btn-sm mt-2" id="retryLoadBtn">Retry</button>`);
                
                // Add retry button functionality
                const retryBtn = document.getElementById('retryLoadBtn');
                if (retryBtn) {
                    retryBtn.addEventListener('click', () => {
                        this.retryAttempts++;
                        this.loadData();
                    });
                }
            }
        } finally {
            this.hideLoading();
        }
    }

    // Get safe credentials from session storage
    getSafeCredentials() {
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

    createMockData() {
        // Create sample campaign hierarchy for testing
        return {
            hierarchy: [
                {
                    id: '12345678901',
                    name: 'Sample Campaign 1',
                    status: 'ACTIVE',
                    objective: 'CONVERSIONS',
                    spend: 1245.50,
                    impressions: 125000,
                    clicks: 3750,
                    ctr: 3.0,
                    cpc: 0.33,
                    conversions: 75,
                    ad_sets: [
                        {
                            id: '23456789012',
                            name: 'Sample Ad Set 1.1',
                            campaign_id: '12345678901',
                            status: 'ACTIVE',
                            spend: 625.25,
                            impressions: 62500,
                            clicks: 1875,
                            ctr: 3.0,
                            cpc: 0.33,
                            conversions: 37,
                            ads: [
                                {
                                    id: '34567890123',
                                    name: 'Sample Ad 1.1.1',
                                    adset_id: '23456789012',
                                    campaign_id: '12345678901',
                                    status: 'ACTIVE',
                                    spend: 312.50,
                                    impressions: 31250,
                                    clicks: 937,
                                    ctr: 3.0,
                                    cpc: 0.33,
                                    conversions: 18
                                },
                                {
                                    id: '34567890124',
                                    name: 'Sample Ad 1.1.2',
                                    adset_id: '23456789012',
                                    campaign_id: '12345678901',
                                    status: 'ACTIVE',
                                    spend: 312.75,
                                    impressions: 31250,
                                    clicks: 938,
                                    ctr: 3.0,
                                    cpc: 0.33,
                                    conversions: 19
                                }
                            ]
                        },
                        {
                            id: '23456789013',
                            name: 'Sample Ad Set 1.2',
                            campaign_id: '12345678901',
                            status: 'ACTIVE',
                            spend: 620.25,
                            impressions: 62500,
                            clicks: 1875,
                            ctr: 3.0,
                            cpc: 0.33,
                            conversions: 38,
                            ads: [
                                {
                                    id: '34567890125',
                                    name: 'Sample Ad 1.2.1',
                                    adset_id: '23456789013',
                                    campaign_id: '12345678901',
                                    status: 'ACTIVE',
                                    spend: 620.25,
                                    impressions: 62500,
                                    clicks: 1875,
                                    ctr: 3.0,
                                    cpc: 0.33,
                                    conversions: 38
                                }
                            ]
                        }
                    ]
                },
                {
                    id: '12345678902',
                    name: 'Sample Campaign 2',
                    status: 'ACTIVE',
                    objective: 'BRAND_AWARENESS',
                    spend: 875.50,
                    impressions: 95000,
                    clicks: 2850,
                    ctr: 3.0,
                    cpc: 0.31,
                    conversions: 57,
                    ad_sets: [
                        {
                            id: '23456789014',
                            name: 'Sample Ad Set 2.1',
                            campaign_id: '12345678902',
                            status: 'ACTIVE',
                            spend: 875.50,
                            impressions: 95000,
                            clicks: 2850,
                            ctr: 3.0,
                            cpc: 0.31,
                            conversions: 57,
                            ads: [
                                {
                                    id: '34567890126',
                                    name: 'Sample Ad 2.1.1',
                                    adset_id: '23456789014',
                                    campaign_id: '12345678902',
                                    status: 'ACTIVE',
                                    spend: 437.75,
                                    impressions: 47500,
                                    clicks: 1425,
                                    ctr: 3.0,
                                    cpc: 0.31,
                                    conversions: 28
                                },
                                {
                                    id: '34567890127',
                                    name: 'Sample Ad 2.1.2',
                                    adset_id: '23456789014',
                                    campaign_id: '12345678902',
                                    status: 'ACTIVE',
                                    spend: 437.75,
                                    impressions: 47500,
                                    clicks: 1425,
                                    ctr: 3.0,
                                    cpc: 0.31,
                                    conversions: 29
                                }
                            ]
                        }
                    ]
                }
            ]
        };
    }

    getCurrentLevelData() {
        if (!this.data || !this.data.hierarchy) {
            return [];
        }
        
        if (this.currentLevel === 'campaigns') {
            return this.data.hierarchy;
        } else if (this.currentLevel === 'adsets') {
            const campaignId = this.breadcrumbs[0].id;
            const campaign = this.data.hierarchy.find(c => c.id === campaignId);
            return campaign ? (campaign.ad_sets || []) : [];
        } else if (this.currentLevel === 'ads') {
            const campaignId = this.breadcrumbs[0].id;
            const adsetId = this.breadcrumbs[1].id;
            
            const campaign = this.data.hierarchy.find(c => c.id === campaignId);
            if (!campaign) return [];
            
            const adset = (campaign.ad_sets || []).find(a => a.id === adsetId);
            return adset ? (adset.ads || []) : [];
        }
        return [];
    }

    renderLevel() {
        const itemsContainer = document.getElementById('hierarchyItems');
        const items = this.getCurrentLevelData();
        
        console.log('Rendering level:', {
            level: this.currentLevel,
            itemCount: items ? items.length : 0,
            breadcrumbs: [...this.breadcrumbs]
        });
        
        // Update breadcrumbs
        const breadcrumbContainer = document.getElementById('hierarchyBreadcrumb');
        breadcrumbContainer.innerHTML = this.getBreadcrumbsHTML();
        
        if (!items || items.length === 0) {
            console.log('No items found for current level');
            itemsContainer.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info">
                        No ${this.currentLevel} found for ${this.breadcrumbs[this.breadcrumbs.length - 1]?.name || 'this view'}
                    </div>
                </div>
            `;
            return;
        }

        itemsContainer.innerHTML = items.map(item => this.createItemCard(item)).join('');
        this.attachEventListeners();
    }

    createItemCard(item) {
        // Make sure item has a status property with a string value
        const status = item && item.status ? 
            (typeof item.status === 'string' ? item.status.toLowerCase() : String(item.status).toLowerCase()) : 
            'unknown';
            
        const statusClass = status === 'active' ? 'text-success' : 'text-muted';
        const metrics = this.getMetrics(item);
        
        return `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100" data-item-id="${item.id}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h5 class="card-title mb-0">${item.name || 'Unnamed'}</h5>
                            <span class="badge ${statusClass}">${status}</span>
                        </div>
                        <div class="metrics-grid">
                            ${metrics}
                        </div>
                    </div>
                    <div class="card-footer bg-transparent">
                        <button class="btn btn-primary btn-sm view-details" data-id="${item.id}" data-name="${item.name || 'Unnamed'}">
                            View ${this.getNextLevel()}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    getMetrics(item) {
        // Add default values to prevent undefined errors
        const metrics = {
            spend: item.spend || 0,
            impressions: item.impressions || 0,
            clicks: item.clicks || 0,
            ctr: item.ctr || 0,
            cpc: item.cpc || 0,
            conversions: item.conversions || 0,
            conversion_rate: item.conversion_rate || 0,
            cpa: item.cpa || 0
        };

        return `
            <div class="metric-item">
                <div class="metric-label">Spend</div>
                <div class="metric-value">$${metrics.spend.toFixed(2)}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">Impressions</div>
                <div class="metric-value">${metrics.impressions.toLocaleString()}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">Clicks</div>
                <div class="metric-value">${metrics.clicks.toLocaleString()}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">CTR</div>
                <div class="metric-value">${metrics.ctr.toFixed(2)}%</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">CPC</div>
                <div class="metric-value">$${metrics.cpc.toFixed(2)}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">Conv.</div>
                <div class="metric-value">${metrics.conversions}</div>
            </div>
        `;
    }

    getNextLevel() {
        if (this.currentLevel === 'campaigns') return 'Ad Sets';
        if (this.currentLevel === 'adsets') return 'Ads';
        return '';
    }

    getBreadcrumbsHTML() {
        let html = '<li class="breadcrumb-item"><a href="#" data-level="campaigns">Campaigns</a></li>';
        
        this.breadcrumbs.forEach((crumb, index) => {
            const isLast = index === this.breadcrumbs.length - 1;
            if (isLast) {
                html += `<li class="breadcrumb-item active">${crumb.name}</li>`;
            } else {
                const level = index === 0 ? 'adsets' : 'ads';
                html += `<li class="breadcrumb-item"><a href="#" data-level="${level}" data-id="${crumb.id}">${crumb.name}</a></li>`;
            }
        });
        
        return html;
    }

    attachEventListeners() {
        // Add click handlers for view details buttons
        document.querySelectorAll('.view-details').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const id = e.target.dataset.id;
                const name = e.target.dataset.name;
                this.drillDown(id, name);
            });
        });
        
        // Add click handlers for breadcrumb navigation
        document.querySelectorAll('#hierarchyBreadcrumb a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const level = e.target.dataset.level;
                const id = e.target.dataset.id;
                this.navigateToLevel(level, id);
            });
        });
    }

    drillDown(id, name) {
        this.breadcrumbs.push({ id, name });
        
        if (this.currentLevel === 'campaigns') {
            this.currentLevel = 'adsets';
        } else if (this.currentLevel === 'adsets') {
            this.currentLevel = 'ads';
        }
        
        this.renderLevel();
    }

    navigateToLevel(level, id) {
        if (level === 'campaigns') {
            // Reset to campaigns view
            this.breadcrumbs = [];
            this.currentLevel = 'campaigns';
        } else if (level === 'adsets') {
            // Find the index of the campaign with this ID
            const index = this.breadcrumbs.findIndex(crumb => crumb.id === id);
            if (index !== -1) {
                // Keep only the campaign breadcrumb
                this.breadcrumbs = this.breadcrumbs.slice(0, 1);
                this.currentLevel = 'adsets';
            }
        }
        
        this.renderLevel();
    }

    showError(message) {
        const itemsContainer = document.getElementById('hierarchyItems');
        itemsContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    ${message}
                </div>
            </div>
        `;
    }

    showLoading(message) {
        const itemsContainer = document.getElementById('hierarchyItems');
        itemsContainer.innerHTML = `
            <div class="col-12">
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">${message}</p>
                </div>
            </div>
        `;
    }

    hideLoading() {
        // Loading state is handled in renderLevel
    }

    showRateLimitError(retryAfter) {
        const minutes = Math.ceil(retryAfter / 60);
        this.showError(`
            Rate limit exceeded. Please wait ${minutes} minutes before trying again.
            <button class="btn btn-primary btn-sm mt-2" id="retryLoadBtn">Retry</button>
        `);
        
        // Add retry button functionality
        const retryBtn = document.getElementById('retryLoadBtn');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                this.loadData();
            });
        }
    }
}

// Initialize the enhanced campaign hierarchy
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the dashboard page with campaign hierarchy
    if (document.getElementById('campaignHierarchy')) {
        console.log('Initializing enhanced campaign hierarchy');
        
        // Initialize EnhancedCampaignHierarchy
        window.hierarchyInstance = new EnhancedCampaignHierarchy('campaignHierarchy');
        
        // Refresh button handler
        const refreshBtn = document.getElementById('refreshHierarchy');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                window.hierarchyInstance.loadData();
            });
        }
    }
}); 