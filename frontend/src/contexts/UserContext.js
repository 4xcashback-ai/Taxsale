import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const UserContext = createContext();

// Environment variables with fallbacks
const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Configure axios defaults
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Check authentication status on app load
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      // Try to get user info - for admin this will fail, so we handle it
      try {
        const response = await axios.get(`${API}/api/users/me`);
        const userData = response.data;
        
        // Use actual database user data for regular users
        setUser(userData);
        setIsAuthenticated(true);
      } catch (userError) {
        // If /api/users/me fails, check if it's because we're admin
        // Admin tokens are valid but don't have user data in the users table
        if (userError.response?.status === 404 || userError.response?.status === 401) {
          // Try to verify token by calling a protected admin endpoint
          try {
            await axios.get(`${API}/api/deployment/status`);
            // If this succeeds, we're admin
            const adminUser = {
              id: 'admin',
              email: 'admin@taxsalecompass.ca',
              subscription_tier: 'paid'
            };
            setUser(adminUser);
            setIsAuthenticated(true);
          } catch (adminError) {
            // Token is invalid
            logout();
          }
        } else {
          logout();
        }
      }
    } catch (error) {
      console.error('Auth status check failed:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      console.log('UserContext login attempt:', { email, password: '***' });
      
      // Check if this is admin login
      if (email === 'admin@taxsalecompass.ca' || email === 'admin') {
        console.log('Admin login detected, using /api/auth/login');
        
        // Use admin login endpoint
        const response = await axios.post(`${API}/api/auth/login`, {
          username: 'admin',
          password
        });

        console.log('Admin login response received:', response.status);
        const { access_token } = response.data;
        
        // Store token and create admin user object
        localStorage.setItem('authToken', access_token);
        setToken(access_token);
        
        // Create admin user object
        const adminUser = {
          id: 'admin',
          email: 'admin@taxsalecompass.ca',
          subscription_tier: 'admin'
        };
        
        setUser(adminUser);
        setIsAuthenticated(true);

        console.log('Admin authentication successful, state updated');
        return { success: true, user: adminUser };
      } else {
        console.log('Regular user login, using /api/users/login');
        
        // Use regular user login endpoint
        const response = await axios.post(`${API}/api/users/login`, {
          email,
          password
        });

        console.log('User login response received:', response.status);
        const { access_token, user: userData } = response.data;
        
        // Store token and user data for all users
        localStorage.setItem('authToken', access_token);
        setToken(access_token);
        setUser(userData);
        setIsAuthenticated(true);

        console.log('User authentication successful, state updated');
        return { success: true, user: userData };
      }
    } catch (error) {
      console.error('Login error in UserContext:', error);
      const message = error.response?.data?.detail || 'Login failed';
      throw new Error(message);
    }
  };

  const register = async (email, password) => {
    try {
      const response = await axios.post(`${API}/api/users/register`, {
        email,
        password
      });

      const { access_token, user: userData } = response.data;
      
      // Store token and user data
      localStorage.setItem('authToken', access_token);
      setToken(access_token);
      setUser(userData);
      setIsAuthenticated(true);

      return { success: true, user: userData };
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed';
      throw new Error(message);
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    delete axios.defaults.headers.common['Authorization'];
  };

  const verifyEmail = async (token) => {
    try {
      await axios.post(`${API}/api/users/verify-email`, { token });
      
      // Refresh user data after verification
      if (isAuthenticated) {
        await checkAuthStatus();
      }
      
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Email verification failed';
      throw new Error(message);
    }
  };

  const upgradeSubscription = async () => {
    // This would integrate with a payment system
    // For now, we'll simulate an upgrade
    try {
      // In a real app, this would call a payment/subscription endpoint
      const updatedUser = { ...user, subscription_tier: 'paid' };
      setUser(updatedUser);
      return { success: true };
    } catch (error) {
      throw new Error('Subscription upgrade failed');
    }
  };

  const isAdmin = () => {
    return user?.email === 'admin@taxsalecompass.ca' || user?.subscription_tier === 'admin' || user?.id === 'admin';
  };

  const isPaidUser = () => {
    return user?.subscription_tier === 'paid' || isAdmin();
  };

  const isFreeUser = () => {
    return user?.subscription_tier === 'free' && !isAdmin();
  };

  const canViewActiveProperties = () => {
    return isPaidUser();
  };

  const value = {
    // State
    user,
    token,
    loading,
    isAuthenticated,
    
    // Actions
    login,
    register,
    logout,
    verifyEmail,
    upgradeSubscription,
    checkAuthStatus,
    
    // Helpers
    isAdmin,
    isPaidUser,
    isFreeUser,
    canViewActiveProperties
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};

export default UserContext;