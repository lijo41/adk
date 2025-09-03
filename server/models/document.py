"""Document models for the GST filing system."""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class DocumentType(Enum):
    """Document type enumeration."""
    INVOICE = "invoice"
    RECEIPT = "receipt"
    BILL = "bill"
    OTHER = "other"

@dataclass
class DocumentChunk:
    """Represents a chunk of document content."""
    content: str
    chunk_index: int
    start_char: int = 0
    end_char: int = 0
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Document:
    """Represents a processed document."""
    id: str
    filename: str
    content: str
    chunks: List[DocumentChunk]
    document_type: DocumentType = DocumentType.OTHER
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
