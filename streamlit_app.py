import streamlit as st
import tempfile
import os
from pathlib import Path
import json
from agent import parse_document_content, answer_with_context, list_available_documents
from gstr1_template import get_empty_gstr1_template
# No database - using direct JSON storage
import google.generativeai as genai

# Configure Streamlit page
st.set_page_config(
    page_title="Document Chat Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

# Main title
st.title("📄 Document Chat Assistant")
st.markdown("Upload documents, chat with them, and optionally process invoices for GSTR1")

# Sidebar for file upload and GSTR1
with st.sidebar:
    st.header("📁 Document Upload")
    
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['pdf', 'txt', 'docx', 'md'],
        help="Upload PDF, TXT, DOCX, or MD files",
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.uploaded_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # Handle different file types
                        file_extension = Path(uploaded_file.name).suffix.lower()
                        
                        if file_extension in ['.pdf', '.docx']:
                            # For binary files, process through agent first
                            result = parse_document_content(tmp_file_path)
                            if "Error" not in result:
                                content = result  # Use processed content
                            else:
                                st.error(f"❌ Error processing file: {result}")
                                content = None
                        else:
                            # For text files, decode directly
                            try:
                                content = uploaded_file.getvalue().decode('utf-8')
                            except UnicodeDecodeError:
                                try:
                                    content = uploaded_file.getvalue().decode('latin-1')
                                except:
                                    st.error("❌ Unable to decode file. Please ensure it's a valid text file.")
                                    content = None
                        
                        if content:
                            # Process the document
                            result = parse_document_content(tmp_file_path)
                            
                            if "Error" not in result:
                                st.session_state.uploaded_files.append(uploaded_file.name)
                                st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": f"📄 Document uploaded: {uploaded_file.name}"
                                })
                            else:
                                st.error(f"❌ Error: {result}")
                            
                    finally:
                        # Clean up temporary file
                        if os.path.exists(tmp_file_path):
                            os.unlink(tmp_file_path)
    
    # Show uploaded files and database stats
    if st.session_state.uploaded_files:
        st.subheader("📚 Uploaded Documents")
        for file in st.session_state.uploaded_files:
            st.write(f"• {file}")
    
    # Storage statistics
    with st.expander("📊 Storage Statistics", expanded=False):
        gstr1_dir = Path("gstr1_data")
        if gstr1_dir.exists():
            json_files = list(gstr1_dir.glob("*.json"))
            st.metric("Stored GSTR-1 Files", len([f for f in json_files if f.name != "index.json"]))
        else:
            st.metric("Stored GSTR-1 Files", 0)
    
    st.divider()
    
    # GSTR1 Section
    st.header("🧾 GSTR1 Generator")
    
    with st.expander("GSTR1 Setup", expanded=False):
        gstin = st.text_input("GSTIN", placeholder="15-digit GSTIN")
        company_name = st.text_input("Company Name", placeholder="Legal company name")
        filing_period = st.text_input("Filing Period (MMYYYY)", placeholder="e.g., 082024")
        gross_turnover = st.number_input("Gross Turnover (Optional)", min_value=0.0, value=0.0)
        
        if st.button("Generate GSTR1 JSON", type="primary"):
            if gstin and company_name and filing_period:
                with st.spinner("Generating GSTR1..."):
                    try:
                        # Get empty template
                        gstr1_data = get_empty_gstr1_template()
                        
                        # Update header with form data
                        header_data = gstr1_data["gstr1_return"]["header"]
                        header_data["gstin"] = gstin
                        header_data["company_name"] = company_name
                        header_data["filing_period"] = filing_period
                        header_data["return_period"] = filing_period
                        header_data["gross_turnover"] = gross_turnover
                        header_data["filing_date"] = "02-09-2024"
                        
                        # Store GSTR1 JSON as file
                        import uuid
                        return_id = str(uuid.uuid4())
                        
                        # Create storage directory
                        storage_dir = Path("gstr1_data")
                        storage_dir.mkdir(exist_ok=True)
                        
                        # Save JSON file
                        file_path = storage_dir / f"{return_id}.json"
                        file_path.write_text(json.dumps(gstr1_data, indent=2))
                        
                        # If documents are available, try to extract invoice data
                        try:
                            from agent import document_store
                            if document_store["chunks"]:
                                model = genai.GenerativeModel(model_name="gemini-2.0-flash")
                                
                                all_chunks = []
                                for filename, chunks in document_store["chunks"].items():
                                    all_chunks.extend(chunks)
                                
                                combined_content = "\n\n".join(all_chunks[:5])  # Limit to first 5 chunks
                                
                                prompt = f"""
                                Analyze the following document content and extract any invoice/billing information for GSTR1 B2B format.
                                Look for: invoice numbers, dates, amounts, GSTIN, HSN codes, tax details.
                                
                                Content: {combined_content}
                                
                                If invoice data is found, format it as B2B invoice entries. If no invoice data, return empty.
                                """
                                
                                try:
                                    response = model.generate_content(prompt)
                                    st.info("📊 Document analysis completed")
                                except Exception as e:
                                    st.warning(f"Document analysis failed: {str(e)}")
                        except (ImportError, NameError, KeyError):
                            # No documents available for analysis
                            pass
                        
                        # Display the generated JSON
                        st.success(f"✅ GSTR1 JSON Generated and stored! (Return ID: {return_id})")
                        st.json(gstr1_data)
                        
                        # Add download button
                        json_str = json.dumps(gstr1_data, indent=2)
                        st.download_button(
                            label="📥 Download GSTR1 JSON",
                            data=json_str,
                            file_name=f"gstr1_{gstin}_{filing_period}.json",
                            mime="application/json"
                        )
                        
                        # Add to chat
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": f"📄 GSTR1 JSON generated and stored for {company_name} (GSTIN: {gstin}, Return ID: {return_id})"
                        })
                        
                    except Exception as e:
                        st.error(f"❌ Error generating GSTR1: {str(e)}")
                        st.write("Full error details:", e)
                        import traceback
                        st.code(traceback.format_exc())
            else:
                st.error("Please fill in all required fields (GSTIN, Company Name, Filing Period)")

# Main chat interface
st.header("💬 Chat with Your Documents")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask questions about your documents..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = answer_with_context(prompt)
                st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    📄 Document Chat Assistant with GSTR1 Support | Built with Streamlit
</div>
""", unsafe_allow_html=True)
