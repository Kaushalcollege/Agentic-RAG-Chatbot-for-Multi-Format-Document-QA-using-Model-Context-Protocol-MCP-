import { useEffect, useRef } from "react";
import { Card } from "./ui/card";
import { User, Bot, FileText } from "lucide-react";

export interface Source {
  document: string;
  page?: number;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  type: "user" | "agent";
  content: string;
  timestamp: Date;
  sources?: Source[];
}

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isTyping: boolean;
}

export function ChatInterface({ messages, isTyping }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // This component now renders its content within the parent's scrolling container.
  return (
    <div className="space-y-6">
      {messages.length === 0 && !isTyping && (
        <div className="text-center text-muted-foreground pt-12">
          <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>The document is ready. Ask a question to begin!</p>
        </div>
      )}

      {messages.map((message) => (
        <div key={message.id} className="space-y-3">
          <div
            className={`flex gap-3 ${
              message.type === "user" ? "justify-end" : ""
            }`}
          >
            {message.type === "agent" && (
              <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="h-4 w-4" />
              </div>
            )}

            <div className={`max-w-[80%]`}>
              <div
                className={`p-3 rounded-lg ${
                  message.type === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="whitespace-pre-wrap break-words">
                  {message.content}
                </p>
              </div>

              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">
                    Sources:
                  </p>
                  {message.sources.map((source, index) => (
                    <Card key={index} className="p-3 bg-background/50">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                        <span className="text-xs font-semibold truncate">
                          {source.document}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground italic leading-relaxed">
                        "{source.snippet}"
                      </p>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {message.type === "user" && (
              <div className="w-8 h-8 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center flex-shrink-0 mt-1">
                <User className="h-4 w-4" />
              </div>
            )}
          </div>
        </div>
      ))}

      {isTyping && (
        <div className="flex gap-3">
          <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 mt-1">
            <Bot className="h-4 w-4" />
          </div>
          <div className="bg-muted p-3 rounded-lg">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.3s]"></div>
              <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.15s]"></div>
              <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}
