"""GSTR-1 data extraction agent for invoice processing."""

import google.generativeai as genai
import json
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
                # Remove duplicates within the AI response
                unique_invoices = []
                seen_invoices = set()
                for invoice in invoice_data:
                    invoice_key = f"{invoice.get('invoice_no', '')}_{invoice.get('invoice_date', '')}"
                    if invoice_key not in seen_invoices:
                        seen_invoices.add(invoice_key)
                        unique_invoices.append(invoice)
                return unique_invoices
            else:
                return [invoice_data]
                
        except Exception as e:
            print(f"Error extracting invoice data from {document.filename}: {str(e)}")
            return []
    
    def validate_gst_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean GST invoice data."""
        validated = {}
        
        # Validate GSTIN format (15 characters)
        gstin = invoice_data.get('recipient_gstin', '')
        if len(gstin) == 15:
            validated['recipient_gstin'] = gstin
        else:
            validated['recipient_gstin'] = None
            
        # Validate invoice number
        validated['invoice_no'] = invoice_data.get('invoice_no', '').strip()
        
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
            validated_item['product_name'] = item.get('product_name', '').strip()
            validated_item['hsn_code'] = item.get('hsn_code', '').strip()
            
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
        validated['place_of_supply'] = invoice_data.get('place_of_supply', '').strip()
        
        return validated
    
    def extract_gstr1_data(self, chunks: List[str], user_gstin: str, user_company_name: str) -> Dict[str, Any]:
        """Extract GSTR-1 data from filtered chunks."""
        try:
            # Convert chunks to content
            content = "\n".join(chunks)
            
            prompt = f"""
Extract GST invoice information from these document chunks for GSTR-1 filing.

Company Details:
- GSTIN: {user_gstin}
- Company Name: {user_company_name}

Extract all B2B invoices and return structured data in this exact format:
{{
  "total_invoices": 0,
  "b2b_invoices": 0,
  "total_taxable_value": 0.0,
  "total_tax_amount": 0.0,
  "invoices": [
    {{
      "invoice_no": "INV-001",
      "invoice_date": "2025-08-24",
      "recipient_gstin": "32AACCB1122B1ZB",
      "place_of_supply": "Kerala (32)",
      "invoice_value": 13924,
      "items": [
        {{
          "product_name": "Product Name",
          "hsn_code": "8467",
          "quantity": 2,
          "unit_price": 3500,
          "taxable_value": 7000,
          "igst": 1260,
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

Return as JSON with the exact structure above:"""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response to extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            result = json.loads(response_text)
            
            # Ensure required fields exist
            return {
                "total_invoices": result.get("total_invoices", 0),
                "b2b_invoices": result.get("b2b_invoices", 0),
                "total_taxable_value": float(result.get("total_taxable_value", 0)),
                "total_tax_amount": float(result.get("total_tax_amount", 0)),
                "invoices": result.get("invoices", [])
            }
            
        except Exception as e:
            print(f"Error in extract_gstr1_data: {str(e)}")
            # Return fallback data
            return {
                "total_invoices": 0,
                "b2b_invoices": 0,
                "total_taxable_value": 0.0,
                "total_tax_amount": 0.0,
                "invoices": []
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
