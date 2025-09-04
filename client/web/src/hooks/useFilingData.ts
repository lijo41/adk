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
        setError(null);
        
        console.log('=== FETCHING FILING DATA ===');
        console.log('Report ID:', reportId);
        
        const data = await reportsApi.getLatestGSTR1();
        console.log('=== RAW API RESPONSE ===');
        console.log('Fetched filing data:', JSON.stringify(data, null, 2));
        
        if (data && data.json_data) {
          console.log('=== PROCESSING JSON DATA ===');
          processGSTR1Data(data.json_data);
        } else if (data) {
          console.log('=== PROCESSING DIRECT DATA ===');
          processGSTR1Data(data);
        } else {
          console.log('=== NO DATA FOUND ===');
          setError('No filing data found');
        }
      } catch (err) {
        console.error('=== API ERROR ===');
        console.error('Error fetching filing data:', err);
        setError('Failed to fetch filing data');
      } finally {
        setLoading(false);
      }
    };

    fetchFilingData();
  }, [reportId]);

  const processGSTR1Data = (gstr1Data: any) => {
    console.log('=== FULL GSTR1 DATA STRUCTURE ===');
    console.log('gstr1Data:', JSON.stringify(gstr1Data, null, 2));
    
    // Set the filing data for the report page
    setFilingData(gstr1Data);
    
    // Extract data from correct path: results['GSTR-1'].gstr1_extraction
    const extractionResult = gstr1Data?.results?.['GSTR-1']?.gstr1_extraction || {};
    
    console.log('=== EXTRACTION RESULT ===');
    console.log('Extraction result keys:', Object.keys(extractionResult));
    console.log('Extraction result:', JSON.stringify(extractionResult, null, 2));
    
    // Use invoices array and categorize based on category field
    const allInvoices = extractionResult.invoices || [];
    const categorizedInvoices = {
      b2b: allInvoices.filter((inv: any) => inv.category === 'B2B'),
      b2cl: allInvoices.filter((inv: any) => inv.category === 'B2CL'),
      b2cs: allInvoices.filter((inv: any) => inv.category === 'B2CS')
    };

    console.log('=== CATEGORIZED INVOICES ===');
    console.log('Database categorization:', {
      b2b: categorizedInvoices.b2b.length,
      b2cl: categorizedInvoices.b2cl.length,
      b2cs: categorizedInvoices.b2cs.length
    });
    
    if (categorizedInvoices.b2b.length > 0) {
      console.log('First B2B invoice:', JSON.stringify(categorizedInvoices.b2b[0], null, 2));
    }
    if (categorizedInvoices.b2cl.length > 0) {
      console.log('First B2CL invoice:', JSON.stringify(categorizedInvoices.b2cl[0], null, 2));
    }
    if (categorizedInvoices.b2cs.length > 0) {
      console.log('First B2CS invoice:', JSON.stringify(categorizedInvoices.b2cs[0], null, 2));
    }

    // Process B2B data - map directly to database fields
    const processedB2B = categorizedInvoices.b2b.map((inv: any, index: number) => {
      // Calculate totals from items array
      const items = inv.items || [];
      let totalTaxableValue = 0;
      let totalIgst = 0;
      let totalCgst = 0;
      let totalSgst = 0;
      let totalCess = 0;

      items.forEach((item: any) => {
        totalTaxableValue += parseFloat(item.taxable_value || 0);
        totalIgst += parseFloat(item.igst || 0);
        totalCgst += parseFloat(item.cgst || 0);
        totalSgst += parseFloat(item.sgst || 0);
        totalCess += parseFloat(item.cess || 0);
      });

      return {
        id: index + 1,
        gstin: inv.recipient_gstin || '',
        recipient_name: inv.recipient_name || '',
        invoice_number: inv.invoice_no || '',
        invoice_date: inv.invoice_date || '',
        invoice_value: parseFloat(inv.invoice_value || 0),
        place_of_supply: inv.place_of_supply || '',
        reverse_charge: 'N',
        invoice_type: 'B2B',
        ecommerce_gstin: '',
        taxable_value: totalTaxableValue,
        igst_amount: totalIgst,
        cgst_amount: totalCgst,
        sgst_amount: totalSgst,
        cess_amount: totalCess
      };
    });
    
    console.log('=== PROCESSED B2B DATA ===');
    console.log('Processed B2B count:', processedB2B.length);
    console.log('First processed B2B:', processedB2B[0]);
    
    setB2bData(processedB2B);

    // Process B2CL data - map directly to database fields
    const processedB2CL = categorizedInvoices.b2cl.map((inv: any, index: number) => {
      // Calculate totals from items array
      const items = inv.items || [];
      let totalTaxableValue = 0;
      let totalIgst = 0;
      let totalCgst = 0;
      let totalSgst = 0;
      let totalCess = 0;

      items.forEach((item: any) => {
        totalTaxableValue += parseFloat(item.taxable_value || 0);
        totalIgst += parseFloat(item.igst || 0);
        totalCgst += parseFloat(item.cgst || 0);
        totalSgst += parseFloat(item.sgst || 0);
        totalCess += parseFloat(item.cess || 0);
      });

      return {
        id: index + 1,
        invoice_number: inv.invoice_no || '',
        invoice_date: inv.invoice_date || '',
        invoice_value: parseFloat(inv.invoice_value || 0),
        place_of_supply: inv.place_of_supply || '',
        taxable_value: totalTaxableValue,
        igst_amount: totalIgst,
        cgst_amount: totalCgst,
        sgst_amount: totalSgst,
        cess_amount: totalCess,
        ecommerce_gstin: ''
      };
    });
    
    console.log('=== PROCESSED B2CL DATA ===');
    console.log('Processed B2CL count:', processedB2CL.length);
    
    setB2clData(processedB2CL);

    // Process B2CS data - map directly to database fields
    const processedB2CS = categorizedInvoices.b2cs.map((inv: any, index: number) => {
      // Calculate totals from items array
      const items = inv.items || [];
      let totalTaxableValue = 0;
      let totalCess = 0;
      let taxRate = 0;

      items.forEach((item: any) => {
        totalTaxableValue += parseFloat(item.taxable_value || 0);
        totalCess += parseFloat(item.cess || 0);
        // Calculate tax rate from CGST + SGST + IGST
        const cgst = parseFloat(item.cgst || 0);
        const sgst = parseFloat(item.sgst || 0);
        const igst = parseFloat(item.igst || 0);
        const itemTaxableValue = parseFloat(item.taxable_value || 0);
        
        if (itemTaxableValue > 0) {
          const itemRate = ((cgst + sgst + igst) / itemTaxableValue) * 100;
          if (itemRate > taxRate) taxRate = itemRate;
        }
      });

      return {
        id: index + 1,
        invoice_number: inv.invoice_no || '',
        invoice_date: inv.invoice_date || '',
        invoice_value: parseFloat(inv.invoice_value || 0),
        type: 'OE',
        place_of_supply: inv.place_of_supply || '',
        applicable_percent_of_tax_rate: Math.round(taxRate * 100) / 100,
        rate: Math.round(taxRate * 100) / 100,
        taxable_value: totalTaxableValue,
        cess_amount: totalCess,
        ecommerce_gstin: ''
      };
    });
    setB2csData(processedB2CS);

    // Process HSN data
    processHSNData(gstr1Data);
  };

  const processHSNData = (gstr1Data: any) => {
    const hsnMap = new Map();
    
    // Extract invoices from correct path: results['GSTR-1'].gstr1_extraction
    const extractionResult = gstr1Data?.results?.['GSTR-1']?.gstr1_extraction || {};
    const invoicesData = extractionResult.invoices || [];
    
    // Process all invoices for HSN data
    invoicesData.forEach((inv: any) => {
      const itemsArray = inv.items || inv.line_items || inv.itms || [];
      
      if (itemsArray && itemsArray.length > 0) {
        itemsArray.forEach((item: any) => {
          const hsnCode = item.hsn_code || item.hsn || item.sac || '';
          
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
