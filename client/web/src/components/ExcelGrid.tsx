import React, { useState, useMemo } from 'react';
import { DataGrid } from 'react-data-grid';
import type { Column, RenderEditCellProps } from 'react-data-grid';
import 'react-data-grid/lib/styles.css';
import { Button } from './ui/Button';

interface ExcelGridProps {
  data: any[];
  columns: Column<any>[];
  title: string;
  onDataChange?: (data: any[]) => void;
}

const ExcelGrid: React.FC<ExcelGridProps> = ({ data, columns, title, onDataChange }) => {
  const [gridData, setGridData] = useState(data);

  const handleRowsChange = (rows: any[]) => {
    setGridData(rows);
    onDataChange?.(rows);
  };

  const deleteRow = (rowIndex: number) => {
    const newData = gridData.filter((_, index) => index !== rowIndex);
    setGridData(newData);
    onDataChange?.(newData);
  };

  const addRow = () => {
    const newRow: any = {};
    columns.forEach(col => {
      newRow[col.key] = '';
    });
    const newData = [...gridData, newRow];
    setGridData(newData);
    onDataChange?.(newData);
  };


  const editableColumns = useMemo(() => {
    const cols = columns.map(col => ({
      ...col,
      editable: true,
      renderEditCell: (props: RenderEditCellProps<any>) => (
        <input
          className="w-full h-full px-2 border-0 outline-none"
          value={props.row[props.column.key] || ''}
          onChange={(e) => {
            const newRow = { ...props.row, [props.column.key]: e.target.value };
            props.onRowChange(newRow);
          }}
          onBlur={() => props.onClose()}
          autoFocus
        />
      )
    }));
    
    // Add delete column
    cols.push({
      key: 'delete',
      name: '',
      width: 50,
      editable: false,
      renderCell: ({ rowIdx }: any) => (
        <button
          onClick={() => deleteRow(rowIdx)}
          className="w-full h-full flex items-center justify-center text-red-500 hover:text-red-700 hover:bg-red-50 transition-colors"
        >
          🗑️
        </button>
      ),
      renderEditCell: () => <div></div>
    });
    
    return cols;
  }, [columns, gridData]);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        <div className="flex gap-2">
          <Button
            onClick={addRow}
            size="sm"
            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium"
          >
            Add Row
          </Button>
        </div>
      </div>
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="h-96">
          <DataGrid
            columns={editableColumns}
            rows={gridData}
            onRowsChange={handleRowsChange}
            className="rdg-light"
          />
        </div>
      </div>
      <div className="text-sm text-blue-700 mt-2">
        <p>Total rows: {gridData.length}</p>
      </div>
    </div>
  );
};

export default ExcelGrid;
