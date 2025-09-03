import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card.tsx';
import { toast } from 'react-hot-toast';
import { useAnalysis, useFiling } from '../store/appStore';
import { filingApi } from '../api';

const FilingDetails: React.FC = () => {
  const navigate = useNavigate();
  const { analysisData } = useAnalysis();
  const { setFilingResult } = useFiling();
  
  const [selectedFilings, setSelectedFilings] = useState<string[]>(['GSTR-1']);
  const [gstr1Details, setGstr1Details] = useState({
    startDate: '',
    endDate: ''
  });
  const [gstr2Details, setGstr2Details] = useState({
    startDate: '',
    endDate: ''
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');

  // Check if we have analysis data from Zustand store
  useEffect(() => {
    if (analysisData) {
      console.log('Loaded analysis data for filing:', analysisData);
        
      // Display analysis results to user
      if (analysisData.gstr1_analysis) {
        console.log('GSTR-1 Analysis Results:', {
          outward_supply_count: analysisData.gstr1_analysis.outward_supply_count,
          total_transactions: analysisData.gstr1_analysis.total_transactions,
          relevant_chunks: analysisData.gstr1_analysis.relevant_chunks.length
        });
      }
    } else {
      // No analysis data available, redirect back to analysis
      navigate('/filing/analysis');
    }
  }, [analysisData, navigate]);

  const handleSubmit = async () => {
    if (selectedFilings.includes('GSTR-1') && (!gstr1Details.startDate || !gstr1Details.endDate)) {
      toast.error('Please provide start and end dates for GSTR-1');
      return;
    }
    
    if (selectedFilings.includes('GSTR-2') && (!gstr2Details.startDate || !gstr2Details.endDate)) {
      toast.error('Please provide start and end dates for GSTR-2');
      return;
    }
    
    if (selectedFilings.length === 0) {
      toast.error('Please select at least one filing type');
      return;
    }

    setIsProcessing(true);
    setProcessingStep('Initializing...');

    try {
      // Get stored data from previous steps
      const uploadedDocIds = JSON.parse(sessionStorage.getItem('uploadedDocIds') || '[]');
      const analysisSessionId = sessionStorage.getItem('analysisSessionId') || '';

      // Debug logging
      console.log('Filing submission data:');
      console.log('- Document IDs:', uploadedDocIds);
      console.log('- Analysis Session ID:', analysisSessionId);
      console.log('- Analysis Data:', analysisData);
      console.log('- Categorization Results:', analysisData?.categorization_summary);

      // Validate session data
      if (!uploadedDocIds.length) {
        console.error('No uploaded documents found in session');
        toast.error('No documents found. Please upload documents first.');
        navigate('/filing/upload');
        return;
      }

      if (!analysisSessionId) {
        console.error('No analysis session found');
        toast.error('Analysis session not found. Please run analysis first.');
        navigate('/filing/analysis');
        return;
      }

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

      console.log('Auth token status:', token ? 'Present' : 'Missing');

      if (!token) {
        toast.error('Authentication required. Please login again.');
        navigate('/login');
        return;
      }

      setProcessingStep('Submitting filing request...');
      
      // Submit filing request using centralized API
      const filingRequest = {
        document_ids: uploadedDocIds,
        session_id: analysisSessionId || '',
        filing_types: selectedFilings,
        filing_details: {
          ...(selectedFilings.includes('GSTR-1') ? {
            'GSTR-1': {
              start_date: gstr1Details.startDate,
              end_date: gstr1Details.endDate
            }
          } : {}),
          ...(selectedFilings.includes('GSTR-2') ? {
            'GSTR-2': {
              start_date: gstr2Details.startDate,
              end_date: gstr2Details.endDate
            }
          } : {})
        },
        categorization_results: analysisData?.categorization_summary || {}
      };

      const result = await filingApi.submitFiling(filingRequest);
      console.log('Filing submission successful:', result);
      
      setProcessingStep('Processing documents and extracting data...');
      
      // Wait for processing to complete and fetch final result
      await new Promise(resolve => setTimeout(resolve, 2000)); // Give backend time to process
      
      setProcessingStep('Finalizing and saving to database...');
      
      // Store filing result in Zustand store
      setFilingResult(result);
      
      setProcessingStep('Complete! Redirecting to report...');
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      navigate('/filing/report');
    } catch (error) {
      console.error('Filing error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast.error(`Filing submission failed: ${errorMessage}`);
    } finally {
      setIsProcessing(false);
      setProcessingStep('');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Filing Details</h1>
          <p className="text-gray-600 mt-2">Configure your GST filing parameters</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="flex items-center justify-center w-8 h-8 bg-green-500 text-white rounded-full text-sm font-medium">
                ✓
              </div>
              <span className="ml-2 text-sm text-gray-500">Upload Documents</span>
            </div>
            <div className="flex-1 h-px bg-green-500 mx-4"></div>
            <div className="flex items-center">
              <div className="flex items-center justify-center w-8 h-8 bg-green-500 text-white rounded-full text-sm font-medium">
                ✓
              </div>
              <span className="ml-2 text-sm text-gray-500">Smart Analysis</span>
            </div>
            <div className="flex-1 h-px bg-green-500 mx-4"></div>
            <div className="flex items-center">
              <div className="flex items-center justify-center w-8 h-8 bg-blue-500 text-white rounded-full text-sm font-medium">
                {isProcessing ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  '3'
                )}
              </div>
              <span className="ml-2 text-sm text-blue-600 font-medium">
                {isProcessing ? 'Processing...' : 'GST Filing'}
              </span>
            </div>
            <div className={`flex-1 h-px mx-4 ${isProcessing ? 'bg-blue-500' : 'bg-gray-300'}`}></div>
            <div className="flex items-center">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                isProcessing ? 'bg-blue-500 text-white' : 'bg-gray-300 text-gray-500'
              }`}>
                4
              </div>
              <span className={`ml-2 text-sm ${isProcessing ? 'text-blue-600' : 'text-gray-500'}`}>
                Report
              </span>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Filing Type Selection */}
          <Card>
            <CardHeader>
              <CardTitle>GST Filing Details</CardTitle>
              <CardDescription>
                Select filing types and configure your GST return filing periods
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Filing Type Selection */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Filing Types</h3>
                <div className="space-y-3">
                  {[
                    { id: 'GSTR-1', name: 'GSTR-1', description: 'Outward supplies of taxable goods and/or services' },
                    { id: 'GSTR-2', name: 'GSTR-2', description: 'Inward supplies from registered suppliers' }
                  ].map((filing) => (
                    <div key={filing.id} className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        id={filing.id}
                        checked={selectedFilings.includes(filing.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedFilings([...selectedFilings, filing.id]);
                          } else {
                            setSelectedFilings(selectedFilings.filter(f => f !== filing.id));
                          }
                        }}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <label htmlFor={filing.id} className="block text-sm font-medium text-gray-700 cursor-pointer">
                          {filing.name}
                        </label>
                        <p className="text-sm text-gray-500">{filing.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* GSTR-1 Details */}
              {selectedFilings.includes('GSTR-1') && (
                <div className="space-y-4 p-4 border rounded-lg bg-blue-50">
                  <h4 className="font-medium text-blue-900">GSTR-1 Filing Period</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Start Date
                      </label>
                      <input
                        type="date"
                        value={gstr1Details.startDate}
                        onChange={(e) => setGstr1Details({...gstr1Details, startDate: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        End Date
                      </label>
                      <input
                        type="date"
                        value={gstr1Details.endDate}
                        onChange={(e) => setGstr1Details({...gstr1Details, endDate: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* GSTR-2 Details */}
              {selectedFilings.includes('GSTR-2') && (
                <div className="space-y-4 p-4 border rounded-lg bg-green-50">
                  <h4 className="font-medium text-green-900">GSTR-2 Filing Period</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Start Date
                      </label>
                      <input
                        type="date"
                        value={gstr2Details.startDate}
                        onChange={(e) => setGstr2Details({...gstr2Details, startDate: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        End Date
                      </label>
                      <input
                        type="date"
                        value={gstr2Details.endDate}
                        onChange={(e) => setGstr2Details({...gstr2Details, endDate: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                      />
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>


          {/* Action Buttons */}
          <div className="flex justify-between">
            <Button 
              onClick={handleSubmit} 
              disabled={selectedFilings.length === 0 || isProcessing}
              className="w-full"
            >
              {isProcessing ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {processingStep || 'Processing...'}
                </div>
              ) : (
                `Start ${selectedFilings.join(' & ')} Processing`
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilingDetails;
