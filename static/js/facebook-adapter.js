// facebook-adapter.js
// Handles Facebook API responses and converts them to the format expected by the dashboard

class FacebookAdapter {
    /**
     * Process Facebook data from the campaign hierarchy API
     * @param {Object} data - Raw data from the campaign hierarchy API
     * @returns {Object} - Processed data in the format expected by the dashboard
     */
    static processFacebookData(data) {
        console.log("Processing Facebook data:", data);
        
        if (!data || !data.hierarchy || !Array.isArray(data.hierarchy)) {
            console.error("Invalid data structure from Facebook API:", data);
            return {
                success: false,
                error: "Invalid data structure received from Facebook API"
            };
        }
        
        try {
            // Extract campaigns
            const campaigns = data.hierarchy.map(campaign => this._processCampaign(campaign));
            
            // Extract ad sets and flatten them
            const adSets = data.hierarchy.flatMap(campaign => 
                (campaign.ad_sets || []).map(adSet => this._processAdSet(adSet, campaign))
            );
            
            // Extract ads and flatten them
            const ads = data.hierarchy.flatMap(campaign => 
                (campaign.ad_sets || []).flatMap(adSet => 
                    (adSet.ads || []).map(ad => this._processAd(ad, adSet, campaign))
                )
            );
            
            // Extract insights from each level
            const insights = this._extractInsights(data.hierarchy);
            
            // Calculate account totals
            const accountOverview = this._calculateAccountOverview(campaigns);
            
            return {
                success: true,
                results: {
                    campaigns,
                    ad_sets: adSets,
                    ads,
                    insights,
                    account_overview: accountOverview,
                    platform: 'facebook',
                    timestamp: new Date().toISOString(),
                    // Add recommendations based on the data
                    recommendations: this._generateRecommendations(campaigns, adSets, ads)
                }
            };
        } catch (error) {
            console.error("Error processing Facebook data:", error);
            return {
                success: false,
                error: `Error processing Facebook data: ${error.message}`
            };
        }
    }
    
    /**
     * Process a single campaign
     * @param {Object} campaign - Raw campaign data
     * @returns {Object} - Processed campaign
     */
    static _processCampaign(campaign) {
        if (!campaign) return {};
        
        // Ensure all required fields exist
        return {
            id: campaign.id || '',
            name: campaign.name || 'Unnamed Campaign',
            status: campaign.status || 'UNKNOWN',
            objective: campaign.objective || 'UNKNOWN',
            spend: parseFloat(campaign.spend || 0),
            impressions: parseInt(campaign.impressions || 0, 10),
            clicks: parseInt(campaign.clicks || 0, 10),
            ctr: parseFloat(campaign.ctr || 0),
            cpc: parseFloat(campaign.cpc || 0),
            conversions: parseInt(campaign.conversions || 0, 10),
            conversion_rate: this._calculateConversionRate(campaign.clicks, campaign.conversions),
            cpa: this._calculateCPA(campaign.spend, campaign.conversions)
        };
    }
    
    /**
     * Process a single ad set
     * @param {Object} adSet - Raw ad set data
     * @param {Object} parentCampaign - Parent campaign data
     * @returns {Object} - Processed ad set
     */
    static _processAdSet(adSet, parentCampaign) {
        if (!adSet) return {};
        
        return {
            id: adSet.id || '',
            name: adSet.name || 'Unnamed Ad Set',
            campaign_id: adSet.campaign_id || parentCampaign?.id || '',
            campaign_name: parentCampaign?.name || 'Unknown Campaign',
            status: adSet.status || 'UNKNOWN',
            spend: parseFloat(adSet.spend || 0),
            impressions: parseInt(adSet.impressions || 0, 10),
            clicks: parseInt(adSet.clicks || 0, 10),
            ctr: parseFloat(adSet.ctr || 0),
            cpc: parseFloat(adSet.cpc || 0),
            conversions: parseInt(adSet.conversions || 0, 10),
            conversion_rate: this._calculateConversionRate(adSet.clicks, adSet.conversions),
            cpa: this._calculateCPA(adSet.spend, adSet.conversions)
        };
    }
    
    /**
     * Process a single ad
     * @param {Object} ad - Raw ad data
     * @param {Object} parentAdSet - Parent ad set data
     * @param {Object} parentCampaign - Parent campaign data
     * @returns {Object} - Processed ad
     */
    static _processAd(ad, parentAdSet, parentCampaign) {
        if (!ad) return {};
        
        return {
            id: ad.id || '',
            name: ad.name || 'Unnamed Ad',
            campaign_id: ad.campaign_id || parentCampaign?.id || '',
            campaign_name: parentCampaign?.name || 'Unknown Campaign',
            adset_id: ad.adset_id || parentAdSet?.id || '',
            adset_name: parentAdSet?.name || 'Unknown Ad Set',
            status: ad.status || 'UNKNOWN',
            spend: parseFloat(ad.spend || 0),
            impressions: parseInt(ad.impressions || 0, 10),
            clicks: parseInt(ad.clicks || 0, 10),
            ctr: parseFloat(ad.ctr || 0),
            cpc: parseFloat(ad.cpc || 0),
            conversions: parseInt(ad.conversions || 0, 10),
            conversion_rate: this._calculateConversionRate(ad.clicks, ad.conversions),
            cpa: this._calculateCPA(ad.spend, ad.conversions)
        };
    }
    
    /**
     * Extract insights from the hierarchy
     * @param {Array} hierarchy - Array of campaigns
     * @returns {Array} - Processed insights
     */
    static _extractInsights(hierarchy) {
        const insights = [];
        
        // Process campaign-level insights
        hierarchy.forEach(campaign => {
            insights.push({
                campaign_id: campaign.id,
                campaign_name: campaign.name,
                spend: parseFloat(campaign.spend || 0),
                impressions: parseInt(campaign.impressions || 0, 10),
                clicks: parseInt(campaign.clicks || 0, 10),
                ctr: parseFloat(campaign.ctr || 0),
                cpc: parseFloat(campaign.cpc || 0),
                conversions: parseInt(campaign.conversions || 0, 10),
                level: 'campaign'
            });
            
            // Process ad set-level insights
            (campaign.ad_sets || []).forEach(adSet => {
                insights.push({
                    campaign_id: campaign.id,
                    campaign_name: campaign.name,
                    adset_id: adSet.id,
                    adset_name: adSet.name,
                    spend: parseFloat(adSet.spend || 0),
                    impressions: parseInt(adSet.impressions || 0, 10),
                    clicks: parseInt(adSet.clicks || 0, 10),
                    ctr: parseFloat(adSet.ctr || 0),
                    cpc: parseFloat(adSet.cpc || 0),
                    conversions: parseInt(adSet.conversions || 0, 10),
                    level: 'adset'
                });
                
                // Process ad-level insights
                (adSet.ads || []).forEach(ad => {
                    insights.push({
                        campaign_id: campaign.id,
                        campaign_name: campaign.name,
                        adset_id: adSet.id,
                        adset_name: adSet.name,
                        ad_id: ad.id,
                        ad_name: ad.name,
                        spend: parseFloat(ad.spend || 0),
                        impressions: parseInt(ad.impressions || 0, 10),
                        clicks: parseInt(ad.clicks || 0, 10),
                        ctr: parseFloat(ad.ctr || 0),
                        cpc: parseFloat(ad.cpc || 0),
                        conversions: parseInt(ad.conversions || 0, 10),
                        level: 'ad'
                    });
                });
            });
        });
        
        return insights;
    }
    
    /**
     * Calculate account overview metrics
     * @param {Array} campaigns - Processed campaign data
     * @returns {Object} - Account overview metrics
     */
    static _calculateAccountOverview(campaigns) {
        let totalSpend = 0;
        let totalImpressions = 0;
        let totalClicks = 0;
        let totalConversions = 0;
        let totalActiveCampaigns = 0;
        
        campaigns.forEach(campaign => {
            totalSpend += campaign.spend || 0;
            totalImpressions += campaign.impressions || 0;
            totalClicks += campaign.clicks || 0;
            totalConversions += campaign.conversions || 0;
            
            if (campaign.status && campaign.status.toLowerCase() === 'active') {
                totalActiveCampaigns++;
            }
        });
        
        // Calculate derived metrics
        const ctr = totalImpressions > 0 ? (totalClicks / totalImpressions) * 100 : 0;
        const cpc = totalClicks > 0 ? totalSpend / totalClicks : 0;
        const cpm = totalImpressions > 0 ? (totalSpend / totalImpressions) * 1000 : 0;
        const conversionRate = totalClicks > 0 ? (totalConversions / totalClicks) * 100 : 0;
        const cpa = totalConversions > 0 ? totalSpend / totalConversions : 0;
        
        return {
            total_spend: totalSpend,
            total_impressions: totalImpressions,
            total_clicks: totalClicks,
            total_conversions: totalConversions,
            active_campaigns: totalActiveCampaigns,
            ctr: ctr,
            cpc: cpc,
            cpm: cpm,
            conversion_rate: conversionRate,
            cpa: cpa,
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * Calculate conversion rate
     * @param {number} clicks - Number of clicks
     * @param {number} conversions - Number of conversions
     * @returns {number} - Calculated conversion rate
     */
    static _calculateConversionRate(clicks, conversions) {
        clicks = parseInt(clicks || 0, 10);
        conversions = parseInt(conversions || 0, 10);
        return clicks > 0 ? (conversions / clicks) * 100 : 0;
    }
    
    /**
     * Calculate cost per acquisition
     * @param {number} spend - Total spend
     * @param {number} conversions - Number of conversions
     * @returns {number} - Calculated CPA
     */
    static _calculateCPA(spend, conversions) {
        spend = parseFloat(spend || 0);
        conversions = parseInt(conversions || 0, 10);
        return conversions > 0 ? spend / conversions : 0;
    }
    
    /**
     * Generate recommendations based on campaign data
     * @param {Array} campaigns - Processed campaign data
     * @param {Array} adSets - Processed ad set data
     * @param {Array} ads - Processed ad data
     * @returns {Array} - Array of recommendations
     */
    static _generateRecommendations(campaigns, adSets, ads) {
        const recommendations = [];
        
        // Check for underperforming campaigns
        campaigns.forEach(campaign => {
            if (campaign.status.toLowerCase() === 'active') {
                if (campaign.cpa > 0 && campaign.spend > 100) {
                    if (campaign.conversion_rate < 1) {
                        recommendations.push({
                            type: 'campaign_optimization',
                            severity: 'high',
                            category: 'Performance',
                            target_id: campaign.id,
                            target_name: campaign.name,
                            message: `Campaign "${campaign.name}" has a low conversion rate (${campaign.conversion_rate.toFixed(2)}%) with significant spend ($${campaign.spend.toFixed(2)}). Consider reviewing targeting and creative.`,
                            action_items: [
                                'Review campaign targeting settings',
                                'Analyze ad creative performance',
                                'Consider pausing or adjusting budget'
                            ]
                        });
                    }
                }
            }
        });
        
        // Check for ad set level optimizations
        adSets.forEach(adSet => {
            if (adSet.status.toLowerCase() === 'active') {
                if (adSet.ctr < 0.5 && adSet.spend > 50) {
                    recommendations.push({
                        type: 'adset_optimization',
                        severity: 'medium',
                        category: 'Engagement',
                        target_id: adSet.id,
                        target_name: adSet.name,
                        message: `Ad Set "${adSet.name}" has a low CTR (${adSet.ctr.toFixed(2)}%) with moderate spend ($${adSet.spend.toFixed(2)}). Consider audience refinement.`,
                        action_items: [
                            'Review audience targeting',
                            'Analyze creative relevance',
                            'Test different ad placements'
                        ]
                    });
                }
            }
        });
        
        // Check for ad level improvements
        ads.forEach(ad => {
            if (ad.status.toLowerCase() === 'active') {
                if (ad.cpc > 2 && ad.spend > 20) {
                    recommendations.push({
                        type: 'ad_optimization',
                        severity: 'low',
                        category: 'Cost',
                        target_id: ad.id,
                        target_name: ad.name,
                        message: `Ad "${ad.name}" has a high CPC ($${ad.cpc.toFixed(2)}) with moderate spend ($${ad.spend.toFixed(2)}). Consider creative optimization.`,
                        action_items: [
                            'Review ad creative',
                            'Test new variations',
                            'Analyze audience engagement'
                        ]
                    });
                }
            }
        });
        
        return recommendations;
    }
}

// Export the FacebookAdapter class for use in other modules
window.FacebookAdapter = FacebookAdapter; 