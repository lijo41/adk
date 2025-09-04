import * as XLSX from 'xlsx';

export const downloadCompleteExcel = (
  b2bData: any[],
  b2clData: any[],
  b2csData: any[],
  hsnData: any[],
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

  // Add HSN sheet using processed HSN data
  if (hsnData.length > 0) {
    const hsnSheet = XLSX.utils.json_to_sheet(hsnData);
    XLSX.utils.book_append_sheet(workbook, hsnSheet, 'HSN Summary');
  }

  // Add summary sheet with actual data from extraction result
  const extractionResult = filingData?.results?.['GSTR-1']?.gstr1_extraction || {};
  const summaryData = [
    {
      'Report Type': 'GSTR-1',
      'Filing Period': filingData?.results?.['GSTR-1']?.filing_period || 'N/A',
      'Total Invoices': extractionResult.total_invoices || 0,
      'B2B Invoices': extractionResult.b2b_invoices || 0,
      'B2CL Invoices': b2clData.length || 0,
      'B2CS Invoices': b2csData.length || 0,
      'HSN Codes': hsnData.length || 0,
      'Total Taxable Value': extractionResult.total_taxable_value || 0,
      'Total Tax Amount': extractionResult.total_tax_amount || 0,
      'Status': extractionResult.status || 'Unknown',
      'Generated On': new Date().toLocaleString()
    }
  ];
  
  const summarySheet = XLSX.utils.json_to_sheet(summaryData);
  XLSX.utils.book_append_sheet(workbook, summarySheet, 'Summary');

  // Download the file
  const timestamp = new Date().toISOString().split('T')[0];
  XLSX.writeFile(workbook, `GSTR1_Report_${timestamp}.xlsx`);
};
