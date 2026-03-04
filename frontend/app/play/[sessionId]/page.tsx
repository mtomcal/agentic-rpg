"use client";

import { useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { useGameStore } from "@/lib/store";
import { GameWebSocket } from "@/lib/websocket";
import ChatPanel from "@/components/ChatPanel";
import Sidebar from "@/components/Sidebar";

export default function PlayPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;
  const wsRef = useRef<GameWebSocket | null>(null);

  const {
    gameState,
    messages,
    connectionStatus,
    isAgentThinking,
    setGameState,
    addPlayerMessage,
    startAgentMessage,
    appendAgentChunk,
    finalizeAgentMessage,
    setConnectionStatus,
    setCurrentSessionId,
    setAgentThinking,
  } = useGameStore();

  useEffect(() => {
    const ws = new GameWebSocket();
    wsRef.current = ws;

    ws.onConnected((data: any) => {
      setGameState(data.game_state);
      setConnectionStatus("connected");
    });

    ws.onAgentResponse((data: any) => {
      if (data.is_complete) {
        finalizeAgentMessage();
        setAgentThinking(false);
      } else {
        appendAgentChunk(data.text);
      }
    });

    ws.onStateUpdate((data: any) => {
      useGameStore.getState().updateFromStateEvent(data);
    });

    ws.onError((data: any) => {
      useGameStore.getState().addPlayerMessage("");
      // Add error as system message
      useGameStore.setState((state) => ({
        messages: [
          ...state.messages.filter((m) => m.content !== ""),
          {
            id: `err-${Date.now()}`,
            role: "system" as const,
            content: `Error: ${data.message}`,
            timestamp: new Date().toISOString(),
            isStreaming: false,
          },
        ],
      }));
      setAgentThinking(false);
    });

    ws.onClose(() => {
      setConnectionStatus("disconnected");
    });

    setCurrentSessionId(sessionId);
    setConnectionStatus("connecting");
    ws.connect(sessionId);

    return () => {
      ws.disconnect();
    };
  }, [sessionId]);

  function handleSendMessage(text: string) {
    addPlayerMessage(text);
    setAgentThinking(true);
    startAgentMessage();
    wsRef.current?.sendAction(text);
  }

  const statusColor =
    connectionStatus === "connected"
      ? "bg-green-500"
      : connectionStatus === "connecting"
      ? "bg-yellow-500"
      : "bg-red-500";

  return (
    <div className="flex h-screen">
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
          <button
            onClick={() => router.push("/")}
            className="text-gray-400 hover:text-gray-200 text-sm"
          >
            ← Home
          </button>
          <div className="flex items-center gap-2">
            <div
              data-testid="connection-status"
              className={`w-2 h-2 rounded-full ${statusColor}`}
            />
            <span className="text-xs text-gray-400">{connectionStatus}</span>
          </div>
        </div>

        <ChatPanel
          messages={messages}
          isAgentThinking={isAgentThinking}
          isDisabled={connectionStatus !== "connected"}
          onSendMessage={handleSendMessage}
        />
      </div>

      <Sidebar gameState={gameState} />
    </div>
  );
}
