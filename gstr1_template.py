# gstr1_template.py - GSTR1 JSON Template and Validation
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
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

def get_empty_gstr1_template() -> Dict[str, Any]:
    """Returns an empty GSTR1 template structure."""
    return {
        "gstr1_return": {
            "header": {
                "gstin": "",
                "company_name": "",
                "filing_period": "",
                "gross_turnover": 0,
                "return_period": "",
                "filing_date": "",
                "amendment": False,
                "late_fee": 0
            },
            "b2b_supplies": {
                "section": "4A, 4B, 4C, 6C",
                "description": "Business to Business Supplies",
                "invoices": [],
                "summary": {
                    "total_invoices": 0,
                    "total_taxable_value": 0,
                    "total_tax_amount": 0,
                    "total_invoice_value": 0
                }
            },
            "b2cl_supplies": {
                "section": "5A, 5B",
                "description": "Business to Consumer Large (>2.5L) Supplies",
                "invoices": []
            },
            "b2cs_supplies": {
                "section": "7",
                "description": "Business to Consumer Small (<2.5L) Supplies",
                "consolidated_data": []
            },
            "zero_rated_supplies": {
                "exports": {
                    "section": "8A",
                    "description": "Exports with Payment of Tax",
                    "invoices": []
                },
                "supplies_to_sez": {
                    "section": "8B",
                    "description": "Supplies to SEZ with Payment of Tax",
                    "invoices": []
                },
                "deemed_exports": {
                    "section": "8C",
                    "description": "Deemed Exports",
                    "invoices": []
                }
            },
            "nil_exempt_supplies": {
                "section": "9",
                "description": "Nil Rated, Exempted and Non-GST Supplies",
                "details": [
                    {
                        "description": "Nil Rated Supplies",
                        "inter_state": 0,
                        "intra_state": 0
                    },
                    {
                        "description": "Exempted Supplies",
                        "inter_state": 0,
                        "intra_state": 0
                    },
                    {
                        "description": "Non-GST Supplies",
                        "inter_state": 0,
                        "intra_state": 0
                    }
                ]
            },
            "credit_debit_notes": {
                "registered": {
                    "section": "9B",
                    "description": "Credit/Debit Notes (Registered)",
                    "notes": []
                },
                "unregistered": {
                    "section": "9C",
                    "description": "Credit/Debit Notes (Unregistered)",
                    "notes": []
                }
            },
            "hsn_summary": {
                "section": "12",
                "description": "HSN-wise Summary of Outward Supplies",
                "hsn_data": []
            },
            "documents_issued": {
                "section": "13",
                "description": "Documents Issued During the Tax Period",
                "document_details": [
                    {
                        "sr_no": 1,
                        "nature_of_document": "Invoices for outward supply",
                        "from_serial_no": "",
                        "to_serial_no": "",
                        "total_number": 0,
                        "cancelled": 0
                    }
                ]
            },
            "amendments": {
                "description": "Amendment Details",
                "amended_invoices": [],
                "amendment_summary": {
                    "total_amendments": 0,
                    "net_tax_liability_change": 0
                }
            },
            "overall_summary": {
                "total_taxable_value": 0,
                "total_igst": 0,
                "total_cgst": 0,
                "total_sgst": 0,
                "total_cess": 0,
                "total_tax_liability": 0,
                "total_invoices": 0,
                "filing_status": "Draft",
                "validation_errors": [],
                "warnings": []
            }
        }
    }

def validate_gstr1_data(gstr1_data: Dict[str, Any]) -> List[str]:
    """Validate GSTR1 data and return list of errors."""
    errors = []
    
    try:
        header = gstr1_data.get("gstr1_return", {}).get("header", {})
        
        # Validate header fields
        if not header.get("gstin"):
            errors.append("GSTIN is required in header")
        if not header.get("company_name"):
            errors.append("Company name is required in header")
        if not header.get("filing_period"):
            errors.append("Filing period is required in header")
            
        # Validate B2B invoices
        b2b_invoices = gstr1_data.get("gstr1_return", {}).get("b2b_supplies", {}).get("invoices", [])
        for i, invoice in enumerate(b2b_invoices):
            if not invoice.get("invoice_no"):
                errors.append(f"Invoice number missing for B2B invoice {i+1}")
            if not invoice.get("invoice_date"):
                errors.append(f"Invoice date missing for B2B invoice {i+1}")
            if not invoice.get("recipient", {}).get("gstin"):
                errors.append(f"Recipient GSTIN missing for B2B invoice {i+1}")
                
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
    
    return errors

def calculate_gstr1_totals(gstr1_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate and update totals in GSTR1 data."""
    try:
        # Calculate B2B totals
        b2b_supplies = gstr1_data["gstr1_return"]["b2b_supplies"]
        total_invoices = len(b2b_supplies["invoices"])
        total_taxable_value = 0
        total_tax_amount = 0
        total_invoice_value = 0
        
        for invoice in b2b_supplies["invoices"]:
            total_taxable_value += invoice.get("totals", {}).get("total_taxable_value", 0)
            total_tax_amount += invoice.get("totals", {}).get("total_tax", 0)
            total_invoice_value += invoice.get("invoice_value", 0)
        
        # Update B2B summary
        b2b_supplies["summary"] = {
            "total_invoices": total_invoices,
            "total_taxable_value": total_taxable_value,
            "total_tax_amount": total_tax_amount,
            "total_invoice_value": total_invoice_value
        }
        
        # Update overall summary
        gstr1_data["gstr1_return"]["overall_summary"].update({
            "total_taxable_value": total_taxable_value,
            "total_tax_liability": total_tax_amount,
            "total_invoices": total_invoices
        })
        
        # Update document details
        if gstr1_data["gstr1_return"]["documents_issued"]["document_details"]:
            gstr1_data["gstr1_return"]["documents_issued"]["document_details"][0]["total_number"] = total_invoices
            
    except Exception as e:
        print(f"Error calculating totals: {str(e)}")
    
    return gstr1_data
