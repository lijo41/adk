"""GSTR-1 data extraction agent for invoice processing."""

import google.generativeai as genai
import json
import re
from typing import List, Dict, Any, Optional
from models.document import Document, DocumentChunk


class GSTR1ExtractionAgent:
    """AI agent for extracting GSTR-1 data from documents."""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    
    def extract_invoice_data(self, document: Document, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """Extract structured invoice data from document chunks."""
        # Combine all chunks for comprehensive analysis
        content = "\n".join([chunk.content for chunk in chunks])
        
        prompt = f"""
Extract GST invoice information from this document and return as JSON array.

For each invoice found, extract:
- invoice_no: Invoice number
- invoice_date: Date in YYYY-MM-DD format
- recipient_gstin: Customer GSTIN (15 characters)
- recipient_name: Customer/Buyer name
- place_of_supply: State name or code
- invoice_value: Total invoice amount
- items: Array of line items with:
  - product_name: Item description
  - hsn_code: HSN/SAC code
  - quantity: Quantity
  - unit_price: Rate per unit
  - taxable_value: Taxable amount
  - igst_rate: IGST rate percentage
  - cgst_rate: CGST rate percentage  
  - sgst_rate: SGST rate percentage
  - igst: IGST amount
  - cgst: CGST amount
  - sgst: SGST amount
  - cess: Cess amount (if any)

Document content to analyze:
{content}

Return ONLY the JSON array, no explanations or other text:"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response to extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            invoice_data = json.loads(response_text)
            
            # Ensure we return a list and handle duplicates
            if isinstance(invoice_data, list):
                # Enhanced duplicate detection for current session
                # Note: user_gstin not available at document level, will be handled at extraction level
                return invoice_data
            else:
                return [invoice_data]
                
        except Exception as e:
            print(f"Error extracting invoice data from {document.filename}: {str(e)}")
            return []
    
    def _normalize_invoice_number(self, invoice_no: str) -> str:
        """Normalize invoice number for better duplicate detection."""
        if not invoice_no:
            return ""
        # Remove spaces, hyphens, slashes and convert to uppercase
        normalized = re.sub(r'[-\s/\\]', '', str(invoice_no).upper())
        return normalized
    
    def _get_duplicate_key(self, invoice: Dict[str, Any], user_gstin: str) -> str:
        """Generate GST-compliant duplicate detection key based on invoice category."""
        # Normalize invoice number
        invoice_no = self._normalize_invoice_number(invoice.get('invoice_no', ''))
        invoice_date = invoice.get('invoice_date', '')
        
        # Check if recipient has GSTIN (B2B/B2CL) or not (B2CS)
        recipient_gstin = invoice.get('recipient_gstin', '')
        if recipient_gstin and len(str(recipient_gstin).strip()) == 15:
            # B2B/B2CL: Supplier GSTIN + Recipient GSTIN + Invoice Number + Invoice Date
            return f"B2B_{user_gstin}_{recipient_gstin.strip()}_{invoice_no}_{invoice_date}"
        else:
            # B2CS: Invoice Number + Invoice Date + Invoice Value + Customer Name
            invoice_value = float(invoice.get('invoice_value', 0))
            customer_name = str(invoice.get('recipient_name', '')).strip().upper()
            return f"B2CS_{invoice_no}_{invoice_date}_{invoice_value}_{customer_name}"
    
    def _is_similar_invoice(self, inv1: Dict[str, Any], inv2: Dict[str, Any], user_gstin: str) -> bool:
        """Check if two invoices are duplicates using GST-compliant logic."""
        # Generate duplicate keys for both invoices
        key1 = self._get_duplicate_key(inv1, user_gstin)
        key2 = self._get_duplicate_key(inv2, user_gstin)
        
        # Invoices are duplicates if they have the same key
        return key1 == key2
    
    def _deduplicate_invoices(self, invoices: List[Dict[str, Any]], user_gstin: str = "") -> List[Dict[str, Any]]:
        """Remove duplicate invoices from the current batch using GST-compliant logic."""
        if not invoices:
            return invoices
        
        unique_invoices = []
        seen_keys = set()
        duplicates_removed = 0
        
        for invoice in invoices:
            # Generate GST-compliant duplicate key
            duplicate_key = self._get_duplicate_key(invoice, user_gstin)
            
            if duplicate_key in seen_keys:
                duplicates_removed += 1
                print(f"Duplicate removed: {invoice.get('invoice_no', 'Unknown')} (key: {duplicate_key})")
            else:
                seen_keys.add(duplicate_key)
                unique_invoices.append(invoice)
        
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate invoices using GST-compliant detection")
        
        return unique_invoices
    
    def validate_gst_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean GST invoice data."""
        validated = {}
        
        # Validate GSTIN format (15 characters)
        gstin = invoice_data.get('recipient_gstin', '')
        # Validate string fields
        validated['invoice_no'] = str(invoice_data.get('invoice_no', '') or '').strip()
        validated['recipient_gstin'] = str(invoice_data.get('recipient_gstin', '') or '').strip()
        validated['recipient_name'] = str(invoice_data.get('recipient_name', '') or '').strip()
            
        # Validate date format
        invoice_date = invoice_data.get('invoice_date', '')
        try:
            from datetime import datetime
            datetime.strptime(invoice_date, '%Y-%m-%d')
            validated['invoice_date'] = invoice_date
        except:
            validated['invoice_date'] = None
            
        # Validate numeric fields
        numeric_fields = ['invoice_value', 'taxable_value', 'igst', 'cgst', 'sgst', 'cess']
        for field in numeric_fields:
            try:
                value = float(invoice_data.get(field, 0))
                validated[field] = value
            except:
                validated[field] = 0.0
                
        # Validate items
        items = invoice_data.get('items', [])
        validated_items = []
        for item in items:
            validated_item = {}
            validated_item['product_name'] = str(item.get('product_name', '') or '').strip()
            validated_item['hsn_code'] = str(item.get('hsn_code', '') or '').strip()
            
            # Validate numeric item fields
            item_numeric_fields = ['quantity', 'unit_price', 'taxable_value', 'igst_rate', 'cgst_rate', 'sgst_rate', 'igst', 'cgst', 'sgst', 'cess']
            for field in item_numeric_fields:
                try:
                    value = float(item.get(field, 0))
                    validated_item[field] = value
                except:
                    validated_item[field] = 0.0
                    
            validated_items.append(validated_item)
            
        validated['items'] = validated_items
        validated['place_of_supply'] = str(invoice_data.get('place_of_supply', '') or '').strip()
        
        return validated
    
    def extract_gstr1_data(self, chunks: List[str], user_gstin: str, user_company_name: str) -> Dict[str, Any]:
        """Extract GSTR-1 data from filtered chunks."""
        try:
            content = "\n".join(chunks)
            print(f"Processing {len(chunks)} chunks with total content length: {len(content)}")
            print(f"Content preview: {content[:200]}...")
            
            # Check if Google API key is available
            import os
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                print("ERROR: GOOGLE_API_KEY environment variable not set")
                raise ValueError("Google API key not configured")
            print(f"Google API key configured: {api_key[:10]}...")
            
            # Construct the AI prompt for GSTR-1 extraction
            prompt = f"""You are a GST expert. Extract structured GSTR-1 invoice data from the following document content.

Company Details:
- GSTIN: {user_gstin}
- Company Name: {user_company_name}

IMPORTANT: Extract ALL invoices found, including:
- B2B invoices (recipients with valid 15-digit GSTIN)
- B2CL invoices (recipients without GSTIN or marked as "Unregistered", invoice value > ₹2.5 lakh)
- B2CS invoices (recipients without GSTIN or marked as "Unregistered", invoice value ≤ ₹2.5 lakh)

Look for keywords like "Unregistered", "No GSTIN", or missing GSTIN fields to identify B2CL/B2CS customers.

For each invoice found, extract:
- invoice_no: Invoice number
- invoice_date: Date in YYYY-MM-DD format (convert from DD-MMM-YYYY if needed)
- recipient_gstin: Customer GSTIN (15 characters) - use null if not present or if customer is unregistered
- recipient_name: Customer/Buyer name (include "Unregistered" if mentioned)
- place_of_supply: State name or code
- invoice_value: Total invoice amount (from "Total Amount After Tax" or "Grand Total")
- items: Array of line items with product details and tax amounts

Return structured data in this exact format:
{{
  "total_invoices": 0,
  "total_taxable_value": 0.0,
  "total_tax_amount": 0.0,
  "invoices": [
    {{
      "invoice_no": "B2B-001",
      "invoice_date": "2025-08-24",
      "recipient_gstin": "07ABCDE0001F1ZQ",
      "recipient_name": "M/s Alpha Engineering Pvt Ltd",
      "place_of_supply": "Delhi (07)",
      "invoice_value": 19606.89,
      "items": [
        {{
          "product_name": "Hitachi Power Drill",
          "hsn_code": "8467",
          "quantity": 2,
          "unit_price": 5538.67,
          "taxable_value": 11077.3,
          "igst": 1993.92,
          "cgst": 0,
          "sgst": 0,
          "cess": 0
        }}
      ]
    }}
  ]
}}

Document content:
{content}

Extract ALL invoices and return as JSON with the exact structure above. Do not skip any invoices:"""

            print("Sending prompt to AI model...")
            response = self.model.generate_content(prompt)
            print(f"AI response received: {type(response)}")
            
            # Check if response is None or empty
            if not response or not hasattr(response, 'text') or not response.text:
                print("Warning: AI model returned empty response")
                print(f"Response object: {response}")
                raise ValueError("Empty response from AI model")
            
            response_text = response.text.strip()
            print(f"AI response text length: {len(response_text)}")
            print(f"AI response preview: {response_text[:500]}...")
            
            # Check if response text is empty
            if not response_text:
                print("Warning: AI model returned empty text")
                raise ValueError("Empty text from AI model")
            
            # Clean up response to extract JSON
            print(f"Original response_text type: {type(response_text)}")
            
            if "```json" in response_text:
                json_parts = response_text.split("```json")
                if len(json_parts) > 1:
                    json_content = json_parts[1].split("```")[0]
                    if json_content is not None:
                        response_text = json_content.strip()
                    else:
                        print("Warning: json_content is None")
                        response_text = response_text.strip()
                else:
                    response_text = response_text.strip()
            elif "```" in response_text:
                json_parts = response_text.split("```")
                if len(json_parts) > 1:
                    json_content = json_parts[1].split("```")[0] if len(json_parts) > 2 else json_parts[1]
                    if json_content is not None:
                        response_text = json_content.strip()
                    else:
                        print("Warning: json_content is None")
                        response_text = response_text.strip()
                else:
                    response_text = response_text.strip()
            else:
                response_text = response_text.strip()
            
            print(f"Cleaned response_text type: {type(response_text)}")
            print(f"Cleaned response_text length: {len(response_text) if response_text else 'None'}")
            
            if not response_text:
                raise ValueError("No JSON content found in AI response")
            
            result = json.loads(response_text)
            
            # Apply deduplication and validation to invoices
            if result.get("invoices"):
                # Validate each invoice
                validated_invoices = []
                for invoice in result["invoices"]:
                    validated = self.validate_gst_data(invoice)
                    validated_invoices.append(validated)
                
                # Apply GST-compliant duplicate detection
                deduplicated_invoices = self._deduplicate_invoices(validated_invoices, user_gstin)
                result["invoices"] = deduplicated_invoices
            else:
                result["invoices"] = []
            
            # Categorize invoices based on GST rules
            categorized_result = self._categorize_invoices(result)
            
            return categorized_result
            
        except Exception as e:
            print(f"Error in GSTR-1 extraction: {e}")
            print("Attempting manual parsing fallback...")
            
            # Manual parsing fallback
            try:
                manual_result = self._manual_parse_invoices(content)
                if manual_result and manual_result.get("invoices"):
                    print(f"Manual parsing successful: {len(manual_result['invoices'])} invoices found")
                    categorized_result = self._categorize_invoices(manual_result)
                    return categorized_result
            except Exception as manual_error:
                print(f"Manual parsing also failed: {manual_error}")
            
            return {
                "total_invoices": 0,
                "b2b_invoices": 0,
                "b2cl_invoices": 0,
                "b2cs_invoices": 0,
                "total_taxable_value": 0.0,
                "total_tax_amount": 0.0,
                "invoices": [],
                "b2b": [],
                "b2cl": [],
                "b2cs": []
            }
    
    def _categorize_invoices(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize invoices into B2B, B2CL, and B2CS based on GST rules."""
        
        invoices = extraction_result.get("invoices", [])
        
        # Initialize categorized lists
        b2b_invoices = []
        b2cl_invoices = []
        b2cs_invoices = []
        
        for invoice in invoices:
            # Check if customer has GSTIN
            recipient_gstin = invoice.get("recipient_gstin", "")
            if recipient_gstin:
                recipient_gstin = str(recipient_gstin).strip()
            
            # Handle null/None GSTIN values
            has_gstin = (recipient_gstin and 
                        recipient_gstin.lower() not in ['null', 'none', 'n/a', ''] and 
                        len(recipient_gstin) == 15)
            
            # Get invoice value
            invoice_value = float(invoice.get("invoice_value", 0))
            
            # Apply GST categorization rules:
            # ✅ B2B: Registered buyers with GSTIN (any value, intra/inter)
            # ✅ B2CS: Unregistered buyers, invoice value ≤ ₹2.5 lakh (intra/inter)
            # ✅ B2CL: Unregistered buyers, invoice value > ₹2.5 lakh (inter-state only)
            
            if has_gstin:
                # B2B: Registered buyer (has valid GSTIN) - any value, intra/inter state
                invoice["category"] = "B2B"
                b2b_invoices.append(invoice)
            elif invoice_value > 250000:  # ₹2.5 lakh = 250000
                # B2CL: Unregistered buyer, > ₹2.5 lakh, inter-state only
                invoice["category"] = "B2CL"
                b2cl_invoices.append(invoice)
            else:
                # B2CS: Unregistered buyer, ≤ ₹2.5 lakh, intra OR inter state
                invoice["category"] = "B2CS"
                b2cs_invoices.append(invoice)
        
        # Calculate totals
        total_taxable_value = sum(float(inv.get("invoice_value", 0)) for inv in invoices)
        total_tax_amount = 0
        for inv in invoices:
            for item in inv.get("items", []):
                total_tax_amount += float(item.get("igst", 0))
                total_tax_amount += float(item.get("cgst", 0))
                total_tax_amount += float(item.get("sgst", 0))
        
        # Update the result with categorized data
        categorized_result = {
            **extraction_result,
            "total_invoices": len(invoices),
            "b2b_invoices": len(b2b_invoices),
            "b2cl_invoices": len(b2cl_invoices),
            "b2cs_invoices": len(b2cs_invoices),
            "total_taxable_value": total_taxable_value,
            "total_tax_amount": total_tax_amount,
            "b2b": b2b_invoices,
            "b2cl": b2cl_invoices,
            "b2cs": b2cs_invoices,
            "categorization_summary": {
                "total_invoices": len(invoices),
                "b2b_count": len(b2b_invoices),
                "b2cl_count": len(b2cl_invoices),
                "b2cs_count": len(b2cs_invoices)
            }
        }
        
        print(f"Invoice categorization completed:")
        print(f"- B2B (with GSTIN): {len(b2b_invoices)}")
        print(f"- B2CL (>₹2.5L, no GSTIN): {len(b2cl_invoices)}")
        print(f"- B2CS (≤₹2.5L, no GSTIN): {len(b2cs_invoices)}")
        
        return categorized_result
    
    def _manual_parse_invoices(self, content: str) -> Dict[str, Any]:
        """Manual parsing fallback when AI extraction fails."""
        import re
        
        invoices = []
        
        # Split content by common invoice separators
        invoice_sections = re.split(r'(?i)(?:invoice|bill|receipt|tax invoice)', content)
        
        for section in invoice_sections:
            if len(section.strip()) < 50:  # Skip very short sections
                continue
                
            invoice = {}
            
            # Extract invoice number
            invoice_no_match = re.search(r'(?i)(?:invoice\s*no\.?|bill\s*no\.?|inv\s*no\.?)\s*:?\s*([A-Z0-9\-/]+)', section)
            if invoice_no_match:
                invoice['invoice_no'] = invoice_no_match.group(1)
            
            # Extract date
            date_match = re.search(r'(?i)date\s*:?\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4})', section)
            if date_match:
                date_str = date_match.group(1)
                # Convert to YYYY-MM-DD format
                try:
                    from datetime import datetime
                    if '-' in date_str and len(date_str.split('-')[1]) == 3:  # DD-MMM-YYYY
                        dt = datetime.strptime(date_str, '%d-%b-%Y')
                    else:  # DD-MM-YYYY or DD/MM/YYYY
                        dt = datetime.strptime(date_str.replace('/', '-'), '%d-%m-%Y')
                    invoice['invoice_date'] = dt.strftime('%Y-%m-%d')
                except:
                    invoice['invoice_date'] = '2025-08-24'  # Default date
            
            # Extract GSTIN
            gstin_match = re.search(r'(?i)gstin\s*:?\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9][Z][0-9])', section)
            if gstin_match:
                invoice['recipient_gstin'] = gstin_match.group(1)
            else:
                invoice['recipient_gstin'] = None
            
            # Extract recipient name
            recipient_match = re.search(r'(?i)(?:recipient|customer|buyer|bill to)\s*:?\s*\n?\s*([^\n]+)', section)
            if recipient_match:
                invoice['recipient_name'] = recipient_match.group(1).strip()
            else:
                invoice['recipient_name'] = 'Unknown Customer'
            
            # Extract place of supply
            place_match = re.search(r'(?i)place\s*of\s*supply\s*:?\s*([^\n]+)', section)
            if place_match:
                invoice['place_of_supply'] = place_match.group(1).strip()
            else:
                invoice['place_of_supply'] = 'Unknown'
            
            # Extract total amount
            total_match = re.search(r'(?i)(?:total|grand total|amount)\s*:?\s*₹?\s*([0-9,]+\.?[0-9]*)', section)
            if total_match:
                amount_str = total_match.group(1).replace(',', '')
                invoice['invoice_value'] = float(amount_str)
            else:
                invoice['invoice_value'] = 0.0
            
            # Create basic item structure
            invoice['items'] = [{
                'product_name': 'Extracted Item',
                'hsn_code': '9999',
                'quantity': 1,
                'unit_price': invoice['invoice_value'],
                'taxable_value': invoice['invoice_value'] * 0.85,  # Assume 15% tax
                'igst': invoice['invoice_value'] * 0.15,
                'cgst': 0,
                'sgst': 0,
                'cess': 0
            }]
            
            # Only add if we found essential data
            if invoice.get('invoice_no') and invoice.get('invoice_value', 0) > 0:
                invoices.append(invoice)
        
        return {
            "total_invoices": len(invoices),
            "total_taxable_value": sum(inv.get('invoice_value', 0) for inv in invoices),
            "total_tax_amount": sum(inv.get('invoice_value', 0) * 0.15 for inv in invoices),
            "invoices": invoices
        }
    
    def extract_company_details(self, content: str) -> Dict[str, str]:
        """Extract company details from document content."""
        prompt = f"""
Extract company information from this document:

{content[:1000]}

Extract and return as JSON:
- company_name: Legal company name
- gstin: Company GSTIN (15 characters)
- address: Complete address
- state: State name
- pan: PAN number if available

Return only JSON, no explanations:"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
                
            return json.loads(response_text)
        except Exception as e:
            print(f"Error extracting company details: {str(e)}")
            return {}
