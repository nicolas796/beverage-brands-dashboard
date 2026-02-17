import React, { useState, useEffect } from 'react';
import { Trophy, TrendingUp, TrendingDown, Calendar } from 'lucide-react';
import { api } from '../utils/api';

function Rankings() {
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState('7d');
  const [platform, setPlatform] = useState('instagram');
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    loadRankings();
    loadCategories();
  }, [period, platform, selectedCategory]);

  const loadRankings = async () => {
    try {
      setLoading(true);
      const params = { period, platform };
      if (selectedCategory) {
        // Get all and filter by category client-side for now
        const data = await api.getRankings({ ...params, limit: 200 });
        const filtered = data.rankings.filter(r => r.brand.category === selectedCategory);
        setRankings(filtered);
      } else {
        const data = await api.getRankings({ ...params, limit: 100 });
        setRankings(data.rankings);
      }
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

  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
  };

  const getRankColor = (index) => {
    if (index === 0) return '#FFD700'; // Gold
    if (index === 1) return '#C0C0C0'; // Silver
    if (index === 2) return '#CD7F32'; // Bronze
    return 'var(--text-secondary)';
  };

  if (loading) return <div className="loading">Loading rankings...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div>
      <div className="page-header">
        <h1><Trophy size={32} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} /> Rankings</h1>
        <p>Top growing beverage brands by follower growth</p>
      </div>

      {/* Filters */}
      <div className="filters">
        <div className="filter-group">
          <Calendar size={16} />
          <select 
            className="form-control" 
            value={period} 
            onChange={(e) => setPeriod(e.target.value)}
            style={{ width: '120px' }}
          >
            <option value="7d">7 Days</option>
            <option value="30d">30 Days</option>
            <option value="90d">90 Days</option>
          </select>
        </div>

        <div className="filter-group">
          <select 
            className="form-control" 
            value={platform} 
            onChange={(e) => setPlatform(e.target.value)}
            style={{ width: '120px' }}
          >
            <option value="instagram">Instagram</option>
            <option value="tiktok">TikTok</option>
          </select>
        </div>

        <div className="filter-group">
          <select 
            className="form-control" 
            value={selectedCategory} 
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{ width: '180px' }}
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Rankings Table */}
      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: '60px' }}>Rank</th>
                <th>Brand</th>
                <th>Category</th>
                <th>Location</th>
                <th style={{ textAlign: 'right' }}>Current Followers</th>
                <th style={{ textAlign: 'right' }}>Growth ({period})</th>
                <th style={{ textAlign: 'right' }}>Growth %</th>
              </tr>
            </thead>
            <tbody>
              {rankings.map((item, index) => (
                <tr key={item.brand.id}>
                  <td>
                    <span style={{ 
                      fontWeight: 'bold', 
                      fontSize: index < 3 ? '1.25rem' : '1rem',
                      color: getRankColor(index)
                    }}>
                      #{index + 1}
                    </span>
                  </td>
                  <td>
                    <a href={`/brands/${item.brand.id}`} style={{ fontWeight: 600 }}>
                      {item.brand.name}
                    </a>
                  </td>
                  <td>
                    <span className="badge badge-primary">{item.brand.category}</span>
                  </td>
                  <td>{item.brand.hq_state}, {item.brand.country}</td>
                  <td style={{ textAlign: 'right', fontWeight: 500 }}>
                    {formatNumber(item.growth?.current_followers)}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    {item.growth?.growth_absolute >= 0 ? '+' : ''}
                    {formatNumber(item.growth?.growth_absolute)}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={item.growth?.growth_percentage >= 0 ? 'positive' : 'negative'}>
                      {item.growth?.growth_percentage >= 0 ? (
                        <TrendingUp size={14} style={{ display: 'inline', marginRight: '4px' }} />
                      ) : (
                        <TrendingDown size={14} style={{ display: 'inline', marginRight: '4px' }} />
                      )}
                      {item.growth?.growth_percentage?.toFixed(2)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {rankings.length === 0 && (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
            No rankings available for the selected criteria.
          </div>
        )}
      </div>

      {/* Summary Stats */}
      {rankings.length > 0 && (
        <div className="grid grid-4" style={{ marginTop: '2rem' }}>
          <div className="stat-card">
            <div className="stat-label">Total Brands</div>
            <div className="stat-value">{rankings.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Avg Growth</div>
            <div className="stat-value">
              {(rankings.reduce((sum, r) => sum + (r.growth?.growth_percentage || 0), 0) / rankings.length).toFixed(2)}%
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Top Growth</div>
            <div className="stat-value positive">
              {rankings[0]?.growth?.growth_percentage?.toFixed(2)}%
            </div>
            <div className="stat-change">{rankings[0]?.brand?.name}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total Reach</div>
            <div className="stat-value">
              {formatNumber(rankings.reduce((sum, r) => sum + (r.growth?.current_followers || 0), 0))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Rankings;
