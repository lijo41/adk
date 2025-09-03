#!/usr/bin/env python3
"""Check database contents for GSTR-1 data."""

from database import SessionLocal
from schemas import GSTR1Return, Invoice, InvoiceItem, GSTR1Summary

def check_database():
    """Check what's stored in the database."""
    db = SessionLocal()
    try:
        # Check GSTR1 Returns
        returns = db.query(GSTR1Return).all()
        print(f"GSTR1 Returns in database: {len(returns)}")
        
        for gstr1_return in returns:
            print(f"\nReturn ID: {gstr1_return.id}")
            print(f"GSTIN: {gstr1_return.gstin}")
            print(f"Company: {gstr1_return.company_name}")
            print(f"Filing Period: {gstr1_return.filing_period}")
            print(f"Status: {gstr1_return.status}")
            print(f"Created: {gstr1_return.created_at}")
            
            # Check invoices for this return
            invoices = db.query(Invoice).filter(Invoice.gstr1_id == gstr1_return.id).all()
            print(f"Invoices: {len(invoices)}")
            
            for invoice in invoices:
                print(f"  Invoice No: {invoice.invoice_no}")
                print(f"  Date: {invoice.invoice_date}")
                print(f"  Recipient GSTIN: {invoice.recipient_gstin}")
                print(f"  Value: {invoice.invoice_value}")
                
                # Check items for this invoice
                items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).all()
                print(f"  Items: {len(items)}")
                
                for item in items:
                    print(f"    Product: {item.product_name}")
                    print(f"    HSN: {item.hsn_code}")
                    print(f"    Quantity: {item.quantity}")
                    print(f"    Taxable Value: {item.taxable_value}")
                    print(f"    IGST: {item.igst}")
            
            # Check summary
            summary = db.query(GSTR1Summary).filter(GSTR1Summary.gstr1_id == gstr1_return.id).first()
            if summary:
                print(f"Summary:")
                print(f"  Total Invoices: {summary.total_invoices}")
                print(f"  Total Taxable Value: {summary.total_taxable_value}")
                print(f"  Total Tax: {summary.total_tax}")
                print(f"  Total Invoice Value: {summary.total_invoice_value}")
            
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
