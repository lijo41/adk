#!/usr/bin/env python3
"""
Test script to upload and categorize actual GSTR-1 and GSTR-2 PDFs
"""
import requests
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/lijo/Documents/adk/server/.env')

# Add server path for imports
sys.path.append('/home/lijo/Documents/adk/server')

from agents.document_processing_agent import DocumentProcessingAgent
from agents.categorization_agent import CategorizationAgent

def test_pdf_categorization():
    """Test categorization with actual GSTR-1 and GSTR-2 PDFs"""
    
    # Initialize agents
    doc_agent = DocumentProcessingAgent()
    cat_agent = CategorizationAgent()
    
    # PDF file paths
    gstr1_pdf = "/home/lijo/Documents/adk/server/gst_invoice1.pdf"
    gstr2_pdf = "/home/lijo/Documents/adk/server/gstr2.pdf"
    
    print("🔍 Testing PDF Categorization")
    print("=" * 50)
    
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
    
    # Process both PDFs
    all_chunks = []
    chunk_metadata = []
    
    for pdf_path, doc_type in [(gstr1_pdf, "GSTR-1"), (gstr2_pdf, "GSTR-2")]:
        print(f"📄 Processing {doc_type} PDF...")
        
        try:
            # Process document
            doc_id = doc_agent.process_document(pdf_path)
            chunks = doc_agent.get_document_chunks(doc_id)
            
            print(f"   - Document ID: {doc_id}")
            print(f"   - Chunks created: {len(chunks)}")
            
            # Add chunks to combined list
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata.append({
                    "chunk_index": len(all_chunks) - 1,
                    "source_document": os.path.basename(pdf_path),
                    "document_type": doc_type,
                    "chunk_id": f"{doc_id}_chunk_{i}"
                })
            
            print(f"   ✅ {doc_type} processed successfully")
            
        except Exception as e:
            print(f"   ❌ Error processing {doc_type}: {str(e)}")
            return
    
    print(f"\n📊 Total chunks for categorization: {len(all_chunks)}")
    print()
    
    # Perform categorization
    print("🤖 Running AI Categorization...")
    try:
        categorization_result = cat_agent.categorize_chunks(all_chunks)
        
        print("✅ Categorization completed!")
        print()
        
        # Display results
        print("📋 CATEGORIZATION RESULTS")
        print("=" * 30)
        
        # Summary
        summary = categorization_result.get("categorization_summary", {})
        print(f"Total Chunks: {summary.get('total_chunks', 0)}")
        print(f"GSTR-1 Chunks: {summary.get('gstr1_chunks', 0)}")
        print(f"GSTR-2 Chunks: {summary.get('gstr2_chunks', 0)}")
        print(f"Irrelevant Chunks: {summary.get('irrelevant_chunks', 0)}")
        print(f"Overall Confidence: {summary.get('overall_confidence', 0):.2%}")
        print()
        
        # Per-document breakdown
        chunk_categorizations = categorization_result.get("chunk_categorization", [])
        doc_breakdown = {}
        
        for i, categorization in enumerate(chunk_categorizations):
            if i < len(chunk_metadata):
                source_doc = chunk_metadata[i]["source_document"]
                category = categorization.get("category", "irrelevant")
                confidence = categorization.get("confidence", 0)
                
                if source_doc not in doc_breakdown:
                    doc_breakdown[source_doc] = {
                        "gstr1": 0, "gstr2": 0, "irrelevant": 0, "total": 0
                    }
                
                doc_breakdown[source_doc][category] += 1
                doc_breakdown[source_doc]["total"] += 1
        
        print("📄 PER-DOCUMENT BREAKDOWN")
        print("-" * 25)
        for doc, stats in doc_breakdown.items():
            print(f"{doc}:")
            print(f"  - GSTR-1: {stats['gstr1']} chunks")
            print(f"  - GSTR-2: {stats['gstr2']} chunks") 
            print(f"  - Irrelevant: {stats['irrelevant']} chunks")
            print(f"  - Total: {stats['total']} chunks")
            print()
        
        # Detailed chunk analysis
        print("🔍 DETAILED CHUNK ANALYSIS")
        print("-" * 25)
        for i, categorization in enumerate(chunk_categorizations[:10]):  # Show first 10
            if i < len(chunk_metadata):
                metadata = chunk_metadata[i]
                category = categorization.get("category", "unknown")
                confidence = categorization.get("confidence", 0)
                reasoning = categorization.get("reasoning", "No reasoning provided")
                
                print(f"Chunk {i+1} ({metadata['source_document']}):")
                print(f"  Category: {category.upper()}")
                print(f"  Confidence: {confidence:.2%}")
                print(f"  Reasoning: {reasoning[:100]}...")
                print()
        
        if len(chunk_categorizations) > 10:
            print(f"... and {len(chunk_categorizations) - 10} more chunks")
        
        # Test GSTR-1 analysis
        print("\n🔧 Testing GSTR-1 Analysis...")
        gstr1_analysis = categorization_result.get("gstr1_analysis", {})
        print(f"Outward Supply Count: {gstr1_analysis.get('outward_supply_count', 0)}")
        print(f"Total Transactions: {gstr1_analysis.get('total_transactions', 0)}")
        print(f"Relevant Chunks: {len(gstr1_analysis.get('relevant_chunks', []))}")
        
        # Test GSTR-2 analysis  
        print("\n🔧 Testing GSTR-2 Analysis...")
        gstr2_analysis = categorization_result.get("gstr2_analysis", {})
        print(f"Inward Supply Count: {gstr2_analysis.get('inward_supply_count', 0)}")
        print(f"Total Transactions: {gstr2_analysis.get('total_transactions', 0)}")
        print(f"Relevant Chunks: {len(gstr2_analysis.get('relevant_chunks', []))}")
        
        return categorization_result
        
    except Exception as e:
        print(f"❌ Categorization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_pdf_categorization()
    if result:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
