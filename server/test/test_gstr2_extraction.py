#!/usr/bin/env python3
"""Test script for GSTR-2 extraction functionality."""

import sys
import os
sys.path.append('/home/lijo/Documents/adk/server')

from agents.gstr2_extraction_agent import GSTR2ExtractionAgent
from agents.report_agent import ReportAgent
import json

def test_gstr2_extraction():
    """Test GSTR-2 extraction with sample data."""
    
    # Sample inward supply invoice data (chunks)
    sample_chunks = [
        """
        INVOICE
        Invoice No: INV-2024-001
        Date: 15/01/2024
        
        From: ABC Suppliers Pvt Ltd
        GSTIN: 29ABCDE1234F1Z5
        Address: 123 Main Street, Bangalore
        
        To: Test Company
        GSTIN: 27PQRST5678G2H9
        
        Items:
        1. Raw Materials - HSN: 1234 - Qty: 100 - Rate: 500 - Amount: 50,000
           CGST @ 9%: 4,500
           SGST @ 9%: 4,500
           Total: 59,000
        
        2. Packaging Material - HSN: 5678 - Qty: 50 - Rate: 200 - Amount: 10,000
           CGST @ 6%: 600
           SGST @ 6%: 600
           Total: 11,200
        
        Total Invoice Value: 70,200
        """,
        
        """
        TAX INVOICE
        Invoice Number: TI-2024-002
        Invoice Date: 20/01/2024
        
        Supplier: XYZ Trading Co.
        GSTIN: 29FGHIJ9876K3L4
        
        Recipient: Test Company
        GSTIN: 27PQRST5678G2H9
        
        Description of Goods:
        - Office Supplies (HSN: 9999) - Taxable Value: 25,000
          IGST @ 18%: 4,500
        
        - Computer Equipment (HSN: 8471) - Taxable Value: 75,000
          IGST @ 18%: 13,500
        
        Total Taxable Value: 100,000
        Total Tax: 18,000
        Invoice Total: 118,000
        """,
        
        """
        PURCHASE INVOICE
        Ref: PI-JAN-003
        Date: 25/01/2024
        
        Vendor: DEF Industries Ltd
        GSTIN: 29MNOPQ4567R8S9
        
        Buyer: Test Company
        GSTIN: 27PQRST5678G2H9
        
        Items Purchased:
        1. Steel Rods (HSN: 7213) - Value: 80,000
           CGST: 7,200 (9%)
           SGST: 7,200 (9%)
        
        2. Cement (HSN: 2523) - Value: 30,000
           CGST: 1,500 (5%)
           SGST: 1,500 (5%)
        
        Total Purchase Value: 127,400
        """
    ]
    
    print("🧪 Testing GSTR-2 Extraction Agent...")
    print("=" * 50)
    
    try:
        # Initialize GSTR-2 agent
        gstr2_agent = GSTR2ExtractionAgent()
        
        # Extract GSTR-2 data
        print("📄 Processing sample inward supply invoices...")
        extraction_result = gstr2_agent.extract_gstr2_data(
            chunks=sample_chunks,
            filing_period="January 2024"
        )
        
        print("\n✅ GSTR-2 Extraction Results:")
        print(json.dumps(extraction_result, indent=2))
        
        # Test report generation
        print("\n📊 Testing Report Generation...")
        report_agent = ReportAgent()
        
        # Create mock filing data structure
        filing_data = {
            "results": {
                "GSTR-2": {
                    "status": "completed",
                    "filing_period": "January 2024",
                    "gstr2_extraction": extraction_result
                }
            }
        }
        
        report = report_agent.generate_filing_report(filing_data)
        
        print("\n📋 Generated Report Summary:")
        print(f"Report ID: {report['report_id']}")
        print(f"Filing Types: {report['filing_summary']['filing_types_processed']}")
        print(f"Total Transactions: {report['filing_summary']['total_transactions']}")
        print(f"Total Taxable Value: ₹{report['filing_summary']['total_taxable_value']:,.2f}")
        print(f"Total Tax Amount: ₹{report['filing_summary']['total_tax_amount']:,.2f}")
        
        # Show detailed analysis
        if report['detailed_analysis']['gstr2_analysis']:
            gstr2_analysis = report['detailed_analysis']['gstr2_analysis']
            print(f"\n📈 GSTR-2 Analysis:")
            print(f"Suppliers: {len(gstr2_analysis.get('supplier_breakdown', {}))}")
            print(f"HSN Codes: {len(gstr2_analysis.get('hsn_analysis', {}))}")
            print(f"Eligible ITC: ₹{gstr2_analysis.get('itc_analysis', {}).get('eligible_itc', 0):,.2f}")
        
        # Show compliance status
        compliance = report['compliance_check']
        print(f"\n✅ Compliance Status: {compliance['status'].upper()}")
        if compliance['issues']:
            print(f"Issues Found: {len(compliance['issues'])}")
        if compliance['warnings']:
            print(f"Warnings: {len(compliance['warnings'])}")
        
        print("\n🎉 GSTR-2 extraction and reporting test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gstr2_extraction()
    sys.exit(0 if success else 1)
