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
                            
                            # Store return_id in session state for use outside form
                            st.session_state.latest_return_id = result.get("return_id")
                            
                            # Show table data from database instead of JSON
                            if st.session_state.latest_return_id:
                                try:
                                    table_response = requests.get(f"{BACKEND_URL}/api/gstr1/{st.session_state.latest_return_id}/table")
                                    if table_response.status_code == 200:
                                        table_data = table_response.json()
                                        
                                        # Display header info
                                        st.subheader("📋 GSTR-1 Filing Summary")
                                        header = table_data.get('header', {})
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.write(f"**GSTIN:** {header.get('gstin', 'N/A')}")
                                            st.write(f"**Company:** {header.get('company_name', 'N/A')}")
                                        with col2:
                                            st.write(f"**Period:** {header.get('filing_period', 'N/A')}")
                                            st.write(f"**Status:** {header.get('status', 'N/A')}")
                                        
                                        # Display summary
                                        summary = table_data.get('summary', {})
                                        st.subheader("📊 Summary")
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            st.metric("Total Invoices", summary.get('total_invoices', 0))
                                        with col2:
                                            st.metric("Taxable Value", f"₹{summary.get('total_taxable_value', 0):,.2f}")
                                        with col3:
                                            st.metric("Total Tax", f"₹{summary.get('total_tax', 0):,.2f}")
                                        with col4:
                                            st.metric("Invoice Value", f"₹{summary.get('total_invoice_value', 0):,.2f}")
                                        
                                        # Display invoices table
                                        invoices = table_data.get('invoices', [])
                                        if invoices:
                                            st.subheader("🧾 Invoice Details")
                                            for i, invoice in enumerate(invoices, 1):
                                                with st.expander(f"Invoice {i}: {invoice.get('invoice_no', 'N/A')} - ₹{invoice.get('invoice_value', 0):,.2f}"):
                                                    col1, col2 = st.columns(2)
                                                    with col1:
                                                        st.write(f"**Invoice No:** {invoice.get('invoice_no', 'N/A')}")
                                                        st.write(f"**Date:** {invoice.get('invoice_date', 'N/A')}")
                                                        st.write(f"**Recipient GSTIN:** {invoice.get('recipient_gstin', 'N/A')}")
                                                    with col2:
                                                        st.write(f"**Place of Supply:** {invoice.get('place_of_supply', 'N/A')}")
                                                        st.write(f"**Invoice Value:** ₹{invoice.get('invoice_value', 0):,.2f}")
                                                    
                                                    # Display items
                                                    items = invoice.get('items', [])
                                                    if items:
                                                        st.write("**Items:**")
                                                        for item in items:
                                                            st.write(f"• {item.get('product_name', 'N/A')} (HSN: {item.get('hsn_code', 'N/A')})")
                                                            st.write(f"  Qty: {item.get('quantity', 0)}, Rate: ₹{item.get('unit_price', 0):,.2f}, Taxable: ₹{item.get('taxable_value', 0):,.2f}")
                                                            st.write(f"  IGST: ₹{item.get('igst', 0):,.2f}, CGST: ₹{item.get('cgst', 0):,.2f}, SGST: ₹{item.get('sgst', 0):,.2f}")
                                except Exception as e:
                                    st.error(f"Failed to load table data: {str(e)}")
                        else:
                            st.error(f"Creation failed: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Request failed: {str(e)}")
                else:
                    st.error("Please fill all required fields")
        
    
    with col2:
        st.subheader("GSTR-1 Returns")
        if st.button("List Returns"):
            st.session_state.show_returns = True
        
        if st.session_state.get("show_returns", False):
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
                                if st.button(f"View Table", key=f"table_{return_id}"):
                                    st.session_state[f"show_table_{return_id}"] = True
                            
                            with col_b:
                                if st.button(f"View Details", key=f"details_{return_id}"):
                                    st.session_state[f"show_details_{return_id}"] = True
                            
                            # Display table data if requested
                            if st.session_state.get(f"show_table_{return_id}", False):
                                try:
                                    table_response = requests.get(f"{BACKEND_URL}/api/gstr1/{return_id}/table")
                                    if table_response.status_code == 200:
                                        table_data = table_response.json()
                                        st.subheader(f"GSTR-1 Table Data for {return_id}")
                                        
                                        # Display header info
                                        header = table_data.get('header', {})
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.write(f"**GSTIN:** {header.get('gstin', 'N/A')}")
                                            st.write(f"**Company:** {header.get('company_name', 'N/A')}")
                                        with col2:
                                            st.write(f"**Period:** {header.get('filing_period', 'N/A')}")
                                            st.write(f"**Status:** {header.get('status', 'N/A')}")
                                        
                                        # Display summary
                                        summary = table_data.get('summary', {})
                                        st.write("**Summary:**")
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            st.metric("Invoices", summary.get('total_invoices', 0))
                                        with col2:
                                            st.metric("Taxable Value", f"₹{summary.get('total_taxable_value', 0):,.2f}")
                                        with col3:
                                            st.metric("Total Tax", f"₹{summary.get('total_tax', 0):,.2f}")
                                        with col4:
                                            st.metric("Invoice Value", f"₹{summary.get('total_invoice_value', 0):,.2f}")
                                        
                                        # Display invoices
                                        invoices = table_data.get('invoices', [])
                                        if invoices:
                                            st.write("**Invoice Details:**")
                                            for i, invoice in enumerate(invoices, 1):
                                                with st.expander(f"Invoice {i}: {invoice.get('invoice_no', 'N/A')}"):
                                                    st.write(f"Date: {invoice.get('invoice_date', 'N/A')}")
                                                    st.write(f"Value: ₹{invoice.get('invoice_value', 0):,.2f}")
                                                    st.write(f"Recipient: {invoice.get('recipient_gstin', 'N/A')}")
                                        
                                        if st.button(f"Hide Table", key=f"hide_table_{return_id}"):
                                            st.session_state[f"show_table_{return_id}"] = False
                                            st.rerun()
                                    else:
                                        st.error(f"Failed to fetch table data: {table_response.status_code}")
                                except requests.exceptions.RequestException as e:
                                    st.error(f"Request failed: {str(e)}")
                            
                            # Display details if requested
                            if st.session_state.get(f"show_details_{return_id}", False):
                                try:
                                    details_response = requests.get(f"{BACKEND_URL}/api/gstr1/{return_id}")
                                    if details_response.status_code == 200:
                                        details = details_response.json()
                                        st.subheader(f"Return Details for {return_id}")
                                        st.write(f"**GSTIN:** {details.get('gstin', 'N/A')}")
                                        st.write(f"**Company:** {details.get('company_name', 'N/A')}")
                                        st.write(f"**Period:** {details.get('filing_period', 'N/A')}")
                                        st.write(f"**Status:** {details.get('status', 'N/A')}")
                                        st.write(f"**Created:** {details.get('created_time', 'N/A')}")
                                        
                                        if st.button(f"Hide Details", key=f"hide_details_{return_id}"):
                                            st.session_state[f"show_details_{return_id}"] = False
                                            st.rerun()
                                    else:
                                        st.error(f"Failed to fetch details: {details_response.status_code}")
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

