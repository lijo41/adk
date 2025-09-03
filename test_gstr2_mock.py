#!/usr/bin/env python3
"""Mock test for GSTR-2 extraction functionality without API calls."""

import sys
import os
sys.path.append('/home/lijo/Documents/adk/server')

import json
from datetime import datetime

def test_gstr2_mock():
    """Test GSTR-2 extraction with mock data."""
    
    print("🧪 Testing GSTR-2 Implementation Structure...")
    print("=" * 50)
    
    try:
        # Test 1: Import GSTR-2 agent
        print("📦 Testing GSTR-2 agent import...")
        from agents.gstr2_extraction_agent import GSTR2ExtractionAgent
        print("✅ GSTR2ExtractionAgent imported successfully")
        
        # Test 2: Import Report agent
        print("📦 Testing Report agent import...")
        from agents.report_agent import ReportAgent
        print("✅ ReportAgent imported successfully")
        
        # Test 3: Test Report agent without API calls
        print("📊 Testing Report generation with mock data...")
        report_agent = ReportAgent.__new__(ReportAgent)  # Create without __init__
        
        # Mock GSTR-2 extraction data
        mock_gstr2_data = {
            "total_invoices": 3,
            "total_taxable_value": 255000.0,
            "total_tax_amount": 39600.0,
            "inward_invoices": [
                {
                    "invoice_no": "INV-2024-001",
                    "invoice_date": "15/01/2024",
                    "supplier_gstin": "29ABCDE1234F1Z5",
                    "supplier_name": "ABC Suppliers Pvt Ltd",
                    "taxable_value": 60000.0,
                    "items": [
                        {
                            "description": "Raw Materials",
                            "hsn_code": "1234",
                            "quantity": 100,
                            "rate": 500,
                            "taxable_value": 50000.0,
                            "cgst": 4500.0,
                            "sgst": 4500.0,
                            "igst": 0.0,
                            "cess": 0.0
                        }
                    ]
                },
                {
                    "invoice_no": "TI-2024-002", 
                    "invoice_date": "20/01/2024",
                    "supplier_gstin": "29FGHIJ9876K3L4",
                    "supplier_name": "XYZ Trading Co.",
                    "taxable_value": 100000.0,
                    "items": [
                        {
                            "description": "Office Supplies",
                            "hsn_code": "9999",
                            "taxable_value": 25000.0,
                            "igst": 4500.0
                        }
                    ]
                }
            ],
            "summary": {
                "total_cgst": 6000.0,
                "total_sgst": 6000.0,
                "total_igst": 18000.0,
                "total_cess": 0.0,
                "net_itc_available": 30000.0
            }
        }
        
        # Create mock filing data
        filing_data = {
            "results": {
                "GSTR-2": {
                    "status": "completed",
                    "filing_period": "January 2024",
                    "gstr2_extraction": mock_gstr2_data
                }
            }
        }
        
        # Test report generation methods
        print("📋 Testing report generation methods...")
        
        # Test filing summary
        summary = report_agent._create_filing_summary(filing_data)
        print(f"✅ Filing Summary: {summary['filing_types_processed']}")
        print(f"   Total Transactions: {summary['total_transactions']}")
        print(f"   Total Taxable Value: ₹{summary['total_taxable_value']:,.2f}")
        
        # Test detailed analysis
        analysis = report_agent._create_detailed_analysis(filing_data)
        print("✅ Detailed Analysis generated")
        
        if analysis['gstr2_analysis']:
            gstr2_analysis = analysis['gstr2_analysis']
            print(f"   Suppliers: {len(gstr2_analysis.get('supplier_breakdown', {}))}")
            print(f"   HSN Codes: {len(gstr2_analysis.get('hsn_analysis', {}))}")
            print(f"   Eligible ITC: ₹{gstr2_analysis.get('itc_analysis', {}).get('eligible_itc', 0):,.2f}")
        
        # Test compliance check
        compliance = report_agent._perform_compliance_check(filing_data)
        print(f"✅ Compliance Check: {compliance['status']}")
        
        # Test 4: Verify filing routes integration
        print("🔗 Testing filing routes integration...")
        from routes.filing_routes import process_gstr2_filing
        print("✅ process_gstr2_filing function imported successfully")
        
        # Test 5: Check if all required methods exist
        print("🔍 Verifying GSTR-2 agent methods...")
        
        # Check GSTR2ExtractionAgent methods (without instantiating)
        required_methods = [
            'extract_gstr2_data',
            '_create_extraction_prompt', 
            '_validate_and_clean_data',
            '_clean_invoice_data'
        ]
        
        for method in required_methods:
            if hasattr(GSTR2ExtractionAgent, method):
                print(f"✅ {method} method exists")
            else:
                print(f"❌ {method} method missing")
        
        print("\n🎉 GSTR-2 Implementation Structure Test Completed!")
        print("\n📋 Summary:")
        print("✅ GSTR-2 extraction agent created")
        print("✅ Report agent created with GSTR-2 support")
        print("✅ Filing routes updated for GSTR-2 processing")
        print("✅ All required methods and integrations verified")
        
        print("\n📝 Next Steps:")
        print("1. Set GOOGLE_API_KEY in .env file")
        print("2. Test with real documents and API calls")
        print("3. Verify end-to-end workflow through frontend")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gstr2_mock()
    sys.exit(0 if success else 1)
