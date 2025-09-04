import { create } from 'zustand';

// Types for our store (GSTR-1 only, GSTR-2 is auto-generated)
interface AnalysisResult {
  gstr1_analysis: {
    relevant_chunks: number[];
    outward_supply_count: number;
    total_transactions: number;
  };
  categorization_summary: {
    total_chunks: number;
    gstr1_chunks: number;
    irrelevant_chunks: number;
    ambiguous_chunks_processed: number;
    overall_confidence: number;
  };
  document_breakdown?: {
    [filename: string]: {
      gstr1_chunks: number[];
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

export const useAppStore = create<AppState>()((set) => ({
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
}));

// Selectors for better performance
export const useUploadedDocs = () => {
  const uploadedDocIds = useAppStore(state => state.uploadedDocIds);
  const setUploadedDocIds = useAppStore(state => state.setUploadedDocIds);
  const clearUploadedDocIds = useAppStore(state => state.clearUploadedDocIds);
  
  return { uploadedDocIds, setUploadedDocIds, clearUploadedDocIds };
};

export const useAnalysis = () => {
  const analysisData = useAppStore(state => state.analysisData);
  const analysisSessionId = useAppStore(state => state.analysisSessionId);
  const setAnalysisData = useAppStore(state => state.setAnalysisData);
  const clearAnalysisData = useAppStore(state => state.clearAnalysisData);
  
  return { analysisData, analysisSessionId, setAnalysisData, clearAnalysisData };
};

export const useFiling = () => {
  const filingResult = useAppStore(state => state.filingResult);
  const filingId = useAppStore(state => state.filingId);
  const setFilingResult = useAppStore(state => state.setFilingResult);
  const clearFilingResult = useAppStore(state => state.clearFilingResult);
  
  return { filingResult, filingId, setFilingResult, clearFilingResult };
};

export const useUI = () => {
  const isLoading = useAppStore(state => state.isLoading);
  const setIsLoading = useAppStore(state => state.setIsLoading);
  
  return { isLoading, setIsLoading };
};
