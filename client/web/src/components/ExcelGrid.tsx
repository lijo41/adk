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
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">{title}</h3>
        <div className="space-x-2">
          <Button variant="outline" size="sm" onClick={addRow}>
            Add Row
          </Button>
        </div>
      </div>
      
      <div className="border rounded-lg overflow-hidden">
        <DataGrid
          columns={editableColumns}
          rows={gridData}
          onRowsChange={handleRowsChange}
          className="rdg-light"
          style={{ height: '400px' }}
          rowKeyGetter={(row: any) => row.id || Math.random()}
        />
      </div>
      
      {gridData.length > 0 && (
        <div className="text-sm text-gray-600">
          Total rows: {gridData.length}
        </div>
      )}
    </div>
  );
};

export default ExcelGrid;
