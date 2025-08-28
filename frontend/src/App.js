import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Search, MapPin, Calendar, DollarSign, Building2, BarChart3 } from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [taxSales, setTaxSales] = useState([]);
  const [municipalities, setMunicipalities] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMunicipality, setSelectedMunicipality] = useState("");

  // Fetch initial data
  useEffect(() => {
    fetchStats();
    fetchMunicipalities();
    fetchTaxSales();
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

  const handleSearch = async () => {
    await fetchTaxSales(selectedMunicipality, searchQuery);
  };

  const initializeMunicipalities = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/init-municipalities`);
      await fetchMunicipalities();
      await fetchStats();
    } catch (error) {
      console.error("Error initializing municipalities:", error);
    } finally {
      setLoading(false);
    }
  };

  const scrapeAllMunicipalities = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/scrape-all`);
      console.log("Scraping results:", response.data);
      await fetchTaxSales();
      await fetchStats();
    } catch (error) {
      console.error("Error scraping municipalities:", error);
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
                <p className="text-sm text-slate-600">Nova Scotia Municipality Tax Sale Aggregator</p>
              </div>
            </div>
            
            {/* Stats Display */}
            {stats && (
              <div className="hidden md:flex items-center space-x-6 text-sm text-slate-600">
                <div className="flex items-center space-x-2">
                  <Building2 className="h-4 w-4" />
                  <span>{stats.total_municipalities} Municipalities</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MapPin className="h-4 w-4" />
                  <span>{stats.total_properties} Properties</span>
                </div>
                <div className="flex items-center space-x-2">
                  <BarChart3 className="h-4 w-4" />
                  <span>{stats.scraped_today} Scraped Today</span>
                </div>
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
              <span>Map View</span>
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
                  Find tax sale properties across Nova Scotia municipalities
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
                  <div className="flex-1">
                    <Input
                      placeholder="Search by address, municipality, or property..."
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
                      <MapPin className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">No Tax Sales Found</h3>
                      <p className="text-slate-600 mb-4">
                        Try adjusting your search criteria or check back later for updates.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  taxSales.map((property) => (
                    <Card key={property.id} className="bg-white/80 backdrop-blur-sm border-slate-200/50 hover:shadow-lg transition-shadow">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-lg text-slate-900">
                              {property.property_address}
                            </CardTitle>
                            <CardDescription className="flex items-center space-x-2 mt-1">
                              <MapPin className="h-4 w-4 text-slate-500" />
                              <span>{property.municipality_name}</span>
                            </CardDescription>
                          </div>
                          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                            Tax Sale
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
                              <Building2 className="h-4 w-4 text-blue-500" />
                              <div>
                                <p className="text-sm text-slate-600">Assessment</p>
                                <p className="font-semibold text-blue-600">
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
                          
                          {property.sale_location && (
                            <div className="flex items-center space-x-2">
                              <MapPin className="h-4 w-4 text-green-500" />
                              <div>
                                <p className="text-sm text-slate-600">Sale Location</p>
                                <p className="font-semibold text-green-600 text-sm">
                                  {property.sale_location}
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        {property.property_description && (
                          <div className="mt-4 p-3 bg-slate-50/80 rounded-lg">
                            <p className="text-sm text-slate-700">{property.property_description}</p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            )}
          </TabsContent>

          {/* Map Tab */}
          <TabsContent value="map">
            <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MapPin className="h-5 w-5 text-blue-600" />
                  <span>Tax Sale Properties Map</span>
                </CardTitle>
                <CardDescription>
                  Interactive map view of tax sale properties across Nova Scotia
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-96 bg-slate-100 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <MapPin className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-slate-900 mb-2">Interactive Map</h3>
                    <p className="text-slate-600">Map integration coming soon...</p>
                    <p className="text-sm text-slate-500 mt-2">
                      Will display tax sale properties with location data
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Admin Tab */}
          <TabsContent value="admin">
            <div className="space-y-6">
              {/* Statistics Card */}
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

              {/* Admin Actions */}
              <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                <CardHeader>
                  <CardTitle>Administrative Actions</CardTitle>
                  <CardDescription>
                    Initialize municipalities and trigger data scraping
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
                      <Button
                        onClick={initializeMunicipalities}
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        Initialize Municipalities
                      </Button>
                      <Button
                        onClick={scrapeAllMunicipalities}
                        disabled={loading}
                        variant="outline"
                        className="border-slate-300 hover:bg-slate-50"
                      >
                        Scrape All Municipalities
                      </Button>
                    </div>
                    <p className="text-sm text-slate-600">
                      Initialize municipalities first, then run scraping to collect tax sale data.
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Municipalities List */}
              <Card className="bg-white/80 backdrop-blur-sm border-slate-200/50">
                <CardHeader>
                  <CardTitle>Municipalities ({municipalities.length})</CardTitle>
                  <CardDescription>
                    Currently configured Nova Scotia municipalities
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {municipalities.map((muni) => (
                      <div key={muni.id} className="p-4 border border-slate-200 rounded-lg bg-white/50">
                        <h4 className="font-semibold text-slate-900 mb-1">{muni.name}</h4>
                        <p className="text-sm text-slate-600 mb-2">{muni.region}</p>
                        <div className="flex items-center justify-between">
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
                          {muni.last_scraped && (
                            <span className="text-xs text-slate-500">
                              {formatDate(muni.last_scraped)}
                            </span>
                          )}
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