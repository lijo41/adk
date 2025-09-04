import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card.tsx';
import { toast } from 'react-hot-toast';
import { useUploadedDocs, useFiling } from '../store/appStore';
import { filingApi } from '../api';

const FilingDetails: React.FC = () => {
  const navigate = useNavigate();
  const { uploadedDocIds } = useUploadedDocs();
  const { setFilingResult } = useFiling();
  
  const [selectedFilings, setSelectedFilings] = useState<string[]>(['GSTR-1']);
  const [gstr1Details, setGstr1Details] = useState({
    startDate: '',
    endDate: ''
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');

  // Check if we have uploaded documents
  useEffect(() => {
    if (!uploadedDocIds || uploadedDocIds.length === 0) {
      console.log('No uploaded documents found, redirecting to upload');
      navigate('/filing/upload');
    } else {
      console.log('Found uploaded documents:', uploadedDocIds);
    }
  }, [uploadedDocIds, navigate]);

  const handleSubmit = async () => {
    if (selectedFilings.includes('GSTR-1') && (!gstr1Details.startDate || !gstr1Details.endDate)) {
      toast.error('Please provide start and end dates for GSTR-1');
      return;
    }
    
    
    if (selectedFilings.length === 0) {
      toast.error('Please select at least one filing type');
      return;
    }

    setIsProcessing(true);
    setProcessingStep('Initializing...');

    try {
      // Debug logging
      console.log('Filing submission data:');
      console.log('- Document IDs:', uploadedDocIds);
      console.log('- Filing Types:', selectedFilings);

      // Validate session data
      if (!uploadedDocIds.length) {
        console.error('No uploaded documents found');
        toast.error('No documents found. Please upload documents first.');
        navigate('/filing/upload');
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
        analysis_session_id: 'direct-upload-session',
        filing_types: {
          ...(selectedFilings.includes('GSTR-1') ? {
            'GSTR-1': {
              start_date: gstr1Details.startDate,
              end_date: gstr1Details.endDate
            }
          } : {}),
        }
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
              <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                ✓
              </div>
              <span className="ml-2 text-sm font-medium text-green-600">Upload Documents</span>
            </div>
            <div className="flex-1 mx-4 h-0.5 bg-green-600"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                2
              </div>
              <span className="ml-2 text-sm font-medium text-blue-600">GST Filing</span>
            </div>
            <div className="flex-1 mx-4 h-0.5 bg-gray-200"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gray-200 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">
                3
              </div>
              <span className="ml-2 text-sm text-gray-500">Report</span>
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
                    { id: 'GSTR-1', name: 'GSTR-1', description: 'Outward supplies of taxable goods and/or services' }
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
