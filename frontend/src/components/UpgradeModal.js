import React from 'react';
import { X, Star, CheckCircle, ArrowRight } from 'lucide-react';

const UpgradeModal = ({ isOpen, onClose, onUpgrade, propertyAddress = null }) => {
  if (!isOpen) return null;

  const features = [
    "View all active property details",
    "Access enhanced property information",
    "Interactive property boundary maps",
    "Detailed assessment and tax data",
    "Historical auction results",
    "Priority customer support"
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center">
            <Star className="h-6 w-6 text-yellow-500 mr-2" />
            <h2 className="text-xl font-bold text-gray-900">Upgrade to Premium</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {propertyAddress && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-blue-800 text-sm">
                <strong>Unlock details for:</strong> {propertyAddress}
              </p>
            </div>
          )}

          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Get Full Access to Active Properties
            </h3>
            <p className="text-gray-600">
              Your free account lets you view all property listings and details for inactive properties.
              Upgrade to access complete information for active auctions.
            </p>
          </div>

          {/* Features List */}
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-3">Premium Features Include:</h4>
            <div className="space-y-2">
              {features.map((feature, index) => (
                <div key={index} className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
                  <span className="text-gray-700">{feature}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Pricing */}
          <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200">
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-900 mb-1">
                Coming Soon
              </div>
              <p className="text-gray-600 text-sm">
                Premium subscriptions will be available during our beta launch
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col space-y-3">
            <button
              onClick={onUpgrade}
              disabled
              className="w-full bg-gray-400 text-white py-3 px-4 rounded-lg font-semibold cursor-not-allowed flex items-center justify-center"
            >
              Join Waitlist for Premium
              <ArrowRight className="ml-2 h-5 w-5" />
            </button>
            
            <button
              onClick={onClose}
              className="w-full border border-gray-300 text-gray-700 py-3 px-4 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
            >
              Continue with Free Account
            </button>
          </div>

          {/* Free Account Benefits */}
          <div className="mt-6 p-4 bg-green-50 rounded-lg">
            <h5 className="font-semibold text-green-800 mb-2">Your Free Account Includes:</h5>
            <ul className="text-sm text-green-700 space-y-1">
              <li>• View all property listings</li>
              <li>• Access inactive property details</li>
              <li>• Basic search and filtering</li>
              <li>• Property location maps</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpgradeModal;