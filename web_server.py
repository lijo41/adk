
# web_server.py - FastAPI web interface for document chat
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os
import tempfile
from pathlib import Path
from agent import parse_document_content, answer_with_context, list_available_documents
# Removed gstr1_agent import - functionality moved inline

app = FastAPI(title="Document Chat Assistant", version="1.0.0")

# Pydantic models for API
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: list = []

class SearchRequest(BaseModel):
    query: str

class GSTR1HeaderRequest(BaseModel):
    gstin: str
    company_name: str
    filing_period: str
    return_period: str = ""
    gross_turnover: float = 0

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
            .info { background: #d1ecf1; color: #0c5460; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📄 Document Chat Assistant</h1>
                <p>Upload documents, chat with them, and optionally process invoices for GSTR1</p>
            </div>
            
            <div class="upload-section">
                <div class="input-group">
                    <input type="file" id="fileInput" accept=".pdf,.txt,.docx,.md" />
                    <button class="upload-btn" onclick="uploadDocument()">Upload Document</button>
                    <button onclick="showGSTR1Setup()">GSTR1 Setup</button>
                </div>
                <div id="uploadStatus" class="status" style="display: none;"></div>
            </div>
            
            <div class="chat-container">
                <div class="messages" id="messages">
                    <div class="message bot-message">
                        👋 Welcome to Document Chat Assistant!<br><br>
                        📄 <strong>Document Chat:</strong><br>
                        • Upload any document (PDF, DOCX, TXT, MD)<br>
                        • Ask questions about your documents<br>
                        • Get intelligent summaries and analysis<br><br>
                        🧾 <strong>GSTR1 Feature:</strong><br>
                        • Upload invoice documents first<br>
                        • Click "GSTR1 Setup" to enter details and generate JSON<br><br>
                        💬 Start by uploading a document or asking a question!
                    </div>
                </div>
                
                <div class="input-section">
                    <div class="input-group">
                        <input type="text" id="questionInput" placeholder="Ask questions about your documents or type 'gstr1 help' for invoice commands..." 
                               onkeypress="if(event.key==='Enter') sendMessage()" />
                        <button onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- GSTR1 Setup Modal -->
        <div id="gstr1Modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 15px; width: 90%; max-width: 500px;">
                <h2>🏢 GSTR1 Header Details</h2>
                <div style="margin: 15px 0;">
                    <label>GSTIN:</label><br>
                    <input type="text" id="gstin" placeholder="15-digit GSTIN" style="width: 100%; padding: 8px; margin-top: 5px;">
                </div>
                <div style="margin: 15px 0;">
                    <label>Company Name:</label><br>
                    <input type="text" id="companyName" placeholder="Legal company name" style="width: 100%; padding: 8px; margin-top: 5px;">
                </div>
                <div style="margin: 15px 0;">
                    <label>Filing Period (MMYYYY):</label><br>
                    <input type="text" id="filingPeriod" placeholder="e.g., 082024" style="width: 100%; padding: 8px; margin-top: 5px;">
                </div>
                <div style="margin: 15px 0;">
                    <label>Gross Turnover (Optional):</label><br>
                    <input type="number" id="grossTurnover" placeholder="0" style="width: 100%; padding: 8px; margin-top: 5px;">
                </div>
                <div style="margin-top: 20px; text-align: right;">
                    <button onclick="closeGSTR1Modal()" style="margin-right: 10px; background: #ccc;">Cancel</button>
                    <button onclick="submitGSTR1Header()">Save Details</button>
                </div>
            </div>
        </div>

        <script>
            // Define functions directly in global scope
            async function uploadDocument() {
                console.log('Upload button clicked');
                
                try {
                    const fileInput = document.getElementById('fileInput');
                    console.log('File input found:', fileInput);
                    
                    if (!fileInput || !fileInput.files[0]) {
                        showStatus('Please select a file first', 'error');
                        return;
                    }
                    
                    console.log('File selected:', fileInput.files[0].name);
                    
                    const formData = new FormData();
                    formData.append('file', fileInput.files[0]);
                    
                    showStatus('Uploading and processing document...', 'info');
                    
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showStatus(result.message, 'success');
                        fileInput.value = '';
                        // Also add message to chat
                        addMessage('📄 Document uploaded: ' + result.message, 'bot');
                    } else {
                        showStatus(result.detail || 'Upload failed', 'error');
                    }
                } catch (error) {
                    showStatus('Upload failed: ' + error.message, 'error');
                    console.error('Upload error:', error);
                }
            }
            
            async function sendMessage() {
                const input = document.getElementById('questionInput');
                const question = input.value.trim();
                
                if (!question) return;
                
                addMessage(question, 'user');
                input.value = '';
                
                // Show typing indicator
                addMessage('🤔 Thinking...', 'bot');
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question: question })
                    });
                    
                    // Remove typing indicator
                    const messages = document.getElementById('messages');
                    messages.removeChild(messages.lastChild);
                    
                    const result = await response.json();
                    if (response.ok) {
                        addMessage(result.answer, 'bot');
                    } else {
                        addMessage('Error: ' + (result.detail || 'Failed to get response'), 'bot');
                    }
                } catch (error) {
                    // Remove typing indicator
                    const messages = document.getElementById('messages');
                    messages.removeChild(messages.lastChild);
                    addMessage('Error: ' + error.message, 'bot');
                }
            }
            
            function addMessage(text, sender) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + sender + '-message';
                
                // Handle multiline text properly
                if (text.includes('\n')) {
                    messageDiv.innerHTML = text.replace(/\n/g, '<br>');
                } else {
                    messageDiv.textContent = text;
                }
                
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function showStatus(message, type) {
                const statusDiv = document.getElementById('uploadStatus');
                statusDiv.textContent = message;
                statusDiv.className = 'status ' + type;
                statusDiv.style.display = 'block';
                
                if (type === 'success') {
                    setTimeout(function() {
                        statusDiv.style.display = 'none';
                    }, 3000);
                }
            }
            
            function showGSTR1Setup() {
                document.getElementById('gstr1Modal').style.display = 'block';
            }
            
            function closeGSTR1Modal() {
                document.getElementById('gstr1Modal').style.display = 'none';
            }
            
            async function submitGSTR1Header() {
                const gstin = document.getElementById('gstin').value;
                const companyName = document.getElementById('companyName').value;
                const filingPeriod = document.getElementById('filingPeriod').value;
                const grossTurnover = document.getElementById('grossTurnover').value || 0;
                
                if (!gstin || !companyName || !filingPeriod) {
                    alert('Please fill in all required fields');
                    return;
                }
                
                try {
                    const response = await fetch('/gstr1/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            gstin: gstin,
                            company_name: companyName,
                            filing_period: filingPeriod,
                            return_period: filingPeriod,
                            gross_turnover: parseFloat(grossTurnover)
                        })
                    });
                    
                    const result = await response.json();
                    if (response.ok) {
                        addMessage('📄 GSTR1 JSON Generated:\n\n' + result.gstr1_json, 'bot');
                        closeGSTR1Modal();
                    } else {
                        alert(result.detail || 'Error generating GSTR1');
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
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
        
        # Extract filename for summarization - use the stored filename from parsing
        stored_filename = Path(tmp_file_path).name
        from agent import summarize_document
        summary_result = summarize_document(stored_filename)
        
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

# New GSTR1 endpoints
@app.post("/gstr1/generate")
async def generate_gstr1_from_chunks(request: GSTR1HeaderRequest):
    """Generate GSTR1 JSON directly from available document chunks."""
    try:
        from agent import document_store
        from gstr1_template import get_empty_gstr1_template
        import google.generativeai as genai
        import json
        
        # Get all available document content
        all_content = ""
        for filename, content in document_store["documents"].items():
            all_content += f"\n\n--- From {filename} ---\n{content}"
        
        if not all_content.strip():
            return {"gstr1_json": "No documents uploaded. Please upload documents first."}
        
        # Create GSTR1 template with header details
        gstr1_template = get_empty_gstr1_template()
        gstr1_template["gstr1_return"]["header"] = {
            "gstin": request.gstin,
            "company_name": request.company_name,
            "filing_period": request.filing_period,
            "gross_turnover": request.gross_turnover,
            "return_period": request.return_period or request.filing_period,
            "filing_date": "02-09-2024",
            "amendment": False,
            "late_fee": 0
        }
        
        # Use AI to extract invoice data and fill GSTR1 template
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        prompt = f"""
        Extract all invoice/tax data from the uploaded documents and fill this GSTR1 template.
        
        Documents content:
        {all_content[:8000]}
        
        GSTR1 Template to fill:
        {json.dumps(gstr1_template, indent=2)}
        
        Instructions:
        1. Extract all invoices from the documents
        2. Fill the B2B supplies section with proper invoice details
        3. Calculate all totals correctly
        4. Ensure HSN codes, tax rates, and amounts are accurate
        5. Update the overall summary with calculated totals
        
        Return ONLY the complete filled GSTR1 JSON:
        """
        
        response = model.generate_content(prompt)
        
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            filled_gstr1 = json_match.group()
            return {"gstr1_json": filled_gstr1}
        else:
            return {"gstr1_json": response.text}
            
    except Exception as e:
        return {"gstr1_json": f"Error generating GSTR1: {str(e)}"}

@app.get("/gstr1/status")
async def get_filing_status():
    """Get current GSTR1 filing status."""
    try:
        status = get_gstr1_status()
        return {"status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gstr1/generate")
async def generate_filing():
    """Generate final GSTR1 JSON."""
    try:
        result = generate_gstr1_json()
        return {"gstr1_json": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/invoices/list")
async def list_invoices():
    """List processed invoices."""
    try:
        invoice_list = get_invoice_list()
        return {"invoice_list": invoice_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Invoice Processing & GSTR1 Filing System is running"}

if __name__ == "__main__":
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
