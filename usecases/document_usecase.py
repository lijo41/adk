"""Document processing use cases."""

import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from docling.document_converter import DocumentConverter

# Document models removed - processing in-memory only


class DocumentUseCase:
    """Business logic for document operations."""
    
    def __init__(self):
        self.storage_path = Path("storage/documents")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._documents = {}  # In-memory storage for documents
        self._chunks = {}  # In-memory storage for chunks
        
    def upload_document(self, filename: str, file_content: bytes, file_type: str) -> Document:
        """Upload and process a document."""
        doc_id = str(uuid.uuid4())
        
        # Determine document type
        try:
            # Handle MIME types and file extensions
            if file_type in ['application/pdf', 'pdf']:
                doc_type = DocumentType.PDF
            elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx']:
                doc_type = DocumentType.DOCX
            elif file_type in ['text/plain', 'txt']:
                doc_type = DocumentType.TXT
            elif file_type in ['text/markdown', 'md']:
                doc_type = DocumentType.MD
            else:
                # Fallback: try to get from filename extension
                ext = filename.split('.')[-1].lower() if '.' in filename else ''
                doc_type = DocumentType(ext)
        except ValueError:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Save file to storage
        file_path = self.storage_path / f"{doc_id}_{filename}"
        file_path.write_bytes(file_content)
        
        # Create document model
        document = Document(
            id=doc_id,
            filename=filename,
            file_type=doc_type,
            file_size=len(file_content),
            content="",  # Will be populated after processing
            status=DocumentStatus.UPLOADED,
            upload_time=datetime.now(),
            metadata={"file_path": str(file_path)}
        )
        
        # Process document content
        try:
            content = self._extract_content(file_path, doc_type)
            document.content = content
            document.status = DocumentStatus.PROCESSED
            document.processed_time = datetime.now()
        except Exception as e:
            document.status = DocumentStatus.ERROR
            document.error_message = str(e)
        
        # Store document in memory
        self._documents[doc_id] = document
        return document
    
    def _extract_content(self, file_path: Path, doc_type: DocumentType) -> str:
        """Extract text content from document."""
        if doc_type == DocumentType.TXT:
            return file_path.read_text(encoding='utf-8')
        elif doc_type == DocumentType.MD:
            return file_path.read_text(encoding='utf-8')
        else:
            # Use DocumentConverter for PDF, DOCX
            converter = DocumentConverter()
            result = converter.convert(str(file_path))
            return result.document.export_to_markdown()
    
    def create_chunks(self, document: Document, chunk_size: int = 1500, overlap: int = 200) -> List[DocumentChunk]:
        """Create text chunks from document."""
        if not document.content:
            return []
            
        chunks = []
        content = document.content
        
        if len(content) <= chunk_size:
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document.id,
                chunk_index=0,
                content=content,
                chunk_size=len(content),
                overlap_size=0,
                created_time=datetime.now()
            )
            chunks.append(chunk)
            # Store chunks in memory
            self._chunks[document.id] = [chunk]
            return chunks
        
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + chunk_size
            chunk_content = content[start:end]
            
            # Try to break at sentence boundaries
            if end < len(content):
                last_period = chunk_content.rfind('.')
                last_newline = chunk_content.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > start + chunk_size // 2:
                    chunk_content = content[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document.id,
                chunk_index=chunk_index,
                content=chunk_content.strip(),
                chunk_size=len(chunk_content),
                overlap_size=overlap if chunk_index > 0 else 0,
                created_time=datetime.now()
            )
            chunks.append(chunk)
            
            start = end - overlap
            chunk_index += 1
        
        # Store chunks in memory - clear existing chunks first
        self._chunks[document.id] = chunks
        return chunks
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self._documents.get(doc_id)
    
    def list_documents(self) -> List[Document]:
        """List all documents."""
        return list(self._documents.values())
    
    def get_all_documents(self) -> List[Document]:
        """List all documents."""
        return list(self._documents.values())
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document and its file."""
        if doc_id in self._documents:
            document = self._documents[doc_id]
            # Delete file from storage
            file_path = Path(document.metadata.get("file_path", ""))
            if file_path.exists():
                file_path.unlink()
            # Remove from memory
            del self._documents[doc_id]
            if doc_id in self._chunks:
                del self._chunks[doc_id]
            return True
        return False
    
    def get_chunks(self, document_id: str) -> List[DocumentChunk]:
        """Get chunks for a document."""
        return self._chunks.get(document_id, [])
