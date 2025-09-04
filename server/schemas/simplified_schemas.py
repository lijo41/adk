"""Simplified database schemas with user authentication support."""

from sqlalchemy import Column, String, DateTime, Text, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base
import uuid
from datetime import datetime


class UserDB(Base):
    """User table for JWT authentication with seller/company details."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User profile
    full_name = Column(String(255))
    phone = Column(String(20))
    
    # Seller/Company Header Details (for GSTR-1 reports)
    company_name = Column(String(255), nullable=False)
    gstin = Column(String(15), nullable=False, index=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    gstr1_returns = relationship("GSTR1ReturnDB", back_populates="user")


class GSTR1ReturnDB(Base):
    """Simplified GSTR-1 Return table with user relationship."""
    __tablename__ = "gstr1_returns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Header details
    gstin = Column(String(15), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    filing_period = Column(String(6), nullable=False, index=True)  # MMYYYY
    gross_turnover = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default="draft", index=True)
    
    # Complete JSON data storage
    json_data = Column(Text)  # Stores complete GSTR-1 JSON structure
    
    # Summary fields for quick queries and reporting
    total_invoices = Column(Numeric(10, 0), default=0)
    total_taxable_value = Column(Numeric(15, 2), default=0)
    total_tax = Column(Numeric(15, 2), default=0)
    total_invoice_value = Column(Numeric(15, 2), default=0)
    
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime)  # When submitted to tax authorities
    
    # Relationships
    user = relationship("UserDB", back_populates="gstr1_returns")




# Relationships are already defined in the class definitions above
