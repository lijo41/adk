import { apiClient } from './client';

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  message: string;
  content_length?: number;
  content_type?: string;
}

export interface AnalysisRequest {
  document_ids: string[];
}

export interface AnalysisResponse {
  session_id: string;
  gstr1_analysis: {
    relevant_chunks: number[];
    outward_supply_count: number;
    total_transactions: number;
  };
  gstr2_analysis: {
    relevant_chunks: number[];
    inward_supply_count: number;
    total_transactions: number;
  };
  categorization_summary: {
    total_chunks: number;
    gstr1_chunks: number;
    gstr2_chunks: number;
    irrelevant_chunks: number;
    ambiguous_chunks_processed: number;
    overall_confidence: number;
  };
}

export const documentsApi = {
  /**
   * Upload a single document file
   */
  async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.postFormData<DocumentUploadResponse>('/documents/upload', formData);
  },

  /**
   * Analyze uploaded documents for categorization
   */
  async analyzeDocuments(documentIds: string[]): Promise<AnalysisResponse> {
    return apiClient.post<AnalysisResponse>('/categorization/analyze', { document_ids: documentIds });
  }
};
