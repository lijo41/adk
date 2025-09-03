"""Categorization agent for fast GST document analysis."""

import google.generativeai as genai
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import json
import re

load_dotenv()

class CategorizationAgent:
    """Fast categorization agent using keyword filtering + batch LLM processing."""
    
    def __init__(self):
        """Initialize the categorization agent."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def _keyword_filter(self, chunk: str, chunk_index: int) -> Dict[str, Any]:
        """Fast keyword-based pre-filtering before LLM analysis."""
        chunk_lower = chunk.lower()
        
        # GSTR-1 keywords (outward supplies/sales) - Company is SELLING
        gstr1_keywords = [
            'sale', 'sold', 'selling', 'outward supply', 'supply made', 'supply to',
            'customer', 'buyer', 'gstin of recipient', 'sold to',
            'place of supply', 'sales invoice', 'invoice to', 'billed to',
            'delivered to', 'shipped to', 'consignee', 'b2b supply', 'b2c supply',
            'tax invoice', 'original for recipient', 'invoice original'
        ]
        
        # GSTR-2 keywords (inward supplies/purchases) - Company is BUYING  
        gstr2_keywords = [
            'purchase', 'purchased', 'buying', 'procurement', 'inward supply', 'supply received',
            'input tax credit', 'itc', 'vendor', 'supplier', 'gstin of supplier',
            'reverse charge', 'import', 'customs', 'bill of entry', 'purchase invoice',
            'from supplier', 'received from', 'bought from', 'procured from',
            'invoice from', 'billed by', 'supplied by', 'vendor invoice',
            'gstr-2', 'gstr2', 'inward supply invoice'
        ]
        
        # Common keywords that appear in both (should not heavily weight either direction)
        common_keywords = ['invoice', 'bill', 'taxable value', 'cgst', 'sgst', 'igst']
        
        gstr1_score = sum(1 for keyword in gstr1_keywords if keyword in chunk_lower)
        gstr2_score = sum(1 for keyword in gstr2_keywords if keyword in chunk_lower)
        
        # Enhanced classification logic with stronger GSTR-1 indicators
        # Special handling for tax invoices (strong GSTR-1 indicator)
        if 'tax invoice' in chunk_lower or 'original for recipient' in chunk_lower:
            return {
                "chunk_index": chunk_index,
                "category": "gstr1",
                "confidence": 0.9,
                "detected_data_types": ["outward_supply"],
                "method": "keyword_strong"
            }
        
        # Special handling for GSTR-2 specific documents
        if any(keyword in chunk_lower for keyword in ['gstr-2', 'gstr2', 'inward supply invoice']):
            return {
                "chunk_index": chunk_index,
                "category": "gstr2",
                "confidence": 0.9,
                "detected_data_types": ["inward_supply"],
                "method": "keyword_strong"
            }
        
        if gstr2_score > gstr1_score and gstr2_score >= 1:
            return {
                "chunk_index": chunk_index,
                "category": "gstr2",
                "confidence": min(0.8, 0.5 + (gstr2_score * 0.1)), 
                "detected_data_types": ["purchase"] if "purchase" in chunk_lower else ["inward_supply"],
                "method": "keyword"
            }
        elif gstr1_score > gstr2_score and gstr1_score >= 1:
            return {
                "chunk_index": chunk_index,
                "category": "gstr1", 
                "confidence": min(0.8, 0.5 + (gstr1_score * 0.1)),
                "detected_data_types": ["sale"] if any(word in chunk_lower for word in ['sale', 'sold']) else ["outward_supply"],
                "method": "keyword"
            }
        elif gstr1_score == gstr2_score and (gstr1_score > 0 or gstr2_score > 0):
            return {
                "chunk_index": chunk_index,
                "category": "ambiguous",
                "confidence": 0.4,
                "detected_data_types": [],
                "method": "keyword"
            }
        else:
            return {
                "chunk_index": chunk_index,
                "category": "irrelevant",
                "confidence": 0.9,
                "detected_data_types": [],
                "method": "keyword"
            }

    def categorize_chunks(self, chunks: List[str]) -> Dict[str, Any]:
        """
        Fast categorization using keyword filtering + batch LLM for ambiguous cases.
        
        Args:
            chunks: List of document text chunks
            
        Returns:
            Dictionary containing categorization results
        """
        # Step 1: Fast keyword-based filtering
        categorizations = []
        ambiguous_chunks = []
        
        for i, chunk in enumerate(chunks):
            result = self._keyword_filter(chunk, i)
            categorizations.append(result)
            
            # Collect ambiguous chunks for LLM analysis
            if result["category"] == "ambiguous":
                ambiguous_chunks.append((i, chunk))
        
        # Step 2: Batch process ambiguous chunks with LLM
        if ambiguous_chunks:
            llm_results = self._batch_llm_analysis(ambiguous_chunks)
            
            # Update categorizations with LLM results
            for chunk_idx, llm_result in llm_results.items():
                categorizations[chunk_idx] = llm_result
        
        # Step 3: Generate summary statistics
        gstr1_chunks = [i for i, cat in enumerate(categorizations) if cat["category"] == "gstr1"]
        gstr2_chunks = [i for i, cat in enumerate(categorizations) if cat["category"] == "gstr2"]
        
        return {
            "gstr1_analysis": {
                "relevant_chunks": gstr1_chunks,
                "outward_supply_count": len([c for c in categorizations if c["category"] == "gstr1" and any(dt in c.get("detected_data_types", []) for dt in ["sale", "outward_supply"])]),
                "total_transactions": len(gstr1_chunks)
            },
            "gstr2_analysis": {
                "relevant_chunks": gstr2_chunks,
                "inward_supply_count": len([c for c in categorizations if c["category"] == "gstr2" and any(dt in c.get("detected_data_types", []) for dt in ["purchase", "inward_supply"])]),
                "total_transactions": len(gstr2_chunks)
            },
            "categorization_summary": {
                "total_chunks": len(chunks),
                "gstr1_chunks": len(gstr1_chunks),
                "gstr2_chunks": len(gstr2_chunks),
                "irrelevant_chunks": len([c for c in categorizations if c["category"] == "irrelevant"]),
                "ambiguous_chunks_processed": len(ambiguous_chunks),
                "overall_confidence": self._calculate_confidence(categorizations)
            },
            "chunk_categorization": categorizations
        }

    def _batch_llm_analysis(self, ambiguous_chunks: List[tuple]) -> Dict[int, Dict[str, Any]]:
        """Batch process ambiguous chunks with LLM for accurate classification."""
        if not ambiguous_chunks:
            return {}
        
        # Create batch prompt for all ambiguous chunks
        batch_prompt = """Analyze these document chunks for GST categorization:

GSTR-1 (outward supplies/sales): 
- TAX INVOICES issued by the company to customers
- Documents where company is SELLING/SUPPLYING goods/services
- Company GSTIN appears as supplier, customer GSTIN as recipient
- Strong indicators: "TAX INVOICE", "ORIGINAL FOR RECIPIENT", company name at top as issuer
- Keywords: "sold to", "supply to", "customer", "buyer", "billed to"

GSTR-2 (inward supplies/purchases):
- PURCHASE invoices received FROM other companies
- Documents where company is BUYING/RECEIVING goods/services  
- Company GSTIN appears as buyer, supplier GSTIN as issuer
- Strong indicators: "PURCHASE INVOICE", "RECEIVED FROM", "SUPPLIER GSTIN"
- Keywords: "purchased from", "supplier", "vendor", "received from", "bought from"

Chunks to analyze:
"""
        
        for i, (chunk_idx, chunk) in enumerate(ambiguous_chunks):
            batch_prompt += f"\nChunk {i+1} (Index {chunk_idx}): {chunk[:300]}...\n"
        
        batch_prompt += """
Look for these key indicators:
- GSTR-1: "TAX INVOICE" header, "ORIGINAL FOR RECIPIENT", company issuing invoice
- GSTR-2: "PURCHASE INVOICE", "GSTR-2", company receiving invoice from supplier

Respond with JSON only:
{
  "results": [
    {
      "chunk_index": 0,
      "category": "gstr1|gstr2|irrelevant", 
      "confidence": 0.0-1.0,
      "detected_data_types": ["outward_supply", "inward_supply", "sale", "purchase"]
    }
  ]
}"""

        try:
            response = self.model.generate_content(batch_prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result_data = json.loads(json_match.group())
                
                # Convert to indexed results
                indexed_results = {}
                for result in result_data.get("results", []):
                    chunk_idx = result["chunk_index"]
                    indexed_results[chunk_idx] = {
                        "chunk_index": chunk_idx,
                        "category": result["category"],
                        "confidence": result["confidence"],
                        "detected_data_types": result.get("detected_data_types", []),
                        "method": "llm"
                    }
                
                return indexed_results
            
        except Exception as e:
            print(f"LLM batch analysis failed: {e}")
        
        # Fallback: mark all as irrelevant
        return {chunk_idx: {
            "chunk_index": chunk_idx,
            "category": "irrelevant", 
            "confidence": 0.5,
            "detected_data_types": [],
            "method": "fallback"
        } for chunk_idx, _ in ambiguous_chunks}


    def _calculate_confidence(self, categorizations: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score."""
        if not categorizations:
            return 0.0
        
        total_confidence = sum(cat.get("confidence", 0.0) for cat in categorizations)
        return min(1.0, total_confidence / len(categorizations))
