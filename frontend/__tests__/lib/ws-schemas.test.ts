/**
 * Tests for lib/ws-schemas.ts — Zod WebSocket message schemas.
 */

import {
  PlayerActionMessageSchema,
  ConnectedMessageSchema,
  AgentResponseMessageSchema,
  StateUpdateMessageSchema,
  StateSnapshotMessageSchema,
  ErrorMessageSchema,
  InboundMessageSchema,
} from "@/lib/ws-schemas";

describe("PlayerActionMessageSchema", () => {
  it("parses a valid player action message", () => {
    const msg = {
      type: "player_action",
      data: { text: "I go north" },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = PlayerActionMessageSchema.parse(msg);
    expect(result.type).toBe("player_action");
    expect(result.data.text).toBe("I go north");
    expect(result.timestamp).toBe("2024-01-01T00:00:00Z");
  });

  it("rejects empty text", () => {
    const msg = {
      type: "player_action",
      data: { text: "" },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = PlayerActionMessageSchema.safeParse(msg);
    expect(result.success).toBe(false);
  });

  it("rejects missing text field", () => {
    const msg = {
      type: "player_action",
      data: {},
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = PlayerActionMessageSchema.safeParse(msg);
    expect(result.success).toBe(false);
  });
});

describe("ConnectedMessageSchema", () => {
  it("parses a valid connected message", () => {
    const msg = {
      type: "connected",
      data: { session_id: "sess-001", game_state: { character: { name: "Aldric" } } },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = ConnectedMessageSchema.parse(msg);
    expect(result.type).toBe("connected");
    expect(result.data.session_id).toBe("sess-001");
    expect(result.data.game_state.character.name).toBe("Aldric");
  });

  it("rejects missing session_id", () => {
    const msg = {
      type: "connected",
      data: { game_state: {} },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = ConnectedMessageSchema.safeParse(msg);
    expect(result.success).toBe(false);
  });
});

describe("AgentResponseMessageSchema", () => {
  it("parses a valid agent response message", () => {
    const msg = {
      type: "agent_response",
      data: { text: "You walk north.", is_complete: false },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = AgentResponseMessageSchema.parse(msg);
    expect(result.type).toBe("agent_response");
    expect(result.data.text).toBe("You walk north.");
    expect(result.data.is_complete).toBe(false);
  });

  it("rejects missing is_complete", () => {
    const msg = {
      type: "agent_response",
      data: { text: "You walk north." },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = AgentResponseMessageSchema.safeParse(msg);
    expect(result.success).toBe(false);
  });
});

describe("StateUpdateMessageSchema", () => {
  it("parses a valid state update message", () => {
    const msg = {
      type: "state_update",
      data: { event_type: "character.stat_changed", changes: { health: 80 } },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = StateUpdateMessageSchema.parse(msg);
    expect(result.type).toBe("state_update");
    expect(result.data.event_type).toBe("character.stat_changed");
    expect(result.data.changes.health).toBe(80);
  });

  it("rejects missing event_type", () => {
    const msg = {
      type: "state_update",
      data: { changes: {} },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = StateUpdateMessageSchema.safeParse(msg);
    expect(result.success).toBe(false);
  });
});

describe("StateSnapshotMessageSchema", () => {
  it("parses a valid state snapshot message", () => {
    const msg = {
      type: "state_snapshot",
      data: { game_state: { character: { name: "Aldric" } } },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = StateSnapshotMessageSchema.parse(msg);
    expect(result.type).toBe("state_snapshot");
    expect(result.data.game_state.character.name).toBe("Aldric");
  });

  it("rejects missing game_state", () => {
    const msg = {
      type: "state_snapshot",
      data: {},
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = StateSnapshotMessageSchema.safeParse(msg);
    expect(result.success).toBe(false);
  });
});

describe("ErrorMessageSchema", () => {
  it("parses a valid error message", () => {
    const msg = {
      type: "error",
      data: { code: "agent_error", message: "Failed" },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = ErrorMessageSchema.parse(msg);
    expect(result.type).toBe("error");
    expect(result.data.code).toBe("agent_error");
    expect(result.data.message).toBe("Failed");
  });

  it("rejects missing code", () => {
    const msg = {
      type: "error",
      data: { message: "Failed" },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = ErrorMessageSchema.safeParse(msg);
    expect(result.success).toBe(false);
  });
});

describe("InboundMessageSchema", () => {
  it("routes connected messages correctly", () => {
    const msg = {
      type: "connected",
      data: { session_id: "sess-001", game_state: {} },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = InboundMessageSchema.parse(msg);
    expect(result.type).toBe("connected");
  });

  it("routes agent_response messages correctly", () => {
    const msg = {
      type: "agent_response",
      data: { text: "Hello", is_complete: true },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = InboundMessageSchema.parse(msg);
    expect(result.type).toBe("agent_response");
  });

  it("routes state_update messages correctly", () => {
    const msg = {
      type: "state_update",
      data: { event_type: "test", changes: {} },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = InboundMessageSchema.parse(msg);
    expect(result.type).toBe("state_update");
  });

  it("routes state_snapshot messages correctly", () => {
    const msg = {
      type: "state_snapshot",
      data: { game_state: {} },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = InboundMessageSchema.parse(msg);
    expect(result.type).toBe("state_snapshot");
  });

  it("routes error messages correctly", () => {
    const msg = {
      type: "error",
      data: { code: "err", message: "fail" },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = InboundMessageSchema.parse(msg);
    expect(result.type).toBe("error");
  });

  it("rejects unknown message types", () => {
    const msg = {
      type: "unknown_type",
      data: { foo: "bar" },
      timestamp: "2024-01-01T00:00:00Z",
    };
    const result = InboundMessageSchema.safeParse(msg);
    expect(result.success).toBe(false);
  });
});
