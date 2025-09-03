import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card.tsx';
import { useFiling } from '../store/appStore';

const FilingReport: React.FC = () => {
  const navigate = useNavigate();
  const { filingResult } = useFiling();
  const [filingData, setFilingData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFilingData = async () => {
      try {
        // Check if we have filing result from Zustand store
        if (!filingResult) {
          navigate('/filing/upload');
          return;
        }

        // Use filing result from Zustand store
        setFilingData(filingResult);
        setIsLoading(false);
      } catch (error) {
        console.error('Error loading filing data:', error);
        setError('Failed to load filing data');
        setIsLoading(false);
      }
    };

    fetchFilingData();
  }, [filingResult, navigate]);

  const downloadReport = async (type: string) => {
    try {
      if (type === 'GSTR1_JSON' && filingData?.filing_id) {
        // Get authentication token
        let token = localStorage.getItem('token');
        if (!token) {
          const authStorage = localStorage.getItem('auth-storage');
          if (authStorage) {
            try {
              const authData = JSON.parse(authStorage);
              token = authData.state?.token;
            } catch (error) {
              console.error('Error parsing auth token:', error);
            }
          }
        }

        if (!token) {
          console.error('No authentication token found');
          return;
        }

        // Download GSTR-1 JSON from API
        const response = await fetch(`http://localhost:8000/api/reports/gstr1/returns/${filingData.filing_id}/download`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const element = document.createElement('a');
          element.href = url;
          element.download = `GSTR1_${filingData.results['GSTR-1'].filing_period.replace(' ', '_')}.json`;
          document.body.appendChild(element);
          element.click();
          document.body.removeChild(element);
          window.URL.revokeObjectURL(url);
        } else {
          console.error('Failed to download GSTR-1 JSON');
        }
      } else {
        // Simulate file download for other types
        const element = document.createElement('a');
        element.href = '#';
        element.download = `${type}_report.pdf`;
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
      }
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Filing Report</h1>
          <p className="text-gray-600 mt-2">Your GST returns are ready for download and submission</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                ✓
              </div>
              <span className="ml-2 text-sm font-medium text-green-600">Upload Documents</span>
            </div>
            <div className="flex-1 mx-4 h-0.5 bg-green-600"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                ✓
              </div>
              <span className="ml-2 text-sm font-medium text-green-600">Smart Analysis</span>
            </div>
            <div className="flex-1 mx-4 h-0.5 bg-green-600"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                ✓
              </div>
              <span className="ml-2 text-sm font-medium text-green-600">GST Filing</span>
            </div>
            <div className="flex-1 mx-4 h-0.5 bg-green-600"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                ✓
              </div>
              <span className="ml-2 text-sm font-medium text-green-600">Report</span>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading filing report...</span>
          </div>
        )}
        
        {/* Error State */}
        {error && (
          <Card>
            <CardHeader>
              <CardTitle className="text-red-600">Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-red-700">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        {!isLoading && !error && filingData && (
        <div className="space-y-6">
          {/* Success Message */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-green-600">
                <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Processing Complete!
              </CardTitle>
              <CardDescription>
                Your GST data has been processed and structured for filing
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Processed Data Structure */}
          {filingData?.results && Object.keys(filingData.results).map((filingType) => (
            <Card key={filingType}>
              <CardHeader>
                <CardTitle>Processed {filingType} Data Structure</CardTitle>
                <CardDescription>
                  Structured JSON data extracted from your documents
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify({
                      [`${filingType.toLowerCase()}_return`]: {
                        "header": {
                          "gstin": "Your GSTIN",
                          "company_name": "Your Company",
                          "filing_period": filingData.results[filingType].filing_period
                        },
                        "invoices": filingData.results[filingType].gstr1_extraction?.invoices || 
                                   filingData.results[filingType].gstr2_extraction?.invoices || [],
                        "summary": {
                          "total_invoices": filingData.results[filingType].gstr1_extraction?.total_invoices ||
                                           filingData.results[filingType].gstr2_extraction?.total_invoices || 0,
                          "total_taxable_value": filingData.results[filingType].gstr1_extraction?.total_taxable_value ||
                                               filingData.results[filingType].gstr2_extraction?.total_taxable_value || 0,
                          "total_tax": filingData.results[filingType].gstr1_extraction?.total_tax_amount ||
                                      filingData.results[filingType].gstr2_extraction?.total_tax_amount || 0
                        }
                      }
                    }, null, 2)}
                  </pre>
                </div>
                <div className={`mt-4 p-3 rounded-lg ${filingType === 'GSTR-1' ? 'bg-blue-50' : 'bg-green-50'}`}>
                  <h4 className={`font-medium mb-2 ${filingType === 'GSTR-1' ? 'text-blue-900' : 'text-green-900'}`}>
                    {filingType} Processing Summary
                  </h4>
                  <div className={`text-sm space-y-1 ${filingType === 'GSTR-1' ? 'text-blue-700' : 'text-green-700'}`}>
                    <p>• Chunks Analyzed: {filingData.results[filingType].date_filtering?.total_chunks_analyzed || 'N/A'}</p>
                    <p>• Filtered Chunks: {filingData.results[filingType].date_filtering?.filtered_chunks_count || 'N/A'}</p>
                    <p>• Invoices Found: {filingData.results[filingType].gstr1_extraction?.total_invoices || 
                                         filingData.results[filingType].gstr2_extraction?.total_invoices || 0}</p>
                    <p>• Total Value: ₹{(filingData.results[filingType].gstr1_extraction?.total_taxable_value || 
                                       filingData.results[filingType].gstr2_extraction?.total_taxable_value || 0)?.toLocaleString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Filing Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Filing Summary</CardTitle>
              <CardDescription>
                Overview of processed returns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                {/* GSTR-1 Summary */}
                {filingData?.results?.['GSTR-1'] && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-blue-900 mb-3">GSTR-1 Return</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Return Period:</span>
                        <span className="font-medium">{filingData.results['GSTR-1'].filing_period}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Invoices:</span>
                        <span className="font-medium">{filingData.results['GSTR-1'].gstr1_extraction?.total_invoices || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Taxable Value:</span>
                        <span className="font-medium">₹{filingData.results['GSTR-1'].gstr1_extraction?.total_taxable_value?.toLocaleString() || '0'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Tax Amount:</span>
                        <span className="font-medium">₹{filingData.results['GSTR-1'].gstr1_extraction?.total_tax_amount?.toLocaleString() || '0'}</span>
                      </div>
                      <div className="flex justify-between border-t pt-2 font-semibold">
                        <span>Status:</span>
                        <span className="text-green-600">{filingData.results['GSTR-1'].status === 'completed' ? 'Ready to Submit' : filingData.results['GSTR-1'].status}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* GSTR-2 Summary */}
                {filingData?.results?.['GSTR-2'] ? (
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-green-900 mb-3">GSTR-2 Return</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Return Period:</span>
                        <span className="font-medium">{filingData.results['GSTR-2'].filing_period}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Invoices:</span>
                        <span className="font-medium">{filingData.results['GSTR-2'].total_invoices || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Taxable Value:</span>
                        <span className="font-medium">₹{filingData.results['GSTR-2'].total_taxable_value?.toLocaleString() || '0'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total ITC Available:</span>
                        <span className="font-medium">₹{filingData.results['GSTR-2'].total_itc?.toLocaleString() || '0'}</span>
                      </div>
                      <div className="flex justify-between border-t pt-2 font-semibold">
                        <span>Status:</span>
                        <span className="text-green-600">{filingData.results['GSTR-2'].status === 'completed' ? 'Ready to Submit' : filingData.results['GSTR-2'].status}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-700 mb-3">GSTR-2 Return</h3>
                    <div className="text-sm text-gray-600">
                      <p>No GSTR-2 data available for this filing</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Download Options */}
          <Card>
            <CardHeader>
              <CardTitle>Download Reports</CardTitle>
              <CardDescription>
                Download your GST returns in various formats
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                {/* GSTR-1 Downloads */}
                <div className="space-y-3">
                  <h3 className="font-medium text-gray-900">GSTR-1 Downloads</h3>
                  <div className="space-y-2">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => downloadReport('GSTR1_JSON')}
                    >
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                      GSTR-1 JSON File
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => downloadReport('GSTR1_PDF')}
                    >
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                      GSTR-1 PDF Report
                    </Button>
                  </div>
                </div>

                {/* GSTR-2 Downloads */}
                <div className="space-y-3">
                  <h3 className="font-medium text-gray-900">GSTR-2 Downloads</h3>
                  <div className="space-y-2">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => downloadReport('GSTR2_JSON')}
                    >
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                      GSTR-2 JSON File
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => downloadReport('GSTR2_PDF')}
                    >
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                      GSTR-2 PDF Report
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Next Steps */}
          <Card>
            <CardHeader>
              <CardTitle>Next Steps</CardTitle>
              <CardDescription>
                What to do after downloading your returns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0">
                    1
                  </div>
                  <div>
                    <h4 className="font-medium">Review the Generated Returns</h4>
                    <p className="text-sm text-gray-600">Carefully review all extracted data for accuracy</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0">
                    2
                  </div>
                  <div>
                    <h4 className="font-medium">Upload to GST Portal</h4>
                    <p className="text-sm text-gray-600">Log into the official GST portal and upload the JSON files</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0">
                    3
                  </div>
                  <div>
                    <h4 className="font-medium">Submit Returns</h4>
                    <p className="text-sm text-gray-600">Complete the submission process on the GST portal</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex justify-between">
            <Button 
              variant="outline" 
              onClick={() => navigate('/dashboard')}
            >
              Back to Dashboard
            </Button>
            <Button onClick={() => navigate('/filing/upload')}>
              Start New Filing
            </Button>
          </div>
        </div>
        )}
      </div>
    </div>
  );
};

export default FilingReport;
