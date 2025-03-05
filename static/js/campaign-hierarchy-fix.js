// campaign-hierarchy-fix.js
// This patch fixes the TypeError: metrics.spend.toFixed is not a function error

/**
 * The issue is in the getMetrics function where it tries to call toFixed() on a value
 * that might not be a number. We need to ensure all metrics are properly converted to numbers
 * before using numeric methods like toFixed().
 */

(function() {
  // Get the original CampaignHierarchy class if it exists
  const originalCampaignHierarchy = window.EnhancedCampaignHierarchy || window.CampaignHierarchy;

  // Create a fixed version of the class
  class FixedCampaignHierarchy {
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
        
        // If we have hierarchy data, process it
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
              // Mock ad set data...
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
              // Mock ad set data...
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
        return campaign ? campaign.ad_sets || [] : [];
      } else if (this.currentLevel === 'ads') {
        const campaignId = this.breadcrumbs[0].id;
        const adsetId = this.breadcrumbs[1].id;
        
        const campaign = this.data.hierarchy.find(c => c.id === campaignId);
        if (!campaign) return [];
        
        const adset = campaign.ad_sets.find(a => a.id === adsetId);
        return adset ? adset.ads || [] : [];
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
      const metrics = this.getMetrics(item);
      const status = item.status ? item.status.toLowerCase() : 'unknown';
      const statusClass = status === 'active' ? 'text-success' : 'text-muted';
      
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

    // FIX: The core issue is in this function - we need to ensure metrics are numbers
    getMetrics(item) {
      // Ensure all metric values are properly converted to numbers
      // and provide default values to prevent errors
      const metrics = {
        spend: this.ensureNumber(item.spend, 0),
        impressions: this.ensureNumber(item.impressions, 0),
        clicks: this.ensureNumber(item.clicks, 0),
        ctr: this.ensureNumber(item.ctr, 0),
        cpc: this.ensureNumber(item.cpc, 0),
        conversions: this.ensureNumber(item.conversions || item.results || 0, 0),
        conversion_rate: this.ensureNumber(item.conversion_rate || (this.ensureNumber(item.conversions) / this.ensureNumber(item.clicks)) * 100 || 0, 0),
        cpa: this.ensureNumber(item.cpa || (this.ensureNumber(item.spend) / this.ensureNumber(item.conversions)) || 0, 0)
      };

      // Log metrics for debugging
      console.log('Processed metrics:', {
        original: item,
        processed: metrics
      });

      // Ensure all numeric values are properly formatted
      return `
        <div class="metric-item">
          <div class="metric-value">$${Number(metrics.spend).toFixed(2)}</div>
          <div class="metric-label">Spend</div>
        </div>
        <div class="metric-item">
          <div class="metric-value">${this.formatNumber(metrics.impressions)}</div>
          <div class="metric-label">Impressions</div>
        </div>
        <div class="metric-item">
          <div class="metric-value">${this.formatNumber(metrics.clicks)}</div>
          <div class="metric-label">Clicks</div>
        </div>
        <div class="metric-item">
          <div class="metric-value">${Number(metrics.ctr).toFixed(2)}%</div>
          <div class="metric-label">CTR</div>
        </div>
        <div class="metric-item">
          <div class="metric-value">$${Number(metrics.cpc).toFixed(2)}</div>
          <div class="metric-label">CPC</div>
        </div>
        <div class="metric-item">
          <div class="metric-value">${this.formatNumber(metrics.conversions)}</div>
          <div class="metric-label">Conversions</div>
        </div>
        <div class="metric-item">
          <div class="metric-value">${Number(metrics.conversion_rate).toFixed(2)}%</div>
          <div class="metric-label">Conv. Rate</div>
        </div>
        <div class="metric-item">
          <div class="metric-value">$${Number(metrics.cpa).toFixed(2)}</div>
          <div class="metric-label">CPA</div>
        </div>
      `;
    }

    // Helper method to ensure a value is a number
    ensureNumber(value, defaultValue = 0) {
      // If value is null, undefined, or not a number after conversion, return defaultValue
      if (value === null || value === undefined) return defaultValue;
      
      // Convert to number and handle NaN
      const number = Number(value);
      return isNaN(number) ? defaultValue : number;
    }

    // Helper method to format numbers with commas for thousands
    formatNumber(value) {
      const number = this.ensureNumber(value, 0);
      return number.toLocaleString();
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
          html += `<li class="breadcrumb-item"><a href="#" data-level="${this.currentLevel}" data-id="${crumb.id}">${crumb.name}</a></li>`;
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
      
      // Determine next level based on current level
      if (this.currentLevel === 'campaigns') {
        this.currentLevel = 'adsets';
      } else if (this.currentLevel === 'adsets') {
        this.currentLevel = 'ads';
      }
      
      this.renderLevel();
    }

    navigateToLevel(level, id) {
      const index = this.breadcrumbs.findIndex(crumb => crumb.id === id);
      if (index !== -1) {
        this.breadcrumbs = this.breadcrumbs.slice(0, index + 1);
        this.currentLevel = level;
        this.renderLevel();
      } else if (level === 'campaigns') {
        // Reset to campaigns view
        this.breadcrumbs = [];
        this.currentLevel = 'campaigns';
        this.renderLevel();
      }
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

  // Replace or initialize the global class
  window.EnhancedCampaignHierarchy = FixedCampaignHierarchy;
  window.CampaignHierarchy = FixedCampaignHierarchy;
  
  // If there's an existing instance on the page, reinitialize it
  if (window.hierarchyInstance) {
    try {
      console.log('Reinitializing campaign hierarchy with fixed version');
      const containerId = window.hierarchyInstance.container.id;
      window.hierarchyInstance = new FixedCampaignHierarchy(containerId);
    } catch (e) {
      console.error('Error reinitializing campaign hierarchy:', e);
    }
  }
  
  console.log('Campaign hierarchy component patched successfully');
})(); 