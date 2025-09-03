import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card.tsx';
import { useUploadedDocs, useAnalysis } from '../store/appStore';
import { documentsApi } from '../api';


const SmartAnalysis: React.FC = () => {
  const navigate = useNavigate();
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const { uploadedDocIds } = useUploadedDocs();
  const { analysisData, setAnalysisData } = useAnalysis();

  useEffect(() => {
    const performAnalysis = async () => {
      try {
        if (uploadedDocIds.length === 0) {
          // No documents uploaded, redirect back to upload
          navigate('/filing/upload');
          return;
        }

        // Get token from auth storage (same as auth.ts)
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

        console.log('Analysis token check:');
        console.log('- Direct token:', localStorage.getItem('token') ? 'Found' : 'Not found');
        console.log('- Auth storage:', localStorage.getItem('auth-storage') ? 'Found' : 'Not found');
        console.log('- Final token:', token ? 'Found' : 'Not found');
        console.log('- Document IDs:', uploadedDocIds);

        if (!token) {
          console.error('No authentication token found');
          setIsAnalyzing(false);
          navigate('/filing/upload');
          return;
        }

        // Call actual categorization API with uploaded document IDs
        const result = await documentsApi.analyzeDocuments(uploadedDocIds);
        console.log('Analysis result received:', result);
        
        // Store analysis result in Zustand store
        setAnalysisData(result, result.session_id || '');
        setIsAnalyzing(false);
        
      } catch (error) {
        console.error('Analysis error:', error);
        setIsAnalyzing(false);
        // Show error state instead of redirecting
        setAnalysisData({
          gstr1_analysis: { relevant_chunks: [], outward_supply_count: 0, total_transactions: 0 },
          gstr2_analysis: { relevant_chunks: [], inward_supply_count: 0, total_transactions: 0 },
          categorization_summary: { 
            total_chunks: 0, 
            gstr1_chunks: 0, 
            gstr2_chunks: 0, 
            irrelevant_chunks: 0, 
            ambiguous_chunks_processed: 0, 
            overall_confidence: 0 
          }
        }, '');
      }
    };

    performAnalysis();
  }, [uploadedDocIds, navigate, setAnalysisData]);

  const handleContinue = () => {
    navigate('/filing/details');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Smart Analysis</h1>
          <p className="text-gray-600 mt-2">AI-powered document categorization and analysis</p>
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
              <span className="ml-2 text-sm font-medium text-blue-600">Smart Analysis</span>
            </div>
            <div className="flex-1 mx-4 h-0.5 bg-gray-200"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gray-200 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">
                3
              </div>
              <span className="ml-2 text-sm text-gray-500">GST Filing</span>
            </div>
            <div className="flex-1 mx-4 h-0.5 bg-gray-200"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gray-200 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">
                4
              </div>
              <span className="ml-2 text-sm text-gray-500">Report</span>
            </div>
          </div>
        </div>

        {isAnalyzing ? (
          <Card>
            <CardHeader>
              <CardTitle>Analyzing Documents...</CardTitle>
              <CardDescription>
                Our AI is categorizing your documents and extracting GST data
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-sm text-gray-600">Total Chunks Processed: {analysisData?.categorization_summary?.total_chunks}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : !analysisData ? (
          <Card>
            <CardContent>
              <div className="text-center py-8">
                <p className="text-gray-600">No analysis results available. Please try uploading documents again.</p>
                <Button 
                  className="mt-4"
                  onClick={() => navigate('/filing/upload')}
                >
                  Back to Upload
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
              {/* Analysis Results */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <span className="text-green-600 mr-2">✓</span>
                    Analysis Complete
                  </CardTitle>
                  <CardDescription>
                    Smart analysis completed - documents categorized by AI
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* GSTR-1 Analysis */}
                    <div className="p-4 border rounded-lg bg-blue-50">
                      <h3 className="font-semibold text-blue-900 mb-3">GSTR-1 (Outward Supplies)</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Relevant Chunks:</span>
                          <span className="font-medium">{analysisData.gstr1_analysis.relevant_chunks.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Outward Supply Count:</span>
                          <span className="font-medium">{analysisData.gstr1_analysis.outward_supply_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Total Transactions:</span>
                          <p className="text-lg font-semibold">{analysisData.gstr1_analysis.total_transactions}</p>
                        </div>
                      </div>
                    </div>

                    {/* GSTR-2 Analysis */}
                    <div className="p-4 border rounded-lg bg-green-50">
                      <h3 className="font-semibold text-green-900 mb-3">GSTR-2 (Inward Supplies)</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Relevant Chunks:</span>
                          <span className="font-medium">{analysisData.gstr2_analysis.relevant_chunks.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Inward Supply Count:</span>
                          <span className="font-medium">{analysisData.gstr2_analysis.inward_supply_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Total Transactions:</span>
                          <p className="text-lg font-semibold">{analysisData.gstr2_analysis.total_transactions}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Categorization Summary */}
                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <h3 className="font-semibold text-gray-900 mb-2">Categorization Summary</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {analysisData.categorization_summary.gstr1_chunks}
                        </div>
                        <p className="text-sm text-gray-600">GSTR-1 Chunks</p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {analysisData.categorization_summary.gstr2_chunks}
                        </div>
                        <p className="text-sm text-gray-600">GSTR-2 Chunks</p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-600">
                          {analysisData.categorization_summary.total_chunks}
                        </div>
                        <p className="text-sm text-gray-600">Total Chunks</p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">
                          {Math.round((analysisData.categorization_summary.overall_confidence) * 100)}%
                        </div>
                        <div className="text-gray-600">Confidence</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Action Buttons */}
              <div className="flex justify-between">
                <Button 
                  variant="outline" 
                  onClick={() => navigate('/filing/upload')}
                >
                  Back to Upload
                </Button>
                <Button onClick={handleContinue}>
                  Continue to Filing Details
                </Button>
              </div>
            </div>
        )}
      </div>
    </div>
  );
};

export default SmartAnalysis;
