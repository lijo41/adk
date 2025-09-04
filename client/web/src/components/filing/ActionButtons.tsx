import React from 'react';
import { Button } from '../ui/Button';

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
      <Button variant="outline" onClick={onBackToDashboard}>
        ← Back to Dashboard
      </Button>
      <Button onClick={onStartNewFiling}>
        Start New Filing
      </Button>
    </div>
  );
};

export default ActionButtons;
