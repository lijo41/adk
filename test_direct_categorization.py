#!/usr/bin/env python3
"""
Direct test of GSTR-1 and GSTR-2 PDF categorization using the agents directly
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/lijo/Documents/adk/server/.env')

# Add server path for imports
sys.path.append('/home/lijo/Documents/adk/server')

from agents.categorization_agent import CategorizationAgent
from markitdown import MarkItDown

def process_pdf_to_chunks(pdf_path, chunk_size=1500, overlap=200):
    """Convert PDF to text chunks using MarkItDown"""
    try:
        md = MarkItDown()
        result = md.convert(pdf_path)
        text = result.text_content
        
        # Create chunks
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
            
        return chunks
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {str(e)}")
        return []

def test_direct_categorization():
    """Test categorization directly with PDF files"""
    
    # PDF file paths
    gstr1_pdf = "/home/lijo/Documents/adk/server/gst_invoice1.pdf"
    gstr2_pdf = "/home/lijo/Documents/adk/server/gstr2.pdf"
    
    print("🔍 Direct PDF Categorization Test")
    print("=" * 40)
    
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
    
    # Process PDFs to chunks
    all_chunks = []
    chunk_metadata = []
    
    for pdf_path, doc_type in [(gstr1_pdf, "GSTR-1"), (gstr2_pdf, "GSTR-2")]:
        print(f"📄 Processing {doc_type} PDF...")
        
        chunks = process_pdf_to_chunks(pdf_path)
        print(f"   - Chunks created: {len(chunks)}")
        
        # Add to combined list
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            chunk_metadata.append({
                "chunk_index": len(all_chunks) - 1,
                "source_document": os.path.basename(pdf_path),
                "document_type": doc_type,
                "chunk_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
            })
        
        print(f"   ✅ {doc_type} processed successfully")
    
    print(f"\n📊 Total chunks for categorization: {len(all_chunks)}")
    print()
    
    # Initialize categorization agent
    print("🤖 Initializing Categorization Agent...")
    try:
        cat_agent = CategorizationAgent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization failed: {str(e)}")
        return
    
    # Perform categorization
    print("\n🔄 Running AI Categorization...")
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
        print(f"Ambiguous Processed: {summary.get('ambiguous_chunks_processed', 0)}")
        print(f"Overall Confidence: {summary.get('overall_confidence', 0):.2%}")
        print()
        
        # GSTR-1 Analysis
        gstr1_analysis = categorization_result.get("gstr1_analysis", {})
        print("📘 GSTR-1 ANALYSIS")
        print("-" * 18)
        print(f"Outward Supply Count: {gstr1_analysis.get('outward_supply_count', 0)}")
        print(f"Total Transactions: {gstr1_analysis.get('total_transactions', 0)}")
        print(f"Relevant Chunks: {len(gstr1_analysis.get('relevant_chunks', []))}")
        
        if gstr1_analysis.get('outward_supply_count', 0) == 0:
            print("⚠️  WARNING: GSTR-1 agent found no outward supplies!")
        else:
            print("✅ GSTR-1 agent working correctly")
        print()
        
        # GSTR-2 Analysis
        gstr2_analysis = categorization_result.get("gstr2_analysis", {})
        print("📗 GSTR-2 ANALYSIS")
        print("-" * 18)
        print(f"Inward Supply Count: {gstr2_analysis.get('inward_supply_count', 0)}")
        print(f"Total Transactions: {gstr2_analysis.get('total_transactions', 0)}")
        print(f"Relevant Chunks: {len(gstr2_analysis.get('relevant_chunks', []))}")
        
        if gstr2_analysis.get('inward_supply_count', 0) == 0:
            print("⚠️  WARNING: GSTR-2 agent found no inward supplies!")
        else:
            print("✅ GSTR-2 agent working correctly")
        print()
        
        # Per-document breakdown
        chunk_categorizations = categorization_result.get("chunk_categorization", [])
        doc_breakdown = {}
        
        for i, categorization in enumerate(chunk_categorizations):
            if i < len(chunk_metadata):
                source_doc = chunk_metadata[i]["source_document"]
                category = categorization.get("category", "irrelevant")
                
                if source_doc not in doc_breakdown:
                    doc_breakdown[source_doc] = {
                        "gstr1": 0, "gstr2": 0, "irrelevant": 0, "ambiguous": 0, "total": 0
                    }
                
                if category in doc_breakdown[source_doc]:
                    doc_breakdown[source_doc][category] += 1
                else:
                    doc_breakdown[source_doc]["irrelevant"] += 1
                doc_breakdown[source_doc]["total"] += 1
        
        print("📄 PER-DOCUMENT BREAKDOWN")
        print("-" * 25)
        for doc, stats in doc_breakdown.items():
            print(f"{doc}:")
            print(f"  - GSTR-1: {stats['gstr1']} chunks")
            print(f"  - GSTR-2: {stats['gstr2']} chunks") 
            print(f"  - Irrelevant: {stats['irrelevant']} chunks")
            print(f"  - Ambiguous: {stats['ambiguous']} chunks")
            print(f"  - Total: {stats['total']} chunks")
            print()
        
        # Show sample categorizations with content preview
        print("🔍 SAMPLE CHUNK ANALYSIS")
        print("-" * 25)
        for i, categorization in enumerate(chunk_categorizations[:3]):
            if i < len(chunk_metadata):
                metadata = chunk_metadata[i]
                category = categorization.get("category", "unknown")
                confidence = categorization.get("confidence", 0)
                reasoning = categorization.get("reasoning", "No reasoning provided")
                
                print(f"Chunk {i+1} from {metadata['source_document']}:")
                print(f"  Category: {category.upper()}")
                print(f"  Confidence: {confidence:.2%}")
                print(f"  Content: {metadata['chunk_preview']}")
                print(f"  Reasoning: {reasoning[:150]}...")
                print()
        
        return categorization_result
        
    except Exception as e:
        print(f"❌ Categorization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_gstr2_extraction_directly():
    """Test GSTR-2 extraction agent with actual PDF content"""
    
    gstr2_pdf = "/home/lijo/Documents/adk/server/gstr2.pdf"
    
    print("\n🔧 TESTING GSTR-2 EXTRACTION DIRECTLY")
    print("=" * 45)
    
    # Process GSTR-2 PDF to get content
    chunks = process_pdf_to_chunks(gstr2_pdf)
    print(f"GSTR-2 PDF chunks: {len(chunks)}")
    
    if chunks:
        print(f"First chunk content preview:")
        print(f"'{chunks[0][:200]}...'")
        print()
        
        # Test GSTR-2 extraction agent directly
        try:
            from agents.gstr2_extraction_agent import GSTR2ExtractionAgent
            
            gstr2_agent = GSTR2ExtractionAgent()
            
            print("🤖 Running GSTR-2 extraction...")
            extraction_result = gstr2_agent.extract_gstr2_data(
                chunks=chunks,
                filing_period="2024-12"
            )
            
            print("📋 GSTR-2 EXTRACTION RESULT:")
            print("-" * 30)
            
            gstr2_return = extraction_result.get("gstr2_return", {})
            inward_invoices = gstr2_return.get("inward_invoices", [])
            summary = gstr2_return.get("summary", {})
            
            print(f"Invoices found: {len(inward_invoices)}")
            print(f"Total taxable value: ₹{summary.get('total_taxable_value', 0)}")
            print(f"Total tax: ₹{summary.get('total_tax', 0)}")
            
            if inward_invoices:
                print("\n📄 INVOICE DETAILS:")
                for i, invoice in enumerate(inward_invoices[:3]):  # Show first 3
                    print(f"Invoice {i+1}:")
                    print(f"  - Number: {invoice.get('invoice_no', 'N/A')}")
                    print(f"  - Date: {invoice.get('invoice_date', 'N/A')}")
                    print(f"  - Supplier GSTIN: {invoice.get('supplier_gstin', 'N/A')}")
                    print(f"  - Value: ₹{invoice.get('invoice_value', 0)}")
                    print(f"  - Items: {len(invoice.get('items', []))}")
            else:
                print("\n⚠️  NO INVOICES EXTRACTED")
                print("This indicates the GSTR-2 agent is not recognizing invoice data")
                
                # Show extraction notes if available
                notes = extraction_result.get("extraction_notes", "")
                if notes:
                    print(f"Notes: {notes}")
            
            return extraction_result
            
        except Exception as e:
            print(f"❌ GSTR-2 extraction failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    return None

if __name__ == "__main__":
    result = test_direct_categorization()
    if result:
        print("✅ Direct categorization test completed!")
        
        # Now test GSTR-2 extraction directly
        gstr2_result = test_gstr2_extraction_directly()
        if gstr2_result:
            print("\n✅ GSTR-2 extraction test completed!")
        else:
            print("\n❌ GSTR-2 extraction test failed!")
    else:
        print("❌ Test failed!")
