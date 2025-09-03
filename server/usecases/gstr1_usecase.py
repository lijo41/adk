"""GSTR-1 processing use cases."""

import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal

from models.gstr1 import GSTR1Return, GSTR1Header, B2BInvoice, B2BItem, HSNSummary
from gstr1_template import get_empty_gstr1_template


class GSTR1UseCase:
    """Business logic for GSTR-1 operations."""
    
    def __init__(self):
        self.storage_path = Path("storage/gstr1")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._gstr1_returns = {}  # In-memory storage for GSTR-1 returns
    
    def create_gstr1_return(self, gstin: str, company_name: str, filing_period: str, 
                           gross_turnover: Decimal) -> GSTR1Return:
        """Create a new GSTR-1 return."""
        return_id = str(uuid.uuid4())
        
        header = GSTR1Header(
            gstin=gstin,
            company_name=company_name,
            filing_period=filing_period,
            return_period=filing_period,
            filing_date=datetime.now().strftime("%d-%m-%Y"),
            gross_turnover=gross_turnover
        )
        
        gstr1_return = GSTR1Return(
            id=return_id,
            header=header,
            b2b_invoices=[],
            hsn_summary=[],
            created_time=datetime.now()
        )
        
        # Store in memory
        self._gstr1_returns[return_id] = gstr1_return
        return gstr1_return
    
    def generate_gstr1_json(self, gstr1_return: GSTR1Return) -> Dict[str, Any]:
        """Generate GSTR-1 JSON from document chunks using AI."""
        from shared_instances import document_usecase, chat_usecase
        
        template = get_empty_gstr1_template()
        
        # Update header
        template["gstr1_return"]["header"].update({
            "gstin": gstr1_return.header.gstin,
            "company_name": gstr1_return.header.company_name,
            "filing_period": gstr1_return.header.filing_period
        })
        
        # Get all uploaded documents
        documents = document_usecase.list_documents()
        
        if not documents:
            return template
        
        # Extract invoice data from documents using AI
        invoices = []
        seen_invoices = set()  # Track unique invoices by invoice_no + date
        total_taxable_value = 0
        total_tax = 0
        total_invoice_value = 0
        
        for document in documents:
            # Only process successfully processed documents
            if document.status.value != "processed":
                continue
                
            chunks = document_usecase.get_chunks(document.id)
            if not chunks:
                chunks = document_usecase.create_chunks(document)
            
            # Debug: Print chunk info
            print(f"Document {document.filename}: {len(chunks)} chunks found")
            
            # Use AI to extract invoice information
            invoice_data = self._extract_invoice_from_chunks(document, chunks)
            if invoice_data:
                # Remove duplicates based on invoice_no + invoice_date
                for invoice in invoice_data:
                    invoice_key = f"{invoice.get('invoice_no', '')}_{invoice.get('invoice_date', '')}"
                    if invoice_key not in seen_invoices:
                        seen_invoices.add(invoice_key)
                        invoices.append(invoice)
                    else:
                        print(f"Skipping duplicate invoice: {invoice.get('invoice_no', 'Unknown')}")
        
        # Calculate totals
        for invoice in invoices:
            total_invoice_value += invoice.get("invoice_value", 0) or 0
            for item in invoice.get("items", []):
                total_taxable_value += item.get("taxable_value", 0) or 0
                igst = item.get("igst", 0) or 0
                cgst = item.get("cgst", 0) or 0
                sgst = item.get("sgst", 0) or 0
                cess = item.get("cess", 0) or 0
                total_tax += igst + cgst + sgst + cess
        
        template["gstr1_return"]["invoices"] = invoices
        
        # Update summary
        template["gstr1_return"]["summary"].update({
            "total_invoices": len(invoices),
            "total_taxable_value": total_taxable_value,
            "total_tax": total_tax,
            "total_invoice_value": total_invoice_value
        })
        
        return template
    
    def _extract_invoice_from_chunks(self, document, chunks) -> List[Dict[str, Any]]:
        """Extract invoice data from document chunks using AI."""
        from shared_instances import chat_usecase
        
        if not chunks:
            return []
        
        # Use ALL available chunks, not just first 5
        content = "\n\n".join([chunk.content for chunk in chunks])
        
        # Debug: Print content length
        print(f"Processing document {document.filename} with {len(chunks)} chunks, content length: {len(content)}")
        
        prompt = f"""You are a GST invoice data extraction expert. Extract ALL invoice information from this document content.

IMPORTANT: This appears to be a GST tax invoice. Look carefully for:

1. INVOICE DETAILS:
   - Invoice number (may be prefixed with GST-, INV-, etc.)
   - Invoice date (DD-MM-YYYY or DD/MM/YYYY format)
   - Total invoice value/amount

2. RECIPIENT/BUYER DETAILS:
   - Recipient GSTIN (15-digit alphanumeric)
   - Company/buyer name
   - State/place of supply

3. ITEM/PRODUCT DETAILS:
   - Product/service descriptions
   - HSN/SAC codes (4-8 digits)
   - Quantities
   - Unit prices/rates
   - Taxable values

4. TAX DETAILS:
   - IGST amounts and rates
   - CGST amounts and rates  
   - SGST amounts and rates
   - CESS amounts (if any)

Extract this information and format as a JSON array. Even if some fields are missing, include what you can find:

[
  {{
    "invoice_no": "found_invoice_number",
    "invoice_date": "YYYY-MM-DD",
    "recipient_gstin": "found_gstin_or_empty",
    "place_of_supply": "found_state_or_location",
    "invoice_value": found_total_amount,
    "items": [
      {{
        "product_name": "found_product_description",
        "hsn_code": "found_hsn_code",
        "quantity": found_quantity,
        "unit_price": found_unit_price,
        "taxable_value": found_taxable_value,
        "igst": found_igst_amount,
        "cgst": found_cgst_amount,
        "sgst": found_sgst_amount,
        "cess": found_cess_amount
      }}
    ]
  }}
]

Document content to analyze:
{content}

Return ONLY the JSON array, no explanations or other text:"""
        
        try:
            response = chat_usecase.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Debug: Print AI response
            print(f"AI Response for {document.filename}: {response_text[:500]}...")
            
            # Clean up response to extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            import json
            invoice_data = json.loads(response_text)
            print(f"Parsed invoice data: {invoice_data}")
            
            # Ensure we return a list and handle duplicates within the AI response
            if isinstance(invoice_data, list):
                # Remove duplicates within the AI response itself
                unique_invoices = []
                seen_in_response = set()
                for invoice in invoice_data:
                    invoice_key = f"{invoice.get('invoice_no', '')}_{invoice.get('invoice_date', '')}"
                    if invoice_key not in seen_in_response:
                        seen_in_response.add(invoice_key)
                        unique_invoices.append(invoice)
                return unique_invoices
            else:
                return [invoice_data]
            
        except Exception as e:
            print(f"Error extracting invoice data from {document.filename}: {str(e)}")
            print(f"Raw response: {response_text[:200] if 'response_text' in locals() else 'No response'}")
            return []
    
    def save_gstr1_return(self, gstr1_return: GSTR1Return) -> str:
        """Save GSTR-1 return to storage."""
        json_data = self.generate_gstr1_json(gstr1_return)
        gstr1_return.json_data = json_data
        gstr1_return.updated_time = datetime.now()
        
        # Save to file
        file_path = self.storage_path / f"{gstr1_return.id}.json"
        file_path.write_text(json.dumps(json_data, indent=2))
        
        return str(file_path)
    
    def load_gstr1_return(self, return_id: str) -> Optional[GSTR1Return]:
        """Load GSTR-1 return from storage."""
        return self._gstr1_returns.get(return_id)
    
    def list_gstr1_returns(self) -> List[str]:
        """List all GSTR-1 return IDs."""
        return list(self._gstr1_returns.keys())
