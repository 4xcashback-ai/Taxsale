import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const UserContext = createContext();

// Environment variables with fallbacks
const API = process.env.REACT_APP_BACKEND_URL || 'https://taxsale-mapper.preview.emergentagent.com';

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
      // Try to get user info from the regular user endpoint first
      const response = await axios.get(`${API}/api/users/me`);
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      // If that fails, try admin auth verification
      try {
        const adminResponse = await axios.get(`${API}/auth/verify`);
        if (adminResponse.data.authenticated) {
          // Create admin user object
          const adminUser = {
            id: 'admin',
            email: 'admin',
            subscription_tier: 'admin',
            is_verified: true,
            created_at: new Date()
          };
          setUser(adminUser);
          setIsAuthenticated(true);
        } else {
          logout();
        }
      } catch (adminError) {
        console.error('Auth check failed:', error, adminError);
        // Token is invalid, clear it
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      // Check if this is an admin login (email is "admin")
      if (email === 'admin') {
        // Use admin login endpoint
        const response = await axios.post(`${API}/api/auth/login`, {
          username: email,
          password
        });

        const { access_token } = response.data;
        
        // Store token
        localStorage.setItem('authToken', access_token);
        setToken(access_token);
        
        // Create admin user object
        const adminUser = {
          id: 'admin',
          email: 'admin',
          subscription_tier: 'admin',
          is_verified: true,
          created_at: new Date()
        };
        
        setUser(adminUser);
        setIsAuthenticated(true);

        return { success: true, user: adminUser };
      } else {
        // Regular user login
        const response = await axios.post(`${API}/api/users/login`, {
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
      }
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed';
      throw new Error(message);
    }
  };

  const register = async (email, password) => {
    try {
      const response = await axios.post(`${API}/users/register`, {
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
      await axios.post(`${API}/users/verify-email`, { token });
      
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
    return user?.email === 'admin' || user?.subscription_tier === 'admin' || user?.id === 'admin';
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