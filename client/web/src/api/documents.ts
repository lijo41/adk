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
  status: string;
  processed_documents: string[];
  total_chunks: number;
  user_id: string;
  categorization: {
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
    chunk_categorization: Array<{
      chunk_index: number;
      category: string;
      confidence: number;
      detected_data_types: string[];
      method: string;
    }>;
    chunk_metadata: any[];
    document_breakdown: Record<string, any>;
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
