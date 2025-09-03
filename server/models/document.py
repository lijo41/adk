"""Document data models."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"


class DocumentStatus(Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


@dataclass
class Document:
    """Main document model."""
    id: str
    filename: str
    file_type: DocumentType
    file_size: int
    content: str
    status: DocumentStatus
    upload_time: datetime
    processed_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DocumentChunk:
    """Document chunk for processing."""
    id: str
    document_id: str
    chunk_index: int
    content: str
    chunk_size: int
    overlap_size: int
    created_time: datetime


@dataclass
class DocumentSummary:
    """AI-generated document summary."""
    id: str
    document_id: str
    summary: str
    key_topics: List[str]
    entities: List[str]
    created_time: datetime
    model_used: str = "gemini-2.0-flash"


@dataclass
class DocumentContext:
    """Context extracted for specific queries."""
    id: str
    document_id: str
    query: str
    relevant_chunks: List[str]
    context: str
    relevance_score: float
    created_time: datetime
