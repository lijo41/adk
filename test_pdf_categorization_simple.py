#!/usr/bin/env python3
"""
Simple test script to test GSTR-1 and GSTR-2 PDF categorization via API
"""
import requests
import json
import os

def test_pdf_upload_and_categorization():
    """Test uploading PDFs and running categorization via API"""
    
    # API endpoints
    base_url = "http://localhost:8000"
    upload_url = f"{base_url}/api/documents/upload"
    categorize_url = f"{base_url}/api/categorization/analyze"
    
    # PDF file paths
    gstr1_pdf = "/home/lijo/Documents/adk/server/gst_invoice1.pdf"
    gstr2_pdf = "/home/lijo/Documents/adk/server/gstr2.pdf"
    
    print("🔍 Testing PDF Upload and Categorization via API")
    print("=" * 55)
    
    # Check if files exist
    if not os.path.exists(gstr1_pdf):
        print(f"❌ GSTR-1 PDF not found: {gstr1_pdf}")
        return
    if not os.path.exists(gstr2_pdf):
        print(f"❌ GSTR-2 PDF not found: {gstr2_pdf}")
        return
    
    print(f"✅ Found GSTR-1 PDF: {os.path.basename(gstr1_pdf)}")
    print(f"✅ Found GSTR-2 PDF: {os.path.basename(gstr2_pdf)}")
    print()
    
    # Get auth token (using test token for now)
    token = "test_token"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    uploaded_doc_ids = []
    
    # Upload both PDFs
    for pdf_path, doc_type in [(gstr1_pdf, "GSTR-1"), (gstr2_pdf, "GSTR-2")]:
        print(f"📤 Uploading {doc_type} PDF...")
        
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
                response = requests.post(upload_url, files=files, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                doc_id = result.get('document_id')
                uploaded_doc_ids.append(doc_id)
                print(f"   ✅ {doc_type} uploaded successfully - ID: {doc_id}")
            else:
                print(f"   ❌ Upload failed: {response.status_code} - {response.text}")
                return
                
        except Exception as e:
            print(f"   ❌ Error uploading {doc_type}: {str(e)}")
            return
    
    print(f"\n📊 Total documents uploaded: {len(uploaded_doc_ids)}")
    print(f"Document IDs: {uploaded_doc_ids}")
    print()
    
    # Perform categorization
    print("🤖 Running AI Categorization...")
    try:
        categorize_payload = {
            "document_ids": uploaded_doc_ids
        }
        
        response = requests.post(
            categorize_url, 
            json=categorize_payload, 
            headers={**headers, "Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Categorization completed!")
            print()
            
            # Display results
            print("📋 CATEGORIZATION RESULTS")
            print("=" * 30)
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Processed Documents: {result.get('processed_documents', [])}")
            print(f"Total Chunks: {result.get('total_chunks', 0)}")
            print()
            
            # Get categorization data
            categorization = result.get('categorization', {})
            
            # Summary
            summary = categorization.get("categorization_summary", {})
            print("📊 SUMMARY")
            print("-" * 15)
            print(f"Total Chunks: {summary.get('total_chunks', 0)}")
            print(f"GSTR-1 Chunks: {summary.get('gstr1_chunks', 0)}")
            print(f"GSTR-2 Chunks: {summary.get('gstr2_chunks', 0)}")
            print(f"Irrelevant Chunks: {summary.get('irrelevant_chunks', 0)}")
            print(f"Overall Confidence: {summary.get('overall_confidence', 0):.2%}")
            print()
            
            # GSTR-1 Analysis
            gstr1_analysis = categorization.get("gstr1_analysis", {})
            print("📘 GSTR-1 ANALYSIS")
            print("-" * 18)
            print(f"Outward Supply Count: {gstr1_analysis.get('outward_supply_count', 0)}")
            print(f"Total Transactions: {gstr1_analysis.get('total_transactions', 0)}")
            print(f"Relevant Chunks: {len(gstr1_analysis.get('relevant_chunks', []))}")
            print()
            
            # GSTR-2 Analysis
            gstr2_analysis = categorization.get("gstr2_analysis", {})
            print("📗 GSTR-2 ANALYSIS")
            print("-" * 18)
            print(f"Inward Supply Count: {gstr2_analysis.get('inward_supply_count', 0)}")
            print(f"Total Transactions: {gstr2_analysis.get('total_transactions', 0)}")
            print(f"Relevant Chunks: {len(gstr2_analysis.get('relevant_chunks', []))}")
            print()
            
            # Chunk categorizations (first 5)
            chunk_categorizations = categorization.get("chunk_categorization", [])
            if chunk_categorizations:
                print("🔍 SAMPLE CHUNK CATEGORIZATIONS")
                print("-" * 32)
                for i, cat in enumerate(chunk_categorizations[:5]):
                    category = cat.get("category", "unknown")
                    confidence = cat.get("confidence", 0)
                    reasoning = cat.get("reasoning", "No reasoning")[:80]
                    print(f"Chunk {i+1}: {category.upper()} ({confidence:.1%}) - {reasoning}...")
                
                if len(chunk_categorizations) > 5:
                    print(f"... and {len(chunk_categorizations) - 5} more chunks")
            
            return result
            
        else:
            print(f"❌ Categorization failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Categorization error: {str(e)}")
        return None

if __name__ == "__main__":
    print("🚀 Starting PDF categorization test...")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    result = test_pdf_upload_and_categorization()
    if result:
        print("\n✅ Test completed successfully!")
        
        # Check if GSTR-1 agent is working
        categorization = result.get('categorization', {})
        gstr1_analysis = categorization.get('gstr1_analysis', {})
        gstr2_analysis = categorization.get('gstr2_analysis', {})
        
        print("\n🔧 AGENT STATUS CHECK")
        print("=" * 20)
        
        if gstr1_analysis.get('outward_supply_count', 0) > 0:
            print("✅ GSTR-1 Agent: Working correctly")
        else:
            print("⚠️  GSTR-1 Agent: May not be detecting outward supplies properly")
            
        if gstr2_analysis.get('inward_supply_count', 0) > 0:
            print("✅ GSTR-2 Agent: Working correctly")
        else:
            print("⚠️  GSTR-2 Agent: May not be detecting inward supplies properly")
            
    else:
        print("\n❌ Test failed!")
