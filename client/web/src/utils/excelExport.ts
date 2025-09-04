import * as XLSX from 'xlsx';

export const downloadCompleteExcel = (
  b2bData: any[],
  b2clData: any[],
  b2csData: any[],
  filingData: any
) => {
  const workbook = XLSX.utils.book_new();

  // Add B2B sheet
  if (b2bData.length > 0) {
    const b2bSheet = XLSX.utils.json_to_sheet(b2bData);
    XLSX.utils.book_append_sheet(workbook, b2bSheet, 'B2B Invoices');
  }

  // Add B2CL sheet
  if (b2clData.length > 0) {
    const b2clSheet = XLSX.utils.json_to_sheet(b2clData);
    XLSX.utils.book_append_sheet(workbook, b2clSheet, 'B2CL Invoices');
  }

  // Add B2CS sheet
  if (b2csData.length > 0) {
    const b2csSheet = XLSX.utils.json_to_sheet(b2csData);
    XLSX.utils.book_append_sheet(workbook, b2csSheet, 'B2CS Summary');
  }

  // Process and add HSN data
  const hsnMap = new Map();
  
  // Process all invoice types for HSN data
  ['b2b', 'b2cl', 'b2cs'].forEach(invoiceType => {
    const invoices = filingData?.results?.['GSTR-1']?.[invoiceType] || [];
    
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
        });
      }
    });
  });

  const hsnDataForExcel = Array.from(hsnMap.values());
  if (hsnDataForExcel.length > 0) {
    const hsnSheet = XLSX.utils.json_to_sheet(hsnDataForExcel);
    XLSX.utils.book_append_sheet(workbook, hsnSheet, 'HSN Summary');
  }

  // Add summary sheet
  const summaryData = [
    {
      'Report Type': 'GSTR-1',
      'Total Invoices': filingData?.results?.['GSTR-1']?.summary?.total_invoices || 0,
      'Total Taxable Value': filingData?.results?.['GSTR-1']?.summary?.total_taxable_value || 0,
      'Total Tax Amount': filingData?.results?.['GSTR-1']?.summary?.total_tax_amount || 0,
      'Status': filingData?.results?.['GSTR-1']?.status || 'Unknown'
    }
  ];
  
  const summarySheet = XLSX.utils.json_to_sheet(summaryData);
  XLSX.utils.book_append_sheet(workbook, summarySheet, 'Summary');

  // Download the file
  const timestamp = new Date().toISOString().split('T')[0];
  XLSX.writeFile(workbook, `GSTR1_Report_${timestamp}.xlsx`);
};
