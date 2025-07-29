import React from "react";

interface Props {
  file: File;
  onClear: () => void;
}

export const SelectedFileDisplay: React.FC<Props> = ({ file, onClear }) => {
  return (
    <div className="bg-muted p-3 rounded-lg flex justify-between items-center text-sm">
      <div className="flex items-center gap-3">
        <span className="font-medium text-foreground">Selected File:</span>
        <span className="text-muted-foreground">{file.name}</span>
      </div>
      <button
        onClick={onClear}
        className="text-muted-foreground hover:text-destructive"
        title="Clear file"
      >
        &#x2715; {/* A simple 'X' icon */}
      </button>
    </div>
  );
};
