"use client";

import { useState, useRef, useEffect } from "react";
import type { ChatMessage } from "@/lib/store";

interface ChatPanelProps {
  messages: ChatMessage[];
  isAgentThinking: boolean;
  isDisabled: boolean;
  onSendMessage: (text: string) => void;
}

export default function ChatPanel({
  messages,
  isAgentThinking,
  isDisabled,
  onSendMessage,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    onSendMessage(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && !isAgentThinking && (
          <p className="text-center text-gray-500 italic mt-8">
            Start your adventure by typing an action...
          </p>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${
              msg.role === "player"
                ? "justify-end"
                : msg.role === "system"
                ? "justify-center"
                : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === "player"
                  ? "bg-indigo-600 text-white"
                  : msg.role === "system"
                  ? "text-gray-400 italic text-sm"
                  : "bg-gray-800 text-gray-100"
              }`}
            >
              <span>{msg.content}</span>
              {msg.isStreaming && (
                <span
                  data-testid="streaming-indicator"
                  className="inline-block w-2 h-4 bg-gray-400 ml-1 animate-pulse"
                />
              )}
            </div>
          </div>
        ))}

        {isAgentThinking && (
          <div className="flex justify-start">
            <div className="bg-gray-800 text-gray-400 rounded-lg px-4 py-2 italic">
              Agent is thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-700 p-4">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isDisabled}
            placeholder="Type your action..."
            className="flex-1 bg-gray-800 text-gray-100 rounded-lg px-4 py-2 border border-gray-600 focus:border-indigo-500 focus:outline-none disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isDisabled}
            aria-label="Send"
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
