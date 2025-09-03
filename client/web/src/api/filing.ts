import { apiClient } from './client';
import type { FilingRequest, FilingResponse } from '../types';

export const filingApi = {
  /**
   * Submit filing request for GSTR-1 and/or GSTR-2
   */
  async submitFiling(request: FilingRequest): Promise<FilingResponse> {
    return apiClient.post<FilingResponse>('/filing/submit', request);
  },

  /**
   * Get filing status by ID
   */
  async getFilingStatus(filingId: string): Promise<any> {
    return apiClient.get(`/filing/status/${filingId}`);
  },

  /**
   * Get all filings for current user
   */
  async getUserFilings(): Promise<any[]> {
    return apiClient.get('/filing/user-filings');
  }
};
