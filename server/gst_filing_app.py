"""
Comprehensive GST Return Filing Streamlit Application
Features: Document Upload, Chat Interface, GSTR-1 Filing with Preview Reports
"""

import streamlit as st
import pandas as pd
import requests
import json
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
import base64
from pathlib import Path

# Configure Streamlit
st.set_page_config(
    page_title="GST Return Filing System",
    page_icon="📊",
    layout="wide"
)

# Backend URL
BACKEND_URL = "http://localhost:8000"

# Initialize session state
if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "gstr1_data" not in st.session_state:
    st.session_state.gstr1_data = None

# Helper Functions
def check_backend_status():
    """Check if backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def upload_document(uploaded_file):
    """Upload document to backend."""
    try:
        files = [("file", (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type))]
        response = requests.post(f"{BACKEND_URL}/api/documents/upload", files=files)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return None

def get_documents_list():
    """Get list of uploaded documents."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/documents/list")
        if response.status_code == 200:
            return response.json()["documents"]
        return []
    except requests.exceptions.RequestException:
        return []

def chat_with_documents(question: str):
    """Send chat query to backend."""
    try:
        data = {"question": question}
        response = requests.post(f"{BACKEND_URL}/api/chat/ask", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {"answer": f"Error: {response.text}", "sources": []}
    except requests.exceptions.RequestException as e:
        return {"answer": f"Request failed: {str(e)}", "sources": []}

def create_gstr1_return(gstin: str, company_name: str, filing_period: str, gross_turnover: float):
    """Create GSTR-1 return."""
    try:
        data = {
            "gstin": gstin,
            "company_name": company_name,
            "filing_period": filing_period,
            "gross_turnover": gross_turnover
        }
        response = requests.post(f"{BACKEND_URL}/api/gstr1/create", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"GSTR-1 creation failed: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return None

def get_gstr1_json(return_id: str):
    """Get GSTR-1 JSON data."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/gstr1/{return_id}/json")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

def get_gstr1_table_data(return_id: str):
    """Get GSTR-1 table format data."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/gstr1/{return_id}/table")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

def generate_gstr1_report_layout(gstr1_data: Dict):
    """Generate complete GSTR-1 preview layout with all sections."""
    if not gstr1_data or "gstr1_return" not in gstr1_data:
        st.error("No GSTR-1 data available")
        return
    
    gstr1_return = gstr1_data["gstr1_return"]
    header = gstr1_return.get("header", {})
    invoices = gstr1_return.get("invoices", [])
    summary = gstr1_return.get("summary", {})
    
    # Title
    filing_period = header.get("filing_period", "")
    month_year = f"{filing_period[2:4]}/{filing_period[:2]}" if len(filing_period) == 6 else filing_period
    st.title(f"📊 GSTR-1 Preview ({month_year})")
    
    # 1. Header Summary
    st.markdown("### 1. Header Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("GSTIN", header.get("gstin", "N/A"))
    with col2:
        st.metric("Company", header.get("company_name", "N/A"))
    with col3:
        st.metric("Filing Period", filing_period)
    with col4:
        st.metric("Gross Turnover", f"₹{500000:,.2f}")  # Default value
    with col5:
        st.metric("Status", "Draft")
    
    st.markdown("---")
    
    # 2. B2B Supplies
    st.markdown("### 2. B2B Supplies")
    if invoices:
        b2b_data = []
        for invoice in invoices:
            for item in invoice.get("items", []):
                b2b_data.append({
                    "Invoice No": invoice.get("invoice_no", ""),
                    "Date": invoice.get("invoice_date", ""),
                    "Customer GSTIN": invoice.get("recipient_gstin", ""),
                    "POS": invoice.get("place_of_supply", ""),
                    "Taxable Value": f"₹{float(item.get('taxable_value') or 0):,.2f}",
                    "IGST": f"₹{float(item.get('igst') or 0):,.2f}",
                    "CGST": f"₹{float(item.get('cgst') or 0):,.2f}",
                    "SGST": f"₹{float(item.get('sgst') or 0):,.2f}",
                    "Total": f"₹{float(invoice.get('invoice_value') or 0):,.2f}"
                })
        
        st.dataframe(pd.DataFrame(b2b_data), use_container_width=True)
    else:
        st.info("📝 No B2B records found")
    
    st.markdown("---")
    
    # 3. B2CL Supplies
    st.markdown("### 3. B2CL Supplies (Large Consumers)")
    st.info("📝 No B2CL records found")
    st.markdown("---")
    
    # 4. B2CS Supplies
    st.markdown("### 4. B2CS Supplies (Small Consumers)")
    st.info("📝 No B2CS records found")
    st.markdown("---")
    
    # 5. Zero-rated Supplies
    st.markdown("### 5. Zero-rated Supplies")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Exports")
        st.info("📝 No export records found")
    with col2:
        st.subheader("SEZ Supplies")
        st.info("📝 No SEZ records found")
    with col3:
        st.subheader("Deemed Exports")
        st.info("📝 No deemed export records found")
    st.markdown("---")
    
    # 6. Nil/Exempt/Non-GST Supplies
    st.markdown("### 6. Nil/Exempt/Non-GST Supplies")
    st.info("📝 No nil/exempt records found")
    st.markdown("---")
    
    # 7. Credit/Debit Notes
    st.markdown("### 7. Credit/Debit Notes")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Registered Recipients")
        st.info("📝 No credit/debit notes found")
    with col2:
        st.subheader("Unregistered Recipients")
        st.info("📝 No credit/debit notes found")
    st.markdown("---")
    
    # 8. HSN Summary
    st.markdown("### 8. HSN Summary")
    if invoices:
        hsn_data = {}
        for invoice in invoices:
            for item in invoice.get("items", []):
                hsn = item.get("hsn_code", "")
                if hsn and hsn not in hsn_data:
                    hsn_data[hsn] = {
                        "HSN Code": hsn,
                        "Description": item.get("product_name", ""),
                        "Qty": 0,
                        "Taxable Value": 0,
                        "IGST": 0,
                        "CGST": 0,
                        "SGST": 0,
                        "Cess": 0
                    }
                if hsn:
                    hsn_data[hsn]["Qty"] += float(item.get("quantity") or 0)
                    hsn_data[hsn]["Taxable Value"] += float(item.get("taxable_value") or 0)
                    hsn_data[hsn]["IGST"] += float(item.get("igst") or 0)
                    hsn_data[hsn]["CGST"] += float(item.get("cgst") or 0)
                    hsn_data[hsn]["SGST"] += float(item.get("sgst") or 0)
        
        if hsn_data:
            # Format HSN data for display
            hsn_display = []
            for hsn_info in hsn_data.values():
                hsn_display.append({
                    "HSN Code": hsn_info["HSN Code"],
                    "Description": hsn_info["Description"],
                    "Qty": f"{hsn_info['Qty']:.2f}",
                    "Taxable Value": f"₹{hsn_info['Taxable Value']:,.2f}",
                    "IGST": f"₹{hsn_info['IGST']:,.2f}",
                    "CGST": f"₹{hsn_info['CGST']:,.2f}",
                    "SGST": f"₹{hsn_info['SGST']:,.2f}",
                    "Cess": f"₹{hsn_info['Cess']:,.2f}"
                })
            st.dataframe(pd.DataFrame(hsn_display), use_container_width=True)
        else:
            st.info("📝 No HSN records found")
    else:
        st.info("📝 No HSN records found")
    st.markdown("---")
    
    # 9. Documents Issued
    st.markdown("### 9. Documents Issued")
    if invoices:
        doc_data = [{
            "Document Type": "Tax Invoice",
            "From Serial No": "1",
            "To Serial No": str(len(invoices)),
            "Total Number": len(invoices),
            "Cancelled": 0
        }]
        st.dataframe(pd.DataFrame(doc_data), use_container_width=True)
    else:
        st.info("📝 No documents issued")
    st.markdown("---")
    
    # 10. Amendments
    st.markdown("### 10. Amendments")
    st.info("📝 No amendments found")
    st.markdown("---")
    
    # 11. Overall Summary
    st.markdown("### 11. Overall Summary")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Total Invoices", summary.get("total_invoices", 0))
    with col2:
        st.metric("Total Taxable", f"₹{summary.get('total_taxable_value', 0):,.2f}")
    with col3:
        st.metric("IGST", f"₹{summary.get('total_tax', 0):,.2f}")
    with col4:
        st.metric("CGST", "₹0.00")
    with col5:
        st.metric("SGST", "₹0.00")
    with col6:
        st.metric("Total Outward", f"₹{summary.get('total_invoice_value', 0):,.2f}")
    
    return gstr1_data

def download_json(data: Dict, filename: str):
    """Generate download link for JSON."""
    json_str = json.dumps(data, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{filename}">Download JSON</a>'
    return href

def download_excel(gstr1_data: Dict, filename: str):
    """Generate download link for Excel with all GSTR-1 sections."""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if gstr1_data and "gstr1_return" in gstr1_data:
            gstr1_return = gstr1_data["gstr1_return"]
            invoices = gstr1_return.get("invoices", [])
            
            # B2B Sheet
            if invoices:
                b2b_data = []
                for invoice in invoices:
                    for item in invoice.get("items", []):
                        b2b_data.append({
                            "Invoice No": invoice.get("invoice_no", ""),
                            "Date": invoice.get("invoice_date", ""),
                            "Customer GSTIN": invoice.get("recipient_gstin", ""),
                            "POS": invoice.get("place_of_supply", ""),
                            "Taxable Value": float(item.get("taxable_value") or 0),
                            "IGST": float(item.get("igst") or 0),
                            "CGST": float(item.get("cgst") or 0),
                            "SGST": float(item.get("sgst") or 0),
                            "Total": float(invoice.get("invoice_value") or 0)
                        })
                pd.DataFrame(b2b_data).to_excel(writer, sheet_name="B2B Supplies", index=False)
            
            # HSN Summary Sheet
            if invoices:
                hsn_data = {}
                for invoice in invoices:
                    for item in invoice.get("items", []):
                        hsn = item.get("hsn_code", "")
                        if hsn and hsn not in hsn_data:
                            hsn_data[hsn] = {
                                "HSN Code": hsn,
                                "Description": item.get("product_name", ""),
                                "Qty": 0,
                                "Taxable Value": 0,
                                "IGST": 0,
                                "CGST": 0,
                                "SGST": 0,
                                "Cess": 0
                            }
                        if hsn:
                            hsn_data[hsn]["Qty"] += float(item.get("quantity") or 0)
                            hsn_data[hsn]["Taxable Value"] += float(item.get("taxable_value") or 0)
                            hsn_data[hsn]["IGST"] += float(item.get("igst") or 0)
                            hsn_data[hsn]["CGST"] += float(item.get("cgst") or 0)
                            hsn_data[hsn]["SGST"] += float(item.get("sgst") or 0)
                
                if hsn_data:
                    pd.DataFrame(list(hsn_data.values())).to_excel(writer, sheet_name="HSN Summary", index=False)
            
            # Summary Sheet
            summary = gstr1_return.get("summary", {})
            summary_data = [{
                "Total Invoices": summary.get("total_invoices", 0),
                "Total Taxable Value": summary.get("total_taxable_value", 0),
                "Total Tax": summary.get("total_tax", 0),
                "Total Invoice Value": summary.get("total_invoice_value", 0)
            }]
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
    
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel</a>'
    return href

def download_pdf(gstr1_data: Dict, filename: str):
    """Generate download link for PDF report."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        if gstr1_data and "gstr1_return" in gstr1_data:
            gstr1_return = gstr1_data["gstr1_return"]
            header = gstr1_return.get("header", {})
            invoices = gstr1_return.get("invoices", [])
            summary = gstr1_return.get("summary", {})
            
            # Title
            filing_period = header.get("filing_period", "")
            month_year = f"{filing_period[2:4]}/{filing_period[:2]}" if len(filing_period) == 6 else filing_period
            title = Paragraph(f"GSTR-1 Preview Report ({month_year})", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Header Summary
            header_data = [
                ['GSTIN', 'Company', 'Filing Period', 'Status'],
                [header.get("gstin", "N/A"), header.get("company_name", "N/A"), 
                 filing_period, "Draft"]
            ]
            header_table = Table(header_data)
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(header_table)
            story.append(Spacer(1, 12))
            
            # B2B Supplies
            if invoices:
                story.append(Paragraph("B2B Supplies", styles['Heading2']))
                b2b_data = [['Invoice No', 'Date', 'Customer GSTIN', 'Taxable Value', 'IGST', 'Total']]
                for invoice in invoices:
                    for item in invoice.get("items", []):
                        b2b_data.append([
                            invoice.get("invoice_no", ""),
                            invoice.get("invoice_date", ""),
                            invoice.get("recipient_gstin", ""),
                            f"₹{float(item.get('taxable_value') or 0):,.2f}",
                            f"₹{float(item.get('igst') or 0):,.2f}",
                            f"₹{float(invoice.get('invoice_value') or 0):,.2f}"
                        ])
                
                b2b_table = Table(b2b_data)
                b2b_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(b2b_table)
                story.append(Spacer(1, 12))
            
            # Summary
            story.append(Paragraph("Overall Summary", styles['Heading2']))
            summary_data = [
                ['Total Invoices', 'Total Taxable Value', 'Total Tax', 'Total Invoice Value'],
                [str(summary.get("total_invoices", 0)),
                 f"₹{summary.get('total_taxable_value', 0):,.2f}",
                 f"₹{summary.get('total_tax', 0):,.2f}",
                 f"₹{summary.get('total_invoice_value', 0):,.2f}"]
            ]
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
        
        doc.build(story)
        output.seek(0)
        b64 = base64.b64encode(output.read()).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF</a>'
        return href
        
    except ImportError:
        return "PDF generation requires reportlab package. Install with: pip install reportlab"

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
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Upload Invoices")
        uploaded_files = st.file_uploader(
            "Choose invoice files",
            type=['pdf', 'doc', 'docx', 'txt'],
            accept_multiple_files=True,
            key="file_uploader"
        )
        
        if uploaded_files and st.button("Upload Files", type="primary"):
            with st.spinner("Uploading files..."):
                upload_results = []
                for uploaded_file in uploaded_files:
                    result = upload_document(uploaded_file)
                    if result:
                        upload_results.append({
                            "Filename": result["filename"],
                            "Status": result["status"],
                            "Size": f"{result['content_length']} bytes",
                            "Chunks": result["chunks_count"]
                        })
                
                if upload_results:
                    st.success(f"Successfully uploaded {len(upload_results)} files!")
                    st.session_state.uploaded_documents = upload_results
    
    with col2:
        st.subheader("Uploaded Documents")
        if st.button("Refresh Document List"):
            documents = get_documents_list()
            if documents:
                doc_data = []
                for doc in documents:
                    doc_data.append({
                        "Filename": doc["filename"],
                        "Type": doc["file_type"],
                        "Status": doc["status"],
                        "Size": f"{doc['file_size']} bytes",
                        "Upload Time": doc["upload_time"][:19]
                    })
                
                st.dataframe(pd.DataFrame(doc_data), use_container_width=True)
            else:
                st.info("No documents uploaded yet")

# Tab 2: Chat with Documents
with tab2:
    st.header("💬 Chat with Documents")
    
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    st.markdown("**Sources:**")
                    for source in message["sources"]:
                        st.markdown(f"- {source['filename']} (relevance: {source['relevance_score']:.2f})")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents"):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = chat_with_documents(prompt)
                answer = result["answer"]
                sources = result.get("sources", [])
                
                st.markdown(answer)
                
                if sources:
                    st.markdown("**Sources:**")
                    for source in sources:
                        st.markdown(f"- {source['filename']} (relevance: {source['relevance_score']:.2f})")
                
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources
                })

# Tab 3: GSTR-1 Filing
with tab3:
    st.header("📊 GSTR-1 Filing")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Header Details")
        with st.form("gstr1_header_form"):
            gstin = st.text_input("GSTIN *", placeholder="15-digit GSTIN (e.g., 27ABCDE1234F1Z5)")
            company_name = st.text_input("Company Name *", placeholder="Enter company name")
            
            # Filing Period
            col_month, col_year = st.columns(2)
            with col_month:
                month = st.selectbox("Month", 
                    ["01", "02", "03", "04", "05", "06", 
                     "07", "08", "09", "10", "11", "12"],
                    index=7  # Default to August
                )
            with col_year:
                year = st.selectbox("Year", 
                    ["2024", "2025", "2026"], 
                    index=0  # Default to 2024
                )
            
            filing_period = f"{month}{year}"
            gross_turnover = st.number_input("Gross Turnover (₹)", min_value=0.0, step=10000.0, value=500000.0)
            
            if st.form_submit_button("Create GSTR-1", type="primary"):
                if gstin and company_name:
                    with st.spinner("Creating GSTR-1 return..."):
                        result = create_gstr1_return(gstin, company_name, filing_period, gross_turnover)
                        if result:
                            st.success("GSTR-1 return created successfully!")
                            st.session_state.gstr1_return_id = result["return_id"]
                            
                            # Get JSON data
                            json_data = get_gstr1_json(result["return_id"])
                            if json_data:
                                st.session_state.gstr1_data = json_data
                else:
                    st.error("Please fill all required fields")
    
    with col2:
        st.subheader("Return Status")
        if hasattr(st.session_state, 'gstr1_return_id'):
            st.info(f"Return ID: {st.session_state.gstr1_return_id}")
            
            if st.button("Generate Preview Report"):
                if st.session_state.gstr1_data:
                    st.session_state.show_preview = True
        else:
            st.info("Create a GSTR-1 return to see status")
    
    # Preview Report Section
    if st.session_state.get("show_preview", False) and st.session_state.gstr1_data:
        st.markdown("---")
        st.subheader("📋 GSTR-1 Preview Report")
        
        gstr1_return = st.session_state.gstr1_data["gstr1_return"]
        header = gstr1_return["header"]
        summary = gstr1_return["summary"]
        
        # Header Summary Cards
        st.markdown("#### Header Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("GSTIN", header["gstin"])
        with col2:
            st.metric("Company", header["company_name"])
        with col3:
            st.metric("Period", header["filing_period"])
        with col4:
            st.metric("Total Invoices", summary["total_invoices"])
        
        # Financial Summary
        st.markdown("#### Financial Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Taxable Value", f"₹{summary['total_taxable_value']:,.2f}")
        with col2:
            st.metric("Total Tax", f"₹{summary['total_tax']:,.2f}")
        with col3:
            st.metric("Invoice Value", f"₹{summary['total_invoice_value']:,.2f}")
        
        # Generate GSTR-1 Report Layout
        generate_gstr1_report_layout(st.session_state.gstr1_data)
        
        # Action Buttons
        st.markdown("---")
        st.markdown("### Actions")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("✅ Validate", type="primary"):
                st.success("✅ GSTR-1 data validated successfully!")
        
        with col2:
            if st.button("📄 Download JSON"):
                json_link = download_json(st.session_state.gstr1_data, f"gstr1_{filing_period}.json")
                st.markdown(json_link, unsafe_allow_html=True)
        
        with col3:
            if st.button("📊 Download Excel"):
                excel_link = download_excel(st.session_state.gstr1_data, f"gstr1_{filing_period}.xlsx")
                st.markdown(excel_link, unsafe_allow_html=True)
        
        with col4:
            if st.button("📑 Download PDF"):
                pdf_link = download_pdf(st.session_state.gstr1_data, f"gstr1_{filing_period}.pdf")
                st.markdown(pdf_link, unsafe_allow_html=True)
        
        with col5:
            if st.button("🚀 Submit", type="secondary"):
                st.info("🔄 Submit functionality will be implemented for GST portal integration")

# Footer
st.markdown("---")
st.markdown("**GST Return Filing System** - Powered by AI Document Processing")
