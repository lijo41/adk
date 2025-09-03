"""Database schemas for GSTR-1 filing system using SQLAlchemy."""

from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()


class GSTR1Return(Base):
    """GSTR-1 return header table."""
    __tablename__ = 'gstr1_return'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gstin = Column(String(15), nullable=False)
    company_name = Column(String(255))
    filing_period = Column(String(6))  # e.g., '072024'
    status = Column(String(20), default='draft')  # draft, filed, submitted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="gstr1_return", cascade="all, delete-orphan")
    summary = relationship("GSTR1Summary", back_populates="gstr1_return", uselist=False, cascade="all, delete-orphan")


class Invoice(Base):
    """Invoices table for GSTR-1 filing."""
    __tablename__ = 'invoices'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gstr1_id = Column(String(36), ForeignKey('gstr1_return.id', ondelete='CASCADE'), nullable=False)
    invoice_no = Column(String(50))
    invoice_date = Column(Date)
    recipient_gstin = Column(String(15))
    place_of_supply = Column(String(50))
    invoice_value = Column(Numeric(12, 2))
    
    # Unique constraint to prevent duplicates
    __table_args__ = (
        UniqueConstraint('gstr1_id', 'invoice_no', 'invoice_date', name='unique_invoice_per_return'),
    )
    
    # Relationships
    gstr1_return = relationship("GSTR1Return", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    """Invoice items/line items table."""
    __tablename__ = 'invoice_items'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String(36), ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)
    product_name = Column(String(255))
    hsn_code = Column(String(10))
    quantity = Column(Numeric(12, 2))
    unit_price = Column(Numeric(12, 2))
    taxable_value = Column(Numeric(12, 2))
    igst = Column(Numeric(12, 2))
    cgst = Column(Numeric(12, 2))
    sgst = Column(Numeric(12, 2))
    cess = Column(Numeric(12, 2))
    
    # Relationship
    invoice = relationship("Invoice", back_populates="items")


class GSTR1Summary(Base):
    """GSTR-1 summary table."""
    __tablename__ = 'gstr1_summary'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gstr1_id = Column(String(36), ForeignKey('gstr1_return.id', ondelete='CASCADE'), nullable=False)
    total_invoices = Column(Integer)
    total_taxable_value = Column(Numeric(12, 2))
    total_tax = Column(Numeric(12, 2))
    total_invoice_value = Column(Numeric(12, 2))
    
    # Relationship
    gstr1_return = relationship("GSTR1Return", back_populates="summary")
