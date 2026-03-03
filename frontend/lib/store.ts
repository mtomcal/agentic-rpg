import { create } from "zustand";
import type { GameState } from "@/types/game";

let messageCounter = 0;
function generateId(): string {
  return `msg-${Date.now()}-${++messageCounter}`;
}

export interface ChatMessage {
  id: string;
  role: "player" | "agent" | "system";
  content: string;
  timestamp: string;
  isStreaming: boolean;
}

interface GameStore {
  gameState: GameState | null;
  messages: ChatMessage[];
  connectionStatus: "connecting" | "connected" | "disconnected";
  currentSessionId: string | null;
  isAgentThinking: boolean;

  setGameState: (state: GameState) => void;
  addPlayerMessage: (text: string) => void;
  startAgentMessage: () => void;
  appendAgentChunk: (text: string) => void;
  finalizeAgentMessage: () => void;
  updateFromStateEvent: (event: { event_type: string; changes: Record<string, any> }) => void;
  setConnectionStatus: (status: "connecting" | "connected" | "disconnected") => void;
  setCurrentSessionId: (id: string | null) => void;
  setAgentThinking: (thinking: boolean) => void;
  clearMessages: () => void;
}

export const useGameStore = create<GameStore>((set) => ({
  gameState: null,
  messages: [],
  connectionStatus: "disconnected",
  currentSessionId: null,
  isAgentThinking: false,

  setGameState: (gameState) => set({ gameState }),

  addPlayerMessage: (text) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: generateId(),
          role: "player",
          content: text,
          timestamp: new Date().toISOString(),
          isStreaming: false,
        },
      ],
    })),

  startAgentMessage: () =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: generateId(),
          role: "agent",
          content: "",
          timestamp: new Date().toISOString(),
          isStreaming: true,
        },
      ],
    })),

  appendAgentChunk: (text) =>
    set((state) => {
      const messages = [...state.messages];
      const lastIndex = messages.length - 1;
      if (lastIndex < 0 || !messages[lastIndex].isStreaming) return state;
      messages[lastIndex] = {
        ...messages[lastIndex],
        content: messages[lastIndex].content + text,
      };
      return { messages };
    }),

  finalizeAgentMessage: () =>
    set((state) => {
      const messages = [...state.messages];
      const lastIndex = messages.length - 1;
      if (lastIndex < 0) return state;
      messages[lastIndex] = { ...messages[lastIndex], isStreaming: false };
      return { messages };
    }),

  updateFromStateEvent: (event) =>
    set((state) => {
      if (!state.gameState) return state;
      const gameState = { ...state.gameState };

      // Apply changes from the event
      for (const [path, change] of Object.entries(event.changes)) {
        const parts = path.split(".");
        let target: any = gameState;
        for (let i = 0; i < parts.length - 1; i++) {
          if (target[parts[i]] === undefined) break;
          target[parts[i]] = { ...target[parts[i]] };
          target = target[parts[i]];
        }
        const lastKey = parts[parts.length - 1];
        if (target && change && typeof change === "object" && "new" in change) {
          target[lastKey] = change.new;
        }
      }

      return { gameState };
    }),

  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),

  setCurrentSessionId: (currentSessionId) => set({ currentSessionId }),

  setAgentThinking: (isAgentThinking) => set({ isAgentThinking }),

  clearMessages: () => set({ messages: [] }),
}));
