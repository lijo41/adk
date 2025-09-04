import type { Column } from 'react-data-grid';

export const b2bColumns: Column<any>[] = [
  { key: 'gstin', name: 'GSTIN', width: 150 },
  { key: 'recipient_name', name: 'Recipient Name', width: 200 },
  { key: 'invoice_number', name: 'Invoice Number', width: 150 },
  { key: 'invoice_date', name: 'Invoice Date', width: 120 },
  { key: 'invoice_value', name: 'Invoice Value', width: 120 },
  { key: 'place_of_supply', name: 'Place of Supply', width: 120 },
  { key: 'reverse_charge', name: 'Reverse Charge', width: 120 },
  { key: 'invoice_type', name: 'Invoice Type', width: 120 },
  { key: 'taxable_value', name: 'Taxable Value', width: 120 },
  { key: 'igst_amount', name: 'IGST Amount', width: 100 },
  { key: 'cgst_amount', name: 'CGST Amount', width: 100 },
  { key: 'sgst_amount', name: 'SGST/UTGST Amount', width: 150 },
  { key: 'cess_amount', name: 'Cess Amount', width: 100 },
  { key: 'ecommerce_gstin', name: 'E-commerce GSTIN', width: 150 }
];

export const b2clColumns: Column<any>[] = [
  { key: 'invoice_number', name: 'Invoice Number', width: 150 },
  { key: 'invoice_date', name: 'Invoice Date', width: 120 },
  { key: 'invoice_value', name: 'Invoice Value', width: 120 },
  { key: 'place_of_supply', name: 'Place of Supply', width: 120 },
  { key: 'taxable_value', name: 'Taxable Value', width: 120 },
  { key: 'igst_amount', name: 'IGST Amount', width: 100 },
  { key: 'cgst_amount', name: 'CGST Amount', width: 100 },
  { key: 'sgst_amount', name: 'SGST/UTGST Amount', width: 150 },
  { key: 'cess_amount', name: 'Cess Amount', width: 100 },
  { key: 'ecommerce_gstin', name: 'E-commerce GSTIN', width: 150 }
];

export const b2csColumns: Column<any>[] = [
  { key: 'invoice_number', name: 'Invoice Number', width: 150 },
  { key: 'invoice_date', name: 'Invoice Date', width: 120 },
  { key: 'invoice_value', name: 'Invoice Value', width: 120 },
  { key: 'type', name: 'Type', width: 80 },
  { key: 'place_of_supply', name: 'Place of Supply', width: 120 },
  { key: 'applicable_percent_of_tax_rate', name: 'Applicable % of Tax Rate', width: 180 },
  { key: 'rate', name: 'Rate', width: 80 },
  { key: 'taxable_value', name: 'Taxable Value', width: 120 },
  { key: 'cess_amount', name: 'Cess Amount', width: 100 },
  { key: 'ecommerce_gstin', name: 'E-commerce GSTIN', width: 150 }
];

export const hsnColumns: Column<any>[] = [
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
