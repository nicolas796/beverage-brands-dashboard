import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { BarChart2, TrendingUp, Search, CreditCard, LogOut } from 'lucide-react';
import { AuthProvider, useAuth, ProtectedRoute } from './context/AuthContext';
import Dashboard from './pages/Dashboard';
import Brands from './pages/Brands';
import BrandDetail from './pages/BrandDetail';
import Rankings from './pages/Rankings';
import BillingTab from './pages/BillingTab';
import Login from './pages/Login';
import './App.css';

// Navigation component that shows/hides based on auth state
function Navigation() {
  const { isAuthenticated, logout, user } = useAuth();
  
  if (!isAuthenticated) return null;

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <BarChart2 size={24} />
        <span>Beverage Brands Dashboard</span>
      </div>
      <div className="nav-links">
        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
          Dashboard
        </NavLink>
        <NavLink to="/brands" className={({ isActive }) => isActive ? 'active' : ''}>
          Brands
        </NavLink>
        <NavLink to="/rankings" className={({ isActive }) => isActive ? 'active' : ''}>
          Rankings
        </NavLink>
        <NavLink to="/billing" className={({ isActive }) => isActive ? 'active' : ''}>
          Billing
        </NavLink>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          {user?.name}
        </span>
        <button 
          onClick={logout}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            background: 'transparent',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = 'var(--bg-secondary)';
            e.target.style.color = 'var(--text-primary)';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = 'transparent';
            e.target.style.color = 'var(--text-secondary)';
          }}
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </nav>
  );
}

// Main app routes with auth protection
function AppRoutes() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} 
      />
      <Route 
        path="/" 
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/brands" 
        element={
          <ProtectedRoute requiredPermission="view_brands">
            <Brands />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/brands/:id" 
        element={
          <ProtectedRoute requiredPermission="view_brands">
            <BrandDetail />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/rankings" 
        element={
          <ProtectedRoute requiredPermission="view_rankings">
            <Rankings />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/billing" 
        element={
          <ProtectedRoute requiredPermission="view_billing">
            <BillingTab />
          </ProtectedRoute>
        } 
      />
      <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="app">
          <Navigation />
          
          <main className="main-content">
            <AppRoutes />
          </main>

          <footer className="footer">
            <p>Beverage Brands Social Listening System &copy; 2024</p>
          </footer>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
