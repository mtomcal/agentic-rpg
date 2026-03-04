/**
 * Integration test: WebSocket ↔ Store.
 * Tests that WebSocket message handlers correctly update the Zustand store.
 */

import { render, screen, act } from "@testing-library/react";
import PlayPage from "@/app/play/[sessionId]/page";
import { useGameStore } from "@/lib/store";
import { GameWebSocket } from "@/lib/websocket";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  useParams: () => ({ sessionId: "sess-001" }),
}));

jest.mock("@/lib/websocket");
const MockGameWebSocket = GameWebSocket as jest.MockedClass<typeof GameWebSocket>;

let handlers: Record<string, Function>;

beforeEach(() => {
  MockGameWebSocket.mockClear();
  handlers = {};

  MockGameWebSocket.mockImplementation(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    sendAction: jest.fn(),
    onConnected: jest.fn((cb) => { handlers.connected = cb; }),
    onAgentResponse: jest.fn((cb) => { handlers.agent_response = cb; }),
    onStateUpdate: jest.fn((cb) => { handlers.state_update = cb; }),
    onError: jest.fn((cb) => { handlers.error = cb; }),
    onClose: jest.fn((cb) => { handlers.close = cb; }),
    getStatus: jest.fn().mockReturnValue("connected"),
  } as any));

  useGameStore.setState({
    gameState: null,
    messages: [],
    connectionStatus: "disconnected",
    currentSessionId: null,
    isAgentThinking: false,
  });
});

const mockGameState = {
  session: { session_id: "sess-001", player_id: "p1", created_at: "", updated_at: "", schema_version: 1, status: "active" as const },
  character: { id: "c1", name: "Aldric", profession: "Knight", background: "", stats: { health: 100, max_health: 100 }, status_effects: [], level: 1, experience: 0, location_id: "loc-001" },
  inventory: { items: [], equipment: {}, capacity: null },
  world: { locations: {}, current_location_id: "loc-001", discovered_locations: [], world_flags: {} },
  story: { outline: { premise: "", setting: "", beats: [] }, active_beat_index: 0, summary: "", adaptation_history: [] },
  conversation: { history: [], window_size: 20, summary: "" },
  recent_events: [],
};

describe("WebSocket ↔ Store Integration", () => {
  it("connected message → sets gameState and connectionStatus", () => {
    render(<PlayPage />);

    act(() => {
      handlers.connected({ game_state: mockGameState });
    });

    const state = useGameStore.getState();
    expect(state.gameState?.character.name).toBe("Aldric");
    expect(state.connectionStatus).toBe("connected");
  });

  it("agent_response (streaming) → appends chunk to message", () => {
    render(<PlayPage />);

    // Simulate connected
    act(() => {
      handlers.connected({ game_state: mockGameState });
    });

    // Start agent message (normally done by send handler)
    act(() => {
      useGameStore.getState().setAgentThinking(true);
      useGameStore.getState().startAgentMessage();
    });

    // Simulate streaming chunk
    act(() => {
      handlers.agent_response({ text: "You walk ", is_complete: false });
    });

    const messages = useGameStore.getState().messages;
    expect(messages[0].content).toBe("You walk ");
    expect(messages[0].isStreaming).toBe(true);
  });

  it("agent_response (complete) → finalizes message and clears thinking", () => {
    render(<PlayPage />);

    act(() => {
      handlers.connected({ game_state: mockGameState });
    });

    act(() => {
      useGameStore.getState().setAgentThinking(true);
      useGameStore.getState().startAgentMessage();
    });

    act(() => {
      handlers.agent_response({ text: "Done.", is_complete: true });
    });

    const state = useGameStore.getState();
    expect(state.messages[0].isStreaming).toBe(false);
    expect(state.isAgentThinking).toBe(false);
  });

  it("state_update → updates gameState", () => {
    render(<PlayPage />);

    act(() => {
      handlers.connected({ game_state: mockGameState });
    });

    act(() => {
      handlers.state_update({
        event_type: "character.stat_changed",
        changes: { "character.stats.health": { old: 100, new: 75 } },
      });
    });

    expect(useGameStore.getState().gameState?.character.stats.health).toBe(75);
  });

  it("close → sets connectionStatus to disconnected", () => {
    render(<PlayPage />);

    act(() => {
      handlers.connected({ game_state: mockGameState });
    });

    act(() => {
      handlers.close({});
    });

    expect(useGameStore.getState().connectionStatus).toBe("disconnected");
  });
});
