"""GSTR-1 processing use cases."""

import uuid
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime
from decimal import Decimal

from models.gstr1 import GSTR1Return, GSTR1Header
from database import SessionLocal
from schemas import GSTR1Return as GSTR1ReturnDB, Invoice as InvoiceDB, InvoiceItem as InvoiceItemDB, GSTR1Summary as GSTR1SummaryDB
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
        from shared_instances import document_usecase
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
        """Save GSTR-1 return to storage and database."""
        json_data = self.generate_gstr1_json(gstr1_return)
        gstr1_return.json_data = json_data
        gstr1_return.updated_time = datetime.now()
        
        # Save to file
        file_path = self.storage_path / f"{gstr1_return.id}.json"
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        # Save to database with duplicate check
        saved_id = self._save_to_database(gstr1_return, json_data)
        if saved_id != str(gstr1_return.id):
            # Return existing duplicate ID instead of creating new one
            return saved_id
        
        # Store in memory
        self._gstr1_returns[gstr1_return.id] = gstr1_return
        
        return str(file_path)
    
    def load_gstr1_return(self, return_id: str) -> Optional[GSTR1Return]:
        """Load GSTR-1 return from storage."""
        return self._gstr1_returns.get(return_id)
    
    def clear_database(self):
        """Clear all GSTR-1 data from database."""
        db = SessionLocal()
        try:
            # Delete in correct order due to foreign key constraints
            db.query(InvoiceItemDB).delete()
            db.query(InvoiceDB).delete()
            db.query(GSTR1SummaryDB).delete()
            db.query(GSTR1ReturnDB).delete()
            db.commit()
            print("Database cleared successfully")
        except Exception as e:
            db.rollback()
            print(f"Error clearing database: {str(e)}")
            raise
        finally:
            db.close()
    
    def list_gstr1_returns(self) -> List[str]:
        """List all GSTR-1 return IDs from database."""
        db = SessionLocal()
        try:
            returns = db.query(GSTR1ReturnDB).all()
            return [return_obj.id for return_obj in returns]
        except Exception as e:
            print(f"Error listing returns: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_gstr1_table_view(self, return_id: str) -> Optional[Dict[str, Any]]:
        """Get GSTR-1 data in table format from database."""
        db = SessionLocal()
        try:
            # Try to find by UUID directly in database
            db_return = db.query(GSTR1ReturnDB).filter(GSTR1ReturnDB.id == return_id).first()
            
            if not db_return:
                return None
            
            # Get invoices with items
            invoices = db.query(InvoiceDB).filter(InvoiceDB.gstr1_id == db_return.id).all()
            
            # Get summary
            summary = db.query(GSTR1SummaryDB).filter(GSTR1SummaryDB.gstr1_id == db_return.id).first()
            
            # Format data for table view
            table_data = {
                "header": {
                    "gstin": db_return.gstin,
                    "company_name": db_return.company_name,
                    "filing_period": db_return.filing_period,
                    "status": db_return.status,
                    "created_at": db_return.created_at.isoformat(),
                    "updated_at": db_return.updated_at.isoformat() if db_return.updated_at else None
                },
                "invoices": [],
                "summary": {
                    "total_invoices": summary.total_invoices if summary else 0,
                    "total_taxable_value": float(summary.total_taxable_value) if summary else 0,
                    "total_tax": float(summary.total_tax) if summary else 0,
                    "total_invoice_value": float(summary.total_invoice_value) if summary else 0
                }
            }
            
            # Add invoice details
            for invoice in invoices:
                items = db.query(InvoiceItemDB).filter(InvoiceItemDB.invoice_id == invoice.id).all()
                
                invoice_data = {
                    "invoice_no": invoice.invoice_no,
                    "invoice_date": invoice.invoice_date if isinstance(invoice.invoice_date, str) else invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                    "recipient_gstin": invoice.recipient_gstin,
                    "place_of_supply": invoice.place_of_supply,
                    "invoice_value": float(invoice.invoice_value) if invoice.invoice_value else 0,
                    "items": []
                }
                
                for item in items:
                    invoice_data["items"].append({
                        "product_name": item.product_name,
                        "hsn_code": item.hsn_code,
                        "quantity": float(item.quantity) if item.quantity else 0,
                        "unit_price": float(item.unit_price) if item.unit_price else 0,
                        "taxable_value": float(item.taxable_value) if item.taxable_value else 0,
                        "igst": float(item.igst) if item.igst else 0,
                        "cgst": float(item.cgst) if item.cgst else 0,
                        "sgst": float(item.sgst) if item.sgst else 0,
                        "cess": float(item.cess) if item.cess else 0
                    })
                
                table_data["invoices"].append(invoice_data)
            
            return table_data
            
        except Exception as e:
            return None
        finally:
            db.close()
    
    def _check_duplicate_return(self, gstin: str, filing_period: str, invoices: List[Dict]) -> str:
        """Check if duplicate GSTR-1 return exists based on GSTIN, period, and invoice signatures."""
        db = SessionLocal()
        try:
            # Get existing returns for same GSTIN and period
            existing_returns = db.query(GSTR1ReturnDB).filter(
                GSTR1ReturnDB.gstin == gstin,
                GSTR1ReturnDB.filing_period == filing_period
            ).all()
            
            if not existing_returns:
                return None
                
            # Create signature for current invoices
            current_signature = self._create_invoice_signature(invoices)
            
            # Check each existing return
            for existing_return in existing_returns:
                existing_invoices = db.query(InvoiceDB).filter(
                    InvoiceDB.gstr1_id == existing_return.id
                ).all()
                
                existing_invoice_data = []
                for inv in existing_invoices:
                    existing_invoice_data.append({
                        "invoice_no": inv.invoice_no,
                        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
                        "recipient_gstin": inv.recipient_gstin,
                        "invoice_value": float(inv.invoice_value)
                    })
                
                existing_signature = self._create_invoice_signature(existing_invoice_data)
                
                if current_signature == existing_signature:
                    return str(existing_return.id)
                    
            return None
        finally:
            db.close()
    
    def _create_invoice_signature(self, invoices: List[Dict]) -> str:
        """Create a unique signature for a set of invoices."""
        invoice_keys = []
        for invoice in invoices:
            key = f"{invoice.get('invoice_no', '')}_{invoice.get('invoice_date', '')}_{invoice.get('recipient_gstin', '')}_{invoice.get('invoice_value', 0)}"
            invoice_keys.append(key)
        
        # Sort to ensure consistent signature regardless of order
        invoice_keys.sort()
        return "|".join(invoice_keys)

    def _save_to_database(self, gstr1_return: GSTR1Return, json_data: dict):
        """Save GSTR-1 return to database with duplicate check."""
        # Check for duplicates first
        invoices_data = json_data.get("gstr1_return", {}).get("invoices", [])
        duplicate_id = self._check_duplicate_return(
            gstr1_return.header.gstin,
            gstr1_return.header.filing_period,
            invoices_data
        )
        
        if duplicate_id:
            print(f"Duplicate GSTR-1 return found with ID: {duplicate_id}")
            return duplicate_id
        
        db = SessionLocal()
        try:
            # Save GSTR-1 return
            db_return = GSTR1ReturnDB(
                id=gstr1_return.id,
                gstin=gstr1_return.header.gstin,
                company_name=gstr1_return.header.company_name,
                filing_period=gstr1_return.header.filing_period,
                status=gstr1_return.header.status,
                created_at=gstr1_return.created_time,
                updated_at=gstr1_return.updated_time
            )
            db.add(db_return)
            db.flush()  # Get the ID
            
            # Extract invoices from JSON data
            invoices_data = json_data.get('gstr1_return', {}).get('invoices', [])
            
            for invoice_data in invoices_data:
                # Create Invoice record
                db_invoice = InvoiceDB(
                    gstr1_id=db_return.id,
                    invoice_no=invoice_data.get('invoice_no'),
                    invoice_date=datetime.strptime(invoice_data.get('invoice_date'), '%Y-%m-%d').date() if invoice_data.get('invoice_date') else None,
                    recipient_gstin=invoice_data.get('recipient_gstin'),
                    place_of_supply=invoice_data.get('place_of_supply'),
                    invoice_value=Decimal(str(invoice_data.get('invoice_value', 0)))
                )
                db.add(db_invoice)
                db.flush()  # Get the ID
                
                # Create Invoice Items
                for item_data in invoice_data.get('items', []):
                    db_item = InvoiceItemDB(
                        invoice_id=db_invoice.id,
                        product_name=item_data.get('product_name'),
                        hsn_code=item_data.get('hsn_code'),
                        quantity=Decimal(str(item_data.get('quantity', 0))) if item_data.get('quantity') else None,
                        unit_price=Decimal(str(item_data.get('unit_price', 0))) if item_data.get('unit_price') else None,
                        taxable_value=Decimal(str(item_data.get('taxable_value', 0))) if item_data.get('taxable_value') else None,
                        igst=Decimal(str(item_data.get('igst', 0))) if item_data.get('igst') else None,
                        cgst=Decimal(str(item_data.get('cgst', 0))) if item_data.get('cgst') else None,
                        sgst=Decimal(str(item_data.get('sgst', 0))) if item_data.get('sgst') else None,
                        cess=Decimal(str(item_data.get('cess', 0))) if item_data.get('cess') else None
                    )
                    db.add(db_item)
            
            # Create Summary record
            summary_data = json_data.get('gstr1_return', {}).get('summary', {})
            db_summary = GSTR1SummaryDB(
                gstr1_id=db_return.id,
                total_invoices=summary_data.get('total_invoices', 0),
                total_taxable_value=Decimal(str(summary_data.get('total_taxable_value', 0))),
                total_tax=Decimal(str(summary_data.get('total_tax', 0))),
                total_invoice_value=Decimal(str(summary_data.get('total_invoice_value', 0)))
            )
            db.add(db_summary)
            
            db.commit()
            print(f"Successfully saved GSTR-1 return {gstr1_return.id} to database")
            return str(gstr1_return.id)
            
        except Exception as e:
            db.rollback()
            print(f"Error saving to database: {str(e)}")
            raise
        finally:
            db.close()
