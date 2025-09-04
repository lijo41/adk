import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';

interface GSTR1SummaryProps {
  filingData: any;
}

const GSTR1Summary: React.FC<GSTR1SummaryProps> = ({ filingData }) => {
  if (!filingData?.results?.['GSTR-1']) {
    return null;
  }

  const gstr1Data = filingData.results['GSTR-1'];
  
  // Calculate summary statistics
  const totalInvoices = gstr1Data.b2b?.length || 0;
  const totalTaxableValue = gstr1Data.b2b?.reduce((sum: number, invoice: any) => 
    sum + (invoice.inv?.reduce((invSum: number, inv: any) => 
      invSum + (inv.itms?.reduce((itemSum: number, item: any) => 
        itemSum + (item.itm_det?.txval || 0), 0) || 0), 0) || 0), 0) || 0;
  const totalTaxAmount = gstr1Data.b2b?.reduce((sum: number, invoice: any) => 
    sum + (invoice.inv?.reduce((invSum: number, inv: any) => 
      invSum + (inv.itms?.reduce((itemSum: number, item: any) => 
        itemSum + ((item.itm_det?.iamt || 0) + (item.itm_det?.camt || 0) + (item.itm_det?.samt || 0)), 0) || 0), 0) || 0), 0) || 0;
  const totalInvoiceValue = totalTaxableValue + totalTaxAmount;
  
  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle>GSTR-1 Filing Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-blue-100 border-l-4 border-blue-500 p-6 rounded-lg hover:shadow-md transition-shadow">
            <div className="text-2xl font-bold text-slate-900 mb-1">{totalInvoices}</div>
            <div className="text-sm font-medium text-blue-700">Total Invoices</div>
          </div>
          <div className="bg-green-100 border-l-4 border-green-500 p-6 rounded-lg hover:shadow-md transition-shadow">
            <div className="text-2xl font-bold text-slate-900 mb-1">₹{totalTaxableValue.toLocaleString()}</div>
            <div className="text-sm font-medium text-blue-700">Total Taxable Value</div>
          </div>
          <div className="bg-cyan-100 border-l-4 border-cyan-500 p-6 rounded-lg hover:shadow-md transition-shadow">
            <div className="text-2xl font-bold text-slate-900 mb-1">₹{totalTaxAmount.toLocaleString()}</div>
            <div className="text-sm font-medium text-blue-700">Total Tax Amount</div>
          </div>
          <div className="bg-yellow-100 border-l-4 border-yellow-500 p-6 rounded-lg hover:shadow-md transition-shadow">
            <div className="text-2xl font-bold text-slate-900 mb-1">₹{totalInvoiceValue.toLocaleString()}</div>
            <div className="text-sm font-medium text-blue-700">Total Invoice Value</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default GSTR1Summary;
