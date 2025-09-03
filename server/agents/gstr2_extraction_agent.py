"""GSTR-2 Extraction Agent for processing inward supply invoices."""

import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

class GSTR2ExtractionAgent:
    """Agent for extracting GSTR-2 data from document chunks."""
    
    def __init__(self):
        """Initialize the GSTR-2 extraction agent."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GOOGLE_API_KEY in .env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    
    def extract_gstr2_data(self, chunks: List[str], filing_period: str = None, user=None) -> Dict[str, Any]:
        """
        Extract GSTR-2 data from document chunks.
        
        Args:
            chunks: List of document text chunks to process
            filing_period: Filing period (e.g., "2025-08")
            
        Returns:
            Dictionary containing extracted GSTR-2 data
        """
        try:
            # Combine all chunks for processing
            combined_text = "\n\n".join(chunks)
            
            # Create extraction prompt
            prompt = self._create_extraction_prompt(combined_text, filing_period)
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            
            if not response.text:
                return self._create_empty_response(filing_period)
            
            # Parse the JSON response
            try:
                # Clean the response text - remove markdown code blocks if present
                response_text = response.text.strip()
                
                # More robust markdown cleaning
                if response_text.startswith('```json'):
                    response_text = response_text[7:]  # Remove ```json
                elif response_text.startswith('```'):
                    response_text = response_text[3:]   # Remove ```
                
                if response_text.endswith('```'):
                    response_text = response_text[:-3]  # Remove closing ```
                
                # Remove any remaining backticks at start/end
                response_text = response_text.strip('`').strip()
                
                # Debug logging
                print(f"Cleaned response text (first 200 chars): {response_text[:200]}...")
                
                extracted_data = json.loads(response_text)
                
                # Validate and clean the data
                validated_data = self._validate_and_clean_data(extracted_data, filing_period)
                
                # Save to database if extraction successful
                if validated_data.get("total_invoices", 0) > 0:
                    self._save_to_database(validated_data, filing_period, user)
                
                return validated_data
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Raw response: {response.text[:500]}...")
                return self._create_empty_response(filing_period)
                
        except Exception as e:
            print(f"GSTR-2 extraction error: {e}")
            return self._create_empty_response(filing_period)
    
    def _create_extraction_prompt(self, text: str, filing_period: str = None) -> str:
        """Create the extraction prompt for Gemini."""
        period = filing_period or datetime.now().strftime("%Y-%m")
        
        return f"""
You are a GST expert specializing in GSTR-2 (inward supplies) data extraction. 
Extract GSTR-2 data from the following document text and return it in the exact JSON format specified.

DOCUMENT TEXT:
{text}

INSTRUCTIONS:
1. Look for PURCHASE INVOICES, INWARD SUPPLIES, or VENDOR INVOICES
2. Extract supplier GSTIN, invoice details, and tax information
3. Focus on invoices where the document holder is the BUYER/RECIPIENT
4. Calculate totals accurately
5. Use HSN codes from the document or estimate based on product description
6. Return ONLY valid JSON, no additional text

REQUIRED JSON FORMAT:
{{
  "gstr2_return": {{
    "header": {{
      "gstin": "Extract from document or use placeholder",
      "company_name": "Extract company name or use placeholder", 
      "filing_period": "{period}"
    }},
    "inward_invoices": [
      {{
        "invoice_no": "Invoice number",
        "invoice_date": "YYYY-MM-DD format",
        "supplier_gstin": "Supplier's GSTIN",
        "place_of_supply": "State name (code)",
        "invoice_value": total_invoice_amount,
        "items": [
          {{
            "product_name": "Product/service name",
            "hsn_code": "HSN/SAC code",
            "quantity": quantity_number,
            "unit_price": price_per_unit,
            "taxable_value": taxable_amount,
            "igst": igst_amount,
            "cgst": cgst_amount, 
            "sgst": sgst_amount,
            "cess": cess_amount
          }}
        ]
      }}
    ],
    "summary": {{
      "total_invoices": count_of_invoices,
      "total_taxable_value": sum_of_all_taxable_values,
      "total_tax": sum_of_all_taxes
    }}
  }}
}}

Extract data for filing period: {period}
Return only the JSON object, no other text.
"""
    
    def _validate_and_clean_data(self, data: Dict[str, Any], filing_period: str = None) -> Dict[str, Any]:
        """Validate and clean the extracted data."""
        try:
            # Ensure proper structure
            if "gstr2_return" not in data:
                return self._create_empty_response(filing_period)
            
            gstr2_data = data["gstr2_return"]
            
            # Validate header
            if "header" not in gstr2_data:
                gstr2_data["header"] = {}
            
            header = gstr2_data["header"]
            header["filing_period"] = filing_period or datetime.now().strftime("%Y-%m")
            
            # Validate inward_invoices
            if "inward_invoices" not in gstr2_data:
                gstr2_data["inward_invoices"] = []
            
            invoices = gstr2_data["inward_invoices"]
            validated_invoices = []
            
            total_invoices = 0
            total_taxable_value = 0
            total_tax = 0
            
            for invoice in invoices:
                if self._is_valid_invoice(invoice):
                    # Clean and validate invoice data
                    cleaned_invoice = self._clean_invoice_data(invoice)
                    validated_invoices.append(cleaned_invoice)
                    
                    # Update totals
                    total_invoices += 1
                    total_taxable_value += cleaned_invoice.get("taxable_value", 0)
                    
                    # Calculate tax from items
                    for item in cleaned_invoice.get("items", []):
                        total_tax += (
                            item.get("igst", 0) + 
                            item.get("cgst", 0) + 
                            item.get("sgst", 0) + 
                            item.get("cess", 0)
                        )
            
            gstr2_data["inward_invoices"] = validated_invoices
            
            # Update summary
            gstr2_data["summary"] = {
                "total_invoices": total_invoices,
                "total_taxable_value": round(total_taxable_value, 2),
                "total_tax": round(total_tax, 2)
            }
            
            return data
            
        except Exception as e:
            print(f"Data validation error: {e}")
            return self._create_empty_response(filing_period)
    
    def _is_valid_invoice(self, invoice: Dict[str, Any]) -> bool:
        """Check if invoice has minimum required fields."""
        required_fields = ["invoice_no", "supplier_gstin"]
        return all(field in invoice and invoice[field] for field in required_fields)
    
    def _clean_invoice_data(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize invoice data."""
        cleaned = {
            "invoice_no": str(invoice.get("invoice_no", "")),
            "invoice_date": self._format_date(invoice.get("invoice_date")),
            "supplier_gstin": str(invoice.get("supplier_gstin", "")),
            "place_of_supply": str(invoice.get("place_of_supply", "")),
            "invoice_value": float(invoice.get("invoice_value", 0)),
            "items": []
        }
        
        # Clean items
        items = invoice.get("items", [])
        total_taxable = 0
        
        for item in items:
            cleaned_item = {
                "product_name": str(item.get("product_name", "")),
                "hsn_code": str(item.get("hsn_code", "")),
                "quantity": float(item.get("quantity", 0)),
                "unit_price": float(item.get("unit_price", 0)),
                "taxable_value": float(item.get("taxable_value", 0)),
                "igst": float(item.get("igst", 0)),
                "cgst": float(item.get("cgst", 0)),
                "sgst": float(item.get("sgst", 0)),
                "cess": float(item.get("cess", 0))
            }
            cleaned["items"].append(cleaned_item)
            total_taxable += cleaned_item["taxable_value"]
        
        cleaned["taxable_value"] = round(total_taxable, 2)
        return cleaned
    
    def _format_date(self, date_str: str) -> str:
        """Format date to YYYY-MM-DD."""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Try different date formats
            formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(str(date_str), fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
                    
        except ValueError:
            return date_str
    
    def _save_to_database(self, validated_data: Dict[str, Any], filing_period: str, user=None):
        """Save GSTR-2 data to database."""
        try:
            from database.database import get_db
            from schemas.simplified_schemas import GSTR2ReturnDB
            from sqlalchemy.orm import Session
            import json
            import uuid
            from datetime import datetime
            
            # Get database session
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                # Extract header information
                header = validated_data.get("gstr2_return", {}).get("header", {})
                invoices = validated_data.get("gstr2_return", {}).get("inward_invoices", [])
                summary = validated_data.get("gstr2_return", {}).get("summary", {})
                
                # Calculate GSTR-2 specific metrics
                total_itc_claimed = 0
                total_cgst_itc = 0
                total_sgst_itc = 0
                total_igst_itc = 0
                total_cess_itc = 0
                unique_suppliers = set()
                reverse_charge_invoices = 0
                import_invoices = 0
                
                for invoice in invoices:
                    supplier_gstin = invoice.get("supplier_gstin", "")
                    if supplier_gstin:
                        unique_suppliers.add(supplier_gstin)
                    
                    # Check for reverse charge and import indicators
                    if "reverse charge" in str(invoice).lower():
                        reverse_charge_invoices += 1
                    if "import" in str(invoice).lower() or "customs" in str(invoice).lower():
                        import_invoices += 1
                    
                    # Calculate ITC from items
                    for item in invoice.get("items", []):
                        total_cgst_itc += float(item.get("cgst", 0))
                        total_sgst_itc += float(item.get("sgst", 0))
                        total_igst_itc += float(item.get("igst", 0))
                        total_cess_itc += float(item.get("cess", 0))
                
                total_itc_claimed = total_cgst_itc + total_sgst_itc + total_igst_itc + total_cess_itc
                
                # Create return record
                return_id = str(uuid.uuid4())
                
                # Prepare complete JSON data
                json_data = {
                    "return_id": return_id,
                    "filing_period": filing_period,
                    "extraction_result": validated_data,
                    "processed_at": datetime.now().isoformat()
                }
                
                gstr2_return = GSTR2ReturnDB(
                    id=return_id,
                    user_id=user.id if user else "system",
                    gstin=user.gstin if user else header.get("gstin", ""),
                    company_name=user.company_name if user else header.get("company_name", ""),
                    filing_period=filing_period,
                    status="completed",
                    total_invoices=summary.get("total_invoices", len(invoices)),
                    total_taxable_value=summary.get("total_taxable_value", 0.0),
                    total_tax=summary.get("total_tax", 0.0),
                    total_invoice_value=summary.get("total_taxable_value", 0.0) + summary.get("total_tax", 0.0),
                    total_itc_claimed=total_itc_claimed,
                    total_cgst_itc=total_cgst_itc,
                    total_sgst_itc=total_sgst_itc,
                    total_igst_itc=total_igst_itc,
                    total_cess_itc=total_cess_itc,
                    unique_suppliers=len(unique_suppliers),
                    reverse_charge_invoices=reverse_charge_invoices,
                    import_invoices=import_invoices,
                    json_data=json.dumps(json_data),
                    created_at=datetime.now()
                )
                
                db.add(gstr2_return)
                db.commit()
                print(f"✅ GSTR-2 data saved to database with return ID: {return_id}")
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error saving GSTR-2 data to database: {e}")

    def _create_empty_response(self, filing_period: str = None) -> Dict[str, Any]:
        """Create empty GSTR-2 response structure."""
        period = filing_period or datetime.now().strftime("%Y-%m")
        
        return {
            "gstr2_return": {
                "header": {
                    "gstin": "Your GSTIN",
                    "company_name": "Your Company",
                    "filing_period": period
                },
                "inward_invoices": [],
                "summary": {
                    "total_invoices": 0,
                    "total_taxable_value": 0,
                    "total_tax": 0
                }
            },
            "extraction_notes": "No valid GSTR-2 inward supply data found in the provided documents"
        }
