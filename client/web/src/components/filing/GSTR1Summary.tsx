import React from 'react';

interface GSTR1SummaryProps {
  filingData: any;
}

const GSTR1Summary: React.FC<GSTR1SummaryProps> = ({ filingData }) => {
  console.log('GSTR1Summary received filingData:', filingData);
  
  if (!filingData) {
    return (
      <div className="mb-8 bg-black/20 backdrop-blur-sm border border-white/20 rounded-xl p-6">
        <h3 className="text-xl font-bold text-white mb-6">GSTR-1 Filing Summary</h3>
        <p className="text-white/70">No filing data available</p>
      </div>
    );
  }

  // Extract summary data from the API response structure
  const gstr1Result = filingData.results?.['GSTR-1']?.gstr1_extraction || {};
  
  const totalInvoices = gstr1Result.total_invoices || 0;
  const totalTaxableValue = gstr1Result.total_taxable_value || 0;
  const totalTaxAmount = gstr1Result.total_tax_amount || 0;
  const totalInvoiceValue = totalTaxableValue + totalTaxAmount;
  
  return (
    <div className="mb-8 bg-black/20 backdrop-blur-sm border border-white/20 rounded-xl p-6">
      <h3 className="text-xl font-bold text-white mb-6">GSTR-1 Filing Summary</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-blue-500/20 border-l-4 border-blue-400 p-6 rounded-lg hover:bg-blue-500/30 transition-all">
          <div className="text-2xl font-bold text-white mb-1">{totalInvoices}</div>
          <div className="text-sm font-medium text-blue-300">Total Invoices</div>
        </div>
        <div className="bg-green-500/20 border-l-4 border-green-400 p-6 rounded-lg hover:bg-green-500/30 transition-all">
          <div className="text-2xl font-bold text-white mb-1">₹{totalTaxableValue.toLocaleString()}</div>
          <div className="text-sm font-medium text-green-300">Total Taxable Value</div>
        </div>
        <div className="bg-cyan-500/20 border-l-4 border-cyan-400 p-6 rounded-lg hover:bg-cyan-500/30 transition-all">
          <div className="text-2xl font-bold text-white mb-1">₹{totalTaxAmount.toLocaleString()}</div>
          <div className="text-sm font-medium text-cyan-300">Total Tax Amount</div>
        </div>
        <div className="bg-yellow-500/20 border-l-4 border-yellow-400 p-6 rounded-lg hover:bg-yellow-500/30 transition-all">
          <div className="text-2xl font-bold text-white mb-1">₹{totalInvoiceValue.toLocaleString()}</div>
          <div className="text-sm font-medium text-yellow-300">Total Invoice Value</div>
        </div>
      </div>
    </div>
  );
};

export default GSTR1Summary;
