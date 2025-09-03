# GSTR1 Template Models - Pydantic data structures for GSTR1 templates
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator

class GST1HeaderDetails(BaseModel):
    gstin: str = ""
    company_name: str = ""
    filing_period: str = ""
    gross_turnover: float = 0
    return_period: str = ""
    filing_date: str = ""
    amendment: bool = False
    late_fee: float = 0

class GST1Recipient(BaseModel):
    gstin: str = ""
    legal_name: str = ""
    trade_name: str = ""
    address: str = ""
    state_code: str = ""
    pos: str = ""

class GST1Item(BaseModel):
    item_no: int
    product_name: str = ""
    description: str = ""
    hsn_code: str = ""
    quantity: float = 0
    unit: str = ""
    unit_price: float = 0
    discount: float = 0
    taxable_value: float = 0
    tax_rate: float = 0
    igst_rate: float = 0
    igst_amount: float = 0
    cgst_rate: float = 0
    cgst_amount: float = 0
    sgst_rate: float = 0
    sgst_amount: float = 0
    cess_rate: float = 0
    cess_amount: float = 0

class GST1InvoiceTotals(BaseModel):
    total_taxable_value: float = 0
    total_igst: float = 0
    total_cgst: float = 0
    total_sgst: float = 0
    total_cess: float = 0
    total_tax: float = 0
    total_invoice_value: float = 0

class GST1Invoice(BaseModel):
    invoice_no: str = ""
    invoice_date: str = ""
    invoice_value: float = 0
    place_of_supply: str = ""
    reverse_charge: bool = False
    invoice_type: str = "Regular"
    ecommerce_gstin: str = ""
    recipient: GST1Recipient = GST1Recipient()
    items: List[GST1Item] = []
    totals: GST1InvoiceTotals = GST1InvoiceTotals()
