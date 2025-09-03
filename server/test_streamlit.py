"""Streamlit test interface for the backend API."""

import streamlit as st
import requests
import json
from pathlib import Path
import tempfile
import os

# Configure Streamlit
st.set_page_config(
    page_title="ADK Backend Test",
    page_icon="🧪",
    layout="wide"
)

# Backend URL
BACKEND_URL = "http://localhost:8000"

st.title("🧪 ADK Backend Test Interface")
st.markdown("Test the backend API endpoints with this Streamlit interface")

# Sidebar for API status
with st.sidebar:
    st.header("🔌 API Status")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ Backend is running")
            st.json(response.json())
        else:
            st.error("❌ Backend error")
    except requests.exceptions.RequestException:
        st.error("❌ Backend not reachable")
        st.info("Start backend with: `uvicorn main:app --reload`")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📄 Documents", "🧾 GSTR-1", "💬 Chat"])

# Documents Tab
with tab1:
    st.header("Document Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'txt', 'docx', 'md'],
            accept_multiple_files=True
        )
        
        if uploaded_files and st.button("Upload Documents"):
            with st.spinner("Uploading documents..."):
                files = []
                for uploaded_file in uploaded_files:
                    files.append(
                        ("files", (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type))
                    )
                
                try:
                    response = requests.post(f"{BACKEND_URL}/api/documents/upload-multiple", files=files)
                    if response.status_code == 200:
                        st.success("Documents uploaded successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"Upload failed: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Request failed: {str(e)}")
    
    with col2:
        st.subheader("Document List")
        if st.button("Refresh Documents"):
            try:
                response = requests.get(f"{BACKEND_URL}/api/documents/list")
                if response.status_code == 200:
                    documents = response.json()["documents"]
                    if documents:
                        for doc in documents:
                            st.write(f"📄 **{doc['filename']}**")
                            st.write(f"   - ID: `{doc['id']}`")
                            st.write(f"   - Status: {doc['status']}")
                            st.write(f"   - Size: {doc['file_size']} bytes")
                    else:
                        st.info("No documents uploaded yet")
                else:
                    st.error("Failed to fetch documents")
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {str(e)}")

# GSTR-1 Tab
with tab2:
    st.header("GSTR-1 Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create GSTR-1 Return")
        with st.form("gstr1_form"):
            gstin = st.text_input("GSTIN", placeholder="15-digit GSTIN")
            company_name = st.text_input("Company Name")
            filing_period = st.text_input("Filing Period (MMYYYY)", placeholder="082024")
            gross_turnover = st.number_input("Gross Turnover", min_value=0.0, step=1000.0)
            
            if st.form_submit_button("Create GSTR-1"):
                if gstin and company_name and filing_period:
                    try:
                        data = {
                            "gstin": gstin,
                            "company_name": company_name,
                            "filing_period": filing_period,
                            "gross_turnover": gross_turnover
                        }
                        response = requests.post(f"{BACKEND_URL}/api/gstr1/create", json=data)
                        if response.status_code == 200:
                            result = response.json()
                            st.success("GSTR-1 return created!")
                            st.json(result)
                            
                            # Store return_id in session state for use outside form
                            st.session_state.latest_return_id = result.get("return_id")
                        else:
                            st.error(f"Creation failed: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Request failed: {str(e)}")
                else:
                    st.error("Please fill all required fields")
        
        # Button outside the form to view JSON template
        if hasattr(st.session_state, 'latest_return_id') and st.session_state.latest_return_id:
            if st.button("View Full JSON Template", key="view_json_template"):
                try:
                    json_response = requests.get(f"{BACKEND_URL}/api/gstr1/{st.session_state.latest_return_id}/json")
                    if json_response.status_code == 200:
                        st.subheader("Complete GSTR-1 JSON Template")
                        st.json(json_response.json())
                    else:
                        st.error("Failed to fetch JSON template")
                except requests.exceptions.RequestException as e:
                    st.error(f"Request failed: {str(e)}")
    
    with col2:
        st.subheader("GSTR-1 Returns")
        if st.button("List Returns"):
            try:
                response = requests.get(f"{BACKEND_URL}/api/gstr1/list")
                if response.status_code == 200:
                    returns = response.json()["returns"]
                    if returns:
                        for return_id in returns:
                            st.write(f"📋 Return ID: `{return_id}`")
                            
                            # Add buttons for each return
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button(f"View JSON", key=f"view_{return_id}"):
                                    try:
                                        json_response = requests.get(f"{BACKEND_URL}/api/gstr1/{return_id}/json")
                                        if json_response.status_code == 200:
                                            st.subheader(f"GSTR-1 JSON for {return_id}")
                                            st.json(json_response.json())
                                        else:
                                            st.error("Failed to fetch JSON")
                                    except requests.exceptions.RequestException as e:
                                        st.error(f"Request failed: {str(e)}")
                            
                            with col_b:
                                if st.button(f"View Details", key=f"details_{return_id}"):
                                    try:
                                        details_response = requests.get(f"{BACKEND_URL}/api/gstr1/{return_id}")
                                        if details_response.status_code == 200:
                                            st.subheader(f"GSTR-1 Details for {return_id}")
                                            st.json(details_response.json())
                                        else:
                                            st.error("Failed to fetch details")
                                    except requests.exceptions.RequestException as e:
                                        st.error(f"Request failed: {str(e)}")
                    else:
                        st.info("No GSTR-1 returns created yet")
                else:
                    st.error("Failed to fetch returns")
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {str(e)}")

# Chat Tab
with tab3:
    st.header("Document Chat")
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    data = {"question": prompt}
                    response = requests.post(f"{BACKEND_URL}/api/chat/ask", json=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        answer = result["answer"]
                        sources = result["sources"]
                        
                        st.markdown(answer)
                        
                        if sources:
                            st.markdown("**Sources:**")
                            for source in sources:
                                st.markdown(f"- {source['filename']} (relevance: {source['relevance_score']:.2f})")
                        
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        error_msg = f"Error: {response.text}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        
                except requests.exceptions.RequestException as e:
                    error_msg = f"Request failed: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.markdown("---")
st.markdown("**Backend API Endpoints:**")
st.code(f"""
Documents: {BACKEND_URL}/api/documents
GSTR-1: {BACKEND_URL}/api/gstr1  
Chat: {BACKEND_URL}/api/chat
Health: {BACKEND_URL}/health
""")
