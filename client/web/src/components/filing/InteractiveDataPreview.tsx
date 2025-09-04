import React, { useState } from 'react';
import ExcelGrid from '../ExcelGrid';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
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
    <Card className="mb-8">
      <CardHeader>
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">Data Preview & Export</h3>
          <div className="flex gap-2">
            <Button
              onClick={onDownloadExcel}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium"
            >
              📊 Download Complete Excel
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="border-b border-gray-200 mb-6">
          <div className="flex gap-8 -mb-px">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id 
                    ? 'border-blue-500 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
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
      </CardContent>
    </Card>
  );
};

export default InteractiveDataPreview;
