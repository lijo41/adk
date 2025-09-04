#!/usr/bin/env python3
"""
Test script to verify filename preservation in document upload
"""
import requests
import os
import tempfile
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_FILENAME = "sample_invoice.txt"

def create_test_file():
    """Create a simple test text file"""
    # Create a temporary text file for testing
    test_content = """Invoice #12345
Date: 2024-01-15
From: Test Company Ltd.
To: Customer ABC

Items:
1. Product A - $100.00
2. Product B - $50.00

Total: $150.00
GST (18%): $27.00
Grand Total: $177.00"""
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w') as temp_file:
        temp_file.write(test_content)
        return temp_file.name

def test_login():
    """Test login and get auth token"""
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_upload_with_filename(token, test_file_path, original_filename):
    """Test document upload with specific filename"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Upload the file with original filename
    with open(test_file_path, 'rb') as f:
        files = {
            'file': (original_filename, f, 'text/plain')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/documents/upload",
            headers=headers,
            files=files
        )
    
    return response

def main():
    print("Testing filename preservation in document upload...")
    print("=" * 50)
    
    # Step 1: Create test file
    print("1. Creating test text file...")
    test_file_path = create_test_file()
    print(f"   Created: {test_file_path}")
    
    # Step 2: Login to get token
    print("\n2. Logging in to get auth token...")
    token = test_login()
    if not token:
        print("   ❌ Login failed - cannot proceed with test")
        return
    print("   ✅ Login successful")
    
    # Step 3: Test upload with original filename
    print(f"\n3. Testing upload with original filename: {TEST_FILENAME}")
    response = test_upload_with_filename(token, test_file_path, TEST_FILENAME)
    
    if response.status_code == 200:
        result = response.json()
        returned_filename = result.get("filename")
        
        print(f"   Upload successful!")
        print(f"   Original filename: {TEST_FILENAME}")
        print(f"   Returned filename: {returned_filename}")
        
        if returned_filename == TEST_FILENAME:
            print("   ✅ FILENAME PRESERVATION TEST PASSED!")
        else:
            print("   ❌ FILENAME PRESERVATION TEST FAILED!")
            print(f"   Expected: {TEST_FILENAME}")
            print(f"   Got: {returned_filename}")
    else:
        print(f"   ❌ Upload failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Cleanup
    print("\n4. Cleaning up...")
    if os.path.exists(test_file_path):
        os.unlink(test_file_path)
        print("   ✅ Test file cleaned up")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
