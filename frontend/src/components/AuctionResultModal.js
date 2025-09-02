import React, { useState, useEffect } from 'react';
import { X, CheckCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import axios from 'axios';
import { useUser } from '../contexts/UserContext';

const AuctionResultModal = ({ isOpen, property, onClose, onUpdate }) => {
  const [auctionResult, setAuctionResult] = useState('');
  const [winningBidAmount, setWinningBidAmount] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { token } = useUser();
  
  // Environment variables with fallbacks
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
  useEffect(() => {
    if (property) {
      setAuctionResult(property.auction_result || '');
      setWinningBidAmount(property.winning_bid_amount || '');
    }
  }, [property]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const requestData = { auction_result: auctionResult };
      if (auctionResult === 'sold' && winningBidAmount) {
        requestData.winning_bid_amount = parseFloat(winningBidAmount.replace(/,/g, ''));
      }
      
      const response = await axios.put(
        `${API}/api/admin/properties/${property.id}/auction-result`,
        requestData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data.status === 'success') {
        onUpdate(); // Refresh the data
        onClose();
        setAuctionResult('');
        setWinningBidAmount('');
      }
    } catch (error) {
      console.error('Error updating auction result:', error);
      setError(error.response?.data?.detail || 'Failed to update auction result');
    }
    setIsLoading(false);
  };

  if (!isOpen || !property) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Update Auction Result</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X size={24} />
          </button>
        </div>
        
        {/* Property Info */}
        <div className="bg-gray-50 rounded-lg p-3 mb-4">
          <div className="font-semibold">{property.property_address}</div>
          <div className="text-sm text-gray-600">
            Assessment: {property.assessment_number} | 
            Opening Bid: ${parseFloat(property.opening_bid || 0).toLocaleString()}
          </div>
          {property.sale_date && (
            <div className="text-sm text-gray-500">
              Auction Date: {new Date(property.sale_date).toLocaleDateString()}
            </div>
          )}
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Auction Result *
            </label>
            <select
              value={auctionResult}
              onChange={(e) => setAuctionResult(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select result...</option>
              <option value="pending">Pending (Results not available yet)</option>
              <option value="sold">Sold</option>
              <option value="canceled">Canceled</option>
              <option value="deferred">Deferred</option>
              <option value="taxes_paid">Taxes Paid (Redeemed)</option>
            </select>
          </div>
          
          {auctionResult === 'sold' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Final Sale Price *
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                <Input
                  type="text"
                  value={winningBidAmount}
                  onChange={(e) => {
                    // Format number with commas
                    const value = e.target.value.replace(/[^\d.]/g, '');
                    const formatted = value.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
                    setWinningBidAmount(formatted);
                  }}
                  placeholder="0.00"
                  required={auctionResult === 'sold'}
                  className="w-full pl-8"
                />
              </div>
            </div>
          )}
          
          {error && (
            <div className="mb-4 text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
              {error}
            </div>
          )}
          
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? 'Updating...' : 'Update Result'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AuctionResultModal;