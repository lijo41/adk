# web_server.py - FastAPI web interface for document chat
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os
import tempfile
from pathlib import Path
from agent import parse_document_content, answer_with_context, list_available_documents, document_processor_agent

app = FastAPI(title="Document Chat Assistant", version="1.0.0")

# Pydantic models for API
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: list = []

class SearchRequest(BaseModel):
    query: str

# ——————————————————————————————————————————————
# API Endpoints
# ——————————————————————————————————————————————

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the main chat interface."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Document Chat Assistant</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 90%;
                max-width: 800px;
                height: 80vh;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }
            .upload-section {
                padding: 20px;
                border-bottom: 1px solid #eee;
                background: #f8f9fa;
            }
            .chat-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                background: #f8f9fa;
            }
            .message {
                margin-bottom: 15px;
                padding: 12px 16px;
                border-radius: 12px;
                max-width: 80%;
                word-wrap: break-word;
            }
            .user-message {
                background: #667eea;
                color: white;
                margin-left: auto;
            }
            .bot-message {
                background: white;
                border: 1px solid #ddd;
                margin-right: auto;
            }
            .input-section {
                padding: 20px;
                background: white;
                border-top: 1px solid #eee;
            }
            .input-group {
                display: flex;
                gap: 10px;
            }
            input[type="text"], input[type="file"] {
                flex: 1;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
            }
            button {
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: transform 0.2s;
            }
            button:hover { transform: translateY(-2px); }
            .upload-btn {
                background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
            }
            .status {
                margin-top: 10px;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📄 Document Chat Assistant</h1>
                <p>Upload documents and chat with them using AI</p>
            </div>
            
            <div class="upload-section">
                <div class="input-group">
                    <input type="file" id="fileInput" accept=".pdf,.txt,.docx,.md" />
                    <button class="upload-btn" onclick="uploadDocument()">Upload Document</button>
                </div>
                <div id="uploadStatus" class="status" style="display: none;"></div>
            </div>
            
            <div class="chat-container">
                <div class="messages" id="messages">
                    <div class="message bot-message">
                        👋 Hello! Upload a document and start asking questions about it.
                    </div>
                </div>
                
                <div class="input-section">
                    <div class="input-group">
                        <input type="text" id="questionInput" placeholder="Ask a question about your documents..." 
                               onkeypress="if(event.key==='Enter') sendMessage()" />
                        <button onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function uploadDocument() {
                const fileInput = document.getElementById('fileInput');
                const statusDiv = document.getElementById('uploadStatus');
                
                if (!fileInput.files[0]) {
                    showStatus('Please select a file first', 'error');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                showStatus('Uploading and processing document...', 'success');
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showStatus(result.message, 'success');
                        fileInput.value = '';
                    } else {
                        showStatus(result.detail || 'Upload failed', 'error');
                    }
                } catch (error) {
                    showStatus('Upload failed: ' + error.message, 'error');
                }
            }
            
            async function sendMessage() {
                const input = document.getElementById('questionInput');
                const question = input.value.trim();
                
                if (!question) return;
                
                addMessage(question, 'user');
                input.value = '';
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question: question })
                    });
                    
                    const result = await response.json();
                    addMessage(result.answer, 'bot');
                } catch (error) {
                    addMessage('Error: ' + error.message, 'bot');
                }
            }
            
            function addMessage(text, sender) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}-message`;
                messageDiv.textContent = text;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function showStatus(message, type) {
                const statusDiv = document.getElementById('uploadStatus');
                statusDiv.textContent = message;
                statusDiv.className = `status ${type}`;
                statusDiv.style.display = 'block';
                
                if (type === 'success') {
                    setTimeout(() => {
                        statusDiv.style.display = 'none';
                    }, 3000);
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document using agentic processing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Use direct function calls instead of agent execution
        parse_result = parse_document_content(tmp_file_path)
        
        if "Error" in parse_result:
            raise HTTPException(status_code=400, detail=parse_result)
        
        # Extract filename for summarization
        filename = Path(file.filename).name
        from agent import summarize_document
        summary_result = summarize_document(filename)
        
        return {"message": f"{parse_result}. {summary_result}", "filename": file.filename}
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat with uploaded documents using agentic approach."""
    try:
        answer = answer_with_context(request.question)
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """List all available documents with summaries."""
    try:
        documents = list_available_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Document Chat Assistant is running"}

if __name__ == "__main__":
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
