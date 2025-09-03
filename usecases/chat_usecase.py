"""Chat and AI processing use cases."""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import google.generativeai as genai

# Document models removed - processing in-memory only


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
        
        # Simplified chunk processing - no document storage
        return []
    
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
        # Simplified - no document storage
        return {
            "answer": "Document storage disabled - only GSTR-1 processing available",
            "context": "No document storage enabled",
            "question": question,
            "sources": []
        }

    def answer_question(self, question: str, contexts: list) -> str:
        """Generate answer based on document contexts."""
        return "Document storage disabled - only GSTR-1 processing available"
    
    def get_document_summary(self, document_id: str) -> dict:
        """Get document summary - no storage available."""
        return {
            "summary": "Document storage disabled",
            "document_id": document_id,
            "message": "No document storage enabled"
        }
