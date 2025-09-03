import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { Button } from './ui/Button.tsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card.tsx';
import { documentsApi } from '../api';

interface FilingStep {
  id: number;
  title: string;
  status: 'pending' | 'current' | 'completed';
}

interface AnalysisResult {
  session_id?: string;
  gstr1_analysis: {
    relevant_chunks: number[];
    b2b_invoices_count: number;
    b2c_invoices_count: number;
    export_invoices_count: number;
    total_transactions: number;
  };
  gstr2_analysis: {
    relevant_chunks: number[];
    purchase_invoices_count: number;
    import_invoices_count: number;
    total_transactions: number;
  };
  recommendations: {
    suggested_filings: string[];
    confidence_score: number;
    notes: string;
  };
}

interface ProcessingStatus {
  processing_id: string;
  status: string;
  overall_progress: number;
  steps: Array<{
    step: string;
    status: string;
    progress: number;
  }>;
  current_step: string;
}

const FilingWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [selectedFilings, setSelectedFilings] = useState<string[]>([]);
  const [filingDetails, setFilingDetails] = useState({
    gstr1_month: 'March',
    gstr1_year: '2024',
    gstr2_month: 'March',
    gstr2_year: '2024'
  });
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const steps: FilingStep[] = [
    { id: 1, title: 'Upload Documents', status: currentStep === 1 ? 'current' : currentStep > 1 ? 'completed' : 'pending' },
    { id: 2, title: 'Smart Analysis', status: currentStep === 2 ? 'current' : currentStep > 2 ? 'completed' : 'pending' },
    { id: 3, title: 'Filing Details', status: currentStep === 3 ? 'current' : currentStep > 3 ? 'completed' : 'pending' },
    { id: 4, title: 'Processing', status: currentStep === 4 ? 'current' : currentStep > 4 ? 'completed' : 'pending' },
    { id: 5, title: 'Report Generation', status: currentStep === 5 ? 'current' : currentStep > 5 ? 'completed' : 'pending' }
  ];

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setLoading(true);
    try {
      const results = await Promise.all(Array.from(files).map(file => 
        documentsApi.uploadDocument(file)
      ));
      
      const newFiles = results.map(result => ({
        document_id: result.document_id,
        filename: result.filename,
        status: 'uploaded'
      }));
      
      setUploadedFiles(prev => [...prev, ...newFiles]);
      toast.success(`Successfully uploaded ${files.length} files`);
      
      event.target.value = '';
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload files');
    } finally {
      setLoading(false);
    }
  };

  const performSmartAnalysis = async () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please upload documents first');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('auth-storage');
      let authToken = '';
      if (token) {
        const authData = JSON.parse(token);
        authToken = authData.state?.token || '';
      }

      const documentIds = uploadedFiles.map(file => file.document_id);
      
      const response = await fetch('http://localhost:8000/api/categorization/analyze', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(documentIds)
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const result = await response.json();
      setAnalysisResult(result);
      setSelectedFilings(result.recommendations.suggested_filings);
      setCurrentStep(2);
      toast.success('Smart analysis completed!');
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error('Failed to analyze documents');
    } finally {
      setLoading(false);
    }
  };

  const startProcessing = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth-storage');
      let authToken = '';
      if (token) {
        const authData = JSON.parse(token);
        authToken = authData.state?.token || '';
      }

      const filingRequest = {
        session_id: analysisResult?.session_id,
        selected_filings: selectedFilings,
        filing_details: filingDetails
      };

      const response = await fetch('http://localhost:8000/api/categorization/process-filing', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(filingRequest)
      });

      if (!response.ok) {
        throw new Error('Processing failed');
      }

      const result = await response.json();
      setProcessingStatus(result);
      setCurrentStep(4);
      toast.success('Processing started!');
      
      // Poll for status updates
      pollProcessingStatus(result.processing_id, authToken);
    } catch (error) {
      console.error('Processing error:', error);
      toast.error('Failed to start processing');
    } finally {
      setLoading(false);
    }
  };

  const pollProcessingStatus = async (processingId: string, authToken: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/categorization/processing-status/${processingId}`, {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        });

        if (response.ok) {
          const status = await response.json();
          setProcessingStatus(status);
          
          if (status.status === 'completed') {
            clearInterval(pollInterval);
            setCurrentStep(5);
            toast.success('Processing completed!');
          }
        }
      } catch (error) {
        console.error('Status polling error:', error);
      }
    }, 2000);

    // Clear interval after 5 minutes
    setTimeout(() => clearInterval(pollInterval), 300000);
  };

  const renderStepIndicator = () => (
    <div className="flex items-center justify-between mb-8">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center">
          <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
            step.status === 'completed' ? 'bg-green-500 border-green-500 text-white' :
            step.status === 'current' ? 'bg-blue-500 border-blue-500 text-white' :
            'bg-gray-200 border-gray-300 text-gray-500'
          }`}>
            {step.status === 'completed' ? '✓' : step.id}
          </div>
          <div className="ml-3">
            <div className={`text-sm font-medium ${
              step.status === 'current' ? 'text-blue-600' : 
              step.status === 'completed' ? 'text-green-600' : 'text-gray-500'
            }`}>
              {step.title}
            </div>
          </div>
          {index < steps.length - 1 && (
            <div className={`flex-1 h-0.5 mx-4 ${
              step.status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
            }`} />
          )}
        </div>
      ))}
    </div>
  );

  const renderUploadStep = () => (
    <Card>
      <CardHeader>
        <CardTitle>Step 1: Upload Your Documents</CardTitle>
        <CardDescription>
          Upload your GST documents for processing and analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
            <input
              type="file"
              multiple
              accept=".pdf,.xlsx,.csv,.xml"
              onChange={handleFileUpload}
              disabled={loading}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <div className="space-y-2">
                <div className="text-6xl">📁</div>
                <div className="text-xl font-medium">
                  {loading ? 'Uploading...' : 'Drag & drop files here or click to browse'}
                </div>
                <div className="text-sm text-muted-foreground">
                  Supported: PDF, Excel, CSV, XML
                </div>
              </div>
            </label>
          </div>

          {uploadedFiles.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium">Uploaded Files:</h4>
              {uploadedFiles.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded">
                  <span>{file.filename}</span>
                  <span className="text-green-600">✓</span>
                </div>
              ))}
            </div>
          )}

          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-start">
              <div className="text-2xl mr-3">💡</div>
              <div>
                <div className="font-medium text-blue-900">Tip:</div>
                <div className="text-blue-700 text-sm">
                  You can upload multiple files. We'll automatically detect what type of filing you need.
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <Button 
              onClick={performSmartAnalysis} 
              disabled={uploadedFiles.length === 0 || loading}
              className="flex-1"
            >
              Continue to Analysis
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderAnalysisStep = () => (
    <Card>
      <CardHeader>
        <CardTitle>Step 2: Document Analysis Complete</CardTitle>
        <CardDescription>
          We've analyzed your documents and detected the following
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="text-lg font-medium flex items-center">
            <span className="text-2xl mr-2">📋</span>
            We detected the following:
          </div>

          {analysisResult?.gstr1_analysis && (
            <div className="border rounded-lg p-4 bg-green-50">
              <div className="flex items-center mb-3">
                <span className="text-green-600 text-xl mr-2">✅</span>
                <span className="font-medium text-green-900">GSTR1 Data Found</span>
              </div>
              <div className="space-y-1 text-sm text-green-800">
                <div>• {analysisResult.gstr1_analysis.b2b_invoices_count} B2B invoices</div>
                <div>• {analysisResult.gstr1_analysis.b2c_invoices_count} B2C invoices</div>
                <div>• {analysisResult.gstr1_analysis.export_invoices_count} Export invoices</div>
              </div>
            </div>
          )}

          {analysisResult?.gstr2_analysis && analysisResult.gstr2_analysis.total_transactions > 0 && (
            <div className="border rounded-lg p-4 bg-blue-50">
              <div className="flex items-center mb-3">
                <span className="text-blue-600 text-xl mr-2">✅</span>
                <span className="font-medium text-blue-900">GSTR2 Data Found</span>
              </div>
              <div className="space-y-1 text-sm text-blue-800">
                <div>• {analysisResult.gstr2_analysis.purchase_invoices_count} Purchase invoices</div>
                <div>• {analysisResult.gstr2_analysis.import_invoices_count} Import invoices</div>
              </div>
            </div>
          )}

          <div className="border rounded-lg p-4 bg-purple-50">
            <div className="flex items-center mb-3">
              <span className="text-purple-600 text-xl mr-2">📊</span>
              <span className="font-medium text-purple-900">
                Recommended Filing: {analysisResult?.recommendations.suggested_filings.join(' & ')}
              </span>
            </div>
            <div className="text-sm text-purple-800">
              Confidence: {Math.round((analysisResult?.recommendations.confidence_score || 0) * 100)}%
            </div>
          </div>

          <div className="space-y-3">
            <div className="font-medium">Select filings to process:</div>
            <div className="flex gap-4">
              {analysisResult?.recommendations.suggested_filings.includes('GSTR1') && (
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedFilings.includes('GSTR1')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedFilings(prev => [...prev, 'GSTR1']);
                      } else {
                        setSelectedFilings(prev => prev.filter(f => f !== 'GSTR1'));
                      }
                    }}
                    className="mr-2"
                  />
                  ✓ Process GSTR1
                </label>
              )}
              {analysisResult?.recommendations.suggested_filings.includes('GSTR2') && (
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedFilings.includes('GSTR2')}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedFilings(prev => [...prev, 'GSTR2']);
                      } else {
                        setSelectedFilings(prev => prev.filter(f => f !== 'GSTR2'));
                      }
                    }}
                    className="mr-2"
                  />
                  ✓ Process GSTR2
                </label>
              )}
            </div>
          </div>

          <div className="flex gap-4">
            <Button variant="outline" onClick={() => setCurrentStep(1)}>
              Back
            </Button>
            <Button 
              onClick={() => setCurrentStep(3)} 
              disabled={selectedFilings.length === 0}
              className="flex-1"
            >
              Continue
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderFilingDetailsStep = () => (
    <Card>
      <CardHeader>
        <CardTitle>Step 3: Filing Details</CardTitle>
        <CardDescription>
          Configure your filing periods and verify company details
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {selectedFilings.includes('GSTR1') && (
            <div>
              <h4 className="font-medium mb-3">GSTR1 Filing Period</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Month</label>
                  <select 
                    value={filingDetails.gstr1_month}
                    onChange={(e) => setFilingDetails(prev => ({...prev, gstr1_month: e.target.value}))}
                    className="w-full p-2 border rounded"
                  >
                    <option>March</option>
                    <option>April</option>
                    <option>May</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Year</label>
                  <select 
                    value={filingDetails.gstr1_year}
                    onChange={(e) => setFilingDetails(prev => ({...prev, gstr1_year: e.target.value}))}
                    className="w-full p-2 border rounded"
                  >
                    <option>2024</option>
                    <option>2023</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {selectedFilings.includes('GSTR2') && (
            <div>
              <h4 className="font-medium mb-3">GSTR2 Filing Period</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Month</label>
                  <select 
                    value={filingDetails.gstr2_month}
                    onChange={(e) => setFilingDetails(prev => ({...prev, gstr2_month: e.target.value}))}
                    className="w-full p-2 border rounded"
                  >
                    <option>March</option>
                    <option>April</option>
                    <option>May</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Year</label>
                  <select 
                    value={filingDetails.gstr2_year}
                    onChange={(e) => setFilingDetails(prev => ({...prev, gstr2_year: e.target.value}))}
                    className="w-full p-2 border rounded"
                  >
                    <option>2024</option>
                    <option>2023</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-4">
            <Button variant="outline" onClick={() => setCurrentStep(2)}>
              Back
            </Button>
            <Button onClick={startProcessing} className="flex-1">
              Start Processing
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderProcessingStep = () => (
    <Card>
      <CardHeader>
        <CardTitle>Processing Your Filing...</CardTitle>
        <CardDescription>
          Please wait while we process your documents
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {processingStatus?.steps.map((step, index) => (
            <div key={index} className="flex items-center">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-3 ${
                step.status === 'completed' ? 'bg-green-500 text-white' :
                step.status === 'in_progress' ? 'bg-blue-500 text-white' :
                'bg-gray-300 text-gray-600'
              }`}>
                {step.status === 'completed' ? '✓' : 
                 step.status === 'in_progress' ? '⏳' : '⏳'}
              </div>
              <div className="flex-1">
                <div className="capitalize font-medium">
                  {step.step.replace('_', ' ')}
                </div>
                {step.status === 'completed' && (
                  <div className="text-sm text-green-600">Completed</div>
                )}
                {step.status === 'in_progress' && (
                  <div className="text-sm text-blue-600">In progress...</div>
                )}
              </div>
            </div>
          ))}

          <div className="mt-6">
            <div className="flex justify-between text-sm mb-2">
              <span>{processingStatus?.overall_progress}% Complete</span>
              <span>Processing {analysisResult?.gstr1_analysis.total_transactions || 0} transactions...</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${processingStatus?.overall_progress || 0}%` }}
              />
            </div>
          </div>

          {processingStatus?.status === 'completed' && (
            <div className="text-center">
              <Button onClick={() => setCurrentStep(5)} className="w-full">
                View Reports
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const renderReportStep = () => (
    <Card>
      <CardHeader>
        <CardTitle>Reports Generated Successfully!</CardTitle>
        <CardDescription>
          Your GST filing reports are ready for download
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="text-center text-6xl mb-4">🎉</div>
          <div className="text-center">
            <div className="text-lg font-medium mb-2">Filing Complete!</div>
            <div className="text-muted-foreground">
              All selected filings have been processed successfully
            </div>
          </div>
          
          <div className="flex gap-4">
            <Button className="flex-1">Download GSTR1</Button>
            <Button className="flex-1" variant="outline">Download GSTR2</Button>
          </div>
          
          <Button 
            variant="outline" 
            onClick={() => {
              setCurrentStep(1);
              setUploadedFiles([]);
              setAnalysisResult(null);
              setProcessingStatus(null);
            }}
            className="w-full"
          >
            Start New Filing
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="max-w-4xl mx-auto p-6">
      {renderStepIndicator()}
      
      {currentStep === 1 && renderUploadStep()}
      {currentStep === 2 && renderAnalysisStep()}
      {currentStep === 3 && renderFilingDetailsStep()}
      {currentStep === 4 && renderProcessingStep()}
      {currentStep === 5 && renderReportStep()}
    </div>
  );
};

export default FilingWizard;
