import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Types for our store
interface AnalysisResult {
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
  document_breakdown?: {
    [filename: string]: {
      gstr1_chunks: number[];
      gstr2_chunks: number[];
      irrelevant_chunks: number[];
      total_chunks: number;
    };
  };
}

interface FilingResult {
  filing_id: string;
  status: string;
  message?: string;
  results?: {
    'GSTR-1'?: any;
    'GSTR-2'?: any;
  };
  [key: string]: any;
}

interface AppState {
  // Document upload state
  uploadedDocIds: string[];
  setUploadedDocIds: (ids: string[]) => void;
  clearUploadedDocIds: () => void;

  // Analysis state
  analysisSessionId: string | null;
  analysisData: AnalysisResult | null;
  setAnalysisData: (data: AnalysisResult, sessionId: string) => void;
  clearAnalysisData: () => void;

  // Filing state
  filingId: string | null;
  filingResult: FilingResult | null;
  setFilingResult: (result: FilingResult) => void;
  clearFilingResult: () => void;

  // UI state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  
  // Clear all data (for logout)
  clearAllData: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Initial state
      uploadedDocIds: [],
      analysisSessionId: null,
      analysisData: null,
      filingId: null,
      filingResult: null,
      isLoading: false,

      // Document upload actions
      setUploadedDocIds: (ids: string[]) => 
        set({ uploadedDocIds: ids }),
      
      clearUploadedDocIds: () => 
        set({ uploadedDocIds: [] }),

      // Analysis actions
      setAnalysisData: (data: AnalysisResult, sessionId?: string) => 
        set({ 
          analysisData: data, 
          analysisSessionId: sessionId || null
        }),
      
      clearAnalysisData: () => 
        set({ 
          analysisData: null, 
          analysisSessionId: null 
        }),

      // Filing actions
      setFilingResult: (result: FilingResult) => 
        set({ 
          filingResult: result, 
          filingId: result.filing_id 
        }),
      
      clearFilingResult: () => 
        set({ 
          filingResult: null, 
          filingId: null 
        }),

      // UI actions
      setIsLoading: (loading: boolean) => 
        set({ isLoading: loading }),

      // Clear all data
      clearAllData: () => 
        set({
          uploadedDocIds: [],
          analysisSessionId: null,
          analysisData: null,
          filingId: null,
          filingResult: null,
          isLoading: false
        })
    }),
    {
      name: 'adk-app-storage', // localStorage key
      // Only persist essential data, not UI state
      partialize: (state) => ({
        uploadedDocIds: state.uploadedDocIds,
        analysisSessionId: state.analysisSessionId,
        analysisData: state.analysisData,
        filingId: state.filingId,
        filingResult: state.filingResult
      })
    }
  )
);

// Selectors for better performance
export const useUploadedDocs = () => useAppStore(state => ({
  uploadedDocIds: state.uploadedDocIds,
  setUploadedDocIds: state.setUploadedDocIds,
  clearUploadedDocIds: state.clearUploadedDocIds
}));

export const useAnalysis = () => useAppStore(state => ({
  analysisData: state.analysisData,
  analysisSessionId: state.analysisSessionId,
  setAnalysisData: state.setAnalysisData,
  clearAnalysisData: state.clearAnalysisData
}));

export const useFiling = () => useAppStore(state => ({
  filingResult: state.filingResult,
  filingId: state.filingId,
  setFilingResult: state.setFilingResult,
  clearFilingResult: state.clearFilingResult
}));

export const useUI = () => useAppStore(state => ({
  isLoading: state.isLoading,
  setIsLoading: state.setIsLoading
}));
