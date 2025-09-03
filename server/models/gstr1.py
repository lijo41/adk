"""GSTR-1 data models."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal


@dataclass
class B2BItem:
    """B2B invoice line item."""
    sr_no: int
    description: str
    hsn_code: str
    quantity: Decimal
    unit: str
    rate: Decimal
    taxable_value: Decimal
    cgst_rate: Decimal
    cgst_amount: Decimal
    sgst_rate: Decimal
    sgst_amount: Decimal
    igst_rate: Decimal
    igst_amount: Decimal
    cess_rate: Decimal = Decimal('0')
    cess_amount: Decimal = Decimal('0')


@dataclass
class B2BInvoice:
    """B2B invoice model."""
    invoice_number: str
    invoice_date: str
    invoice_value: Decimal
    place_of_supply: str
    reverse_charge: str
    invoice_type: str
    recipient_gstin: str
    recipient_name: str
    recipient_state: str
    items: List[B2BItem]
    
    @property
    def total_taxable_value(self) -> Decimal:
        return sum(item.taxable_value for item in self.items)
    
    @property
    def total_tax_amount(self) -> Decimal:
        return sum(
            item.cgst_amount + item.sgst_amount + item.igst_amount + item.cess_amount 
            for item in self.items
        )


@dataclass
class HSNSummary:
    """HSN-wise summary."""
    hsn_code: str
    description: str
    uqc: str
    total_quantity: Decimal
    total_value: Decimal
    taxable_value: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    cess_amount: Decimal


@dataclass
class GSTR1Header:
    """GSTR-1 return header."""
    gstin: str
    company_name: str
    filing_period: str
    return_period: str
    filing_date: str
    gross_turnover: Decimal
    status: str = "draft"


@dataclass
class GSTR1Return:
    """Complete GSTR-1 return."""
    id: str
    header: GSTR1Header
    b2b_invoices: List[B2BInvoice]
    hsn_summary: List[HSNSummary]
    created_time: datetime
    updated_time: Optional[datetime] = None
    json_data: Optional[Dict[str, Any]] = None
    
    @property
    def total_b2b_value(self) -> Decimal:
        return sum(invoice.invoice_value for invoice in self.b2b_invoices)
    
    @property
    def total_taxable_value(self) -> Decimal:
        return sum(invoice.total_taxable_value for invoice in self.b2b_invoices)
