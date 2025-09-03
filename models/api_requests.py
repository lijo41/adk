# API Request Models - Complete GSTR-1 transaction types
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class ChatRequest(BaseModel):
    question: str
    document_ids: List[str] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []

class GSTR1CreateRequest(BaseModel):
    gstin: str
    company_name: str
    filing_period: str
    gross_turnover: float

# B2B - Business to Business
class B2BItemRequest(BaseModel):
    sr_no: int
    description: str
    hsn_code: str
    quantity: float
    unit: str
    rate: float
    taxable_value: float
    cgst_rate: float
    cgst_amount: float
    sgst_rate: float
    sgst_amount: float
    igst_rate: float
    igst_amount: float
    cess_rate: float = 0.0
    cess_amount: float = 0.0

class B2BInvoiceRequest(BaseModel):
    invoice_number: str
    invoice_date: str
    invoice_value: float
    place_of_supply: str
    reverse_charge: str
    invoice_type: str
    recipient_gstin: str
    recipient_name: str
    recipient_state: str
    items: List[B2BItemRequest]

# B2C - Business to Consumer (Small)
class B2CItemRequest(BaseModel):
    sr_no: int
    description: str
    hsn_code: str
    quantity: float
    unit: str
    rate: float
    taxable_value: float
    cgst_rate: float
    cgst_amount: float
    sgst_rate: float
    sgst_amount: float
    igst_rate: float
    igst_amount: float
    cess_rate: float = 0.0
    cess_amount: float = 0.0

class B2CInvoiceRequest(BaseModel):
    invoice_number: str
    invoice_date: str
    invoice_value: float
    place_of_supply: str
    invoice_type: str = "Regular"
    items: List[B2CItemRequest]

# B2CL - Business to Consumer Large (>2.5L)
class B2CLItemRequest(BaseModel):
    sr_no: int
    description: str
    hsn_code: str
    quantity: float
    unit: str
    rate: float
    taxable_value: float
    cgst_rate: float
    cgst_amount: float
    sgst_rate: float
    sgst_amount: float
    igst_rate: float
    igst_amount: float
    cess_rate: float = 0.0
    cess_amount: float = 0.0

class B2CLInvoiceRequest(BaseModel):
    invoice_number: str
    invoice_date: str
    invoice_value: float
    place_of_supply: str
    invoice_type: str = "Regular"
    items: List[B2CLItemRequest]

# CDNR - Credit/Debit Notes (Registered)
class CDNRItemRequest(BaseModel):
    sr_no: int
    description: str
    hsn_code: str
    quantity: float
    unit: str
    rate: float
    taxable_value: float
    cgst_rate: float
    cgst_amount: float
    sgst_rate: float
    sgst_amount: float
    igst_rate: float
    igst_amount: float
    cess_rate: float = 0.0
    cess_amount: float = 0.0

class CDNRRequest(BaseModel):
    note_number: str
    note_date: str
    note_value: float
    note_type: str  # "C" for Credit, "D" for Debit
    reason: str
    original_invoice_number: str
    original_invoice_date: str
    recipient_gstin: str
    recipient_name: str
    place_of_supply: str
    items: List[CDNRItemRequest]

# CDNUR - Credit/Debit Notes (Unregistered)
class CDNURItemRequest(BaseModel):
    sr_no: int
    description: str
    hsn_code: str
    quantity: float
    unit: str
    rate: float
    taxable_value: float
    cgst_rate: float
    cgst_amount: float
    sgst_rate: float
    sgst_amount: float
    igst_rate: float
    igst_amount: float
    cess_rate: float = 0.0
    cess_amount: float = 0.0

class CDNURRequest(BaseModel):
    note_number: str
    note_date: str
    note_value: float
    note_type: str  # "C" for Credit, "D" for Debit
    reason: str
    original_invoice_number: str
    original_invoice_date: str
    place_of_supply: str
    items: List[CDNURItemRequest]

# EXP - Exports
class ExportItemRequest(BaseModel):
    sr_no: int
    description: str
    hsn_code: str
    quantity: float
    unit: str
    rate: float
    taxable_value: float
    igst_rate: float
    igst_amount: float
    cess_rate: float = 0.0
    cess_amount: float = 0.0

class ExportInvoiceRequest(BaseModel):
    invoice_number: str
    invoice_date: str
    invoice_value: float
    port_code: str
    shipping_bill_number: str
    shipping_bill_date: str
    export_type: str  # "WPAY", "WOPAY"
    items: List[ExportItemRequest]

# AT - Advance Tax
class AdvanceTaxRequest(BaseModel):
    place_of_supply: str
    applicable_percent: float
    source: str  # "Tax Liability", "ITC Reversal"
    igst_amount: float = 0.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    cess_amount: float = 0.0

# ATADJ - Advance Tax Adjustment
class AdvanceTaxAdjustmentRequest(BaseModel):
    place_of_supply: str
    applicable_percent: float
    source: str
    igst_amount: float = 0.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    cess_amount: float = 0.0

# HSN - HSN Summary
class HSNSummaryRequest(BaseModel):
    hsn_code: str
    description: str
    uqc: str  # Unit Quantity Code
    total_quantity: float
    total_value: float
    taxable_value: float
    igst_amount: float = 0.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    cess_amount: float = 0.0
