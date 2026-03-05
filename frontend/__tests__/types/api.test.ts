/**
 * Tests for types/api.ts
 *
 * Verifies API and WebSocket message types match the backend spec
 * from docs/specs/api-layer.md.
 */

import type {
  SessionCreateRequest,
  SessionCreateResponse,
  SessionSummary,
  SessionListResponse,
  WSMessage,
  PlayerActionMessage,
  AgentResponseMessage,
  StateUpdateMessage,
  ConnectedMessage,
  ErrorMessage,
} from "@/types/api";

describe("API Types", () => {
  describe("SessionCreateRequest", () => {
    it("has genre and character fields", () => {
      const request: SessionCreateRequest = {
        genre: "medieval fantasy",
        character: {
          name: "Aldric",
          profession: "Knight",
          background: "A former soldier",
        },
      };
      expect(request.genre).toBe("medieval fantasy");
      expect(request.character.name).toBe("Aldric");
      expect(request.character.profession).toBe("Knight");
      expect(request.character.background).toBe("A former soldier");
    });
  });

  describe("SessionCreateResponse", () => {
    it("has session_id and game_state", () => {
      const response: SessionCreateResponse = {
        session_id: "sess-001",
        game_state: {
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
            stats: { health: 100 },
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
            adaptations: [],
          },
          conversation: { history: [], window_size: 20, summary: "" },
          recent_events: [],
        },
      };
      expect(response.session_id).toBe("sess-001");
      expect(response.game_state.character.name).toBe("Aldric");
    });
  });

  describe("SessionSummary", () => {
    it("has all required fields", () => {
      const summary: SessionSummary = {
        session_id: "sess-001",
        status: "active",
        genre: "medieval fantasy",
        character_name: "Aldric",
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T01:00:00Z",
      };
      expect(summary.session_id).toBe("sess-001");
      expect(summary.status).toBe("active");
      expect(summary.genre).toBe("medieval fantasy");
      expect(summary.character_name).toBe("Aldric");
      expect(summary.created_at).toBe("2024-01-01T00:00:00Z");
      expect(summary.updated_at).toBe("2024-01-01T01:00:00Z");
    });
  });

  describe("SessionListResponse", () => {
    it("contains an array of session summaries", () => {
      const response: SessionListResponse = {
        sessions: [
          {
            session_id: "sess-001",
            status: "active",
            genre: "fantasy",
            character_name: "Aldric",
            created_at: "2024-01-01T00:00:00Z",
            updated_at: "2024-01-01T01:00:00Z",
          },
        ],
      };
      expect(response.sessions).toHaveLength(1);
      expect(response.sessions[0].character_name).toBe("Aldric");
    });
  });

  describe("WSMessage", () => {
    it("has type, data, and timestamp", () => {
      const message: WSMessage = {
        type: "connected",
        data: { session_id: "sess-001" },
        timestamp: "2024-01-01T00:00:00Z",
      };
      expect(message.type).toBe("connected");
      expect(message.data.session_id).toBe("sess-001");
      expect(message.timestamp).toBe("2024-01-01T00:00:00Z");
    });
  });

  describe("PlayerActionMessage", () => {
    it("has type player_action with text data", () => {
      const message: PlayerActionMessage = {
        type: "player_action",
        data: { text: "I walk north" },
        timestamp: "2024-01-01T00:00:00Z",
      };
      expect(message.type).toBe("player_action");
      expect(message.data.text).toBe("I walk north");
    });
  });

  describe("AgentResponseMessage", () => {
    it("has text and is_complete flag", () => {
      const message: AgentResponseMessage = {
        type: "agent_response",
        data: { text: "You walk north...", is_complete: false },
        timestamp: "2024-01-01T00:00:00Z",
      };
      expect(message.type).toBe("agent_response");
      expect(message.data.text).toBe("You walk north...");
      expect(message.data.is_complete).toBe(false);
    });

    it("supports complete responses", () => {
      const message: AgentResponseMessage = {
        type: "agent_response",
        data: { text: "Done.", is_complete: true },
        timestamp: "2024-01-01T00:00:00Z",
      };
      expect(message.data.is_complete).toBe(true);
    });
  });

  describe("StateUpdateMessage", () => {
    it("has event_type and changes", () => {
      const message: StateUpdateMessage = {
        type: "state_update",
        data: {
          event_type: "character.stat_changed",
          changes: { "character.stats.health": { old: 100, new: 85 } },
        },
        timestamp: "2024-01-01T00:00:00Z",
      };
      expect(message.type).toBe("state_update");
      expect(message.data.event_type).toBe("character.stat_changed");
      expect(message.data.changes["character.stats.health"].old).toBe(100);
      expect(message.data.changes["character.stats.health"].new).toBe(85);
    });
  });

  describe("ConnectedMessage", () => {
    it("has session_id and game_state", () => {
      const message: ConnectedMessage = {
        type: "connected",
        data: {
          session_id: "sess-001",
          game_state: {
            character: { name: "Aldric" },
            world: { current_location_id: "tavern" },
          },
        },
        timestamp: "2024-01-01T00:00:00Z",
      };
      expect(message.type).toBe("connected");
      expect(message.data.session_id).toBe("sess-001");
      expect(message.data.game_state.character.name).toBe("Aldric");
      expect(message.data.game_state.world.current_location_id).toBe("tavern");
    });
  });

  describe("ErrorMessage", () => {
    it("has code and message", () => {
      const message: ErrorMessage = {
        type: "error",
        data: { code: "agent_error", message: "Failed to process action" },
        timestamp: "2024-01-01T00:00:00Z",
      };
      expect(message.type).toBe("error");
      expect(message.data.code).toBe("agent_error");
      expect(message.data.message).toBe("Failed to process action");
    });
  });
});
