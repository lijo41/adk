import { apiClient } from './client';
import type { GSTR1Return, GSTR2Report } from '../types';

export const reportsApi = {
  /**
   * Get latest GSTR-1 report
   */
  async getLatestGSTR1(): Promise<GSTR1Return> {
    return apiClient.get<GSTR1Return>('/reports/gstr1/latest');
  },

  /**
   * Get all GSTR-1 reports
   */
  async getAllGSTR1Reports(): Promise<GSTR1Return[]> {
    return apiClient.get<GSTR1Return[]>('/reports/gstr1/all');
  },

  /**
   * Get specific GSTR-1 report by ID
   */
  async getGSTR1Report(filingId: string): Promise<GSTR1Return> {
    return apiClient.get<GSTR1Return>(`/reports/gstr1/${filingId}`);
  },

  /**
   * Get latest GSTR-2 report
   */
  async getLatestGSTR2(): Promise<GSTR2Report> {
    return apiClient.get<GSTR2Report>('/reports/gstr2/latest');
  },

  /**
   * Get all GSTR-2 reports
   */
  async getAllGSTR2Reports(): Promise<GSTR2Report[]> {
    return apiClient.get<GSTR2Report[]>('/reports/gstr2/all');
  },

  /**
   * Get specific GSTR-2 report by ID
   */
  async getGSTR2Report(filingId: string): Promise<GSTR2Report> {
    return apiClient.get<GSTR2Report>(`/reports/gstr2/${filingId}`);
  }
};

/**
 * Download functions using apiClient for consistency
 */
export const downloadGSTR1JSON = async (reportId: string): Promise<void> => {
  try {
    const response = await apiClient.getBlob(`/reports/gstr1/${reportId}/download`);
    const url = window.URL.createObjectURL(response);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `gstr1_${reportId}.json`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    throw new Error(`Failed to download GSTR-1 JSON: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

export const downloadGSTR2JSON = async (reportId: string): Promise<void> => {
  try {
    const response = await apiClient.getBlob(`/reports/gstr2/${reportId}/download`);
    const url = window.URL.createObjectURL(response);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `gstr2_${reportId}.json`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    throw new Error(`Failed to download GSTR-2 JSON: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};
