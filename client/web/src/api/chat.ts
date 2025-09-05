import { apiClient } from './client';

export interface ChatRequest {
  question: string;
  document_ids?: string[];
}

export interface ChatResponse {
  answer: string;
  sources: string[];
}

export const chatApi = {
  async askQuestion(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post<ChatResponse>('/chat/ask', request);
  },

  async getDocumentSummary(documentId: string): Promise<{ summary: string }> {
    return apiClient.get<{ summary: string }>(`/chat/documents/${documentId}/summary`);
  }
};
