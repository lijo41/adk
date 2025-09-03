"""Standalone GSTR-2 Template Extraction Agent - Independent Implementation."""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

class GSTR2TemplateAgent:
    """Standalone agent for GSTR-2 inward supply extraction based on template structure."""
    
    def __init__(self):
        """Initialize the GSTR-2 template agent."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GOOGLE_API_KEY in .env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    
    def extract_gstr2_template(self, document_chunks: List[str], filing_period: str = None) -> Dict[str, Any]:
        """
        Extract GSTR-2 data according to template structure.
        
        Args:
            document_chunks: List of document text chunks to process
            filing_period: Filing period (e.g., "January 2024")
            
        Returns:
            Dictionary containing GSTR-2 template structure
        """
        try:
            # Combine all chunks
            combined_text = "\n\n".join(document_chunks)
            
            # Create extraction prompt
            prompt = self._create_gstr2_template_prompt(combined_text, filing_period)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            extracted_data = json.loads(response.text.strip())
            
            # Validate and clean data
            validated_data = self._validate_template_data(extracted_data, filing_period)
            
            return validated_data
            
        except Exception as e:
            print(f"GSTR-2 template extraction error: {e}")
            return self._create_fallback_template(filing_period)
    
    def _create_gstr2_template_prompt(self, text: str, filing_period: str = None) -> str:
        """Create AI prompt for GSTR-2 template extraction."""
        
        template_structure = {
            "gstr2_return": {
                "header": {
                    "gstin": "Recipient GSTIN",
                    "company_name": "Recipient Company Name",
                    "filing_period": filing_period or "Filing Period",
                    "return_type": "GSTR-2"
                },
                "inward_supplies": {
                    "b2b": [],
                    "b2bur": [],
                    "cdnr": [],
                    "cdnur": [],
                    "imp_g": [],
                    "imp_s": [],
                    "itc_rev": []
                },
                "summary": {
                    "total_invoices": 0,
                    "total_taxable_value": 0.0,
                    "total_tax_amount": 0.0,
                    "total_itc_available": 0.0,
                    "itc_breakdown": {
                        "cgst": 0.0,
                        "sgst": 0.0,
                        "igst": 0.0,
                        "cess": 0.0
                    }
                }
            }
        }
        
        return f"""
You are a GST expert. Extract GSTR-2 inward supply data from the following document text and return it in the exact JSON template structure provided.

GSTR-2 Template Structure:
{json.dumps(template_structure, indent=2)}

Document Text:
{text}

Instructions:
1. Extract all inward supply invoices (purchases/receipts)
2. Categorize into appropriate GSTR-2 sections:
   - b2b: Business to Business supplies
   - b2bur: B2B Unregistered supplies  
   - cdnr: Credit/Debit Notes Registered
   - cdnur: Credit/Debit Notes Unregistered
   - imp_g: Import of Goods
   - imp_s: Import of Services
   - itc_rev: ITC Reversal

3. For each invoice, extract:
   - Invoice number and date
   - Supplier GSTIN and name
   - Item details with HSN codes
   - Taxable values
   - Tax amounts (CGST, SGST, IGST, CESS)
   - ITC eligibility

4. Calculate summary totals accurately
5. Return ONLY valid JSON matching the template structure
6. Use 0.0 for missing numeric values
7. Use empty arrays [] for missing invoice lists

Return the complete GSTR-2 template structure as JSON:
"""
    
    def _validate_template_data(self, data: Dict[str, Any], filing_period: str = None) -> Dict[str, Any]:
        """Validate and clean extracted template data."""
        
        # Ensure main structure exists
        if "gstr2_return" not in data:
            data = {"gstr2_return": data}
        
        gstr2_data = data["gstr2_return"]
        
        # Validate header
        if "header" not in gstr2_data:
            gstr2_data["header"] = {}
        
        header = gstr2_data["header"]
        header.setdefault("gstin", "")
        header.setdefault("company_name", "")
        header.setdefault("filing_period", filing_period or "")
        header.setdefault("return_type", "GSTR-2")
        
        # Validate inward_supplies structure
        if "inward_supplies" not in gstr2_data:
            gstr2_data["inward_supplies"] = {}
        
        supplies = gstr2_data["inward_supplies"]
        
        # Ensure all GSTR-2 sections exist
        gstr2_sections = ["b2b", "b2bur", "cdnr", "cdnur", "imp_g", "imp_s", "itc_rev"]
        for section in gstr2_sections:
            if section not in supplies:
                supplies[section] = []
            elif not isinstance(supplies[section], list):
                supplies[section] = []
        
        # Clean and validate invoices in each section
        total_invoices = 0
        total_taxable_value = 0.0
        total_tax_amount = 0.0
        cgst_total = 0.0
        sgst_total = 0.0
        igst_total = 0.0
        cess_total = 0.0
        
        for section_name, invoices in supplies.items():
            cleaned_invoices = []
            
            for invoice in invoices:
                cleaned_invoice = self._clean_template_invoice(invoice)
                if cleaned_invoice:
                    cleaned_invoices.append(cleaned_invoice)
                    total_invoices += 1
                    
                    # Calculate totals
                    invoice_taxable = cleaned_invoice.get("taxable_value", 0.0)
                    total_taxable_value += invoice_taxable
                    
                    # Sum tax amounts from items
                    for item in cleaned_invoice.get("items", []):
                        cgst_total += item.get("cgst", 0.0)
                        sgst_total += item.get("sgst", 0.0)
                        igst_total += item.get("igst", 0.0)
                        cess_total += item.get("cess", 0.0)
            
            supplies[section_name] = cleaned_invoices
        
        total_tax_amount = cgst_total + sgst_total + igst_total + cess_total
        
        # Validate summary
        if "summary" not in gstr2_data:
            gstr2_data["summary"] = {}
        
        summary = gstr2_data["summary"]
        summary["total_invoices"] = total_invoices
        summary["total_taxable_value"] = round(total_taxable_value, 2)
        summary["total_tax_amount"] = round(total_tax_amount, 2)
        summary["total_itc_available"] = round(total_tax_amount, 2)  # Assuming all tax is eligible ITC
        
        summary["itc_breakdown"] = {
            "cgst": round(cgst_total, 2),
            "sgst": round(sgst_total, 2),
            "igst": round(igst_total, 2),
            "cess": round(cess_total, 2)
        }
        
        return data
    
    def _clean_template_invoice(self, invoice: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean and validate individual invoice data for template."""
        
        if not isinstance(invoice, dict):
            return None
        
        cleaned = {
            "invoice_no": str(invoice.get("invoice_no", "")).strip(),
            "invoice_date": str(invoice.get("invoice_date", "")).strip(),
            "supplier_gstin": str(invoice.get("supplier_gstin", "")).strip(),
            "supplier_name": str(invoice.get("supplier_name", "")).strip(),
            "place_of_supply": str(invoice.get("place_of_supply", "")).strip(),
            "reverse_charge": invoice.get("reverse_charge", "N"),
            "invoice_type": str(invoice.get("invoice_type", "Regular")).strip(),
            "taxable_value": float(invoice.get("taxable_value", 0.0)),
            "items": []
        }
        
        # Skip if no invoice number
        if not cleaned["invoice_no"]:
            return None
        
        # Clean items
        items = invoice.get("items", [])
        if not isinstance(items, list):
            items = []
        
        for item in items:
            if isinstance(item, dict):
                cleaned_item = {
                    "description": str(item.get("description", "")).strip(),
                    "hsn_code": str(item.get("hsn_code", "")).strip(),
                    "quantity": float(item.get("quantity", 0.0)),
                    "unit": str(item.get("unit", "")).strip(),
                    "rate": float(item.get("rate", 0.0)),
                    "taxable_value": float(item.get("taxable_value", 0.0)),
                    "cgst_rate": float(item.get("cgst_rate", 0.0)),
                    "cgst": float(item.get("cgst", 0.0)),
                    "sgst_rate": float(item.get("sgst_rate", 0.0)),
                    "sgst": float(item.get("sgst", 0.0)),
                    "igst_rate": float(item.get("igst_rate", 0.0)),
                    "igst": float(item.get("igst", 0.0)),
                    "cess_rate": float(item.get("cess_rate", 0.0)),
                    "cess": float(item.get("cess", 0.0)),
                    "itc_eligibility": str(item.get("itc_eligibility", "Yes")).strip()
                }
                cleaned["items"].append(cleaned_item)
        
        return cleaned
    
    def _create_fallback_template(self, filing_period: str = None) -> Dict[str, Any]:
        """Create fallback template structure when extraction fails."""
        
        return {
            "gstr2_return": {
                "header": {
                    "gstin": "",
                    "company_name": "",
                    "filing_period": filing_period or "",
                    "return_type": "GSTR-2"
                },
                "inward_supplies": {
                    "b2b": [],
                    "b2bur": [],
                    "cdnr": [],
                    "cdnur": [],
                    "imp_g": [],
                    "imp_s": [],
                    "itc_rev": []
                },
                "summary": {
                    "total_invoices": 0,
                    "total_taxable_value": 0.0,
                    "total_tax_amount": 0.0,
                    "total_itc_available": 0.0,
                    "itc_breakdown": {
                        "cgst": 0.0,
                        "sgst": 0.0,
                        "igst": 0.0,
                        "cess": 0.0
                    }
                },
                "extraction_status": "fallback",
                "message": "Template extraction failed, using fallback structure"
            }
        }
    
    def get_template_structure(self) -> Dict[str, Any]:
        """Return the GSTR-2 template structure for reference."""
        
        return {
            "gstr2_return": {
                "header": {
                    "gstin": "15-character GSTIN of recipient",
                    "company_name": "Legal name of the company",
                    "filing_period": "MM-YYYY format (e.g., 01-2024)",
                    "return_type": "GSTR-2"
                },
                "inward_supplies": {
                    "b2b": [
                        {
                            "invoice_no": "Invoice number",
                            "invoice_date": "DD/MM/YYYY",
                            "supplier_gstin": "15-character supplier GSTIN",
                            "supplier_name": "Supplier legal name",
                            "place_of_supply": "State code",
                            "reverse_charge": "Y/N",
                            "invoice_type": "Regular/SEZ/Deemed Export",
                            "taxable_value": 0.0,
                            "items": [
                                {
                                    "description": "Item description",
                                    "hsn_code": "HSN/SAC code",
                                    "quantity": 0.0,
                                    "unit": "Unit of measurement",
                                    "rate": 0.0,
                                    "taxable_value": 0.0,
                                    "cgst_rate": 0.0,
                                    "cgst": 0.0,
                                    "sgst_rate": 0.0,
                                    "sgst": 0.0,
                                    "igst_rate": 0.0,
                                    "igst": 0.0,
                                    "cess_rate": 0.0,
                                    "cess": 0.0,
                                    "itc_eligibility": "Yes/No/Partial"
                                }
                            ]
                        }
                    ],
                    "b2bur": "B2B Unregistered supplies",
                    "cdnr": "Credit/Debit Notes Registered",
                    "cdnur": "Credit/Debit Notes Unregistered", 
                    "imp_g": "Import of Goods",
                    "imp_s": "Import of Services",
                    "itc_rev": "ITC Reversal entries"
                },
                "summary": {
                    "total_invoices": "Total number of inward invoices",
                    "total_taxable_value": "Sum of all taxable values",
                    "total_tax_amount": "Sum of all tax amounts",
                    "total_itc_available": "Total ITC available for claim",
                    "itc_breakdown": {
                        "cgst": "Total CGST ITC",
                        "sgst": "Total SGST ITC", 
                        "igst": "Total IGST ITC",
                        "cess": "Total CESS ITC"
                    }
                }
            }
        }
