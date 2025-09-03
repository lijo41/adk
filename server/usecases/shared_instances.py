"""Shared instances for dependency injection."""

from usecases.chat_usecase import ChatUseCase
from usecases.gstr1_usecase import GSTR1UseCase
from usecases.document_usecase import DocumentUseCase
import os
from dotenv import load_dotenv

load_dotenv()

# Create shared instances
chat_usecase = ChatUseCase(api_key=os.getenv("GOOGLE_API_KEY"))
gstr1_usecase = GSTR1UseCase()
document_usecase = DocumentUseCase()

def get_document_processing_agent():
    """Get the document processing agent instance."""
    return document_usecase
