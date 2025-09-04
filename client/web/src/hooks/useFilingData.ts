import { useState, useEffect } from 'react';
import { reportsApi } from '../api/reports';

export const useFilingData = (reportId: string) => {
  const [filingData, setFilingData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Data states
  const [b2bData, setB2bData] = useState<any[]>([]);
  const [b2clData, setB2clData] = useState<any[]>([]);
  const [b2csData, setB2csData] = useState<any[]>([]);
  const [hsnData, setHsnData] = useState<any[]>([]);

  useEffect(() => {
    const fetchFilingData = async () => {
      try {
        setLoading(true);
        const response = await reportsApi.getLatestGSTR1();
        setFilingData(response);
        
        // Process and set data for each section
        if (response) {
          processGSTR1Data(response);
        }
      } catch (err) {
        setError('Failed to fetch filing data');
        console.error('Error fetching filing data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (reportId) {
      fetchFilingData();
    }
  }, [reportId]);

  const processGSTR1Data = (gstr1Data: any) => {
    // Process B2B data
    const b2bInvoices = gstr1Data?.b2b || [];
    const processedB2B = b2bInvoices.map((inv: any, index: number) => ({
      id: index + 1,
      gstin: inv.ctin || inv.gstin || '',
      recipient_name: inv.recipient_name || inv.customer_name || inv.party_name || '',
      invoice_number: inv.inum || inv.invoice_number || inv.invoice_no || '',
      invoice_date: inv.idt || inv.invoice_date || '',
      invoice_value: parseFloat(inv.val || inv.invoice_value || inv.total_value || 0),
      place_of_supply: inv.pos || inv.place_of_supply || '',
      reverse_charge: inv.rchrg || inv.reverse_charge || 'N',
      invoice_type: inv.inv_typ || inv.invoice_type || 'Regular',
      ecommerce_gstin: inv.etin || inv.ecommerce_gstin || '',
      taxable_value: parseFloat(inv.taxable_value || inv.taxable_amount || 0),
      igst_amount: parseFloat(inv.igst_amount || inv.igst || 0),
      cgst_amount: parseFloat(inv.cgst_amount || inv.cgst || 0),
      sgst_amount: parseFloat(inv.sgst_amount || inv.sgst || inv.utgst_amount || inv.utgst || 0),
      cess_amount: parseFloat(inv.cess_amount || inv.cess || 0)
    }));
    setB2bData(processedB2B);

    // Process B2CL data
    const b2clInvoices = gstr1Data.b2cl || [];
    const processedB2CL = b2clInvoices.map((inv: any, index: number) => ({
      id: index + 1,
      invoice_number: inv.inum || inv.invoice_number || '',
      invoice_date: inv.idt || inv.invoice_date || '',
      invoice_value: parseFloat(inv.val || inv.invoice_value || 0),
      place_of_supply: inv.pos || inv.place_of_supply || '',
      ecommerce_gstin: inv.etin || inv.ecommerce_gstin || ''
    }));
    setB2clData(processedB2CL);

    // Process B2CS data
    const b2csData = gstr1Data.b2cs || [];
    const processedB2CS = b2csData.map((item: any, index: number) => ({
      id: index + 1,
      type: item.typ || item.type || 'OE',
      place_of_supply: item.pos || item.place_of_supply || '',
      applicable_percent_of_tax_rate: parseFloat(item.rt || item.rate || 0),
      rate: parseFloat(item.rt || item.rate || 0),
      taxable_value: parseFloat(item.txval || item.taxable_value || 0),
      cess_amount: parseFloat(item.csamt || item.cess_amount || 0),
      ecommerce_gstin: item.etin || item.ecommerce_gstin || ''
    }));
    setB2csData(processedB2CS);

    // Process HSN data
    processHSNData(gstr1Data);
  };

  const processHSNData = (gstr1Data: any) => {
    const hsnMap = new Map();
    
    // Process all invoice types for HSN data
    ['b2b', 'b2cl', 'b2cs'].forEach(invoiceType => {
      const invoices = gstr1Data[invoiceType] || [];
      
      invoices.forEach((inv: any) => {
        const itemsArray = inv.items || inv.itms || [];
        
        if (itemsArray && itemsArray.length > 0) {
          itemsArray.forEach((item: any) => {
            const hsnCode = item.hsn_sac || item.hsn || item.sac || item.hsn_code || '';
            
            if (hsnCode && hsnCode.toString().trim() !== '') {
              const cleanHsnCode = hsnCode.toString().trim();
              
              const itemTaxableValue = parseFloat(
                item.taxable_value || item.taxable_amount || item.base_amount || 
                item.net_amount || item.amount || item.value || 0
              );
              
              const itemTaxes = parseFloat(item.igst || item.igst_amount || item.integrated_tax || 0) + 
                              parseFloat(item.cgst || item.cgst_amount || item.central_tax || 0) + 
                              parseFloat(item.sgst || item.sgst_amount || item.state_tax || 
                                       item.utgst || item.utgst_amount || item.ut_tax || 0) + 
                              parseFloat(item.cess || item.cess_amount || item.cess_tax || 0);
              
              if (hsnMap.has(cleanHsnCode)) {
                const existing = hsnMap.get(cleanHsnCode);
                existing.total_quantity += parseFloat(item.quantity || item.qty || 0);
                existing.total_value += itemTaxableValue + itemTaxes;
                existing.taxable_value += itemTaxableValue;
                existing.integrated_tax_amount += parseFloat(item.igst_amount || item.igst || 0);
                existing.central_tax_amount += parseFloat(item.cgst_amount || item.cgst || 0);
                existing.state_ut_tax_amount += parseFloat(
                  item.sgst_amount || item.sgst || item.state_tax || 
                  item.utgst_amount || item.utgst || item.ut_tax || 0
                );
                existing.cess_amount += parseFloat(item.cess_amount || item.cess || 0);
              } else {
                hsnMap.set(cleanHsnCode, {
                  id: hsnMap.size + 1,
                  hsn: cleanHsnCode,
                  description: item.description || item.item_description || item.product_description || 
                             item.item_name || item.product_name || item.goods_description || '',
                  uqc: item.uqc || item.unit || item.unit_of_measurement || item.uom || 'NOS',
                  total_quantity: parseFloat(item.quantity || item.qty || 0),
                  total_value: itemTaxableValue + itemTaxes,
                  taxable_value: itemTaxableValue,
                  integrated_tax_amount: parseFloat(item.igst_amount || item.igst || 0),
                  central_tax_amount: parseFloat(item.cgst_amount || item.cgst || 0),
                  state_ut_tax_amount: parseFloat(
                    item.sgst_amount || item.sgst || item.state_tax || 
                    item.utgst_amount || item.utgst || item.ut_tax || 0
                  ),
                  cess_amount: parseFloat(item.cess_amount || item.cess || 0)
                });
              }
            }
          });
        }
      });
    });

    const processedHSN = Array.from(hsnMap.values());
    setHsnData(processedHSN);
  };

  return {
    filingData,
    loading,
    error,
    b2bData,
    b2clData,
    b2csData,
    hsnData,
    setB2bData,
    setB2clData,
    setB2csData,
    setHsnData
  };
};
