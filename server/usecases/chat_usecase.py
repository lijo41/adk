"""Chat and AI processing use cases."""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from agents.document_processing_agent import document_store


class ChatUseCase:
    """Business logic for chat and AI operations."""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    
    def create_document_summary(self, content: str) -> dict:
        """Generate AI summary for document content."""
        prompt = f"""Analyze this document and create a comprehensive summary that includes:
1. Main topics and themes
2. Key facts and information
3. Important concepts or entities
4. Document structure and sections

Document content:
{content[:8000]}

Provide a detailed summary that will help with future questions:"""
        
        try:
            response = self.model.generate_content(prompt)
            summary_text = response.text
            
            # Extract key topics (simplified)
            topics_prompt = f"Extract 5-10 key topics from this summary as a comma-separated list: {summary_text[:1000]}"
            topics_response = self.model.generate_content(topics_prompt)
            key_topics = [topic.strip() for topic in topics_response.text.split(',')]
            
            return {
                "id": str(uuid.uuid4()),
                "summary": summary_text,
                "key_topics": key_topics[:10],
                "created_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error creating summary: {str(e)}")
    
    def find_relevant_chunks(self, question: str, chunks: list) -> list:
        """Find relevant document chunks for a question."""
        if not chunks:
            return []
        
        # Use AI to find relevant chunks
        relevant_chunks = []
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue
                
            prompt = f"""Question: "{question}"

Does this text chunk contain information that could help answer the question? 
Consider partial matches and related content. Answer YES or NO.

Chunk: {chunk[:800]}

Relevant:"""
            
            try:
                response = self.model.generate_content(prompt)
                if "YES" in response.text.upper():
                    relevant_chunks.append(chunk)
                    
                # Limit to top 3 chunks to avoid token limits
                if len(relevant_chunks) >= 3:
                    break
            except:
                continue
        
        return relevant_chunks
    
    def extract_context_for_query(self, question: str, content: str) -> dict:
        """Extract relevant context for a specific query."""
        # Simplified - no document storage
        return {
            "context": "No document storage - processing in-memory only",
            "relevance_score": 0.0,
            "question": question
        }
    
    def process_question(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Process a question and return answer with context."""
        if not document_store["documents"]:
            return {
                "answer": "No documents available. Please upload documents first to ask questions about them.",
                "sources": [],
                "question": question
            }
        
        # Gather context from all available documents
        all_contexts = []
        sources = []
        
        for filename in document_store["documents"].keys():
            chunks = document_store["chunks"].get(filename, [])
            if chunks:
                relevant_chunks = self.find_relevant_chunks(question, chunks)
                if relevant_chunks:
                    context = "\n\n".join(relevant_chunks)
                    all_contexts.append(f"From {filename}:\n{context}")
                    sources.append(filename)
        
        if not all_contexts:
            return {
                "answer": "I couldn't find relevant information in your uploaded documents to answer this question. Try asking about GST filing procedures, invoice details, or document content.",
                "sources": [],
                "question": question
            }
        
        combined_context = "\n\n---\n\n".join(all_contexts)
        
        # Generate final answer
        prompt = f"""Answer this question based on the provided context from uploaded documents. Be specific and helpful.

Question: {question}

Context from uploaded documents:
{combined_context}

Instructions:
- Provide a direct, helpful answer based on the document context
- Include specific details from the documents when relevant
- If the context doesn't fully answer the question, say what you can determine and suggest what additional information might be needed
- Be concise but comprehensive

Answer:"""
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "answer": response.text.strip(),
                "sources": sources,
                "question": question
            }
        except Exception as e:
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}. Please try again.",
                "sources": [],
                "question": question
            }

    def answer_question(self, question: str, contexts: list) -> str:
        """Generate answer based on document contexts."""
        return "Document storage disabled - only GSTR-1 processing available"
    
    def get_document_summary(self, document_id: str) -> dict:
        """Get document summary from document store."""
        if not document_store["documents"]:
            return {
                "summary": "No documents available",
                "document_id": document_id,
                "message": "Please upload documents first"
            }
        
        # Find document by ID (simplified - using filename as ID)
        for filename in document_store["documents"].keys():
            if document_id in filename or filename in document_id:
                summary = document_store["summaries"].get(filename)
                if not summary:
                    # Generate summary if not exists
                    content = document_store["documents"][filename]
                    summary_data = self.create_document_summary(content)
                    document_store["summaries"][filename] = summary_data["summary"]
                    summary = summary_data["summary"]
                
                return {
                    "summary": summary,
                    "document_id": document_id,
                    "filename": filename
                }
        
        return {
            "summary": "Document not found",
            "document_id": document_id,
            "message": "Document not found in uploaded files"
        }
