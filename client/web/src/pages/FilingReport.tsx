import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ExcelGrid from '../components/ExcelGrid';
import { reportsApi } from '../api/reports';
import * as XLSX from 'xlsx';
import type { Column } from 'react-data-grid';

// Simple UI components
const Card = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`bg-white shadow rounded-lg ${className}`}>{children}</div>
);

const CardHeader = ({ children }: { children: React.ReactNode }) => (
  <div className="px-6 py-4 border-b border-gray-200">{children}</div>
);

const CardTitle = ({ children }: { children: React.ReactNode }) => (
  <h3 className="text-lg font-medium text-gray-900">{children}</h3>
);

const CardDescription = ({ children }: { children: React.ReactNode }) => (
  <p className="mt-1 text-sm text-gray-600">{children}</p>
);

const CardContent = ({ children }: { children: React.ReactNode }) => (
  <div className="px-6 py-4">{children}</div>
);

const Button = ({ children, onClick, variant = 'primary', className = '' }: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'outline';
  className?: string;
}) => {
  const baseClasses = 'inline-flex items-center px-4 py-2 border text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2';
  const variantClasses = variant === 'outline' 
    ? 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-blue-500'
    : 'border-transparent text-white bg-blue-600 hover:bg-blue-700 focus:ring-blue-500';
  
  return (
    <button 
      onClick={onClick}
      className={`${baseClasses} ${variantClasses} ${className}`}
    >
      {children}
    </button>
  );
};

const FilingReport: React.FC = () => {
  const navigate = useNavigate();
  const [filingData, setFilingData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('B2B');
  const [b2bData, setB2bData] = useState<any[]>([]);
  const [b2clData, setB2clData] = useState<any[]>([]);
  const [b2csData, setB2csData] = useState<any[]>([]);
  const [hsnData, setHsnData] = useState<any[]>([]);

  useEffect(() => {
    const fetchFilingData = async () => {
      try {
        // Always fetch latest data from database via reports API
        const latestReport = await reportsApi.getLatestGSTR1();
        
        if (!latestReport) {
          navigate('/filing/upload');
          return;
        }

        // Use latest data from database
        setFilingData(latestReport);
        
        // Transform data for Excel grids - cast to any to handle API structure mismatch
        const reportData = latestReport as any;
        console.log('Latest Report:', reportData);
        console.log('GSTR-1 Data:', reportData?.results?.['GSTR-1']);
        
        if (reportData?.results?.['GSTR-1']?.gstr1_extraction?.invoices) {
          const invoices = reportData.results['GSTR-1'].gstr1_extraction.invoices;
          console.log('Invoices found:', invoices.length, invoices);
          
          // Transform B2B data with comprehensive field mapping - calculate tax amounts from items if not at invoice level
          const b2bInvoices = invoices.filter((inv: any) => inv.invoice_type === 'B2B' || !inv.invoice_type).map((inv: any, index: number) => {
            // Calculate tax amounts from items if not available at invoice level
            let calculatedTaxableValue = parseFloat(inv.taxable_value || inv.taxable_amount || 0);
            let calculatedIgst = parseFloat(inv.igst_amount || inv.igst || 0);
            let calculatedCgst = parseFloat(inv.cgst_amount || inv.cgst || 0);
            let calculatedSgst = parseFloat(inv.sgst_amount || inv.sgst || inv.utgst_amount || inv.utgst || 0);
            let calculatedCess = parseFloat(inv.cess_amount || inv.cess || 0);
            
            // If tax amounts are 0 or missing, calculate from items
            const itemsArray = inv.items || inv.line_items || inv.invoice_items || inv.products || [];
            if ((calculatedTaxableValue === 0 || calculatedIgst === 0) && Array.isArray(itemsArray) && itemsArray.length > 0) {
              itemsArray.forEach((item: any) => {
                calculatedTaxableValue += parseFloat(item.taxable_value || item.taxable_amount || item.base_amount || item.net_amount || item.amount || item.value || 0);
                calculatedIgst += parseFloat(item.igst_amount || item.igst || item.integrated_tax || 0);
                calculatedCgst += parseFloat(item.cgst_amount || item.cgst || item.central_tax || 0);
                calculatedSgst += parseFloat(item.sgst_amount || item.sgst || item.state_tax || item.utgst_amount || item.utgst || 0);
                calculatedCess += parseFloat(item.cess_amount || item.cess || item.cess_tax || 0);
              });
            }
            
            return {
              id: index + 1,
              gstin: inv.recipient_gstin || inv.buyer_gstin || inv.gstin || inv.customer_gstin || inv.party_gstin || 
                     inv.client_gstin || inv.purchaser_gstin || inv.consignee_gstin || '',
              recipient_name: inv.recipient_name || inv.buyer_name || inv.customer_name || inv.party_name || 
                             inv.supplier_name || inv.client_name || inv.purchaser_name || inv.consignee_name || 
                             inv.company_name || inv.firm_name || 'N/A',
              invoice_number: inv.invoice_no || inv.invoice_number || inv.invoice_num || inv.bill_no || 
                             inv.bill_number || inv.doc_no || inv.document_number || inv.voucher_no || '',
              invoice_date: inv.invoice_date || inv.bill_date || inv.date || inv.doc_date || 
                           inv.document_date || inv.voucher_date || inv.transaction_date || '',
              invoice_value: inv.invoice_value || inv.total_invoice_value || inv.total_value || 
                            inv.total_amount || inv.amount || inv.grand_total || inv.net_total || 
                            (calculatedTaxableValue + calculatedIgst + calculatedCgst + calculatedSgst + calculatedCess) || 0,
              place_of_supply: inv.place_of_supply || inv.pos || inv.state || inv.supply_state || 
                              inv.delivery_state || inv.ship_to_state || inv.billing_state || '',
              reverse_charge: inv.reverse_charge || inv.rcm || inv.is_rcm || inv.reverse_charge_applicable || 'N',
              invoice_type: inv.invoice_type || inv.type || inv.transaction_type || inv.document_type || 'Regular',
              ecommerce_gstin: inv.ecommerce_gstin || inv.e_commerce_gstin || inv.marketplace_gstin || 
                              inv.portal_gstin || inv.platform_gstin || '',
              taxable_value: calculatedTaxableValue,
              igst_amount: calculatedIgst,
              cgst_amount: calculatedCgst,
              sgst_amount: calculatedSgst,
              cess_amount: calculatedCess
            };
          });
          setB2bData(b2bInvoices);

          // Transform B2CL data (Large consumers) with comprehensive field mapping
          const b2clInvoices = invoices.filter((inv: any) => inv.invoice_type === 'B2CL').map((inv: any, index: number) => {
            // Calculate values from items if not at invoice level
            let calculatedValue = parseFloat(inv.invoice_value || inv.total_invoice_value || inv.total_value || inv.total_amount || inv.amount || 0);
            const itemsArray = inv.items || inv.line_items || inv.invoice_items || inv.products || [];
            
            if (calculatedValue === 0 && Array.isArray(itemsArray) && itemsArray.length > 0) {
              itemsArray.forEach((item: any) => {
                const itemTaxableValue = parseFloat(item.taxable_value || item.taxable_amount || item.base_amount || item.net_amount || item.amount || item.value || 0);
                const itemTaxes = parseFloat(item.igst_amount || item.igst || 0) + 
                                parseFloat(item.cgst_amount || item.cgst || 0) + 
                                parseFloat(item.sgst_amount || item.sgst || item.utgst_amount || item.utgst || 0) + 
                                parseFloat(item.cess_amount || item.cess || 0);
                calculatedValue += itemTaxableValue + itemTaxes;
              });
            }
            
            return {
              id: index + 1,
              invoice_number: inv.invoice_no || inv.invoice_number || inv.invoice_num || inv.bill_no || 
                             inv.bill_number || inv.doc_no || inv.document_number || inv.voucher_no || '',
              invoice_date: inv.invoice_date || inv.bill_date || inv.date || inv.doc_date || 
                           inv.document_date || inv.voucher_date || inv.transaction_date || '',
              invoice_value: calculatedValue,
              place_of_supply: inv.place_of_supply || inv.pos || inv.state || inv.supply_state || 
                              inv.delivery_state || inv.ship_to_state || inv.billing_state || '',
              ecommerce_gstin: inv.ecommerce_gstin || inv.e_commerce_gstin || inv.marketplace_gstin || 
                              inv.portal_gstin || inv.platform_gstin || ''
            };
          });
          setB2clData(b2clInvoices);

          // Transform B2CS data (Small consumers) with comprehensive field mapping
          const b2csInvoices = invoices.filter((inv: any) => inv.invoice_type === 'B2CS').map((inv: any, index: number) => {
            // Calculate values from items if not at invoice level
            let calculatedTaxableValue = parseFloat(inv.taxable_value || inv.taxable_amount || 0);
            let calculatedCess = parseFloat(inv.cess || inv.cess_amount || 0);
            let calculatedTaxRate = parseFloat(inv.tax_rate || inv.applicable_percent_of_tax_rate || inv.rate || 0);
            
            const itemsArray = inv.items || inv.line_items || inv.invoice_items || inv.products || [];
            if (calculatedTaxableValue === 0 && Array.isArray(itemsArray) && itemsArray.length > 0) {
              itemsArray.forEach((item: any) => {
                calculatedTaxableValue += parseFloat(item.taxable_value || item.taxable_amount || item.base_amount || item.net_amount || item.amount || item.value || 0);
                calculatedCess += parseFloat(item.cess_amount || item.cess || item.cess_tax || 0);
                if (calculatedTaxRate === 0) {
                  calculatedTaxRate = parseFloat(item.tax_rate || item.gst_rate || item.rate || 0);
                }
              });
            }
            
            return {
              id: index + 1,
              type: inv.type || inv.supply_type || inv.transaction_type || 'OE',
              place_of_supply: inv.place_of_supply || inv.pos || inv.state || inv.supply_state || 
                              inv.delivery_state || inv.ship_to_state || inv.billing_state || '',
              applicable_percent_of_tax_rate: calculatedTaxRate,
              rate: calculatedTaxRate,
              taxable_value: calculatedTaxableValue,
              cess_amount: calculatedCess,
              ecommerce_gstin: inv.ecommerce_gstin || inv.e_commerce_gstin || inv.marketplace_gstin || 
                              inv.portal_gstin || inv.platform_gstin || ''
            };
          });
          setB2csData(b2csInvoices);

          // Transform HSN data with comprehensive field mapping
          const hsnMap = new Map();
          invoices.forEach((inv: any) => {
            // Check multiple possible item array locations
            const itemsArray = inv.items || inv.line_items || inv.invoice_items || inv.products || [];
            
            if (Array.isArray(itemsArray) && itemsArray.length > 0) {
              itemsArray.forEach((item: any) => {
                // Enhanced HSN code detection
                const hsnCode = item.hsn_sac || item.hsn || item.sac || item.hsn_code || 
                               item.product_code || item.commodity_code || item.item_code || '';
                
                if (hsnCode && hsnCode.toString().trim() !== '') {
                  const cleanHsnCode = hsnCode.toString().trim();
                  
                  if (hsnMap.has(cleanHsnCode)) {
                    const existing = hsnMap.get(cleanHsnCode);
                    existing.total_quantity += parseFloat(item.quantity || item.qty || item.amount || item.units || 0);
                    
                    // Enhanced taxable value detection
                    const itemTaxableValue = parseFloat(
                      item.taxable_value || item.taxable_amount || item.base_amount || 
                      item.net_amount || item.amount || item.value || 0
                    );
                    
                    // Enhanced tax amount detection
                    const itemTaxes = parseFloat(item.igst || item.igst_amount || item.integrated_tax || 0) + 
                                    parseFloat(item.cgst || item.cgst_amount || item.central_tax || 0) + 
                                    parseFloat(item.sgst || item.sgst_amount || item.state_tax || 
                                             item.utgst || item.utgst_amount || item.ut_tax || 0) + 
                                    parseFloat(item.cess || item.cess_amount || item.cess_tax || 0);
                    
                    existing.total_value += itemTaxableValue + itemTaxes;
                    existing.taxable_value += itemTaxableValue;
                    existing.integrated_tax_amount += parseFloat(item.igst_amount || item.igst || item.integrated_tax || 0);
                    existing.central_tax_amount += parseFloat(item.cgst_amount || item.cgst || item.central_tax || 0);
                    existing.state_ut_tax_amount += parseFloat(
                      item.sgst_amount || item.sgst || item.state_tax || 
                      item.utgst_amount || item.utgst || item.ut_tax || 0
                    );
                    existing.cess_amount += parseFloat(item.cess_amount || item.cess || item.cess_tax || 0);
                  } else {
                    // Enhanced taxable value detection
                    const itemTaxableValue = parseFloat(
                      item.taxable_value || item.taxable_amount || item.base_amount || 
                      item.net_amount || item.amount || item.value || 0
                    );
                    
                    // Enhanced tax amount detection
                    const itemTaxes = parseFloat(item.igst || item.igst_amount || item.integrated_tax || 0) + 
                                    parseFloat(item.cgst || item.cgst_amount || item.central_tax || 0) + 
                                    parseFloat(item.sgst || item.sgst_amount || item.state_tax || 
                                             item.utgst || item.utgst_amount || item.ut_tax || 0) + 
                                    parseFloat(item.cess || item.cess_amount || item.cess_tax || 0);
                    
                    hsnMap.set(cleanHsnCode, {
                      id: hsnMap.size + 1,
                      hsn: cleanHsnCode,
                      description: item.description || item.item_description || item.product_description || 
                                 item.item_name || item.product_name || item.goods_description || '',
                      uqc: item.uqc || item.unit || item.unit_of_measurement || item.uom || 'NOS',
                      total_quantity: parseFloat(item.quantity || item.qty || item.amount || item.units || 0),
                      total_value: itemTaxableValue + itemTaxes,
                      taxable_value: itemTaxableValue,
                      integrated_tax_amount: parseFloat(item.igst_amount || item.igst || item.integrated_tax || 0),
                      central_tax_amount: parseFloat(item.cgst_amount || item.cgst || item.central_tax || 0),
                      state_ut_tax_amount: parseFloat(
                        item.sgst_amount || item.sgst || item.state_tax || 
                        item.utgst_amount || item.utgst || item.ut_tax || 0
                      ),
                      cess_amount: parseFloat(item.cess_amount || item.cess || item.cess_tax || 0)
                    });
                  }
                }
              });
            }
            
            // Fallback: If no items found, try to extract HSN from invoice level
            if (itemsArray.length === 0) {
              const invoiceHsn = inv.hsn_sac || inv.hsn || inv.sac || inv.hsn_code || '';
              if (invoiceHsn && invoiceHsn.toString().trim() !== '') {
                const cleanHsnCode = invoiceHsn.toString().trim();
                const invoiceTaxableValue = parseFloat(inv.taxable_value || inv.taxable_amount || 0);
                const invoiceTaxes = parseFloat(inv.igst_amount || inv.igst || 0) + 
                                   parseFloat(inv.cgst_amount || inv.cgst || 0) + 
                                   parseFloat(inv.sgst_amount || inv.sgst || inv.utgst_amount || inv.utgst || 0) + 
                                   parseFloat(inv.cess_amount || inv.cess || 0);
                
                if (hsnMap.has(cleanHsnCode)) {
                  const existing = hsnMap.get(cleanHsnCode);
                  existing.total_quantity += 1; // Default quantity for invoice-level HSN
                  existing.total_value += invoiceTaxableValue + invoiceTaxes;
                  existing.taxable_value += invoiceTaxableValue;
                  existing.integrated_tax_amount += parseFloat(inv.igst_amount || inv.igst || 0);
                  existing.central_tax_amount += parseFloat(inv.cgst_amount || inv.cgst || 0);
                  existing.state_ut_tax_amount += parseFloat(inv.sgst_amount || inv.sgst || inv.utgst_amount || inv.utgst || 0);
                  existing.cess_amount += parseFloat(inv.cess_amount || inv.cess || 0);
                } else {
                  hsnMap.set(cleanHsnCode, {
                    id: hsnMap.size + 1,
                    hsn: cleanHsnCode,
                    description: inv.description || inv.goods_description || 'Invoice Level HSN',
                    uqc: 'NOS',
                    total_quantity: 1,
                    total_value: invoiceTaxableValue + invoiceTaxes,
                    taxable_value: invoiceTaxableValue,
                    integrated_tax_amount: parseFloat(inv.igst_amount || inv.igst || 0),
                    central_tax_amount: parseFloat(inv.cgst_amount || inv.cgst || 0),
                    state_ut_tax_amount: parseFloat(inv.sgst_amount || inv.sgst || inv.utgst_amount || inv.utgst || 0),
                    cess_amount: parseFloat(inv.cess_amount || inv.cess || 0)
                  });
                }
              }
            }
          });
          setHsnData(Array.from(hsnMap.values()));
        }
      } catch (error) {
        console.error('Error loading filing data:', error);
      }
    };

    fetchFilingData();
  }, [navigate]);


  // Column definitions for Excel grids
  const b2bColumns: Column<any>[] = [
    { key: 'gstin', name: 'GSTIN', width: 150 },
    { key: 'recipient_name', name: 'Recipient Name', width: 200 },
    { key: 'invoice_number', name: 'Invoice Number', width: 150 },
    { key: 'invoice_date', name: 'Invoice Date', width: 120 },
    { key: 'invoice_value', name: 'Invoice Value', width: 120 },
    { key: 'place_of_supply', name: 'Place of Supply', width: 120 },
    { key: 'reverse_charge', name: 'Reverse Charge', width: 100 },
    { key: 'invoice_type', name: 'Invoice Type', width: 120 },
    { key: 'ecommerce_gstin', name: 'E-commerce GSTIN', width: 150 },
    { key: 'taxable_value', name: 'Taxable Value', width: 120 },
    { key: 'igst_amount', name: 'IGST Amount', width: 120 },
    { key: 'cgst_amount', name: 'CGST Amount', width: 120 },
    { key: 'sgst_amount', name: 'SGST/UTGST Amount', width: 140 },
    { key: 'cess_amount', name: 'Cess Amount', width: 120 }
  ];

  const b2clColumns: Column<any>[] = [
    { key: 'invoice_number', name: 'Invoice Number', width: 150 },
    { key: 'invoice_date', name: 'Invoice Date', width: 120 },
    { key: 'invoice_value', name: 'Invoice Value', width: 120 },
    { key: 'place_of_supply', name: 'Place of Supply', width: 120 },
    { key: 'ecommerce_gstin', name: 'E-commerce GSTIN', width: 150 }
  ];

  const b2csColumns: Column<any>[] = [
    { key: 'type', name: 'Type', width: 80 },
    { key: 'place_of_supply', name: 'Place of Supply', width: 120 },
    { key: 'applicable_percent_of_tax_rate', name: 'Tax Rate %', width: 100 },
    { key: 'rate', name: 'Rate', width: 80 },
    { key: 'taxable_value', name: 'Taxable Value', width: 120 },
    { key: 'cess_amount', name: 'Cess Amount', width: 100 },
    { key: 'ecommerce_gstin', name: 'E-commerce GSTIN', width: 150 }
  ];

  const hsnColumns: Column<any>[] = [
    { key: 'hsn', name: 'HSN', width: 100 },
    { key: 'description', name: 'Description', width: 200 },
    { key: 'uqc', name: 'UQC', width: 80 },
    { key: 'total_quantity', name: 'Total Quantity', width: 120 },
    { key: 'total_value', name: 'Total Value', width: 120 },
    { key: 'taxable_value', name: 'Taxable Value', width: 120 },
    { key: 'integrated_tax_amount', name: 'Integrated Tax Amount', width: 150 },
    { key: 'central_tax_amount', name: 'Central Tax Amount', width: 150 },
    { key: 'state_ut_tax_amount', name: 'State/UT Tax Amount', width: 150 },
    { key: 'cess_amount', name: 'Cess Amount', width: 100 }
  ];

  const downloadCompleteExcel = async () => {
    try {
      // Get latest report data with invoices
      const reportData = filingData as any;
      
      if (!reportData?.results?.['GSTR-1']?.gstr1_extraction?.invoices) {
        console.error('No invoice data available for Excel export');
        return;
      }

      const invoices = reportData.results['GSTR-1'].gstr1_extraction.invoices;
      
      // Create workbook
      const workbook = XLSX.utils.book_new();

      // Transform and add B2B data
      const b2bData = invoices
        .filter((inv: any) => inv.invoice_type === 'B2B' || !inv.invoice_type)
        .map((inv: any) => ({
          'GSTIN': inv.recipient_gstin || inv.buyer_gstin || inv.gstin || '',
          'Recipient Name': inv.recipient_name || inv.buyer_name || inv.customer_name || 'N/A',
          'Invoice Number': inv.invoice_no || inv.invoice_number || '',
          'Invoice Date': inv.invoice_date || '',
          'Invoice Value': inv.invoice_value || inv.total_invoice_value || inv.total_value || 0,
          'Place of Supply': inv.place_of_supply || '',
          'Reverse Charge': inv.reverse_charge || 'N',
          'Invoice Type': inv.invoice_type || 'Regular',
          'E-commerce GSTIN': inv.ecommerce_gstin || ''
        }));

      if (b2bData.length > 0) {
        const b2bSheet = XLSX.utils.json_to_sheet(b2bData);
        XLSX.utils.book_append_sheet(workbook, b2bSheet, 'B2B');
      }

      // Transform and add B2CL data
      const b2clData = invoices
        .filter((inv: any) => inv.invoice_type === 'B2CL')
        .map((inv: any) => ({
          'Invoice Number': inv.invoice_no || inv.invoice_number || '',
          'Invoice Date': inv.invoice_date || '',
          'Invoice Value': inv.invoice_value || inv.total_invoice_value || inv.total_value || 0,
          'Place of Supply': inv.place_of_supply || '',
          'E-commerce GSTIN': inv.ecommerce_gstin || ''
        }));

      if (b2clData.length > 0) {
        const b2clSheet = XLSX.utils.json_to_sheet(b2clData);
        XLSX.utils.book_append_sheet(workbook, b2clSheet, 'B2CL');
      }

      // Transform and add B2CS data
      const b2csData = invoices
        .filter((inv: any) => inv.invoice_type === 'B2CS')
        .map((inv: any) => ({
          'Type': inv.type || 'OE',
          'Place of Supply': inv.place_of_supply || '',
          'Tax Rate %': inv.tax_rate || 0,
          'Rate': inv.rate || 0,
          'Taxable Value': inv.taxable_value || inv.taxable_amount || 0,
          'Cess Amount': inv.cess || inv.cess_amount || 0,
          'E-commerce GSTIN': inv.ecommerce_gstin || ''
        }));

      if (b2csData.length > 0) {
        const b2csSheet = XLSX.utils.json_to_sheet(b2csData);
        XLSX.utils.book_append_sheet(workbook, b2csSheet, 'B2CS');
      }

      // Transform and add HSN data
      const hsnMap = new Map();
      invoices.forEach((inv: any) => {
        // Check multiple possible item array locations
        const itemsArray = inv.items || inv.line_items || inv.invoice_items || inv.products || [];
        
        if (Array.isArray(itemsArray) && itemsArray.length > 0) {
          itemsArray.forEach((item: any) => {
            // Enhanced HSN code detection
            const hsnCode = item.hsn_sac || item.hsn || item.sac || item.hsn_code || 
                           item.product_code || item.commodity_code || item.item_code || '';
            
            if (hsnCode && hsnCode.toString().trim() !== '') {
              const cleanHsnCode = hsnCode.toString().trim();
              
              if (hsnMap.has(cleanHsnCode)) {
                const existing = hsnMap.get(cleanHsnCode);
                existing.total_quantity += parseFloat(item.quantity || item.qty || 0);
                
                // Enhanced taxable value detection
                const itemTaxableValue = parseFloat(
                  item.taxable_value || item.taxable_amount || item.base_amount || 
                  item.net_amount || item.amount || item.value || 0
                );
                
                // Enhanced tax amount detection
                const itemTaxes = parseFloat(item.igst || item.igst_amount || item.integrated_tax || 0) + 
                                parseFloat(item.cgst || item.cgst_amount || item.central_tax || 0) + 
                                parseFloat(item.sgst || item.sgst_amount || item.state_tax || 
                                         item.utgst || item.utgst_amount || item.ut_tax || 0) + 
                                parseFloat(item.cess || item.cess_amount || item.cess_tax || 0);
                
                existing.total_value += itemTaxableValue + itemTaxes;
                existing.taxable_value += itemTaxableValue;
                existing.integrated_tax_amount += parseFloat(item.igst_amount || item.igst || item.integrated_tax || 0);
                existing.central_tax_amount += parseFloat(item.cgst_amount || item.cgst || item.central_tax || 0);
                existing.state_ut_tax_amount += parseFloat(
                  item.sgst_amount || item.sgst || item.state_tax || 
                  item.utgst_amount || item.utgst || item.ut_tax || 0
                );
                existing.cess_amount += parseFloat(item.cess_amount || item.cess || item.cess_tax || 0);
              } else {
                // Enhanced taxable value detection
                const itemTaxableValue = parseFloat(
                  item.taxable_value || item.taxable_amount || item.base_amount || 
                  item.net_amount || item.amount || item.value || 0
                );
                
                // Enhanced tax amount detection
                const itemTaxes = parseFloat(item.igst || item.igst_amount || item.integrated_tax || 0) + 
                                parseFloat(item.cgst || item.cgst_amount || item.central_tax || 0) + 
                                parseFloat(item.sgst || item.sgst_amount || item.state_tax || 
                                         item.utgst || item.utgst_amount || item.ut_tax || 0) + 
                                parseFloat(item.cess || item.cess_amount || item.cess_tax || 0);
                
                hsnMap.set(cleanHsnCode, {
                  id: hsnMap.size + 1,
                  hsn: cleanHsnCode,
                  description: item.description || item.item_description || item.product_description || 
                                 item.item_name || item.product_name || item.goods_description || '',
                  uqc: item.uqc || item.unit || item.unit_of_measurement || item.uom || 'NOS',
                  total_quantity: parseFloat(item.quantity || item.qty || 0),
                  total_value: itemTaxableValue + itemTaxes,
                  taxable_value: itemTaxableValue,
                  integrated_tax_amount: parseFloat(item.igst_amount || item.igst || item.integrated_tax || 0),
                  central_tax_amount: parseFloat(item.cgst_amount || item.cgst || item.central_tax || 0),
                  state_ut_tax_amount: parseFloat(
                    item.sgst_amount || item.sgst || item.state_tax || 
                    item.utgst_amount || item.utgst || item.ut_tax || 0
                  ),
                  cess_amount: parseFloat(item.cess_amount || item.cess || item.cess_tax || 0)
                });
              }
            }
          });
        }
      });

      const hsnData = Array.from(hsnMap.values());
      if (hsnData.length > 0) {
        const hsnSheet = XLSX.utils.json_to_sheet(hsnData);
        XLSX.utils.book_append_sheet(workbook, hsnSheet, 'HSN');
      }

      // Generate filename with current date
      const currentDate = new Date().toISOString().split('T')[0];
      const filename = `GSTR1_Complete_Report_${currentDate}.xlsx`;

      // Download the file
      XLSX.writeFile(workbook, filename);
      
      console.log('Excel file downloaded successfully');
    } catch (error) {
      console.error('Error downloading Excel file:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Filing Report</h1>
          <p className="text-gray-600 mt-2">Your GST returns are ready for download and submission</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                ✓
              </div>
              <span className="ml-3 text-sm font-medium text-gray-900">Documents Processed</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                ✓
              </div>
              <span className="ml-3 text-sm font-medium text-gray-900">GSTR-1 Generated</span>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                3
              </div>
              <span className="ml-3 text-sm font-medium text-blue-600">Ready for Download</span>
            </div>
          </div>
        </div>

        {/* GSTR-1 Summary */}
        {filingData?.results?.['GSTR-1'] ? (
          <div>
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>GSTR-1 Summary</CardTitle>
              <CardDescription>
                Overview of your GSTR-1 return for {filingData.results['GSTR-1'].filing_period}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-4 gap-6 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-900">
                    {filingData.results['GSTR-1'].gstr1_extraction?.total_invoices || 0}
                  </div>
                  <div className="text-sm text-blue-700">Total Invoices</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-900">
                    ₹{filingData.results['GSTR-1'].gstr1_extraction?.total_taxable_value?.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-green-700">Taxable Value</div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-purple-900">
                    ₹{filingData.results['GSTR-1'].gstr1_extraction?.total_tax_amount?.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-purple-700">Tax Amount</div>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-orange-900">
                    {filingData.results['GSTR-1'].status === 'completed' ? 'Ready' : filingData.results['GSTR-1'].status}
                  </div>
                  <div className="text-sm text-orange-700">Status</div>
                </div>
              </div>
            </CardContent>
          </Card>

        {/* Interactive Excel Preview */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Interactive Data Preview</CardTitle>
                <CardDescription>
                  View and edit your GSTR-1 data in Excel-like interface
                </CardDescription>
              </div>
              <Button 
                className="bg-green-600 hover:bg-green-700 text-white"
                onClick={downloadCompleteExcel}
              >
                📊 Download Excel
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Tab Navigation */}
            <div className="border-b border-gray-200 mb-6">
              <nav className="-mb-px flex space-x-8">
                {['B2B', 'B2CL', 'B2CS', 'HSN'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="mt-6">
              {activeTab === 'B2B' && (
                <div>
                  <ExcelGrid 
                    data={b2bData} 
                    columns={b2bColumns}
                    title="B2B Invoices"
                    onDataChange={setB2bData}
                  />
                </div>
              )}

              {activeTab === 'B2CL' && (
                <div>
                  <ExcelGrid 
                    data={b2clData} 
                    columns={b2clColumns}
                    title="B2CL Invoices"
                    onDataChange={setB2clData}
                  />
                </div>
              )}

              {activeTab === 'B2CS' && (
                <div>
                  <ExcelGrid 
                    data={b2csData} 
                    columns={b2csColumns}
                    title="B2CS Summary"
                    onDataChange={setB2csData}
                  />
                </div>
              )}

              {activeTab === 'HSN' && (
                <div>
                  <ExcelGrid 
                    data={hsnData} 
                    columns={hsnColumns}
                    title="HSN Summary"
                    onDataChange={setHsnData}
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>


        {/* Next Steps */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
            <CardDescription>
              What to do after downloading your returns
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="flex items-start space-x-4">
                <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0">
                  1
                </div>
                <div>
                  <h4 className="font-medium text-lg">Review the Generated Returns</h4>
                  <p className="text-sm text-gray-600 mt-1">Carefully review all extracted data for accuracy</p>
                </div>
              </div>
              <div className="flex items-start space-x-4">
                <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0">
                  2
                </div>
                <div>
                  <h4 className="font-medium text-lg">Upload to GST Portal</h4>
                  <p className="text-sm text-gray-600 mt-1">Log into the official GST portal and upload the JSON files</p>
                </div>
              </div>
              <div className="flex items-start space-x-4">
                <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0">
                  3
                </div>
                <div>
                  <h4 className="font-medium text-lg">Submit Returns</h4>
                  <p className="text-sm text-gray-600 mt-1">Complete the submission process on the GST portal</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-between mt-8">
          <Button 
            variant="outline" 
            onClick={() => navigate('/dashboard')}
          >
            Back to Dashboard
          </Button>
          <Button onClick={() => navigate('/filing/upload')}>
            Start New Filing
          </Button>
        </div>
          </div>
    ) : (
      <div className="text-center py-12">
        <h3 className="mt-2 text-sm font-medium text-gray-900">No GSTR-1 data available</h3>
        <p className="mt-1 text-sm text-gray-500">
          Please complete a GSTR-1 filing first.
        </p>
        <div className="mt-6">
          <button
            onClick={() => navigate('/filing/upload')}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Start GSTR-1 Filing
          </button>
        </div>
      </div>
    )}
  </div>
</div>
);
};

export default FilingReport;
