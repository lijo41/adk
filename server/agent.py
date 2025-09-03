# agent.py - Document Chat System
import os
import tempfile
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from google.adk.agents import LlmAgent, SequentialAgent
from docling.document_converter import DocumentConverter

# ——————————————————————————————————————————————
# 0) Load .env and configure
# ——————————————————————————————————————————————
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Missing GOOGLE_API_KEY in .env")
genai.configure(api_key=api_key)

# ——————————————————————————————————————————————
# 1) Agentic Document Management (No External DB)
# ——————————————————————————————————————————————

# Global document store - agents manage this dynamically
document_store = {
    "documents": {},  # filename -> full content
    "chunks": {},     # filename -> list of text chunks
    "summaries": {},  # filename -> AI-generated summary
    "contexts": {}    # filename -> relevant contexts for current session
}

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks for better processing."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundaries
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            if break_point > start + chunk_size // 2:
                chunk = text[start:start + break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
        
    return chunks

def parse_document_content(file_path: str) -> str:
    """Agent tool: Parse document and extract content."""
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found"
    
    try:
        # Handle different file types
        file_ext = Path(file_path).suffix.lower()
        filename = Path(file_path).name
        
        if file_ext == '.txt':
            # Direct text file reading
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # Use DocumentConverter for other formats
            converter = DocumentConverter()
            result = converter.convert(file_path)
            content = result.document.export_to_markdown()
        
        # Store full content and create chunks
        document_store["documents"][filename] = content
        document_store["chunks"][filename] = chunk_text(content)
        
        return f"Successfully parsed {filename}. Content length: {len(content)} characters, {len(document_store['chunks'][filename])} chunks created"
    except Exception as e:
        return f"Error parsing document: {str(e)}"

def summarize_document(filename: str) -> str:
    """Agent tool: Create intelligent summary of document."""
    if filename not in document_store["documents"]:
        return f"Error: Document {filename} not found in store"
    
    content = document_store["documents"][filename]
    
    # Use Gemini to create intelligent summary
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    prompt = f"""Analyze this document and create a comprehensive summary that includes:
1. Main topics and themes
2. Key facts and information
3. Important concepts or entities
4. Document structure and sections

Document content:
{content[:8000]}  # Limit for context window

Provide a detailed summary that will help with future questions:"""
    
    try:
        response = model.generate_content(prompt)
        summary = response.text
        
        # Store summary for future agent use
        document_store["summaries"][filename] = summary
        
        return f"Created summary for {filename}: {summary[:200]}..."
    except Exception as e:
        return f"Error creating summary: {str(e)}"

def extract_relevant_context(question: str, filename: str) -> str:
    """Agent tool: Dynamically extract relevant context using chunks."""
    if filename not in document_store["chunks"]:
        return f"Error: Document {filename} not found"
    
    chunks = document_store["chunks"][filename]
    summary = document_store["summaries"].get(filename, "No summary available")
    
    # For general questions like "what's this about", return first few chunks
    general_questions = ["what", "about", "document", "content", "summary", "describe"]
    if any(word in question.lower() for word in general_questions) and len(question.split()) <= 6:
        # Return first 2-3 substantial chunks for general questions
        substantial_chunks = [chunk for chunk in chunks[:5] if len(chunk.strip()) > 100]
        if substantial_chunks:
            return "\n\n".join(substantial_chunks[:2])
    
    # For specific questions, use AI to find relevant chunks
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    relevant_chunks = []
    
    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 50:  # Skip very short chunks
            continue
            
        # More lenient relevance check
        prompt = f"""Question: "{question}"

Does this text chunk contain information that could help answer the question? 
Consider partial matches and related content. Answer YES or NO.

Chunk: {chunk[:800]}

Relevant:"""
        
        try:
            response = model.generate_content(prompt)
            if "YES" in response.text.upper():
                relevant_chunks.append(chunk)
                
            # Limit to top 3 chunks to avoid token limits
            if len(relevant_chunks) >= 3:
                break
        except:
            continue
    
    # Fallback: if no relevant chunks found, return first substantial chunk
    if not relevant_chunks:
        substantial_chunks = [chunk for chunk in chunks if len(chunk.strip()) > 100]
        if substantial_chunks:
            relevant_chunks = [substantial_chunks[0]]
        else:
            return "No substantial content found in this document."
    
    # Combine relevant chunks for final context
    combined_context = "\n\n".join(relevant_chunks)
    
    # Store context for this session
    if filename not in document_store["contexts"]:
        document_store["contexts"][filename] = {}
    document_store["contexts"][filename][question] = combined_context
    
    return combined_context

def answer_with_context(question: str) -> str:
    """Agent tool: Answer question using dynamically gathered context."""
    if not document_store["documents"]:
        return "No documents available. Please upload documents first."
    
    # Gather context from all available documents
    all_contexts = []
    for filename in document_store["documents"].keys():
        context = extract_relevant_context(question, filename)
        if not context.startswith("Error"):
            all_contexts.append(f"From {filename}:\n{context}")
    
    if not all_contexts:
        return "No relevant context found in uploaded documents."
    
    combined_context = "\n\n---\n\n".join(all_contexts)
    
    # Generate final answer
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    prompt = f"""Answer this question based on the provided context. Be specific and cite sources when possible.

Question: {question}

Context:
{combined_context}

Answer:"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating answer: {str(e)}"

def list_available_documents() -> str:
    """Agent tool: List all available documents with summaries."""
    if not document_store["documents"]:
        return "No documents currently available."
    
    doc_list = []
    for filename in document_store["documents"].keys():
        summary = document_store["summaries"].get(filename, "No summary available")
        doc_list.append(f"• {filename}: {summary[:100]}...")
    
    return "Available documents:\n" + "\n".join(doc_list)

# ——————————————————————————————————————————————
# 2) Agentic Workflow Agents
# ——————————————————————————————————————————————


context_agent = LlmAgent(
    name="ContextAgent",
    model="gemini-2.0-flash",
    description="Intelligently extracts relevant context for questions",
    instruction=(
        "For any question, dynamically analyze all available documents and extract "
        "the most relevant context. Use extract_relevant_context for each document "
        "that might contain relevant information."
    ),
    tools=[extract_relevant_context, list_available_documents],
    output_key="context_result"
)

answer_agent = LlmAgent(
    name="AnswerAgent", 
    model="gemini-2.0-flash",
    description="Provides intelligent answers based on document context",
    instruction=(
        "Answer user questions by calling answer_with_context(question). "
        "This will automatically gather relevant context from all documents "
        "and provide a comprehensive answer."
    ),
    tools=[answer_with_context],
    output_key="final_answer"
)

# ——————————————————————————————————————————————
# 3) Main Agentic Pipeline
# ——————————————————————————————————————————————

root_agent = SequentialAgent(
    name="DocumentChatAssistant",
    sub_agents=[answer_agent],  # Primary agent - others called as needed
    description="Fully agentic document chat system - agents dynamically manage context and knowledge"
)