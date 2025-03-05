class CampaignHierarchy {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentLevel = 'campaigns';
        this.breadcrumbs = [];
        this.data = null;
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
            const fbCredentials = JSON.parse(sessionStorage.getItem('fb_credentials') || '{}');
            
            if (!fbCredentials.access_token || !fbCredentials.account_id) {
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
                    // Rate limit error
                    const retryAfter = data.retry_after || 300; // Default to 5 minutes
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
            
            // Store the data
            this.data = data.hierarchy;
            
            // Reset view to campaigns
            this.currentLevel = 'campaigns';
            this.breadcrumbs = [];
            
            // Render the view
            this.renderLevel();
            
        } catch (error) {
            console.error('Error loading hierarchy data:', error);
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
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

    getCurrentLevelData() {
        if (this.currentLevel === 'campaigns') {
            return this.data.campaigns;
        } else if (this.currentLevel === 'adsets') {
            const campaignId = this.breadcrumbs[0].id;
            console.log('Filtering ad sets for campaign:', {
                campaignId: campaignId,
                totalAdSets: this.data.ad_sets ? this.data.ad_sets.length : 0,
                breadcrumbs: this.breadcrumbs
            });
            
            const filteredAdSets = this.data.ad_sets.filter(adset => {
                console.log('Comparing ad set:', {
                    adsetId: adset.id,
                    adsetCampaignId: adset.campaign_id,
                    matches: adset.campaign_id === campaignId
                });
                return adset.campaign_id === campaignId;
            });
            
            console.log('Filtered ad sets result:', {
                campaignId: campaignId,
                filteredCount: filteredAdSets.length,
                filteredAdSets: filteredAdSets
            });
            
            return filteredAdSets;
        } else if (this.currentLevel === 'ads') {
            const adsetId = this.breadcrumbs[1].id;
            // Filter ads by checking if their parent_id matches the adset_id
            return this.data.ads.filter(ad => {
                console.log('Comparing ad:', {
                    adId: ad.id,
                    adsetId: adsetId,
                    adParentId: ad.adset?.id || ad.parent_id,
                    matches: ad.adset?.id === adsetId || ad.parent_id === adsetId
                });
                return ad.adset?.id === adsetId || ad.parent_id === adsetId;
            });
        }
        return [];
    }

    createItemCard(item) {
        const metrics = this.getMetrics(item);
        const status = item.status.toLowerCase();
        const statusClass = status === 'active' ? 'text-success' : 'text-muted';
        
        return `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100" data-item-id="${item.id}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h5 class="card-title mb-0">${item.name}</h5>
                            <span class="badge ${statusClass}">${status}</span>
                        </div>
                        <div class="metrics-grid">
                            ${metrics}
                        </div>
                    </div>
                    <div class="card-footer bg-transparent">
                        <button class="btn btn-primary btn-sm view-details" data-id="${item.id}" data-name="${item.name}">
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
            <div class="metric">
                <div class="metric-value">$${metrics.spend.toFixed(2)}</div>
                <div class="metric-label">Spend</div>
            </div>
            <div class="metric">
                <div class="metric-value">${metrics.impressions.toLocaleString()}</div>
                <div class="metric-label">Impressions</div>
            </div>
            <div class="metric">
                <div class="metric-value">${metrics.clicks.toLocaleString()}</div>
                <div class="metric-label">Clicks</div>
            </div>
            <div class="metric">
                <div class="metric-value">${metrics.ctr.toFixed(2)}%</div>
                <div class="metric-label">CTR</div>
            </div>
            <div class="metric">
                <div class="metric-value">$${metrics.cpc.toFixed(2)}</div>
                <div class="metric-label">CPC</div>
            </div>
            <div class="metric">
                <div class="metric-value">${metrics.conversions}</div>
                <div class="metric-label">Conversions</div>
            </div>
            <div class="metric">
                <div class="metric-value">${metrics.conversion_rate.toFixed(2)}%</div>
                <div class="metric-label">Conv. Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">$${metrics.cpa.toFixed(2)}</div>
                <div class="metric-label">CPA</div>
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
        
        if (this.breadcrumbs.length > 0) {
            const campaign = this.breadcrumbs[0];
            if (this.currentLevel === 'campaigns') {
                html += `<li class="breadcrumb-item active">${campaign.name}</li>`;
            } else {
                html += `<li class="breadcrumb-item"><a href="#" data-level="adsets" data-id="${campaign.id}">${campaign.name}</a></li>`;
            }
        }
        
        if (this.breadcrumbs.length > 1) {
            const adset = this.breadcrumbs[1];
            if (this.currentLevel === 'adsets') {
                html += `<li class="breadcrumb-item active">${adset.name}</li>`;
            } else {
                html += `<li class="breadcrumb-item"><a href="#" data-level="ads" data-id="${adset.id}">${adset.name}</a></li>`;
            }
        }
        
        if (this.breadcrumbs.length > 2) {
            const ad = this.breadcrumbs[2];
            html += `<li class="breadcrumb-item active">${ad.name}</li>`;
        }
        
        return html;
    }

    attachEventListeners() {
        // Handle item clicks for drill-down
        const viewButtons = this.container.querySelectorAll('.view-details');
        viewButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const id = e.target.dataset.id;
                const name = e.target.dataset.name;
                this.drillDown(id, name);
            });
        });

        // Handle breadcrumb navigation
        const breadcrumbLinks = this.container.querySelectorAll('#hierarchyBreadcrumb a');
        breadcrumbLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const level = e.target.dataset.level;
                const id = e.target.dataset.id;
                this.navigateToLevel(level, id);
            });
        });
    }

    drillDown(id, name) {
        console.log('Drilling down:', {
            fromLevel: this.currentLevel,
            itemId: id,
            itemName: name,
            currentBreadcrumbs: [...this.breadcrumbs],
            data: this.data
        });
        
        const currentItem = { id, name };
        
        if (this.currentLevel === 'campaigns') {
            this.breadcrumbs = [currentItem];
            this.currentLevel = 'adsets';
        } else if (this.currentLevel === 'adsets') {
            this.breadcrumbs = [...this.breadcrumbs.slice(0, 1), currentItem];
            this.currentLevel = 'ads';
        }
        
        console.log('After drill down:', {
            newLevel: this.currentLevel,
            newBreadcrumbs: [...this.breadcrumbs],
            filteredData: this.getCurrentLevelData()
        });
        
        this.renderLevel();
    }

    navigateToLevel(level, id) {
        if (level === 'campaigns') {
            this.breadcrumbs = [];
            this.currentLevel = 'campaigns';
        } else if (level === 'adsets') {
            this.breadcrumbs = [this.breadcrumbs[0]];
            this.currentLevel = 'adsets';
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

    showLoading(message = 'Loading...') {
        const container = document.getElementById('hierarchy-container');
        if (container) {
            container.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">${message}</p>
                </div>
            `;
        }
    }

    hideLoading() {
        // Loading will be hidden when content is rendered
    }

    showRateLimitError(retryAfter) {
        const minutes = Math.ceil(retryAfter / 60);
        const container = document.getElementById('hierarchy-container');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <h4 class="alert-heading">Rate Limit Reached</h4>
                    <p>We've hit Facebook's API rate limit. This happens when there are too many requests in a short time.</p>
                    <hr>
                    <p class="mb-0">Please wait approximately ${minutes} minutes before trying again.</p>
                    <button class="btn btn-primary mt-3" onclick="retryLoad(${retryAfter})">
                        Retry in ${minutes} minutes
                    </button>
                </div>
            `;
        }
    }

    retryLoad(retryAfter) {
        const button = document.querySelector('#hierarchy-container button');
        if (button) {
            button.disabled = true;
            let timeLeft = retryAfter;
            
            const countdown = setInterval(() => {
                timeLeft -= 1;
                const minutesLeft = Math.ceil(timeLeft / 60);
                button.textContent = `Retry in ${minutesLeft} minutes`;
                
                if (timeLeft <= 0) {
                    clearInterval(countdown);
                    button.textContent = 'Retrying...';
                    this.loadData();
                }
            }, 1000);
        }
    }
} 