/**
 * Tests for lib/store.ts — Zustand game store.
 */

import { useGameStore, type ChatMessage } from "@/lib/store";
import type { GameState } from "@/types/game";

const mockGameState: GameState = {
  session: {
    session_id: "sess-001",
    player_id: "p-001",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    schema_version: 1,
    status: "active",
  },
  character: {
    id: "c-001",
    name: "Aldric",
    profession: "Knight",
    background: "A soldier",
    stats: { health: 100, max_health: 100, energy: 50, max_energy: 50, money: 10 },
    status_effects: [],
    level: 1,
    experience: 0,
    location_id: "loc-001",
  },
  inventory: { items: [], equipment: {}, capacity: null },
  world: {
    locations: {},
    current_location_id: "loc-001",
    discovered_locations: [],
    world_flags: {},
  },
  story: {
    outline: { premise: "Quest", setting: "Fantasy", beats: [] },
    active_beat_index: 0,
    summary: "",
    adaptation_history: [],
  },
  conversation: { history: [], window_size: 20, summary: "" },
  recent_events: [],
};

describe("useGameStore", () => {
  beforeEach(() => {
    // Reset store between tests
    useGameStore.setState({
      gameState: null,
      messages: [],
      connectionStatus: "disconnected",
      currentSessionId: null,
      isAgentThinking: false,
    });
  });

  describe("setGameState", () => {
    it("sets the game state", () => {
      useGameStore.getState().setGameState(mockGameState);
      expect(useGameStore.getState().gameState?.character.name).toBe("Aldric");
      expect(useGameStore.getState().gameState?.session.session_id).toBe("sess-001");
    });
  });

  describe("addPlayerMessage", () => {
    it("adds a player message to the list", () => {
      useGameStore.getState().addPlayerMessage("I go north");
      const messages = useGameStore.getState().messages;
      expect(messages).toHaveLength(1);
      expect(messages[0].role).toBe("player");
      expect(messages[0].content).toBe("I go north");
      expect(messages[0].isStreaming).toBe(false);
      expect(messages[0].id).toBeDefined();
      expect(messages[0].timestamp).toBeDefined();
    });
  });

  describe("startAgentMessage", () => {
    it("creates a new streaming agent message", () => {
      useGameStore.getState().startAgentMessage();
      const messages = useGameStore.getState().messages;
      expect(messages).toHaveLength(1);
      expect(messages[0].role).toBe("agent");
      expect(messages[0].content).toBe("");
      expect(messages[0].isStreaming).toBe(true);
    });
  });

  describe("appendAgentChunk", () => {
    it("appends text to the current streaming message", () => {
      useGameStore.getState().startAgentMessage();
      useGameStore.getState().appendAgentChunk("Hello ");
      useGameStore.getState().appendAgentChunk("world!");

      const messages = useGameStore.getState().messages;
      expect(messages).toHaveLength(1);
      expect(messages[0].content).toBe("Hello world!");
      expect(messages[0].isStreaming).toBe(true);
    });

    it("does nothing if no streaming message exists", () => {
      useGameStore.getState().appendAgentChunk("orphan text");
      expect(useGameStore.getState().messages).toHaveLength(0);
    });
  });

  describe("finalizeAgentMessage", () => {
    it("sets isStreaming to false on the last message", () => {
      useGameStore.getState().startAgentMessage();
      useGameStore.getState().appendAgentChunk("Done.");
      useGameStore.getState().finalizeAgentMessage();

      const messages = useGameStore.getState().messages;
      expect(messages[0].isStreaming).toBe(false);
      expect(messages[0].content).toBe("Done.");
    });
  });

  describe("updateFromStateEvent", () => {
    it("updates character stats from state event", () => {
      useGameStore.getState().setGameState(mockGameState);
      useGameStore.getState().updateFromStateEvent({
        event_type: "character.stat_changed",
        changes: { "character.stats.health": { old: 100, new: 85 } },
      });

      const state = useGameStore.getState().gameState;
      expect(state?.character.stats.health).toBe(85);
    });

    it("handles missing game state gracefully", () => {
      expect(() =>
        useGameStore.getState().updateFromStateEvent({
          event_type: "character.stat_changed",
          changes: {},
        })
      ).not.toThrow();
    });
  });

  describe("setConnectionStatus", () => {
    it("sets connection status", () => {
      useGameStore.getState().setConnectionStatus("connected");
      expect(useGameStore.getState().connectionStatus).toBe("connected");
    });
  });

  describe("setCurrentSessionId", () => {
    it("sets the current session ID", () => {
      useGameStore.getState().setCurrentSessionId("sess-001");
      expect(useGameStore.getState().currentSessionId).toBe("sess-001");
    });

    it("allows null", () => {
      useGameStore.getState().setCurrentSessionId(null);
      expect(useGameStore.getState().currentSessionId).toBeNull();
    });
  });

  describe("setAgentThinking", () => {
    it("sets agent thinking state", () => {
      useGameStore.getState().setAgentThinking(true);
      expect(useGameStore.getState().isAgentThinking).toBe(true);
      useGameStore.getState().setAgentThinking(false);
      expect(useGameStore.getState().isAgentThinking).toBe(false);
    });
  });

  describe("clearMessages", () => {
    it("removes all messages", () => {
      useGameStore.getState().addPlayerMessage("test");
      useGameStore.getState().startAgentMessage();
      expect(useGameStore.getState().messages).toHaveLength(2);

      useGameStore.getState().clearMessages();
      expect(useGameStore.getState().messages).toHaveLength(0);
    });
  });
});
