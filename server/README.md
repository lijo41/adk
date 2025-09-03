# Document Chat Assistant

A powerful document parsing and chat system built with ADK (Agent Development Kit), using docling for document processing and Gemini for intelligent responses.

## Features

- **Document Parsing**: Support for PDF, TXT, DOCX, and Markdown files using docling
- **Intelligent Chunking**: Automatic text chunking with overlap for better context retrieval
- **Vector Search**: ChromaDB-powered semantic search through document content
- **AI Chat**: Chat with your documents using Google's Gemini 2.0 Flash model
- **Web Interface**: Beautiful FastAPI-powered web interface
- **ADK Integration**: Full integration with Google's Agent Development Kit

## Installation

1. Install dependencies:
```bash
cd /home/lijo/Documents/adk
pip install -e .
```

2. Set up your Google API key in `.env`:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

### Option 1: Web Interface (Recommended)
Start the web server:
```bash
python web_server.py
```
Then open http://localhost:8000 in your browser.

### Option 2: ADK CLI
Run the ADK agent from the parent directory:
```bash
cd /home/lijo/Documents
adk run adk
```

## Architecture

- **DocumentProcessor**: Handles document parsing, chunking, and vector storage
- **Agent Functions**: 
  - `parse_and_store_document()`: Process and store documents
  - `search_documents()`: Semantic search through stored content
  - `chat_with_documents()`: AI-powered Q&A with context retrieval
- **ADK Agents**: Structured agents for document processing and chat
- **FastAPI Server**: Modern web interface with file upload and chat

## Supported Document Types

- PDF files (.pdf)
- Text files (.txt)
- Word documents (.docx)
- Markdown files (.md)

## API Endpoints

- `GET /`: Web chat interface
- `POST /upload`: Upload and process documents
- `POST /chat`: Chat with documents
- `POST /search`: Search document content
- `GET /health`: Health check
