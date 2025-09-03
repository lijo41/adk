"""GSTR-1 API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from usecases.gstr1_usecase import GSTR1UseCase
from models.gstr1 import GSTR1Header
from decimal import Decimal
import os
from dotenv import load_dotenv

from shared_instances import document_usecase, gstr1_usecase

# Load environment
load_dotenv()

gstr1_router = APIRouter(prefix="/api/gstr1", tags=["gstr1"])


class GSTR1CreateRequest(BaseModel):
    gstin: str
    company_name: str
    filing_period: str
    gross_turnover: float


class B2BItemRequest(BaseModel):
    sr_no: int
    description: str
    hsn_code: str
    quantity: float
    unit: str
    rate: float
    taxable_value: float
    cgst_rate: float
    cgst_amount: float
    sgst_rate: float
    sgst_amount: float
    igst_rate: float
    igst_amount: float
    cess_rate: float = 0.0
    cess_amount: float = 0.0


class B2BInvoiceRequest(BaseModel):
    invoice_number: str
    invoice_date: str
    invoice_value: float
    place_of_supply: str
    reverse_charge: str
    invoice_type: str
    recipient_gstin: str
    recipient_name: str
    recipient_state: str
    items: List[B2BItemRequest]


@gstr1_router.post("/create")
async def create_gstr1_return(request: GSTR1CreateRequest):
    """Create a new GSTR-1 return."""
    try:
        gstr1_return = gstr1_usecase.create_gstr1_return(
            gstin=request.gstin,
            company_name=request.company_name,
            filing_period=request.filing_period,
            gross_turnover=Decimal(str(request.gross_turnover))
        )
        
        return {
            "return_id": gstr1_return.id,
            "gstin": gstr1_return.header.gstin,
            "company_name": gstr1_return.header.company_name,
            "filing_period": gstr1_return.header.filing_period,
            "status": gstr1_return.header.status,
            "created_time": gstr1_return.created_time.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.get("/{return_id}/json")
async def generate_gstr1_json(return_id: str):
    """Generate GSTR-1 JSON for a return."""
    try:
        gstr1_return = gstr1_usecase.load_gstr1_return(return_id)
        if not gstr1_return:
            raise HTTPException(status_code=404, detail="GSTR-1 return not found")
        
        # Generate JSON and save to database
        gstr1_usecase.save_gstr1_return(gstr1_return)
        json_data = gstr1_return.json_data
        
        if not json_data:
            json_data = gstr1_usecase.generate_gstr1_json(gstr1_return)
            
        return json_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.delete("/clear")
async def clear_database():
    """Clear all GSTR-1 data from database."""
    try:
        gstr1_usecase.clear_database()
        return {"message": "Database cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.get("/{return_id}/table")
async def get_gstr1_table(return_id: str):
    """Get GSTR-1 data in table format."""
    try:
        table_data = gstr1_usecase.get_gstr1_table_view(return_id)
        if not table_data:
            raise HTTPException(status_code=404, detail="GSTR-1 return not found")
        return table_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.post("/{return_id}/save")
async def save_gstr1_return(return_id: str):
    """Save GSTR-1 return to storage."""
    try:
        gstr1_return = gstr1_usecase.load_gstr1_return(return_id)
        if not gstr1_return:
            raise HTTPException(status_code=404, detail="GSTR-1 return not found")
        
        file_path = gstr1_usecase.save_gstr1_return(gstr1_return)
        
        return {
            "message": "GSTR-1 return saved successfully",
            "file_path": file_path,
            "return_id": return_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.get("/list")
async def list_gstr1_returns():
    """List all GSTR-1 returns."""
    try:
        return_ids = gstr1_usecase.list_gstr1_returns()
        return {
            "returns": return_ids,
            "count": len(return_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.get("/{return_id}")
async def get_gstr1_return(return_id: str):
    """Get GSTR-1 return details."""
    try:
        gstr1_return = gstr1_usecase.load_gstr1_return(return_id)
        if not gstr1_return:
            raise HTTPException(status_code=404, detail="GSTR-1 return not found")
        
        return {
            "return_id": gstr1_return.id,
            "header": {
                "gstin": gstr1_return.header.gstin,
                "company_name": gstr1_return.header.company_name,
                "filing_period": gstr1_return.header.filing_period,
                "gross_turnover": float(gstr1_return.header.gross_turnover),
                "status": gstr1_return.header.status
            },
            "b2b_invoices_count": len(gstr1_return.b2b_invoices),
            "hsn_summary_count": len(gstr1_return.hsn_summary),
            "total_b2b_value": float(gstr1_return.total_b2b_value),
            "created_time": gstr1_return.created_time.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
