import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Instagram, Video, Globe, MapPin, Users, Calendar, TrendingUp, Download } from 'lucide-react';
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
  Filler,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function BrandDetail() {
  const { id } = useParams();
  const [brand, setBrand] = useState(null);
  const [growthData, setGrowthData] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [platform, setPlatform] = useState('instagram');
  const [days, setDays] = useState(30);

  useEffect(() => {
    loadBrandData();
  }, [id, platform, days]);

  const loadBrandData = async () => {
    try {
      setLoading(true);
      
      const [brandData, growth, metricsData] = await Promise.all([
        api.getBrandFull(id),
        api.getBrandGrowth(id, platform, days),
        api.getBrandMetrics(id, { platform, days })
      ]);
      
      setBrand(brandData);
      setGrowthData(growth);
      setMetrics(metricsData.metrics);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await api.exportMetrics(id, 'csv');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${brand?.name}_metrics.csv`;
      a.click();
    } catch (err) {
      alert('Export failed: ' + err.message);
    }
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
  };

  if (loading) return <div className="loading">Loading brand details...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!brand) return <div className="error">Brand not found</div>;

  // Chart data
  const chartData = growthData?.data ? {
    labels: growthData.data.map(d => d.date),
    datasets: [{
      label: 'Followers',
      data: growthData.data.map(d => d.followers),
      borderColor: 'rgb(79, 70, 229)',
      backgroundColor: 'rgba(79, 70, 229, 0.1)',
      fill: true,
      tension: 0.4,
    }]
  } : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => `Followers: ${formatNumber(context.raw)}`
        }
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: (value) => formatNumber(value)
        }
      }
    }
  };

  const latestMetric = metrics[0];
  const previousMetric = metrics[metrics.length - 1];
  const followerGrowth = latestMetric?.followers && previousMetric?.followers
    ? ((latestMetric.followers - previousMetric.followers) / previousMetric.followers * 100).toFixed(2)
    : 0;

  return (
    <div>
      <Link to="/brands" className="btn btn-secondary btn-sm" style={{ marginBottom: '1rem' }}>
        <ArrowLeft size={14} /> Back to Brands
      </Link>

      <div className="page-header">
        <h1>{brand.name}</h1>
        <p>{brand.category}</p>
      </div>

      <div className="grid grid-2">
        {/* Brand Info */}
        <div className="card">
          <h3 className="card-title">Brand Information</h3>
          
          <div style={{ display: 'grid', gap: '1rem' }}>
            {brand.founders && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Users size={18} color="var(--text-secondary)" />
                <span>Founded by {brand.founders}</span>
              </div>
            )}
            
            {brand.founded_year && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Calendar size={18} color="var(--text-secondary)" />
                <span>Founded in {brand.founded_year}</span>
              </div>
            )}

            {(brand.hq_city || brand.hq_state) && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <MapPin size={18} color="var(--text-secondary)" />
                <span>{brand.hq_city}, {brand.hq_state}, {brand.country}</span>
              </div>
            )}

            {brand.parent_company && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Globe size={18} color="var(--text-secondary)" />
                <span>Parent: {brand.parent_company}</span>
              </div>
            )}

            {brand.revenue && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <TrendingUp size={18} color="var(--text-secondary)" />
                <span>Revenue: {brand.revenue}</span>
              </div>
            )}

            {brand.notes && (
              <div style={{ marginTop: '0.5rem', padding: '1rem', background: 'var(--background)', borderRadius: '8px', fontSize: '0.875rem' }}>
                {brand.notes}
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
              {brand.website && (
                <a href={brand.website} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">
                  <Globe size={14} /> Website
                </a>
              )}
              {brand.instagram_handle && (
                <a href={`https://instagram.com/${brand.instagram_handle}`} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">
                  <Instagram size={14} /> Instagram
                </a>
              )}
              {brand.tiktok_handle && (
                <a href={`https://tiktok.com/@${brand.tiktok_handle}`} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm">
                  <Video size={14} /> TikTok
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Current Metrics */}
        <div className="card">
          <h3 className="card-title">Current Metrics</h3>
          
          <div className="filters" style={{ marginBottom: '1rem' }}>
            <select 
              className="form-control" 
              value={platform} 
              onChange={(e) => setPlatform(e.target.value)}
              style={{ width: '120px' }}
            >
              <option value="instagram">Instagram</option>
              <option value="tiktok">TikTok</option>
            </select>
            <select 
              className="form-control" 
              value={days} 
              onChange={(e) => setDays(Number(e.target.value))}
              style={{ width: '100px' }}
            >
              <option value={7}>7 days</option>
              <option value={30}>30 days</option>
              <option value={90}>90 days</option>
            </select>
            <button className="btn btn-secondary btn-sm" onClick={handleExport}>
              <Download size={14} /> Export
            </button>
          </div>

          {latestMetric ? (
            <div className="grid grid-2" style={{ gap: '1rem' }}>
              <div className="stat-card">
                <div className="stat-label">Followers</div>
                <div className="stat-value">{formatNumber(latestMetric.followers)}</div>
                <div className={`stat-change ${followerGrowth >= 0 ? 'positive' : 'negative'}`}>
                  {followerGrowth >= 0 ? '+' : ''}{followerGrowth}% over {days} days
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-label">Posts</div>
                <div className="stat-value">{formatNumber(latestMetric.posts)}</div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Engagement Rate</div>
                <div className="stat-value">{latestMetric.engagement_rate?.toFixed(2) || 0}%</div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Following</div>
                <div className="stat-value">{formatNumber(latestMetric.following)}</div>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
              No metrics available for this platform
            </div>
          )}
        </div>
      </div>

      {/* Growth Chart */}
      {chartData && (
        <div className="card" style={{ marginTop: '2rem' }}>
          <div className="card-header">
            <h3 className="card-title">Follower Growth ({platform})</h3>
          </div>
          <div className="chart-container">
            <Line data={chartData} options={chartOptions} />
          </div>
        </div>
      )}

      {/* Metrics History Table */}
      <div className="card" style={{ marginTop: '2rem' }}>
        <div className="card-header">
          <h3 className="card-title">Metrics History</h3>
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Platform</th>
                <th>Followers</th>
                <th>Following</th>
                <th>Posts</th>
                <th>Engagement Rate</th>
              </tr>
            </thead>
            <tbody>
              {metrics.slice(0, 20).map(metric => (
                <tr key={metric.id}>
                  <td>{new Date(metric.recorded_at).toLocaleDateString()}</td>
                  <td>{metric.platform}</td>
                  <td>{formatNumber(metric.followers)}</td>
                  <td>{formatNumber(metric.following)}</td>
                  <td>{formatNumber(metric.posts)}</td>
                  <td>{metric.engagement_rate?.toFixed(2) || 0}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default BrandDetail;
