#!/usr/bin/env python3
"""
Test GSTR-2 filing workflow end-to-end
"""

import requests
import json
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_FILES = {
    "gstr1": "gst_invoice1.pdf",
    "gstr2": "gstr2.pdf"
}

def test_gstr2_filing():
    """Test complete GSTR-2 filing workflow"""
    
    print("🧪 GSTR-2 Filing Workflow Test")
    print("=" * 50)
    
    # Step 1: Login
    print("1. Authenticating...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # Step 2: Upload documents
    print("\n2. Uploading documents...")
    document_ids = []
    
    for doc_type, filename in TEST_FILES.items():
        file_path = Path("server") / filename
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue
            
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            upload_response = requests.post(
                f"{BASE_URL}/api/documents/upload",
                files=files,
                headers=headers
            )
            
        if upload_response.status_code == 200:
            doc_id = upload_response.json()["document_id"]
            document_ids.append(doc_id)
            print(f"✅ Uploaded {filename}: {doc_id}")
        else:
            print(f"❌ Upload failed for {filename}: {upload_response.status_code}")
    
    if len(document_ids) < 2:
        print("❌ Need both GSTR-1 and GSTR-2 documents")
        return False
    
    # Step 3: Categorize documents
    print("\n3. Running categorization...")
    categorization_response = requests.post(
        f"{BASE_URL}/api/categorization/analyze",
        json={"document_ids": document_ids},
        headers=headers
    )
    
    if categorization_response.status_code != 200:
        print(f"❌ Categorization failed: {categorization_response.status_code}")
        return False
    
    categorization_results = categorization_response.json()
    print("✅ Categorization completed")
    print(f"   GSTR-1 chunks: {len(categorization_results.get('gstr1_chunks', []))}")
    print(f"   GSTR-2 chunks: {len(categorization_results.get('gstr2_chunks', []))}")
    
    # Step 4: Submit filing with GSTR-2 focus
    print("\n4. Submitting GSTR-2 filing...")
    filing_payload = {
        "document_ids": document_ids,
        "analysis_session_id": categorization_results.get("session_id", "test-session"),
        "filing_types": {
            "GSTR-1": {"month": "August", "year": "2025"},
            "GSTR-2": {"month": "August", "year": "2025"}
        },
        "categorization_results": categorization_results
    }
    
    filing_response = requests.post(
        f"{BASE_URL}/api/filing/submit",
        json=filing_payload,
        headers=headers
    )
    
    if filing_response.status_code != 200:
        print(f"❌ Filing failed: {filing_response.status_code}")
        print(f"Response: {filing_response.text}")
        return False
    
    filing_results = filing_response.json()
    print("✅ Filing submitted successfully")
    
    # Step 5: Analyze GSTR-2 results
    print("\n5. GSTR-2 Results Analysis:")
    print("-" * 30)
    
    # Debug: Print full response structure
    print("Full filing results keys:", list(filing_results.get("results", {}).keys()))
    
    gstr2_data = filing_results.get("results", {}).get("GSTR-2", {})
    gstr2_extraction = gstr2_data.get("gstr2_extraction", gstr2_data)
    
    print(f"Status: {gstr2_extraction.get('status', 'Unknown')}")
    print(f"Total Invoices: {gstr2_extraction.get('total_invoices', 0)}")
    print(f"Total Taxable Value: ₹{gstr2_extraction.get('total_taxable_value', 0):,.2f}")
    print(f"Total Tax: ₹{gstr2_extraction.get('total_tax_amount', 0):,.2f}")
    
    # Check if we have actual invoice data
    invoices = gstr2_extraction.get('inward_invoices', [])
    if invoices:
        print(f"\n📋 Invoice Details:")
        for i, invoice in enumerate(invoices[:3], 1):  # Show first 3 invoices
            print(f"   Invoice {i}:")
            print(f"     Number: {invoice.get('invoice_no', 'N/A')}")
            print(f"     Date: {invoice.get('invoice_date', 'N/A')}")
            print(f"     Supplier: {invoice.get('supplier_gstin', 'N/A')}")
            print(f"     Value: ₹{invoice.get('invoice_value', 0):,.2f}")
    else:
        print("⚠️  No invoices extracted")
    
    # Success criteria
    success = (
        gstr2_extraction.get('status') == 'completed' and
        gstr2_extraction.get('total_invoices', 0) > 0 and
        len(invoices) > 0
    )
    
    if success:
        print("\n🎉 GSTR-2 filing test PASSED!")
        print("   ✅ JSON parsing working")
        print("   ✅ Invoice data extracted")
        print("   ✅ Structured output generated")
    else:
        print("\n❌ GSTR-2 filing test FAILED!")
        print("   Issues detected in extraction or data structure")
    
    return success

if __name__ == "__main__":
    test_gstr2_filing()
