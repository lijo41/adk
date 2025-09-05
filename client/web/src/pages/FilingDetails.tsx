import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useUploadedDocs, useFiling } from '../store/appStore';
import { filingApi } from '../api';
import Navbar from '../components/Navbar';
import DatePicker from '../components/ui/DatePicker';
import { FloatingChatBot } from '../components/FloatingChatBot';

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
      
      // Check if any filing type returned no data
      const hasNoData = Object.values(result.results || {}).some((filingResult: any) => 
        filingResult.status === 'no_data' || filingResult.error_type === 'no_chunks_in_date_range'
      );
      
      if (hasNoData) {
        // Show toast message and don't redirect to report
        const noDataResult = Object.values(result.results || {}).find((filingResult: any) => 
          filingResult.status === 'no_data'
        ) as any;
        
        toast.error(noDataResult?.message || 'No transactions found for the selected date period. Please check your date range and try again.');
        return;
      }
      
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
    <div className="min-h-screen flex flex-col">
      <Navbar />
      {/* Hero Section Background - same as upload page */}
      <div className="relative overflow-hidden bg-gradient-to-br from-blue-950 via-blue-800 to-slate-900 flex-1 flex items-center justify-center">
        {/* Subtle gradient overlay for depth - same as upload page */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-blue-900/30"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/40 via-transparent to-slate-800/20"></div>
        
        <div className="relative z-10 w-full max-w-4xl mx-auto px-6 sm:px-8 lg:px-12 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Filing Details</h1>
          <p className="text-lg font-medium text-blue-400">Configure your GST filing parameters</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-12">
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  ✓
                </div>
                <span className="ml-2 text-sm font-medium text-green-400">Upload Documents</span>
              </div>
              <div className="flex-1 mx-4 h-0.5 bg-green-600"></div>
              <div className="flex items-center">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  2
                </div>
                <span className="ml-2 text-sm font-medium text-blue-400">GST Filing</span>
              </div>
              <div className="flex-1 mx-4 h-0.5 bg-white/20"></div>
              <div className="flex items-center">
                <div className="w-8 h-8 bg-white/20 text-white/60 rounded-full flex items-center justify-center text-sm font-medium">
                  3
                </div>
                <span className="ml-2 text-sm text-white/60">Report</span>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-3xl mx-auto">

        <div className="bg-black/40 backdrop-blur-sm rounded-xl p-8">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">GST Filing Details</h2>
            <p className="text-white/70">
              Select filing types and configure your GST return filing periods
            </p>
          </div>
          <div className="space-y-6">
            {/* Filing Type Selection */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-white">Filing Types</h3>
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
                      className="mt-1 accent-blue-500"
                    />
                    <div className="flex-1">
                      <label htmlFor={filing.id} className="block text-sm font-medium text-white cursor-pointer">
                        {filing.name}
                      </label>
                      <p className="text-sm text-white/60">{filing.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* GSTR-1 Details */}
            {selectedFilings.includes('GSTR-1') && (
              <div className="space-y-4 p-4 border border-blue-400/30 rounded-lg bg-black/20">
                <h4 className="font-medium text-blue-300">GSTR-1 Filing Period</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-white mb-1">
                      Start Date
                    </label>
                    <DatePicker
                      value={gstr1Details.startDate}
                      onChange={(date) => setGstr1Details({...gstr1Details, startDate: date})}
                      placeholder="Select start date"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white mb-1">
                      End Date
                    </label>
                    <DatePicker
                      value={gstr1Details.endDate}
                      onChange={(date) => setGstr1Details({...gstr1Details, endDate: date})}
                      placeholder="Select end date"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-between mt-8">
              <button 
                onClick={() => navigate('/filing/upload')}
                className="px-6 py-3 text-white border border-white/30 rounded-lg hover:bg-white/10 transition-colors"
              >
                Back to Upload
              </button>
              <button 
                onClick={handleSubmit} 
                disabled={selectedFilings.length === 0 || isProcessing}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isProcessing ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    {processingStep || 'Processing...'}
                  </div>
                ) : (
                  `Start ${selectedFilings.join(' & ')} Processing`
                )}
              </button>
            </div>
          </div>
        </div>
        </div>
        </div>
      </div>
      <FloatingChatBot />
    </div>
  );
};

export default FilingDetails;
