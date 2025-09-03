/**
 * API endpoints for cleanup operations during logout
 */

import { apiClient } from './client';

export const cleanupApi = {
  /**
   * Clear all user session data including chunks from database
   * Preserves user account data but removes all document chunks and session data
   */
  async clearUserSessionData(): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/cleanup/session', {});
  },

  /**
   * Clear specific document chunks by document IDs
   */
  async clearDocumentChunks(documentIds: string[]): Promise<{ message: string; cleared_count: number }> {
    return apiClient.post<{ message: string; cleared_count: number }>('/cleanup/chunks', { 
      document_ids: documentIds 
    });
  },

  /**
   * Clear all documents and chunks for current user
   */
  async clearAllUserDocuments(): Promise<{ message: string; cleared_documents: number; cleared_chunks: number }> {
    return apiClient.delete<{ message: string; cleared_documents: number; cleared_chunks: number }>('/cleanup/documents');
  }
};
