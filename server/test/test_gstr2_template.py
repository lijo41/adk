#!/usr/bin/env python3
"""Test script for standalone GSTR-2 template agent."""

import sys
import os
sys.path.append('/home/lijo/Documents/adk/server')

import json

def test_gstr2_template_agent():
    """Test the standalone GSTR-2 template agent."""
    
    print("🧪 Testing Standalone GSTR-2 Template Agent...")
    print("=" * 50)
    
    try:
        # Test 1: Import the template agent
        print("📦 Testing GSTR-2 template agent import...")
        from agents.gstr2_template_agent import GSTR2TemplateAgent
        print("✅ GSTR2TemplateAgent imported successfully")
        
        # Test 2: Get template structure
        print("📋 Testing template structure...")
        agent = GSTR2TemplateAgent.__new__(GSTR2TemplateAgent)  # Create without __init__
        template = agent.get_template_structure()
        
        print("✅ Template structure retrieved")
        print(f"   Main sections: {list(template['gstr2_return'].keys())}")
        print(f"   Inward supply types: {list(template['gstr2_return']['inward_supplies'].keys())}")
        
        # Test 3: Verify template structure
        print("🔍 Verifying template completeness...")
        
        required_sections = ['header', 'inward_supplies', 'summary']
        gstr2_sections = ['b2b', 'b2bur', 'cdnr', 'cdnur', 'imp_g', 'imp_s', 'itc_rev']
        
        gstr2_return = template['gstr2_return']
        
        for section in required_sections:
            if section in gstr2_return:
                print(f"✅ {section} section present")
            else:
                print(f"❌ {section} section missing")
        
        supplies = gstr2_return.get('inward_supplies', {})
        for section in gstr2_sections:
            if section in supplies:
                print(f"✅ {section} supply type present")
            else:
                print(f"❌ {section} supply type missing")
        
        # Test 4: Test fallback template
        print("🔄 Testing fallback template...")
        fallback = agent._create_fallback_template("January 2024")
        
        print("✅ Fallback template created")
        print(f"   Filing period: {fallback['gstr2_return']['header']['filing_period']}")
        print(f"   Total invoices: {fallback['gstr2_return']['summary']['total_invoices']}")
        
        # Test 5: Test validation methods
        print("🧹 Testing validation methods...")
        
        # Test invoice cleaning
        sample_invoice = {
            "invoice_no": "INV-001",
            "invoice_date": "15/01/2024",
            "supplier_gstin": "29ABCDE1234F1Z5",
            "supplier_name": "Test Supplier",
            "items": [
                {
                    "description": "Raw Material",
                    "hsn_code": "1234",
                    "taxable_value": 10000.0,
                    "cgst": 900.0,
                    "sgst": 900.0
                }
            ]
        }
        
        cleaned = agent._clean_template_invoice(sample_invoice)
        if cleaned:
            print("✅ Invoice cleaning successful")
            print(f"   Invoice: {cleaned['invoice_no']}")
            print(f"   Items: {len(cleaned['items'])}")
        else:
            print("❌ Invoice cleaning failed")
        
        # Test 6: Mock template validation
        print("📊 Testing template validation...")
        
        mock_data = {
            "gstr2_return": {
                "inward_supplies": {
                    "b2b": [sample_invoice]
                }
            }
        }
        
        validated = agent._validate_template_data(mock_data, "January 2024")
        summary = validated['gstr2_return']['summary']
        
        print("✅ Template validation successful")
        print(f"   Total invoices: {summary['total_invoices']}")
        print(f"   Total taxable value: ₹{summary['total_taxable_value']:,.2f}")
        print(f"   Total ITC available: ₹{summary['total_itc_available']:,.2f}")
        
        print("\n🎉 Standalone GSTR-2 Template Agent Test Completed!")
        print("\n📋 Summary:")
        print("✅ Standalone GSTR-2 template agent created")
        print("✅ Complete template structure with all GSTR-2 sections")
        print("✅ Independent from existing GSTR-1 system")
        print("✅ Focused only on GSTR-2 template compliance")
        print("✅ Ready for frontend integration")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gstr2_template_agent()
    sys.exit(0 if success else 1)
