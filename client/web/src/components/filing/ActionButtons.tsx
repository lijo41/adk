import React from 'react';

interface ActionButtonsProps {
  onBackToDashboard: () => void;
  onStartNewFiling: () => void;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({
  onBackToDashboard,
  onStartNewFiling
}) => {
  return (
    <div className="flex justify-center gap-4 mt-8">
      <button 
        onClick={onBackToDashboard}
        className="px-6 py-3 border border-white/30 text-white bg-transparent hover:bg-white/10 rounded-lg font-medium transition-colors"
      >
        ← Back to Dashboard
      </button>
      <button 
        onClick={onStartNewFiling}
        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
      >
        Start New Filing
      </button>
    </div>
  );
};

export default ActionButtons;
