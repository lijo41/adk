#!/usr/bin/env python3
"""
Complete End-to-End Test Script for GST Filing System
Tests all functionality from document upload to report generation.
"""

import requests
import json
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_document_upload():
    """Test document upload functionality."""
    print("🔄 Testing document upload...")
    
    # Check if test file exists
    test_file = "gst_invoice1.pdf"
    if not Path(test_file).exists():
        print(f"❌ Test file {test_file} not found")
        return None
    
    # Upload document
    with open(test_file, 'rb') as f:
        files = {'file': (test_file, f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    
    if response.status_code == 200:
        doc_data = response.json()
        print(f"✅ Document uploaded successfully: {doc_data['document_id']}")
        return doc_data['document_id']
    else:
        print(f"❌ Document upload failed: {response.text}")
        return None

def test_document_list():
    """Test document listing."""
    print("🔄 Testing document listing...")
    
    response = requests.get(f"{BASE_URL}/api/documents/")
    
    if response.status_code == 200:
        documents = response.json()
        print(f"✅ Found {len(documents)} documents")
        return documents
    else:
        print(f"❌ Document listing failed: {response.text}")
        return []

def test_chat_functionality(doc_id):
    """Test chat/Q&A functionality."""
    print("🔄 Testing chat functionality...")
    
    chat_request = {
        "question": "What is the invoice number and total amount?",
        "document_ids": [doc_id]
    }
    
    response = requests.post(f"{BASE_URL}/api/chat/ask", json=chat_request)
    
    if response.status_code == 200:
        chat_response = response.json()
        print(f"✅ Chat response: {chat_response.get('answer', 'No answer')[:100]}...")
        return chat_response
    else:
        print(f"❌ Chat failed: {response.text}")
        return None

def test_gstr1_creation():
    """Test GSTR-1 return creation."""
    print("🔄 Testing GSTR-1 return creation...")
    
    gstr1_request = {
        "gstin": "27ABCDE1234F1Z5",
        "company_name": "Test Company Ltd",
        "filing_period": "032024",
        "gross_turnover": 1000000.0
    }
    
    response = requests.post(f"{BASE_URL}/api/gstr1/create", json=gstr1_request)
    
    if response.status_code == 200:
        gstr1_data = response.json()
        print(f"✅ GSTR-1 return created: {gstr1_data['return_id']}")
        return gstr1_data['return_id']
    else:
        print(f"❌ GSTR-1 creation failed: {response.text}")
        return None

def test_gstr1_json_generation(return_id):
    """Test GSTR-1 JSON generation."""
    print("🔄 Testing GSTR-1 JSON generation...")
    
    response = requests.get(f"{BASE_URL}/api/gstr1/{return_id}/json")
    
    if response.status_code == 200:
        json_data = response.json()
        print("✅ GSTR-1 JSON generated successfully")
        print(f"   Structure: {list(json_data.keys())}")
        return json_data
    else:
        print(f"❌ GSTR-1 JSON generation failed: {response.text}")
        return None

def test_gstr1_list():
    """Test GSTR-1 returns listing."""
    print("🔄 Testing GSTR-1 returns listing...")
    
    response = requests.get(f"{BASE_URL}/api/gstr1/list")
    
    if response.status_code == 200:
        returns_data = response.json()
        print(f"✅ Found {returns_data.get('count', 0)} GSTR-1 returns")
        return returns_data
    else:
        print(f"❌ GSTR-1 listing failed: {response.text}")
        return None

def test_api_docs():
    """Test API documentation endpoint."""
    print("🔄 Testing API documentation...")
    
    response = requests.get(f"{BASE_URL}/docs")
    
    if response.status_code == 200:
        print("✅ API documentation accessible")
        return True
    else:
        print(f"❌ API documentation failed: {response.status_code}")
        return False

def main():
    """Run complete end-to-end test."""
    print("🚀 Starting Complete GST Filing System Test")
    print("=" * 50)
    
    # Test API availability
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("❌ Server not running. Please start with: uvicorn main:app --reload")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start with: uvicorn main:app --reload")
        return
    
    # Run tests
    test_results = {}
    
    # 1. Test document upload
    doc_id = test_document_upload()
    test_results['document_upload'] = doc_id is not None
    
    # 2. Test document listing
    documents = test_document_list()
    test_results['document_list'] = len(documents) > 0
    
    # 3. Test chat functionality (if document uploaded)
    if doc_id:
        chat_response = test_chat_functionality(doc_id)
        test_results['chat'] = chat_response is not None
    else:
        test_results['chat'] = False
        print("⏭️  Skipping chat test (no document uploaded)")
    
    # 4. Test GSTR-1 creation
    return_id = test_gstr1_creation()
    test_results['gstr1_creation'] = return_id is not None
    
    # 5. Test GSTR-1 JSON generation (if return created)
    if return_id:
        json_data = test_gstr1_json_generation(return_id)
        test_results['gstr1_json'] = json_data is not None
    else:
        test_results['gstr1_json'] = False
        print("⏭️  Skipping JSON generation test (no return created)")
    
    # 6. Test GSTR-1 listing
    returns_list = test_gstr1_list()
    test_results['gstr1_list'] = returns_list is not None
    
    # 7. Test API docs
    docs_available = test_api_docs()
    test_results['api_docs'] = docs_available
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():<20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        
        # Common issues and solutions
        print("\n💡 Common Issues:")
        if not test_results['document_upload'] or not test_results['chat']:
            print("   - Missing GOOGLE_API_KEY in .env file")
        if not test_results['gstr1_creation']:
            print("   - Database connection issues")
        if not test_results['api_docs']:
            print("   - Server not running properly")

if __name__ == "__main__":
    main()
