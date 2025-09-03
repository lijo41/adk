"""API routes for the ADK document processing system."""

from .document_routes import document_router
from .gstr1_routes import gstr1_router
from .chat_routes import chat_router

__all__ = [
    "document_router",
    "gstr1_router", 
    "chat_router"
]
