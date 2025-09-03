"""Chat and AI processing agent for document Q&A."""

import google.generativeai as genai
from typing import List, Dict, Any, Optional
from models.document import Document, DocumentChunk


class ChatAgent:
    """AI agent for chat and document Q&A operations."""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    
    def generate_document_summary(self, document: Document) -> str:
        """Generate AI summary for a document."""
        prompt = f"""
        Analyze this document and provide a comprehensive summary:
        
        Document: {document.filename}
        Content: {document.content[:2000]}...
        
        Provide a summary covering:
        1. Document type and purpose
        2. Key information extracted
        3. Important dates, amounts, or references
        4. Main entities involved
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def answer_question(self, question: str, context_chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Answer question using document context."""
        if not context_chunks:
            return {
                "answer": "No relevant documents found to answer your question.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Combine relevant chunks
        context = "\n\n".join([
            f"Document: {chunk.document_id}\nContent: {chunk.content}"
            for chunk in context_chunks[:5]  # Limit to top 5 chunks
        ])
        
        prompt = f"""
        Based on the following document context, answer the user's question accurately and concisely.
        
        Question: {question}
        
        Context:
        {context}
        
        Instructions:
        - Provide a direct, helpful answer based only on the provided context
        - If the context doesn't contain enough information, say so
        - Include specific details from the documents when relevant
        - Be concise but comprehensive
        """
        
        try:
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            
            # Extract source document IDs
            sources = list(set([chunk.document_id for chunk in context_chunks]))
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": min(len(context_chunks) / 3.0, 1.0)  # Simple confidence score
            }
        except Exception as e:
            return {
                "answer": f"Error processing question: {str(e)}",
                "sources": [],
                "confidence": 0.0
            }
    
    def extract_key_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract key entities from text."""
        prompt = f"""
        Extract key entities from this text and categorize them:
        
        Text: {text[:1500]}
        
        Return entities in these categories:
        - Companies/Organizations
        - People/Names
        - Dates
        - Amounts/Numbers
        - Locations
        - Products/Services
        
        Format as JSON with category names as keys and lists of entities as values.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Parse JSON response (simplified)
            import json
            entities = json.loads(response.text.strip())
            return entities
        except Exception as e:
            return {"error": f"Entity extraction failed: {str(e)}"}
