import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../utils/api';

// Hardcoded users for demo (frontend validation - backend also validates)
const USERS = {
  fred: {
    id: 'fred',
    username: 'fred',
    password: '123456',
    role: 'user',
    name: 'Fred',
    permissions: ['view_dashboard', 'view_brands', 'view_rankings', 'view_billing']
  },
  admin: {
    id: 'admin',
    username: 'admin',
    password: 'password123',
    role: 'admin',
    name: 'Admin',
    permissions: ['view_dashboard', 'view_brands', 'view_rankings', 'view_billing', 'approve_brands', 'manage_settings']
  }
};

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check for existing auth on mount
  useEffect(() => {
    const storedAuth = localStorage.getItem('bb_auth_user');
    if (storedAuth) {
      try {
        const parsedAuth = JSON.parse(storedAuth);
        if (parsedAuth.token && parsedAuth.user) {
          setUser(parsedAuth.user);
          setToken(parsedAuth.token);
        }
      } catch (e) {
        localStorage.removeItem('bb_auth_user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    setError(null);
    
    const normalizedUsername = username.toLowerCase().trim();
    
    try {
      // Try backend authentication first
      const response = await api.login(normalizedUsername, password);
      
      if (response.access_token && response.user) {
        const authData = {
          token: response.access_token,
          user: response.user
        };
        
        setUser(response.user);
        setToken(response.access_token);
        localStorage.setItem('bb_auth_user', JSON.stringify(authData));
        return true;
      }
    } catch (apiError) {
      // Fallback to frontend validation if backend auth fails
      console.log('Backend auth failed, using frontend validation:', apiError.message);
      
      const userRecord = USERS[normalizedUsername];
      
      if (!userRecord || userRecord.password !== password) {
        setError('Invalid username or password');
        return false;
      }
      
      // Create user object without password
      const authenticatedUser = {
        id: userRecord.id,
        username: userRecord.username,
        role: userRecord.role,
        name: userRecord.name,
        permissions: userRecord.permissions
      };
      
      // Generate a mock token for frontend-only mode
      const mockToken = 'frontend-only-' + Date.now();
      
      const authData = {
        token: mockToken,
        user: authenticatedUser
      };
      
      setUser(authenticatedUser);
      setToken(mockToken);
      localStorage.setItem('bb_auth_user', JSON.stringify(authData));
      return true;
    }
    
    return false;
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('bb_auth_user');
  };

  const hasPermission = (permission) => {
    if (!user) return false;
    return user.permissions.includes(permission);
  };

  const isAdmin = () => {
    return user?.role === 'admin';
  };

  const value = {
    user,
    token,
    login,
    logout,
    loading,
    error,
    hasPermission,
    isAdmin,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Protected route wrapper component
export function ProtectedRoute({ children, requiredPermission = null }) {
  const { isAuthenticated, loading, hasPermission } = useAuth();
  
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
  
  if (!isAuthenticated) {
    // Redirect to login - handled by router
    return null;
  }
  
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center',
        maxWidth: '600px',
        margin: '4rem auto'
      }}>
        <h2 style={{ color: 'var(--danger)', marginBottom: '1rem' }}>
          Access Denied
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          You don't have permission to view this page.
        </p>
      </div>
    );
  }
  
  return children;
}
