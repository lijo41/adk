import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card.tsx';
import { toast } from 'react-hot-toast';
import { useUploadedDocs } from '../store/appStore';
import { documentsApi } from '../api';

interface UploadedFile extends File {
  id: string;
  uploadProgress: number;
}

const FileUpload: React.FC = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || []);
    
    const newFiles: UploadedFile[] = selectedFiles.map(file => 
      Object.assign(file, {
        id: Math.random().toString(36).substr(2, 9),
        uploadProgress: 0
      })
    );

    setFiles(prev => [...prev, ...newFiles]);
  };

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const { setUploadedDocIds } = useUploadedDocs();

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('Please select files to upload');
      return;
    }

    setIsUploading(true);
    
    try {
      const uploadedDocIds: string[] = [];
      
      for (const file of files) {
        const actualFile = file;
        
        try {
          const result = await documentsApi.uploadDocument(actualFile);
          uploadedDocIds.push(result.document_id);
          console.log(`Uploaded ${actualFile.name}:`, result.document_id);
        } catch (fileError: any) {
          console.error(`File upload error for ${actualFile.name}:`, fileError);
          
          // Handle specific 422 error with better messaging
          if (fileError?.status === 422) {
            const details = fileError.details?.detail;
            if (Array.isArray(details)) {
              const fieldErrors = details.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
              throw new Error(`Validation error: ${fieldErrors}`);
            } else if (details) {
              throw new Error(`Validation error: ${details}`);
            } else {
              throw new Error('File validation failed - please check file format and try again');
            }
          }
          
          throw fileError;
        }
      }
      
      toast.success(`${uploadedDocIds.length} files processed successfully!`);
      setUploadedDocIds(uploadedDocIds);
      navigate('/filing/details');
      
    } catch (error: any) {
      const errorMessage = error?.message || 'Please check your files and try again.';
      toast.error(`Upload failed: ${errorMessage}`);
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900">Upload Documents</h1>
          <p className="text-lg font-medium text-blue-700 mt-2">Upload your GST documents for processing</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                1
              </div>
              <span className="ml-2 text-sm font-medium text-blue-600">Upload Documents</span>
            </div>
            <div className="flex-1 mx-4 h-0.5 bg-gray-200"></div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gray-200 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">
                2
              </div>
              <span className="ml-2 text-sm text-gray-500">GST Filing</span>
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

        <Card>
          <CardHeader>
            <CardTitle>Document Upload</CardTitle>
            <CardDescription>
              Select PDF, DOCX, or TXT files containing your GST invoices and receipts
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* File Upload Area */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6">
              <div className="space-y-4">
                <div className="text-gray-500">
                  <svg className="mx-auto h-12 w-12" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div>
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-blue-600 hover:text-blue-500 font-medium">
                      Click to upload files
                    </span>
                    <span className="text-gray-500"> or drag and drop</span>
                  </label>
                  <input
                    id="file-upload"
                    type="file"
                    multiple
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>
                <p className="text-sm text-gray-500">
                  PDF, DOCX, TXT up to 10MB each
                </p>
              </div>
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="space-y-3 mb-6">
                <h3 className="text-sm font-medium text-gray-900">Uploaded Files</h3>
                {files.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <svg className="h-8 w-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file.name}</p>
                        <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {file.uploadProgress < 100 ? (
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${file.uploadProgress}%` }}
                          ></div>
                        </div>
                      ) : (
                        <span className="text-green-600 text-sm">✓ Uploaded</span>
                      )}
                      <button
                        onClick={() => removeFile(file.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-between">
              <Button 
                variant="outline" 
                onClick={() => navigate('/dashboard')}
              >
                Back to Dashboard
              </Button>
              <Button 
                onClick={handleUpload}
                disabled={files.length === 0 || isUploading}
              >
                {isUploading ? 'Processing...' : `Continue with ${files.length} files`}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FileUpload;
