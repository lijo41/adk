import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { documentsApi } from '../api';
import { Button } from './ui/Button.tsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card.tsx';

interface UploadedFile {
  document_id: string;
  filename: string;
  status: string;
  content_length: number;
  content_type: string;
}

interface DocUploadProps {
  onFilesUploaded?: (files: UploadedFile[]) => void;
}

const DocUpload: React.FC<DocUploadProps> = ({ onFilesUploaded }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    try {
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });

      const results = await Promise.all(Array.from(files).map(async (file) => {
        const result = await documentsApi.uploadDocument(file);
        return result;
      }));

      const newFiles = results.map(result => ({
        document_id: result.document_id,
        filename: result.filename,
        status: 'uploaded',
        content_length: result.content_length || 0,
        content_type: result.content_type || 'application/octet-stream'
      }));
      setUploadedFiles(prev => [...prev, ...newFiles]);
      toast.success(`Successfully uploaded ${newFiles.length} files`);
      
      // Notify parent component
      if (onFilesUploaded) {
        onFilesUploaded(newFiles);
      }
      
      // Reset file input
      event.target.value = '';
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload files');
    } finally {
      setUploading(false);
    }
  };

  const clearFiles = () => {
    setUploadedFiles([]);
  };

  return (
    <div className="space-y-6">
      {/* File Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Upload your GST documents for processing and GSTR-1 generation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
              <input
                type="file"
                multiple
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer block"
              >
                <div className="space-y-2">
                  <div className="text-4xl">📄</div>
                  <div className="text-lg font-medium">
                    {uploading ? 'Uploading...' : 'Click to upload files'}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    PDF, Images, Word documents supported
                  </div>
                </div>
              </label>
            </div>
            
            {uploading && (
              <div className="text-center">
                <div className="inline-flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                  Processing files...
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Processed Files</CardTitle>
                <CardDescription>
                  Files that have been uploaded and processed
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={clearFiles}>
                Clear All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {uploadedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <div className="font-medium">{file.filename}</div>
                    <div className="text-sm text-muted-foreground">
                      {(file.content_length / 1024).toFixed(1)} KB • {file.content_type}
                    </div>
                  </div>
                  <div className="text-sm text-green-600 font-medium">
                    ✓ Processed
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      {uploadedFiles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
            <CardDescription>
              Process your uploaded documents for GST filing
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Button>
                Generate GSTR-1
              </Button>
              <Button variant="outline">
                Chat with Documents
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DocUpload;
