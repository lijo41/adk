import React from 'react';
import { useNavigate } from 'react-router-dom';
import GSTR1Summary from '../components/filing/GSTR1Summary';
import InteractiveDataPreview from '../components/filing/InteractiveDataPreview';
import ActionButtons from '../components/filing/ActionButtons';
import { useFilingData } from '../hooks/useFilingData';
import { downloadCompleteExcel } from '../utils/excelExport';
import { b2bColumns, b2clColumns, b2csColumns, hsnColumns } from '../utils/columnDefinitions';

const FilingReport: React.FC = () => {
  const navigate = useNavigate();

  const {
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
  } = useFilingData('latest');

  const handleDownloadExcel = () => {
    downloadCompleteExcel(b2bData, b2clData, b2csData, filingData);
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  const handleStartNewFiling = () => {
    navigate('/filing/upload');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-transparent border-t-blue-600 mx-auto"></div>
          <p className="text-lg font-medium text-blue-700 mt-4">Loading filing data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">⚠️</div>
          <h2 className="text-4xl font-bold text-slate-900 mb-4">Error Loading Data</h2>
          <p className="text-slate-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!filingData || Object.keys(filingData).length === 0) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-slate-400 text-xl mb-4">📄</div>
          <h2 className="text-4xl font-bold text-slate-900 mb-4">No Data Available</h2>
          <p className="text-slate-600">No filing data found for the selected period.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">GST Filing Report</h1>
          <p className="text-lg font-medium text-blue-700">
            Complete overview of your GST filing data for the selected period
          </p>
        </div>

        {/* GSTR-1 Summary */}
        <GSTR1Summary filingData={filingData} />

        {/* Interactive Data Preview */}
        <InteractiveDataPreview
          b2bData={b2bData}
          b2clData={b2clData}
          b2csData={b2csData}
          hsnData={hsnData}
          setB2bData={setB2bData}
          setB2clData={setB2clData}
          setB2csData={setB2csData}
          setHsnData={setHsnData}
          b2bColumns={b2bColumns}
          b2clColumns={b2clColumns}
          b2csColumns={b2csColumns}
          hsnColumns={hsnColumns}
          onDownloadExcel={handleDownloadExcel}
        />

        {/* Action Buttons */}
        <ActionButtons
          onBackToDashboard={handleBackToDashboard}
          onStartNewFiling={handleStartNewFiling}
        />
      </div>
    </div>
  );
};

export default FilingReport;
