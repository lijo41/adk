"""Streamlit UI for GST Filing System."""

import streamlit as st
import requests
import pandas as pd
import json
import base64
import io
from typing import Dict, Any

# Backend URL
BACKEND_URL = "http://localhost:8000"

def check_backend_status():
    """Check if backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_document(file):
    """Upload document to backend."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(f"{BACKEND_URL}/api/documents/upload", files=files)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return None

def chat_with_documents(question, document_ids=None):
    """Chat with documents."""
    try:
        payload = {
            "question": question,
            "document_ids": document_ids or []
        }
        response = requests.post(f"{BACKEND_URL}/api/chat/ask", json=payload)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Chat failed: {str(e)}")
        return None

def create_gstr1_return(gstin, company_name, filing_period, gross_turnover=1000000.0):
    """Create GSTR-1 return."""
    try:
        payload = {
            "gstin": gstin,
            "company_name": company_name,
            "filing_period": filing_period,
            "gross_turnover": gross_turnover
        }
        response = requests.post(f"{BACKEND_URL}/api/gstr1/create", json=payload)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"GSTR-1 creation failed: {str(e)}")
        return None

def get_gstr1_table_data(return_id):
    """Get GSTR-1 table format data."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/gstr1/{return_id}/table")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# Main App
st.title("📊 GST Return Filing System")

# Backend Status Check
if not check_backend_status():
    st.error("❌ Backend not reachable. Please start the backend server.")
    st.info("Start backend with: `uvicorn main:app --reload`")
    st.stop()
else:
    st.success("✅ Backend is running")
    
    # Add database clear button in sidebar
    with st.sidebar:
        st.markdown("### Database Management")
        if st.button("🗑️ Clear Database", type="secondary"):
            try:
                response = requests.delete(f"{BACKEND_URL}/api/gstr1/clear")
                if response.status_code == 200:
                    st.success("✅ Database cleared successfully!")
                    # Clear session state
                    if 'gstr1_data' in st.session_state:
                        del st.session_state.gstr1_data
                    if 'show_gstr1_details' in st.session_state:
                        del st.session_state.show_gstr1_details
                    st.rerun()
                else:
                    st.error("❌ Failed to clear database")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Main Tabs
tab1, tab2, tab3 = st.tabs(["📄 Upload Documents", "💬 Chat with Documents", "📊 GSTR-1 Filing"])

# Tab 1: Upload Documents
with tab1:
    st.header("📄 Document Upload")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload GST invoices or related documents"
    )
    
    if uploaded_file is not None:
        if st.button("Upload Document", type="primary"):
            with st.spinner("Processing document..."):
                result = upload_document(uploaded_file)
                if result:
                    st.success(f"✅ Document uploaded successfully!")
                    st.json(result)

# Tab 2: Chat with Documents
with tab2:
    st.header("💬 Chat with Documents")
    
    question = st.text_input("Ask a question about your documents:")
    
    if st.button("Ask Question", type="primary") and question:
        with st.spinner("Getting answer..."):
            result = chat_with_documents(question)
            if result:
                st.markdown("### Answer:")
                st.write(result.get("answer", "No answer provided"))
                
                if "sources" in result:
                    st.markdown("### Sources:")
                    for source in result["sources"]:
                        st.write(f"- {source}")

# Tab 3: GSTR-1 Filing
with tab3:
    st.header("📊 GSTR-1 Filing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gstin = st.text_input("GSTIN", placeholder="27ABCDE1234F1Z5")
        filing_period = st.text_input("Filing Period (MMYYYY)", placeholder="082024")
    
    with col2:
        company_name = st.text_input("Company Name", placeholder="Your Company Ltd")
    
    if st.button("Generate GSTR-1", type="primary"):
        if gstin and company_name and filing_period:
            with st.spinner("Generating GSTR-1..."):
                # Add gross turnover input or use default
                gross_turnover = st.session_state.get('gross_turnover', 1000000.0)
                result = create_gstr1_return(gstin, company_name, filing_period, gross_turnover)
                if result:
                    st.success("✅ GSTR-1 generated successfully!")
                    st.session_state.gstr1_data = get_gstr1_table_data(result["return_id"])
                    st.session_state.show_gstr1_details = True
        else:
            st.error("Please fill all required fields")
    
    # Show GSTR-1 details if available
    if st.session_state.get('show_gstr1_details') and st.session_state.get('gstr1_data'):
        gstr1_data = st.session_state.gstr1_data
        
        st.markdown("---")
        st.markdown("### GSTR-1 Preview")
        
        if gstr1_data:
            # Handle both formats - direct data or nested in gstr1_return
            if "gstr1_return" in gstr1_data:
                gstr1_return = gstr1_data["gstr1_return"]
                header = gstr1_return.get("header", {})
                invoices = gstr1_return.get("invoices", [])
                summary = gstr1_return.get("summary", {})
            else:
                # Direct format from table endpoint
                header = gstr1_data.get("header", {})
                invoices = gstr1_data.get("invoices", [])
                summary = gstr1_data.get("summary", {})
            
            # Header Information
            st.markdown("#### Header Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("GSTIN", header.get("gstin", "N/A"))
            with col2:
                st.metric("Company", header.get("company_name", "N/A"))
            with col3:
                st.metric("Period", header.get("filing_period", "N/A"))
            
            # B2B Supplies
            st.markdown("#### B2B Supplies")
            if invoices:
                b2b_data = []
                for invoice in invoices:
                    for item in invoice.get("items", []):
                        b2b_data.append({
                            "Invoice No": invoice.get("invoice_no", ""),
                            "Date": invoice.get("invoice_date", ""),
                            "Customer GSTIN": invoice.get("recipient_gstin", ""),
                            "Product": item.get("product_name", ""),
                            "HSN Code": item.get("hsn_code", ""),
                            "Taxable Value": f"₹{float(item.get('taxable_value') or 0):,.2f}",
                            "IGST": f"₹{float(item.get('igst') or 0):,.2f}",
                            "Total": f"₹{float(invoice.get('invoice_value') or 0):,.2f}"
                        })
                
                st.dataframe(pd.DataFrame(b2b_data), use_container_width=True)
            else:
                st.warning("📄 No invoices extracted yet. Upload PDF documents first to extract invoice data automatically.")
                st.info("💡 **How it works:** Upload GST invoices → AI extracts data → View structured GSTR-1 preview")
            
            # Summary
            st.markdown("#### Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Invoices", summary.get("total_invoices", 0))
            with col2:
                st.metric("Taxable Value", f"₹{summary.get('total_taxable_value', 0):,.2f}")
            with col3:
                st.metric("Total Tax", f"₹{summary.get('total_tax', 0):,.2f}")

# Footer
st.markdown("---")
st.markdown("**GST Return Filing System** - Powered by AI Document Processing")
