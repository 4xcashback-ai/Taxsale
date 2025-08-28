import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Search, MapPin, Calendar, DollarSign, Building2, BarChart3, RefreshCw, Download, Gavel, Users, Clock } from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom map icons for different property types
const createCustomIcon = (color) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });
};

const residentialIcon = createCustomIcon('#3b82f6'); // Blue
const commercialIcon = createCustomIcon('#f59e0b'); // Orange  
const landIcon = createCustomIcon('#10b981'); // Green

function App() {
  const [taxSales, setTaxSales] = useState([]);
  const [municipalities, setMunicipalities] = useState([]);
  const [mapData, setMapData] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMunicipality, setSelectedMunicipality] = useState("");
  const [scrapeStatus, setScrapeStatus] = useState("");

  // Fetch initial data
  useEffect(() => {
    fetchStats();
    fetchMunicipalities();
    fetchTaxSales();
    fetchMapData();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const fetchMunicipalities = async () => {
    try {
      const response = await axios.get(`${API}/municipalities`);
      setMunicipalities(response.data);
    } catch (error) {
      console.error("Error fetching municipalities:", error);
    }
  };

  const fetchTaxSales = async (municipality = "", query = "") => {
    setLoading(true);
    try {
      let url = `${API}/tax-sales`;
      const params = new URLSearchParams();
      
      if (municipality) {
        params.append("municipality", municipality);
      }
      if (query) {
        url = `${API}/tax-sales/search`;
        params.append("q", query);
      }
      
      if (params.toString()) {
        url += "?" + params.toString();
      }

      const response = await axios.get(url);
      setTaxSales(response.data);
    } catch (error) {
      console.error("Error fetching tax sales:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMapData = async () => {
    try {
      const response = await axios.get(`${API}/tax-sales/map-data`);
      setMapData(response.data);
    } catch (error) {
      console.error("Error fetching map data:", error);
    }
  };

  const handleSearch = async () => {
    await fetchTaxSales(selectedMunicipality, searchQuery);
    await fetchMapData();
  };

  const initializeMunicipalities = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/init-municipalities`);
      await fetchMunicipalities();
      await fetchStats();
      setScrapeStatus("Municipalities initialized successfully!");
    } catch (error) {
      console.error("Error initializing municipalities:", error);
      setScrapeStatus("Failed to initialize municipalities.");
    } finally {
      setLoading(false);
    }
  };

  const scrapeHalifax = async () => {
    setLoading(true);
    setScrapeStatus("Scraping Halifax tax sales...");
    try {
      const response = await axios.post(`${API}/scrape/halifax`);
      console.log("Halifax scraping results:", response.data);
      await fetchTaxSales();
      await fetchStats();
      await fetchMapData();
      setScrapeStatus(`Halifax scraping completed! ${response.data.properties_scraped} properties processed.`);
    } catch (error) {
      console.error("Error scraping Halifax:", error);
      setScrapeStatus("Halifax scraping failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const scrapeAllMunicipalities = async () => {
    setLoading(true);
    setScrapeStatus("Scraping all municipalities...");
    try {
      const response = await axios.post(`${API}/scrape-all`);
      console.log("All scraping results:", response.data);
      await fetchTaxSales();
      await fetchStats();
      await fetchMapData();
      setScrapeStatus("Scraping completed for all municipalities!");
    } catch (error) {
      console.error("Error scraping municipalities:", error);
      setScrapeStatus("Some scraping operations failed. Check logs for details.");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    if (!amount) return "N/A";
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString('en-CA');
  };

  const getPropertyIcon = (propertyType) => {
    switch (propertyType?.toLowerCase()) {
      case 'dwelling':
      case 'residential':
        return residentialIcon;
      case 'commercial':
        return commercialIcon;
      case 'land':
      default:
        return landIcon;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Building2 className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">NS Tax Sales</h1>
                <p className="text-sm text-slate-600">Nova Scotia Municipality Tax Sale Aggregator - Live Data</p>
              </div>
            </div>
            
            {/* Enhanced Stats Display */}
            {stats && (
              <div className="hidden md:flex items-center space-x-6 text-sm text-slate-600">
                <div className="flex items-center space-x-2">
                  <Building2 className="h-4 w-4 text-blue-500" />
                  <span>{stats.total_municipalities} Municipalities</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Gavel className="h-4 w-4 text-orange-500" />
                  <span>{stats.total_properties} Properties</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-green-500" />
                  <span>{stats.scraped_today} Scraped Today</span>
                </div>
                {stats.last_scrape && (
                  <div className="flex items-center space-x-2">
                    <RefreshCw className="h-4 w-4 text-purple-500" />
                    <span>Last: {formatDate(stats.last_scrape)}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="search" className="w-full">
          <TabsList className="grid w-full grid-cols-3 lg:w-96 mx-auto mb-8">
            <TabsTrigger value="search" className="flex items-center space-x-2">
              <Search className="h-4 w-4" />
              <span>Search</span>
            </TabsTrigger>
            <TabsTrigger value="map" className="flex items-center space-x-2">
              <MapPin className="h-4 w-4" />
              <span>Live Map</span>
            </TabsTrigger>
            <TabsTrigger value="admin" className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Admin</span>
            </TabsTrigger>
          </TabsList>

          {/* Search Tab */}
          <TabsContent value="search">
            {/* Search Controls */}
            <Card className="mb-8 bg-white/80 backdrop-blur-sm border-slate-200/50">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Search className="h-5 w-5 text-blue-600" />
                  <span>Search Tax Sale Properties</span>
                </CardTitle>
                <CardDescription>
                  Find tax sale properties across Nova Scotia municipalities with real-time data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
                  <div className="flex-1">
                    <Input
                      placeholder="Search by address, owner name, or property details..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-white/80"
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    />
                  </div>
                  <div className="sm:w-48">
                    <select
                      value={selectedMunicipality}
                      onChange={(e) => setSelectedMunicipality(e.target.value)}
                      className="w-full px-3 py-2 bg-white/80 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">All Municipalities</option>
                      {municipalities.map((muni) => (
                        <option key={muni.id} value={muni.name}>
                          {muni.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button 
                    onClick={handleSearch}
                    disabled={loading}
                    className="sm:w-auto bg-blue-600 hover:bg-blue-700"
                  >
                    <Search className="h-4 w-4 mr-2" />
                    Search
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Tax Sale Results */}
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-slate-600">Loading tax sales...</span>
              </div>
            ) : (
              <div className="grid gap-6">
                {taxSales.length === 0 ? (
                  <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                    <CardContent className="py-12 text-center">
                      <Gavel className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">No Tax Sales Found</h3>
                      <p className="text-slate-600 mb-4">
                        Try scraping Halifax data or adjusting your search criteria.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  taxSales.map((property) => (
                    <Card key={property.id} className="bg-white/80 backdrop-blur-sm border-slate-200/50 hover:shadow-lg transition-shadow">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg text-slate-900 mb-2">
                              {property.property_address}
                            </CardTitle>
                            <CardDescription className="flex items-center space-x-4 mt-1">
                              <div className="flex items-center space-x-2">
                                <MapPin className="h-4 w-4 text-slate-500" />
                                <span>{property.municipality_name}</span>
                              </div>
                              {property.assessment_number && (
                                <div className="flex items-center space-x-2">
                                  <span className="text-xs text-slate-500">AAN: {property.assessment_number}</span>
                                </div>
                              )}
                            </CardDescription>
                          </div>
                          <div className="flex flex-col items-end space-y-2">
                            <Badge 
                              variant="outline" 
                              className={
                                property.property_type === 'Dwelling' || property.property_type === 'Residential' 
                                  ? "bg-blue-50 text-blue-700 border-blue-200"
                                  : property.property_type === 'Commercial' 
                                  ? "bg-orange-50 text-orange-700 border-orange-200"
                                  : "bg-green-50 text-green-700 border-green-200"
                              }
                            >
                              {property.property_type || 'Property'}
                            </Badge>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {property.opening_bid && (
                            <div className="flex items-center space-x-2">
                              <Gavel className="h-4 w-4 text-blue-500" />
                              <div>
                                <p className="text-sm text-slate-600">Opening Bid</p>
                                <p className="font-semibold text-blue-600">
                                  {formatCurrency(property.opening_bid)}
                                </p>
                              </div>
                            </div>
                          )}

                          {property.tax_owing && (
                            <div className="flex items-center space-x-2">
                              <DollarSign className="h-4 w-4 text-red-500" />
                              <div>
                                <p className="text-sm text-slate-600">Tax Owing</p>
                                <p className="font-semibold text-red-600">
                                  {formatCurrency(property.tax_owing)}
                                </p>
                              </div>
                            </div>
                          )}
                          
                          {property.assessment_value && (
                            <div className="flex items-center space-x-2">
                              <Building2 className="h-4 w-4 text-purple-500" />
                              <div>
                                <p className="text-sm text-slate-600">Assessment</p>
                                <p className="font-semibold text-purple-600">
                                  {formatCurrency(property.assessment_value)}
                                </p>
                              </div>
                            </div>
                          )}
                          
                          {property.sale_date && (
                            <div className="flex items-center space-x-2">
                              <Calendar className="h-4 w-4 text-orange-500" />
                              <div>
                                <p className="text-sm text-slate-600">Sale Date</p>
                                <p className="font-semibold text-orange-600">
                                  {formatDate(property.sale_date)}
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        {/* Owner Information */}
                        {property.owner_name && (
                          <div className="mt-4 p-3 bg-slate-50/80 rounded-lg">
                            <div className="flex items-center space-x-2 mb-1">
                              <Users className="h-4 w-4 text-slate-600" />
                              <span className="text-sm font-medium text-slate-700">Owner</span>
                            </div>
                            <p className="text-sm text-slate-600">{property.owner_name}</p>
                          </div>
                        )}

                        {/* Property Description */}
                        {property.property_description && (
                          <div className="mt-4 p-3 bg-blue-50/80 rounded-lg">
                            <p className="text-sm text-slate-700">{property.property_description}</p>
                          </div>
                        )}

                        {/* Additional Details */}
                        <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500">
                          {property.pid_number && (
                            <span className="bg-slate-100 px-2 py-1 rounded">PID: {property.pid_number}</span>
                          )}
                          {property.sale_time && (
                            <span className="bg-slate-100 px-2 py-1 rounded">Time: {property.sale_time}</span>
                          )}
                          {property.sale_location && (
                            <span className="bg-slate-100 px-2 py-1 rounded">Location: {property.sale_location}</span>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            )}
          </TabsContent>

          {/* Enhanced Interactive Map Tab */}
          <TabsContent value="map">
            <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <MapPin className="h-5 w-5 text-blue-600" />
                    <span>Live Tax Sale Properties Map</span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                      <span className="text-slate-600">Residential</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                      <span className="text-slate-600">Commercial</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      <span className="text-slate-600">Land</span>
                    </div>
                  </div>
                </CardTitle>
                <CardDescription>
                  Interactive map showing {mapData.length} tax sale properties across Nova Scotia
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-96 rounded-lg overflow-hidden border border-slate-200">
                  {mapData.length > 0 ? (
                    <MapContainer
                      center={[44.6488, -63.5752]} // Halifax center
                      zoom={8}
                      style={{ height: '100%', width: '100%' }}
                    >
                      <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      />
                      {mapData.map((property) => (
                        <Marker
                          key={property.id}
                          position={[property.latitude, property.longitude]}
                          icon={getPropertyIcon(property.property_type)}
                        >
                          <Popup className="custom-popup">
                            <div className="p-2 max-w-xs">
                              <h4 className="font-semibold text-sm mb-2">{property.address}</h4>
                              <p className="text-xs text-slate-600 mb-2">{property.municipality}</p>
                              
                              <div className="space-y-1 text-xs">
                                {property.opening_bid && (
                                  <div className="flex justify-between">
                                    <span>Opening Bid:</span>
                                    <span className="font-semibold text-blue-600">
                                      {formatCurrency(property.opening_bid)}
                                    </span>
                                  </div>
                                )}
                                
                                {property.tax_owing && (
                                  <div className="flex justify-between">
                                    <span>Tax Owing:</span>
                                    <span className="font-semibold text-red-600">
                                      {formatCurrency(property.tax_owing)}
                                    </span>
                                  </div>
                                )}
                                
                                {property.sale_date && (
                                  <div className="flex justify-between">
                                    <span>Sale Date:</span>
                                    <span className="font-semibold">
                                      {formatDate(property.sale_date)}
                                    </span>
                                  </div>
                                )}

                                <div className="mt-2 pt-1 border-t">
                                  <Badge 
                                    variant="outline" 
                                    className="text-xs"
                                  >
                                    {property.property_type || 'Property'}
                                  </Badge>
                                </div>
                              </div>
                            </div>
                          </Popup>
                        </Marker>
                      ))}
                    </MapContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center bg-slate-100">
                      <div className="text-center">
                        <MapPin className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-slate-900 mb-2">No Map Data</h3>
                        <p className="text-slate-600">Scrape municipality data to see properties on the map</p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Enhanced Admin Tab */}
          <TabsContent value="admin">
            <div className="space-y-6">
              {/* Status Messages */}
              {scrapeStatus && (
                <Card className="bg-blue-50/80 backdrop-blur-sm border-blue-200/50">
                  <CardContent className="py-4">
                    <div className="flex items-center space-x-2">
                      <RefreshCw className="h-4 w-4 text-blue-600" />
                      <span className="text-blue-800">{scrapeStatus}</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Enhanced Statistics Card */}
              {stats && (
                <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <BarChart3 className="h-5 w-5 text-blue-600" />
                      <span>System Statistics</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600">{stats.total_municipalities}</div>
                        <div className="text-sm text-slate-600 mt-1">Total Municipalities</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-green-600">{stats.total_properties}</div>
                        <div className="text-sm text-slate-600 mt-1">Tax Sale Properties</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-orange-600">{stats.scraped_today}</div>
                        <div className="text-sm text-slate-600 mt-1">Scraped Today</div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm font-bold text-slate-700">
                          {stats.last_scrape ? formatDate(stats.last_scrape) : "Never"}
                        </div>
                        <div className="text-sm text-slate-600 mt-1">Last Scrape</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Enhanced Admin Actions */}
              <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                <CardHeader>
                  <CardTitle>Data Management</CardTitle>
                  <CardDescription>
                    Initialize municipalities and manage real-time data scraping
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Button
                        onClick={initializeMunicipalities}
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <Building2 className="h-4 w-4 mr-2" />
                        Initialize Municipalities
                      </Button>
                      
                      <Button
                        onClick={scrapeHalifax}
                        disabled={loading}
                        className="bg-orange-600 hover:bg-orange-700"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Scrape Halifax (Live)
                      </Button>
                      
                      <Button
                        onClick={scrapeAllMunicipalities}
                        disabled={loading}
                        variant="outline"
                        className="border-slate-300 hover:bg-slate-50"
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Scrape All
                      </Button>
                    </div>
                    
                    <div className="p-4 bg-yellow-50 rounded-lg">
                      <h4 className="font-semibold text-yellow-800 mb-2">🚀 Real Scraping Available</h4>
                      <p className="text-sm text-yellow-700">
                        Halifax scraper is fully implemented and will fetch live data from halifax.ca. 
                        Other municipalities use placeholder scrapers - ready for implementation.
                      </p>
                    </div>

                    <div className="p-4 bg-green-50 rounded-lg">
                      <h4 className="font-semibold text-green-800 mb-2">⏰ Weekly Automation</h4>
                      <p className="text-sm text-green-700">
                        System automatically scrapes Halifax data every Sunday at 6 AM. 
                        Manual scraping available anytime via the buttons above.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Enhanced Municipalities List */}
              <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                <CardHeader>
                  <CardTitle>Municipalities ({municipalities.length})</CardTitle>
                  <CardDescription>
                    Currently configured Nova Scotia municipalities with scraper status
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {municipalities.map((muni) => (
                      <div key={muni.id} className="p-4 border border-slate-200 rounded-lg bg-white/50">
                        <h4 className="font-semibold text-slate-900 mb-1">{muni.name}</h4>
                        <p className="text-sm text-slate-600 mb-2">{muni.region}</p>
                        
                        <div className="flex items-center justify-between mb-2">
                          <Badge
                            variant={
                              muni.scrape_status === 'success' ? 'default' : 
                              muni.scrape_status === 'failed' ? 'destructive' : 
                              'secondary'
                            }
                            className="text-xs"
                          >
                            {muni.scrape_status}
                          </Badge>
                          
                          {muni.scraper_type === 'halifax' && (
                            <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700">
                              Live Scraper
                            </Badge>
                          )}
                        </div>
                        
                        <div className="flex items-center justify-between text-xs text-slate-500">
                          <span>
                            {muni.last_scraped ? formatDate(muni.last_scraped) : "Never scraped"}
                          </span>
                          <a 
                            href={muni.website_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:underline"
                          >
                            Website
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;