/**
 * TypeScript type definitions based on server schemas
 * Generated from /server/schemas/simplified_schemas.py
 */

// User and Authentication Types
export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  phone?: string;
  company_name: string;
  gstin: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface UserRegistration {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  phone?: string;
  company_name: string;
  gstin: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// GSTR-1 Return Types
export interface GSTR1Return {
  id: string;
  user_id: string;
  gstin: string;
  company_name: string;
  filing_period: string; // MMYYYY format
  gross_turnover: number;
  status: 'draft' | 'submitted' | 'filed' | 'cancelled';
  json_data?: any; // Complete GSTR-1 JSON structure (parsed object)
  total_invoices: number;
  total_taxable_value: number;
  total_tax: number;
  total_invoice_value: number;
  created_at: string;
  updated_at: string;
  submitted_at?: string;
}

export interface GSTR1Summary {
  total_invoices: number;
  total_taxable_value: number;
  total_tax: number;
  total_invoice_value: number;
  gross_turnover: number;
}

// GSTR-2 Return Types
export interface GSTR2Return {
  id: string;
  user_id: string;
  gstin: string;
  company_name: string;
  filing_period: string; // MMYYYY format
  status: 'draft' | 'submitted' | 'filed' | 'cancelled';
  json_data?: string; // Complete GSTR-2 JSON structure
  total_invoices: number;
  total_taxable_value: number;
  total_tax: number;
  total_invoice_value: number;
  // GSTR-2 specific fields
  total_itc_claimed: number; // Input Tax Credit
  total_cgst_itc: number;
  total_sgst_itc: number;
  total_igst_itc: number;
  total_cess_itc: number;
  // Supplier analysis
  unique_suppliers: number;
  reverse_charge_invoices: number;
  import_invoices: number;
  created_at: string;
  updated_at: string;
  submitted_at?: string;
}

export interface GSTR2Summary {
  total_invoices: number;
  total_taxable_value: number;
  total_tax: number;
  total_invoice_value: number;
  total_itc_claimed: number;
  total_cgst_itc: number;
  total_sgst_itc: number;
  total_igst_itc: number;
  total_cess_itc: number;
  unique_suppliers: number;
  reverse_charge_invoices: number;
  import_invoices: number;
}

// Filing Request Types
export interface FilingRequest {
  document_ids: string[];
  analysis_session_id: string;
  filing_types: {
    'GSTR-1'?: {
      start_date: string;
      end_date: string;
    };
    'GSTR-2'?: {
      start_date: string;
      end_date: string;
    };
  };
}

export interface FilingResponse {
  filing_id: string;
  status: string;
  message?: string;
  gstr1_return?: GSTR1Return;
  gstr2_return?: GSTR2Return;
  results?: {
    [key: string]: {
      status: string;
      message?: string;
      error_type?: string;
      filing_period?: string;
      total_chunks_analyzed?: number;
      [key: string]: any;
    };
  };
}

// Report Types
export interface GSTR1Report {
  id: string;
  filing_id: string;
  user_id: string;
  gstin: string;
  filing_period: string;
  report_data: any;
  summary: GSTR1Summary;
  created_at: string;
}

export interface GSTR2Report {
  id: string;
  filing_id: string;
  user_id: string;
  gstin: string;
  filing_period: string;
  report_data: any;
  summary: GSTR2Summary;
  created_at: string;
}

// Common Status Types
export type FilingStatus = 'draft' | 'submitted' | 'filed' | 'cancelled' | 'processing' | 'completed' | 'error';

// API Response Wrappers
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Error Types
export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}
