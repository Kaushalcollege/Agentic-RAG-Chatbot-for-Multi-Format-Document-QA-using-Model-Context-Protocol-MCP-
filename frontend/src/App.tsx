import React, { useState, useCallback } from "react";
import { FileUpload } from "./components/FileUpload";
import { ChatInterface } from "./components/ChatInterface";
import type { ChatMessage, Source } from "./components/ChatInterface";
import { MessageInput } from "./components/MessageInput";
import { StatusPanel } from "./components/StatusPanel";

type AppStatus = "idle" | "uploading" | "success" | "error" | "querying";

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<AppStatus>("idle");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [chunksProcessed, setChunksProcessed] = useState<number | undefined>(
    undefined
  );

  const handleFileUpload = useCallback((file: File) => {
    setSelectedFile(file);
    setMessages([]);
    setStatus("uploading");
    setSessionId(undefined);
    setChunksProcessed(undefined);

    const uploadAndProcess = async () => {
      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(
          "http://localhost:8000/agent/coordinator/start_session",
          {
            method: "POST",
            body: formData,
          }
        );
        if (!res.ok) throw new Error("File processing failed.");
        const data = await res.json();
        const payload = data.payload;
        setSessionId(payload.session_id);
        setChunksProcessed(payload.chunks_processed);
        setStatus("success");
      } catch (error) {
        console.error("File upload failed:", error);
        setStatus("error");
      }
    };
    uploadAndProcess();
  }, []);

  const handleClearFile = useCallback(() => {
    setSelectedFile(null);
    setMessages([]);
    setStatus("idle");
    setSessionId(undefined);
    setChunksProcessed(undefined);
  }, []);

  const handleSendMessage = useCallback(
    async (messageContent: string) => {
      if (status !== "success" || !sessionId || !selectedFile) return;

      const userMessage: ChatMessage = {
        id: `user_${Date.now()}`,
        type: "user",
        content: messageContent,
        timestamp: new Date(),
      };

      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      setStatus("querying");

      try {
        const chatHistoryForApi = updatedMessages.slice(0, -1).map((msg) => ({
          role: msg.type === "user" ? "user" : "assistant",
          content: msg.content,
        }));

        const res = await fetch(
          "http://localhost:8000/agent/coordinator/query",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: sessionId,
              user_query: messageContent,
              chat_history: chatHistoryForApi,
            }),
          }
        );
        if (!res.ok) throw new Error("Query failed.");
        const data = await res.json();
        const sources: Source[] = (data.source_context || []).map(
          (snippet: string, index: number) => ({
            document: selectedFile.name,
            page: index + 1,
            snippet: snippet,
          })
        );
        const agentMessage: ChatMessage = {
          id: `agent_${Date.now()}`,
          type: "agent",
          content: data.answer || "No answer received.",
          timestamp: new Date(),
          sources: sources,
        };
        setMessages((prev) => [...prev, agentMessage]);
        setStatus("success");
      } catch (error) {
        console.error("Query failed:", error);
        setStatus("error");
        const errorMessage: ChatMessage = {
          id: `error_${Date.now()}`,
          type: "agent",
          content: "Sorry, the query failed. Please try again.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    },
    [sessionId, selectedFile, status, messages]
  );

  const fileUploadStatus =
    status === "querying" || status === "uploading" ? "uploading" : status;

  return (
    <div className="h-screen bg-background flex gap-6 p-6">
      {/* This main column is a flex container that will not overflow the page height */}
      <div className="flex-1 flex flex-col gap-4 overflow-hidden">
        {/* Section 1: File Upload (takes its natural height) */}
        <FileUpload
          onFileUploaded={handleFileUpload}
          uploadStatus={fileUploadStatus}
          onClearFile={handleClearFile}
          uploadedFile={selectedFile}
        />

        {/* Section 2: This wrapper DIV is the key. It takes all remaining space and scrolls internally. */}
        <div className="flex-1 overflow-y-auto pr-2">
          <ChatInterface messages={messages} isTyping={status === "querying"} />
        </div>

        {/* Section 3: Message Input (takes its natural height at the bottom) */}
        <MessageInput
          onSendMessage={handleSendMessage}
          disabled={status !== "success"}
          placeholder={
            status === "success"
              ? "Ask a question..."
              : "Upload a document to begin."
          }
        />
      </div>

      <StatusPanel
        uploadStatus={fileUploadStatus}
        fileName={selectedFile?.name}
        sessionId={sessionId}
        chunksProcessed={chunksProcessed}
      />
    </div>
  );
}
