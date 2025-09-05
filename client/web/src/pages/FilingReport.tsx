import React from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import GSTR1Summary from '../components/filing/GSTR1Summary';
import InteractiveDataPreview from '../components/filing/InteractiveDataPreview';
import ActionButtons from '../components/filing/ActionButtons';
import { useFilingData } from '../hooks/useFilingData';
import { downloadCompleteExcel } from '../utils/excelExport';
import { b2bColumns, b2clColumns, b2csColumns, hsnColumns } from '../utils/columnDefinitions';
import { FloatingChatBot } from '../components/FloatingChatBot';

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
    downloadCompleteExcel(b2bData, b2clData, b2csData, hsnData, filingData);
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  const handleStartNewFiling = () => {
    navigate('/filing/upload');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden">
        <Navbar />
        <div className="absolute inset-0 bg-black/50"></div>
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-transparent border-t-blue-400 mx-auto"></div>
            <p className="text-lg font-medium text-white mt-4">Loading filing data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden">
        <Navbar />
        <div className="absolute inset-0 bg-black/50"></div>
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="text-red-400 text-xl mb-4">⚠️</div>
            <h2 className="text-4xl font-bold text-white mb-4">Error Loading Data</h2>
            <p className="text-white/70">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!filingData || Object.keys(filingData).length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden">
        <Navbar />
        <div className="absolute inset-0 bg-black/50"></div>
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="text-white/60 text-xl mb-4">📄</div>
            <h2 className="text-4xl font-bold text-white mb-4">No Data Available</h2>
            <p className="text-white/70">No filing data found for the selected period.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      {/* Hero Section Background - same as filing page */}
      <div className="relative overflow-hidden bg-gradient-to-br from-blue-950 via-blue-800 to-slate-900 flex-1 flex items-center justify-center">
        {/* Subtle gradient overlay for depth - same as filing page */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-blue-900/30"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/40 via-transparent to-slate-800/20"></div>
        
        <div className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-12">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-white mb-4">GST Filing Report</h1>
            <p className="text-lg font-medium text-blue-400">Complete overview of your GST filing data</p>
          </div>

          {/* Progress Steps */}
          <div className="mb-12">
            <div className="max-w-2xl mx-auto">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                    ✓
                  </div>
                  <span className="ml-2 text-sm font-medium text-green-400">Upload Documents</span>
                </div>
                <div className="flex-1 mx-4 h-0.5 bg-green-600"></div>
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                    ✓
                  </div>
                  <span className="ml-2 text-sm font-medium text-green-400">GST Filing</span>
                </div>
                <div className="flex-1 mx-4 h-0.5 bg-green-600"></div>
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                    ✓
                  </div>
                  <span className="ml-2 text-sm font-medium text-green-400">Report</span>
                </div>
              </div>
            </div>
          </div>

          <div className="w-full">
            <div className="bg-black/40 backdrop-blur-sm rounded-xl p-8 space-y-8">
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
        </div>
      </div>
      <FloatingChatBot />
    </div>
  );
};

export default FilingReport;
