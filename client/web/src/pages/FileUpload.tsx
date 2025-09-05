import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useUploadedDocs, useFiling, useAppStore } from '../store/appStore';
import { documentsApi, cleanupApi } from '../api';
import Navbar from '../components/Navbar';
import { FloatingChatBot } from '../components/FloatingChatBot';

interface UploadedFile extends File {
  id: string;
  uploadProgress: number;
}

const FileUpload: React.FC = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [originalFiles, setOriginalFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const { filingResult } = useFiling();
  const clearAllData = useAppStore(state => state.clearAllData);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || []);
    
    // If user has completed filing and selecting new files, clear previous data
    if (filingResult?.status === 'completed' && files.length === 0) {
      try {
        // Clear backend document store
        await cleanupApi.clearUserSessionData();
        // Clear frontend state
        clearAllData();
        toast.success('Previous filing data cleared for new session');
      } catch (error) {
        console.error('Failed to clear previous data:', error);
        toast.error('Warning: Failed to clear previous data');
      }
    }
    
    // Store original files for API calls
    setOriginalFiles(prev => [...prev, ...selectedFiles]);
    
    const newFiles: UploadedFile[] = selectedFiles.map(file => {
      // Create a proper UploadedFile object that preserves the File object
      const uploadFile = Object.create(file);
      uploadFile.id = Math.random().toString(36).substr(2, 9);
      uploadFile.uploadProgress = 0;
      
      // Ensure we can access File properties
      Object.defineProperty(uploadFile, 'name', { value: file.name, writable: false });
      Object.defineProperty(uploadFile, 'size', { value: file.size, writable: false });
      Object.defineProperty(uploadFile, 'type', { value: file.type, writable: false });
      
      return uploadFile as UploadedFile;
    });

    setFiles(prev => [...prev, ...newFiles]);
  };

  const removeFile = (fileId: string) => {
    const fileToRemove = files.find(f => f.id === fileId);
    if (fileToRemove) {
      // Remove from both files and originalFiles
      setFiles(prev => prev.filter(f => f.id !== fileId));
      setOriginalFiles(prev => prev.filter(f => !(f.name === fileToRemove.name && f.size === fileToRemove.size)));
    }
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
        // Get the original File object from the stored originalFiles
        const originalFile = originalFiles.find(f => f.name === file.name && f.size === file.size);
        const actualFile = originalFile || file;
        
        // Start progress at 10%
        setFiles(prev => prev.map(f => 
          f.id === file.id ? { ...f, uploadProgress: 10 } : f
        ));
        
        try {
          // Simulate progress updates during upload
          const progressInterval = setInterval(() => {
            setFiles(prev => prev.map(f => {
              if (f.id === file.id) {
                const currentProgress = Number(f.uploadProgress) || 0;
                if (currentProgress < 90) {
                  return { ...f, uploadProgress: Math.min(currentProgress + 15, 90) };
                }
              }
              return f;
            }));
          }, 300);
          
          const result = await documentsApi.uploadDocument(actualFile as File);
          clearInterval(progressInterval);
          
          // Set to 100% when complete
          setFiles(prev => prev.map(f => 
            f.id === file.id ? { ...f, uploadProgress: 100 } : f
          ));
          
          uploadedDocIds.push(result.document_id);
          console.log(`Uploaded ${file.name}:`, result.document_id);
        } catch (fileError: any) {
          console.error(`File upload error for ${file.name}:`, fileError);
          
          // Reset progress on error
          setFiles(prev => prev.map(f => 
            f.id === file.id ? { ...f, uploadProgress: 0 } : f
          ));
          
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
    if (!bytes || bytes === 0 || isNaN(bytes)) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const size = parseFloat((bytes / Math.pow(k, i)).toFixed(2));
    return `${isNaN(size) ? 0 : size} ${sizes[i] || 'Bytes'}`;
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      {/* Hero Section Background - same as dashboard */}
      <div className="relative overflow-hidden bg-gradient-to-br from-blue-950 via-blue-800 to-slate-900 flex-1 flex items-center justify-center">
        {/* Subtle gradient overlay for depth - same as dashboard */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-blue-900/30"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/40 via-transparent to-slate-800/20"></div>
        
        <div className="relative z-10 w-full max-w-4xl mx-auto px-6 sm:px-8 lg:px-12 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Upload Documents</h1>
          <p className="text-lg font-medium text-blue-400">Upload your GST documents for processing</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-12">
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  1
                </div>
                <span className="ml-2 text-sm font-medium text-blue-400">Upload Documents</span>
              </div>
              <div className="flex-1 mx-4 h-0.5 bg-white/20"></div>
              <div className="flex items-center">
                <div className="w-8 h-8 bg-white/20 text-white/60 rounded-full flex items-center justify-center text-sm font-medium">
                  2
                </div>
                <span className="ml-2 text-sm text-white/60">GST Filing</span>
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
            <h2 className="text-2xl font-bold text-white mb-2">Document Upload</h2>
            <p className="text-white/70">
              Select PDF, DOCX, or TXT files containing your GST invoices and receipts
            </p>
          </div>
          <div>
            {/* File Upload Area */}
            <div className="border-2 border-dashed border-blue-400/30 rounded-lg p-8 text-center mb-6 bg-black/20">
              <div className="space-y-4">
                <div className="text-blue-300">
                  <svg className="mx-auto h-12 w-12" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-blue-400 hover:text-blue-300 font-medium">
                      Click to upload files
                    </span>
                    <span className="text-white/70"> or drag and drop</span>
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
                <p className="text-sm text-white/60">
                  PDF, DOCX, TXT up to 10MB each
                </p>
              </div>
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="space-y-3 mb-6">
                <h3 className="text-sm font-medium text-white">Uploaded Files</h3>
                {files.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-3 bg-black/30 backdrop-blur-sm rounded-lg border border-white/20">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <svg className="h-8 w-8 text-blue-300" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{file.name}</p>
                        <p className="text-sm text-white/60">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {file.uploadProgress < 100 ? (
                        <div className="w-24 bg-black rounded-full h-2 border border-white/30">
                          <div 
                            className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${isNaN(file.uploadProgress) ? 0 : file.uploadProgress}%` }}
                          ></div>
                        </div>
                      ) : (
                        <span className="text-blue-400 text-sm">✓ Uploaded</span>
                      )}
                      <button
                        onClick={() => removeFile(file.id)}
                        className="text-red-400 hover:text-red-300"
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
              <button 
                onClick={() => navigate('/dashboard')}
                className="px-6 py-3 text-white border border-white/30 rounded-lg hover:bg-white/10 transition-colors"
              >
                Back to Dashboard
              </button>
              <button 
                onClick={handleUpload}
                disabled={files.length === 0 || isUploading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isUploading ? 'Processing...' : `Continue with ${files.length || 0} file${files.length === 1 ? '' : 's'}`}
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

export default FileUpload;
