import React, { useState, useEffect } from 'react';
import { useUser } from '../contexts/UserContext';

const MyFavorites = () => {
  const { user } = useContext(UserContext);
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  const fetchFavorites = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API}/api/favorites`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (response.status === 403) {
        setError('Paid subscription required to access favorites');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to fetch favorites');
      }

      const data = await response.json();
      setFavorites(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const removeFavorite = async (propertyId) => {
    try {
      const response = await fetch(`${API}/api/favorites/${propertyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to remove from favorites');
      }

      // Remove from local state
      setFavorites(favorites.filter(fav => fav.property_id !== propertyId));
    } catch (err) {
      console.error('Error removing favorite:', err);
    }
  };

  useEffect(() => {
    if (user && user.subscription_tier === 'paid') {
      fetchFavorites();
    }
  }, [user]);

  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">My Favorites</h1>
          <p className="text-gray-600">Please log in to view your favorites.</p>
        </div>
      </div>
    );
  }

  if (user.subscription_tier !== 'paid') {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">My Favorites</h1>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <p className="text-yellow-800 mb-4">
              🔒 Favorites are available for paid subscribers only.
            </p>
            <p className="text-gray-600">
              Upgrade your subscription to save up to 50 favorite properties.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">My Favorites</h1>
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading favorites...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">My Favorites</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">My Favorites</h1>
        <div className="text-sm text-gray-600">
          {favorites.length}/50 properties saved
        </div>
      </div>

      {favorites.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🔖</div>
          <h2 className="text-xl font-semibold mb-2">No favorites yet</h2>
          <p className="text-gray-600 mb-4">
            Start browsing properties and bookmark the ones you're interested in!
          </p>
          <a href="/dashboard" className="text-blue-600 hover:underline">
            Browse Properties →
          </a>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {favorites.map((favorite) => (
            <div key={favorite.id} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <div className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-gray-900 text-sm">
                    #{favorite.property_id}
                  </h3>
                  <button
                    onClick={() => removeFavorite(favorite.property_id)}
                    className="text-red-500 hover:text-red-700 text-sm"
                    title="Remove from favorites"
                  >
                    ✕
                  </button>
                </div>
                
                <p className="text-gray-600 text-sm mb-2">
                  {favorite.municipality_name}
                </p>
                
                <p className="text-gray-800 text-sm mb-3">
                  {favorite.property_address}
                </p>
                
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <span>
                    Added {new Date(favorite.created_at).toLocaleDateString()}
                  </span>
                  <a
                    href={`/property/${favorite.property_id}`}
                    className="text-blue-600 hover:underline"
                  >
                    View Details →
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyFavorites;