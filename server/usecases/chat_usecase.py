"""Chat and AI processing use cases."""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from models.document import Document, DocumentChunk, DocumentSummary, DocumentContext


class ChatUseCase:
    """Business logic for chat and AI operations."""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    
    def create_document_summary(self, document: Document) -> DocumentSummary:
        """Generate AI summary for a document."""
        prompt = f"""Analyze this document and create a comprehensive summary that includes:
1. Main topics and themes
2. Key facts and information
3. Important concepts or entities
4. Document structure and sections

Document content:
{document.content[:8000]}

Provide a detailed summary that will help with future questions:"""
        
        try:
            response = self.model.generate_content(prompt)
            summary_text = response.text
            
            # Extract key topics (simplified)
            topics_prompt = f"Extract 5-10 key topics from this summary as a comma-separated list: {summary_text[:1000]}"
            topics_response = self.model.generate_content(topics_prompt)
            key_topics = [topic.strip() for topic in topics_response.text.split(',')]
            
            summary = DocumentSummary(
                id=str(uuid.uuid4()),
                document_id=document.id,
                summary=summary_text,
                key_topics=key_topics[:10],  # Limit to 10
                entities=[],  # Could be enhanced with NER
                created_time=datetime.now()
            )
            
            return summary
            
        except Exception as e:
            raise Exception(f"Error creating summary: {str(e)}")
    
    def find_relevant_chunks(self, question: str, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Find relevant document chunks for a question."""
        if not chunks:
            return []
        
        # For general questions, return first few substantial chunks
        general_questions = ["what", "about", "document", "content", "summary", "describe"]
        if any(word in question.lower() for word in general_questions) and len(question.split()) <= 6:
            substantial_chunks = [chunk for chunk in chunks[:5] if len(chunk.content.strip()) > 100]
            return substantial_chunks[:2]
        
        # For specific questions, use AI to find relevant chunks
        relevant_chunks = []
        
        for chunk in chunks:
            if len(chunk.content.strip()) < 50:
                continue
                
            prompt = f"""Question: "{question}"

Does this text chunk contain information that could help answer the question? 
Consider partial matches and related content. Answer YES or NO.

Chunk: {chunk.content[:800]}

Relevant:"""
            
            try:
                response = self.model.generate_content(prompt)
                if "YES" in response.text.upper():
                    relevant_chunks.append(chunk)
                    
                # Limit to top 3 chunks
                if len(relevant_chunks) >= 3:
                    break
            except:
                continue
        
        # Fallback: if no relevant chunks found, return first substantial chunk
        if not relevant_chunks:
            substantial_chunks = [chunk for chunk in chunks if len(chunk.content.strip()) > 100]
            if substantial_chunks:
                relevant_chunks = [substantial_chunks[0]]
        
        return relevant_chunks
    
    def extract_context_for_query(self, question: str, document: Document, 
                                 chunks: List[DocumentChunk]) -> DocumentContext:
        """Extract relevant context for a specific query."""
        relevant_chunks = self.find_relevant_chunks(question, chunks)
        
        if not relevant_chunks:
            context = "No relevant content found in this document."
            relevance_score = 0.0
        else:
            context = "\n\n".join([chunk.content for chunk in relevant_chunks])
            relevance_score = len(relevant_chunks) / len(chunks) if chunks else 0.0
        
        document_context = DocumentContext(
            id=str(uuid.uuid4()),
            document_id=document.id,
            query=question,
            relevant_chunks=[chunk.id for chunk in relevant_chunks],
            context=context,
            relevance_score=relevance_score,
            created_time=datetime.now()
        )
        
        return document_context
    
    def answer_question(self, question: str, contexts: List[DocumentContext]) -> str:
        """Generate answer based on document contexts."""
        if not contexts:
            return "No documents available. Please upload documents first."
        
        # Filter out contexts with no relevant content
        valid_contexts = [ctx for ctx in contexts if not ctx.context.startswith("No relevant")]
        
        if not valid_contexts:
            return "No relevant context found in uploaded documents."
        
        # Combine contexts
        combined_context = "\n\n---\n\n".join([
            f"From document (relevance: {ctx.relevance_score:.2f}):\n{ctx.context}"
            for ctx in valid_contexts
        ])
        
        prompt = f"""Answer this question based on the provided context. Be specific and cite sources when possible.

Question: {question}

Context:
{combined_context}

Answer:"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating answer: {str(e)}"
