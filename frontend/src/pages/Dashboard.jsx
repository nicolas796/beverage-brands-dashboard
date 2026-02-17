import React, { useState, useEffect } from 'react';
import { TrendingUp, Users, BarChart3, RefreshCw, CreditCard } from 'lucide-react';
import { api } from '../utils/api';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Link } from 'react-router-dom';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [platform, setPlatform] = useState('instagram');

  useEffect(() => {
    loadDashboard();
  }, [platform]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await api.getDashboard(platform, 10);
      setDashboardData(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  const top7d = dashboardData?.top_growing_7d || [];
  const top30d = dashboardData?.top_growing_30d || [];
  const categories = dashboardData?.category_distribution || [];

  // Chart data for category distribution
  const categoryChartData = {
    labels: categories.map(c => c.category),
    datasets: [{
      label: 'Brands',
      data: categories.map(c => c.count),
      backgroundColor: 'rgba(79, 70, 229, 0.8)',
      borderColor: 'rgba(79, 70, 229, 1)',
      borderWidth: 1,
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      y: { beginAtZero: true }
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Overview of beverage brand social performance</p>
      </div>

      <div className="filters">
        <div className="filter-group">
          <label>Platform:</label>
          <select 
            className="form-control" 
            value={platform} 
            onChange={(e) => setPlatform(e.target.value)}
            style={{ width: '150px' }}
          >
            <option value="instagram">Instagram</option>
            <option value="tiktok">TikTok</option>
          </select>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadDashboard}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
        <div className="stat-card">
          <div className="stat-label">Total Brands</div>
          <div className="stat-value">{categories.reduce((sum, c) => sum + c.count, 0)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Categories</div>
          <div className="stat-value">{categories.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Top 7d Growth</div>
          <div className="stat-value positive">
            {top7d[0]?.growth?.growth_percentage?.toFixed(1)}%
          </div>
          <div className="stat-change positive">
            {top7d[0]?.brand?.name}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Platform</div>
          <div className="stat-value" style={{ fontSize: '1.25rem', textTransform: 'capitalize' }}>
            {platform}
          </div>
        </div>
      </div>

      <div className="grid grid-2">
        {/* Top Growing 7 Days */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <TrendingUp size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
              Top Growing (7 Days)
            </h3>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Brand</th>
                  <th>Category</th>
                  <th>Growth</th>
                </tr>
              </thead>
              <tbody>
                {top7d.slice(0, 10).map((item, idx) => (
                  <tr key={item.brand.id}>
                    <td>#{idx + 1}</td>
                    <td>
                      <a href={`/brands/${item.brand.id}`}>{item.brand.name}</a>
                    </td>
                    <td>{item.brand.category}</td>
                    <td className={item.growth?.growth_percentage >= 0 ? 'positive' : 'negative'}>
                      {item.growth?.growth_percentage?.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Growing 30 Days */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <BarChart3 size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
              Top Growing (30 Days)
            </h3>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Brand</th>
                  <th>Category</th>
                  <th>Growth</th>
                </tr>
              </thead>
              <tbody>
                {top30d.slice(0, 10).map((item, idx) => (
                  <tr key={item.brand.id}>
                    <td>#{idx + 1}</td>
                    <td>
                      <a href={`/brands/${item.brand.id}`}>{item.brand.name}</a>
                    </td>
                    <td>{item.brand.category}</td>
                    <td className={item.growth?.growth_percentage >= 0 ? 'positive' : 'negative'}>
                      {item.growth?.growth_percentage?.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Category Distribution */}
      <div className="card" style={{ marginTop: '2rem' }}>
        <div className="card-header">
          <h3 className="card-title">
            <Users size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
            Brands by Category
          </h3>
        </div>
        <div className="chart-container">
          {categories.length > 0 && (
            <Line 
              data={categoryChartData} 
              options={chartOptions}
            />
          )}
        </div>
      </div>

      {/* Billing Link */}
      <div className="card" style={{ marginTop: '2rem' }}>
        <div className="card-header">
          <h3 className="card-title">
            <CreditCard size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
            Billing
          </h3>
        </div>
        <div style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
            View your credit usage and invoicing details
          </p>
          <Link 
            to="/billing" 
            className="btn btn-primary"
            style={{ textDecoration: 'none' }}
          >
            View Billing
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
