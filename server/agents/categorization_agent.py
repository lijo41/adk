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
        
        # GSTR-1 keywords (outward supplies/sales)
        gstr1_keywords = [
            'invoice', 'bill', 'sale', 'supply', 'outward', 'b2b', 'b2c', 
            'export', 'taxable value', 'cgst', 'sgst', 'igst', 'customer',
            'buyer', 'recipient', 'gstin of recipient', 'place of supply'
        ]
        
        # GSTR-2 keywords (inward supplies/purchases)
        gstr2_keywords = [
            'purchase', 'procurement', 'inward', 'input tax credit', 'itc',
            'vendor', 'supplier', 'gstin of supplier', 'reverse charge',
            'import', 'customs', 'bill of entry'
        ]
        
        gstr1_score = sum(1 for keyword in gstr1_keywords if keyword in chunk_lower)
        gstr2_score = sum(1 for keyword in gstr2_keywords if keyword in chunk_lower)
        
        # Quick classification based on keyword density
        if gstr1_score > gstr2_score and gstr1_score >= 2:
            return {
                "chunk_index": chunk_index,
                "category": "gstr1", 
                "confidence": min(0.8, 0.5 + (gstr1_score * 0.1)),
                "detected_data_types": ["invoice"] if "invoice" in chunk_lower else [],
                "method": "keyword"
            }
        elif gstr2_score > gstr1_score and gstr2_score >= 2:
            return {
                "chunk_index": chunk_index,
                "category": "gstr2",
                "confidence": min(0.8, 0.5 + (gstr2_score * 0.1)), 
                "detected_data_types": ["purchase"] if "purchase" in chunk_lower else [],
                "method": "keyword"
            }
        elif gstr1_score > 0 or gstr2_score > 0:
            return {
                "chunk_index": chunk_index,
                "category": "ambiguous",
                "confidence": 0.3,
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
                "b2b_invoices_count": len([c for c in categorizations if c["category"] == "gstr1" and "invoice" in c.get("detected_data_types", [])]),
                "b2c_invoices_count": 0,
                "export_invoices_count": 0,
                "total_transactions": len(gstr1_chunks)
            },
            "gstr2_analysis": {
                "relevant_chunks": gstr2_chunks,
                "purchase_invoices_count": len([c for c in categorizations if c["category"] == "gstr2" and "purchase" in c.get("detected_data_types", [])]),
                "import_invoices_count": 0,
                "total_transactions": len(gstr2_chunks)
            },
            "recommendations": {
                "suggested_filings": self._get_suggested_filings(gstr1_chunks, gstr2_chunks),
                "confidence_score": self._calculate_confidence(categorizations),
                "notes": f"Fast categorization completed. {len(ambiguous_chunks)} chunks required LLM analysis."
            },
            "chunk_categorization": categorizations
        }

    def _batch_llm_analysis(self, ambiguous_chunks: List[tuple]) -> Dict[int, Dict[str, Any]]:
        """Batch process ambiguous chunks with LLM for accurate classification."""
        if not ambiguous_chunks:
            return {}
        
        # Create batch prompt for all ambiguous chunks
        batch_prompt = """Analyze these document chunks for GST categorization:

GSTR-1 (outward supplies/sales): invoices, bills, sales, supplies to customers
GSTR-2 (inward supplies/purchases): purchase invoices, procurement, input tax credit

Chunks to analyze:
"""
        
        for i, (chunk_idx, chunk) in enumerate(ambiguous_chunks):
            batch_prompt += f"\nChunk {i+1} (Index {chunk_idx}): {chunk[:300]}...\n"
        
        batch_prompt += """
Respond with JSON only:
{
  "results": [
    {
      "chunk_index": 0,
      "category": "gstr1|gstr2|irrelevant", 
      "confidence": 0.0-1.0,
      "detected_data_types": ["invoice", "purchase", etc.]
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

    def _get_suggested_filings(self, gstr1_chunks: List[int], gstr2_chunks: List[int]) -> List[str]:
        """Determine suggested filing types based on categorized chunks."""
        suggestions = []
        if gstr1_chunks:
            suggestions.append("GSTR1")
        if gstr2_chunks:
            suggestions.append("GSTR2")
        return suggestions or ["GSTR1"]  # Default to GSTR1

    def _calculate_confidence(self, categorizations: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score."""
        if not categorizations:
            return 0.0
        
        total_confidence = sum(cat.get("confidence", 0.0) for cat in categorizations)
        return min(1.0, total_confidence / len(categorizations))
