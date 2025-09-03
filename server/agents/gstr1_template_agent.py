# GSTR1 Template Agent - Template generation and validation functions
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from models.gstr1_template import GST1HeaderDetails, GST1Recipient, GST1Item, GST1InvoiceTotals, GST1Invoice

def get_empty_gstr1_template() -> Dict[str, Any]:
    """Returns a simplified GSTR1 template structure."""
    return {
        "gstr1_return": {
            "header": {
                "gstin": "",
                "company_name": "",
                "filing_period": ""
            },
            "invoices": [],
            "summary": {
                "total_invoices": 0,
                "total_taxable_value": 0,
                "total_tax": 0,
                "total_invoice_value": 0
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
