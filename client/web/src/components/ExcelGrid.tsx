import React, { useState, useMemo } from 'react';
import { DataGrid } from 'react-data-grid';
import type { Column, RenderEditCellProps } from 'react-data-grid';
import 'react-data-grid/lib/styles.css';

interface ExcelGridProps {
  data: any[];
  columns: Column<any>[];
  title: string;
  onDataChange?: (data: any[]) => void;
}

const ExcelGrid: React.FC<ExcelGridProps> = ({ data, columns, title, onDataChange }) => {
  const [gridData, setGridData] = useState(data);

  // Update gridData when data prop changes
  React.useEffect(() => {
    setGridData(data);
  }, [data]);

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
          className="w-full h-full px-2 border-0 outline-none bg-black/50 text-white"
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
          className="w-full h-full flex items-center justify-center text-red-400 hover:text-red-300 hover:bg-red-500/20 transition-colors"
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
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <div className="flex gap-2">
          <button
            onClick={addRow}
            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors"
          >
            Add Row
          </button>
        </div>
      </div>
      <div className="border border-white/20 rounded-lg overflow-hidden bg-black/30">
        <div className="h-96">
          <DataGrid
            columns={editableColumns}
            rows={gridData}
            onRowsChange={handleRowsChange}
            className="rdg-dark"
            style={{
              '--rdg-color': '#ffffff',
              '--rdg-background-color': 'rgba(0, 0, 0, 0.3)',
              '--rdg-header-background-color': 'rgba(0, 0, 0, 0.5)',
              '--rdg-row-hover-background-color': 'rgba(59, 130, 246, 0.1)',
              '--rdg-row-selected-background-color': 'rgba(59, 130, 246, 0.2)',
              '--rdg-border-color': 'rgba(255, 255, 255, 0.2)'
            } as React.CSSProperties}
          />
        </div>
      </div>
      <div className="text-sm text-blue-300 mt-2">
        <p>Total rows: {gridData.length}</p>
      </div>
    </div>
  );
};

export default ExcelGrid;
