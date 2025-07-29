import React, { useState, useCallback } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import {
  Upload,
  File as FileIcon,
  CheckCircle,
  AlertCircle,
  X,
} from "lucide-react";

// This interface is removed as we will use the native File object directly.
// interface UploadedFile { ... }

interface FileUploadProps {
  // This now expects a native File object.
  onFileUploaded: (file: File) => void;
  uploadStatus: "idle" | "uploading" | "success" | "error";
  onClearFile: () => void;
  // This now expects a native File object.
  uploadedFile: File | null;
}

const ACCEPTED_FILE_TYPES = [".pdf", ".docx", ".pptx", ".csv", ".txt"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function FileUpload({
  onFileUploaded,
  uploadStatus,
  onClearFile,
  uploadedFile,
}: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    },
    [onFileUploaded]
  ); // Added dependency

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault();
      if (e.target.files && e.target.files[0]) {
        handleFileUpload(e.target.files[0]);
      }
    },
    [onFileUploaded]
  ); // Added dependency

  const handleFileUpload = useCallback(
    (file: File) => {
      // Validation logic...
      const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();
      if (!ACCEPTED_FILE_TYPES.includes(fileExtension)) {
        alert(
          `File type not supported. Please upload: ${ACCEPTED_FILE_TYPES.join(
            ", "
          )}`
        );
        return;
      }

      if (file.size > MAX_FILE_SIZE) {
        alert("File size too large. Please upload files smaller than 10MB.");
        return;
      }

      // THE FIX: Pass the original, valid File object directly.
      // Do NOT create a new plain object.
      onFileUploaded(file);
    },
    [onFileUploaded]
  );

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Upload className="h-5 w-5 text-muted-foreground" />
          <h3 className="font-medium">Upload Document</h3>
        </div>

        {!uploadedFile ? (
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50"
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept={ACCEPTED_FILE_TYPES.join(",")}
              onChange={handleChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={uploadStatus === "uploading"}
            />

            <div className="flex flex-col items-center gap-2">
              <div className="p-3 bg-muted rounded-full">
                <Upload className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium">Choose a file or drag & drop</p>
                <p className="text-sm text-muted-foreground mt-1">
                  PDF, DOCX, PPTX, CSV, TXT (max 10MB)
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
              <FileIcon className="h-4 w-4 text-muted-foreground" />
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{uploadedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(uploadedFile.size)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {uploadStatus === "uploading" && (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent" />
                )}
                {uploadStatus === "success" && (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                )}
                {uploadStatus === "error" && (
                  <AlertCircle className="h-4 w-4 text-destructive" />
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClearFile}
                  disabled={uploadStatus === "uploading"}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {uploadStatus === "error" && (
              <p className="text-sm text-destructive">
                Failed to upload file. Please try again.
              </p>
            )}
            {uploadStatus === "success" && (
              <p className="text-sm text-green-600">
                File uploaded successfully. You can now ask questions!
              </p>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
