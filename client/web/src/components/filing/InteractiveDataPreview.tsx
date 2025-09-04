import React, { useState } from 'react';
import ExcelGrid from '../ExcelGrid';
import type { Column } from 'react-data-grid';

interface InteractiveDataPreviewProps {
  b2bData: any[];
  b2clData: any[];
  b2csData: any[];
  hsnData: any[];
  setB2bData: (data: any[]) => void;
  setB2clData: (data: any[]) => void;
  setB2csData: (data: any[]) => void;
  setHsnData: (data: any[]) => void;
  b2bColumns: Column<any>[];
  b2clColumns: Column<any>[];
  b2csColumns: Column<any>[];
  hsnColumns: Column<any>[];
  onDownloadExcel: () => void;
}

const InteractiveDataPreview: React.FC<InteractiveDataPreviewProps> = ({
  b2bData,
  b2clData,
  b2csData,
  hsnData,
  setB2bData,
  setB2clData,
  setB2csData,
  setHsnData,
  b2bColumns,
  b2clColumns,
  b2csColumns,
  hsnColumns,
  onDownloadExcel
}) => {
  const [activeTab, setActiveTab] = useState('B2B');

  const tabs = [
    { id: 'B2B', label: 'B2B Invoices', count: b2bData.length },
    { id: 'B2CL', label: 'B2CL Invoices', count: b2clData.length },
    { id: 'B2CS', label: 'B2CS Invoices', count: b2csData.length },
    { id: 'HSN', label: 'HSN Summary', count: hsnData.length }
  ];

  return (
    <div className="mb-8 bg-black/20 backdrop-blur-sm border border-white/20 rounded-xl p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-white">Data Preview & Export</h3>
        <div className="flex gap-2">
          <button
            onClick={onDownloadExcel}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
          >
            📊 Download Complete Excel
          </button>
        </div>
      </div>
      
      <div className="border-b border-white/20 mb-6">
        <div className="flex gap-8 -mb-px">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id 
                  ? 'border-blue-400 text-blue-300' 
                  : 'border-transparent text-white/60 hover:text-white hover:border-white/30'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
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
    </div>
  );
};

export default InteractiveDataPreview;
