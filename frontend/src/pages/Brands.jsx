import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, ExternalLink, Plus, Loader2, Globe } from 'lucide-react';
import { api } from '../utils/api';

function Brands() {
  const [brands, setBrands] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  
  // New state for website research
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [researchLoading, setResearchLoading] = useState(false);
  const [researchMessage, setResearchMessage] = useState(null);

  useEffect(() => {
    loadBrands();
    loadCategories();
  }, []);

  const loadBrands = async () => {
    try {
      setLoading(true);
      const params = {};
      if (searchQuery) params.search = searchQuery;
      if (selectedCategory) params.category = selectedCategory;
      
      const data = await api.getBrands(params);
      setBrands(data.brands);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await api.getCategories();
      setCategories(data.categories);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadBrands();
  };

  const handleExport = async () => {
    try {
      const response = await api.exportBrands('csv');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'brands.csv';
      a.click();
    } catch (err) {
      alert('Export failed: ' + err.message);
    }
  };

  // Handle website research
  const handleResearchWebsite = async (e) => {
    e.preventDefault();
    if (!websiteUrl.trim()) return;
    
    setResearchLoading(true);
    setResearchMessage(null);
    
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || ''}/api/brands/research/website`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ website_url: websiteUrl })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Research failed');
      }
      
      const result = await response.json();
      setResearchMessage({
        type: 'success',
        text: `✓ ${result.message}`
      });
      setWebsiteUrl('');
      
      // Reload brands to show the new one
      loadBrands();
    } catch (err) {
      setResearchMessage({
        type: 'error',
        text: `✗ ${err.message}`
      });
    } finally {
      setResearchLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  // Check if brand was added within last 7 days
  const isRecentlyAdded = (createdAt) => {
    if (!createdAt) return false;
    const created = new Date(createdAt);
    const now = new Date();
    const diffTime = Math.abs(now - created);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays <= 7;
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  if (loading && brands.length === 0) return <div className="loading">Loading brands...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Brands</h1>
        <p>Browse and search beverage brands</p>
      </div>

      {/* Website Research Input */}
      <div style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '1.5rem',
        borderRadius: '12px',
        marginBottom: '1.5rem',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
          <Globe size={20} color="white" />
          <span style={{ color: 'white', fontWeight: 600, fontSize: '1rem' }}>
            Add New Brand from Website
          </span>
        </div>
        <form onSubmit={handleResearchWebsite} style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            type="url"
            placeholder="https://example-brand.com"
            value={websiteUrl}
            onChange={(e) => setWebsiteUrl(e.target.value)}
            style={{ 
              flex: 1,
              padding: '0.75rem 1rem',
              border: 'none',
              borderRadius: '8px',
              fontSize: '0.95rem'
            }}
            required
          />
          <button 
            type="submit"
            disabled={researchLoading}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'white',
              color: '#667eea',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 600,
              cursor: researchLoading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              opacity: researchLoading ? 0.7 : 1
            }}
          >
            {researchLoading ? (
              <><Loader2 size={18} className="spin" /> Researching...</>
            ) : (
              <><Plus size={18} /> Research & Add</>
            )}
          </button>
        </form>
        {researchMessage && (
          <div style={{ 
            marginTop: '0.75rem',
            padding: '0.75rem 1rem',
            background: researchMessage.type === 'success' ? 'rgba(255,255,255,0.2)' : 'rgba(239, 68, 68, 0.2)',
            borderRadius: '8px',
            color: 'white',
            fontSize: '0.9rem'
          }}>
            {researchMessage.text}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="filters">
        <form onSubmit={handleSearch} className="search-container">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search brands..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </form>

        <div className="filter-group">
          <Filter size={16} />
          <select
            className="form-control"
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setTimeout(loadBrands, 0);
            }}
            style={{ width: '180px' }}
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={handleExport}>
          <Download size={14} /> Export CSV
        </button>
      </div>

      {/* Brand Grid */}
      <div className="grid grid-3">
        {brands.map(brand => (
          <div key={brand.id} className="brand-card">
            <div className="brand-card-header">
              <div style={{ flex: 1 }}>
                <div className="brand-card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <a href={`/brands/${brand.id}`}>{brand.name}</a>
                  {isRecentlyAdded(brand.created_at) && (
                    <span style={{
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      color: 'white',
                      fontSize: '0.65rem',
                      fontWeight: 700,
                      padding: '0.2rem 0.5rem',
                      borderRadius: '9999px',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em'
                    }}>
                      Recently Added
                    </span>
                  )}
                </div>
                <div className="brand-card-category">{brand.category}</div>
              </div>
              <span className="badge badge-primary">{brand.country}</span>
            </div>

            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              {brand.hq_city}, {brand.hq_state}
            </div>

            {brand.founders && (
              <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: 'var(--text-secondary)' }}>
                Founded by {brand.founders}
              </div>
            )}

            {/* Created Date */}
            {brand.created_at && (
              <div style={{ 
                fontSize: '0.7rem', 
                marginTop: '0.5rem', 
                color: 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem'
              }}>
                <span>Added {formatDate(brand.created_at)}</span>
              </div>
            )}

            <div className="brand-card-metrics">
              {brand.instagram_handle && (
                <div className="brand-card-metric">
                  <div className="brand-card-metric-label">Instagram</div>
                  <div className="brand-card-metric-value" style={{ fontSize: '0.875rem' }}>
                    @{brand.instagram_handle}
                  </div>
                </div>
              )}
              {brand.tiktok_handle && (
                <div className="brand-card-metric">
                  <div className="brand-card-metric-label">TikTok</div>
                  <div className="brand-card-metric-value" style={{ fontSize: '0.875rem' }}>
                    @{brand.tiktok_handle}
                  </div>
                </div>
              )}
            </div>

            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
              {brand.website && (
                <a 
                  href={brand.website} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-sm"
                  style={{ flex: 1, justifyContent: 'center' }}
                >
                  <ExternalLink size={12} /> Website
                </a>
              )}
              <a 
                href={`/brands/${brand.id}`}
                className="btn btn-primary btn-sm"
                style={{ flex: 1, justifyContent: 'center' }}
              >
                View Details
              </a>
            </div>
          </div>
        ))}
      </div>

      {brands.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
          No brands found matching your criteria.
        </div>
      )}

      {/* Add CSS for spinner animation */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
}

export default Brands;
