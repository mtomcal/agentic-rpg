import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import PlayPage from "@/app/play/[sessionId]/page";
import { useGameStore } from "@/lib/store";
import { GameWebSocket } from "@/lib/websocket";

// Mock next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useParams: () => ({ sessionId: "sess-001" }),
}));

// Mock WebSocket
jest.mock("@/lib/websocket");
const MockGameWebSocket = GameWebSocket as jest.MockedClass<typeof GameWebSocket>;

let wsInstance: any;

beforeEach(() => {
  mockPush.mockReset();
  MockGameWebSocket.mockClear();

  wsInstance = {
    connect: jest.fn(),
    disconnect: jest.fn(),
    sendAction: jest.fn(),
    onConnected: jest.fn(),
    onAgentResponse: jest.fn(),
    onStateUpdate: jest.fn(),
    onStateSnapshot: jest.fn(),
    onError: jest.fn(),
    onClose: jest.fn(),
    getStatus: jest.fn().mockReturnValue("connected"),
  };
  MockGameWebSocket.mockImplementation(() => wsInstance);

  // Reset store
  useGameStore.setState({
    gameState: null,
    messages: [],
    connectionStatus: "disconnected",
    currentSessionId: null,
    isAgentThinking: false,
  });
});

describe("PlayPage", () => {
  it("connects WebSocket on mount", () => {
    render(<PlayPage />);
    expect(wsInstance.connect).toHaveBeenCalledWith("sess-001");
  });

  it("disconnects WebSocket on unmount", () => {
    const { unmount } = render(<PlayPage />);
    unmount();
    expect(wsInstance.disconnect).toHaveBeenCalled();
  });

  it("registers all message handlers", () => {
    render(<PlayPage />);
    expect(wsInstance.onConnected).toHaveBeenCalledWith(expect.any(Function));
    expect(wsInstance.onAgentResponse).toHaveBeenCalledWith(expect.any(Function));
    expect(wsInstance.onStateUpdate).toHaveBeenCalledWith(expect.any(Function));
    expect(wsInstance.onStateSnapshot).toHaveBeenCalledWith(expect.any(Function));
    expect(wsInstance.onError).toHaveBeenCalledWith(expect.any(Function));
    expect(wsInstance.onClose).toHaveBeenCalledWith(expect.any(Function));
  });

  it("onStateSnapshot handler updates gameState in store", () => {
    render(<PlayPage />);

    const snapshotHandler = wsInstance.onStateSnapshot.mock.calls[0][0];
    act(() => {
      snapshotHandler({
        game_state: {
          session: { session_id: "sess-001", player_id: "p1", created_at: "", updated_at: "", schema_version: 1, status: "active" },
          character: { id: "c1", name: "UpdatedHero", profession: "Mage", background: "", stats: { health: 50, max_health: 100 }, status_effects: [], level: 2, experience: 500, location_id: "market" },
          inventory: { items: [], equipment: {}, capacity: null },
          world: { locations: {}, current_location_id: "market", discovered_locations: [], world_flags: {} },
          story: { outline: { premise: "", setting: "", beats: [] }, active_beat_index: 0, summary: "", adaptations: [] },
          conversation: { history: [], window_size: 20, summary: "" },
          recent_events: [],
        },
      });
    });

    const gameState = useGameStore.getState().gameState;
    expect(gameState?.character.name).toBe("UpdatedHero");
    expect(gameState?.character.stats.health).toBe(50);
    expect(gameState?.world.current_location_id).toBe("market");
  });

  it("renders ChatPanel component", () => {
    render(<PlayPage />);
    expect(
      screen.getByPlaceholderText("Type your action...")
    ).toBeInTheDocument();
  });

  it("renders Sidebar component", () => {
    render(<PlayPage />);
    expect(screen.getByText("Character")).toBeInTheDocument();
    expect(screen.getByText("Inventory")).toBeInTheDocument();
  });

  it("has a back button to home", () => {
    render(<PlayPage />);
    fireEvent.click(screen.getByText("← Home"));
    expect(mockPush).toHaveBeenCalledWith("/");
  });

  it("shows connection status indicator", () => {
    render(<PlayPage />);
    expect(screen.getByTestId("connection-status")).toBeInTheDocument();
  });

  it("sends action through WebSocket when message sent", () => {
    render(<PlayPage />);

    // Simulate the "connected" callback firing
    const connectedHandler = wsInstance.onConnected.mock.calls[0][0];
    act(() => {
      connectedHandler({
        game_state: {
          session: { session_id: "sess-001", player_id: "p1", created_at: "", updated_at: "", schema_version: 1, status: "active" },
          character: { id: "c1", name: "Test", profession: "Knight", background: "", stats: {}, status_effects: [], level: 1, experience: 0, location_id: "loc-001" },
          inventory: { items: [], equipment: {}, capacity: null },
          world: { locations: {}, current_location_id: "loc-001", discovered_locations: [], world_flags: {} },
          story: { outline: { premise: "", setting: "", beats: [] }, active_beat_index: 0, summary: "", adaptations: [] },
          conversation: { history: [], window_size: 20, summary: "" },
          recent_events: [],
        },
      });
    });

    const input = screen.getByPlaceholderText("Type your action...");
    fireEvent.change(input, { target: { value: "I go north" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(wsInstance.sendAction).toHaveBeenCalledWith("I go north");
  });

  it("onError handler adds system error message to store and stops agent thinking", () => {
    render(<PlayPage />);

    act(() => {
      // Set agent thinking first
      useGameStore.getState().setAgentThinking(true);
      const errorHandler = wsInstance.onError.mock.calls[0][0];
      errorHandler({ message: "Agent failed" });
    });

    expect(useGameStore.getState().isAgentThinking).toBe(false);
    const messages = useGameStore.getState().messages;
    const errorMsg = messages.find((m) => m.role === "system");
    expect(errorMsg).toBeDefined();
    expect(errorMsg?.content).toContain("Agent failed");
  });

  it("onClose handler sets connection status to disconnected", () => {
    render(<PlayPage />);

    act(() => {
      useGameStore.getState().setConnectionStatus("connected");
      const closeHandler = wsInstance.onClose.mock.calls[0][0];
      closeHandler({});
    });

    expect(useGameStore.getState().connectionStatus).toBe("disconnected");
  });

  it("onAgentResponse handler with is_complete=true finalizes message and stops thinking", () => {
    render(<PlayPage />);

    act(() => {
      useGameStore.getState().startAgentMessage();
      useGameStore.getState().setAgentThinking(true);
      const agentHandler = wsInstance.onAgentResponse.mock.calls[0][0];
      agentHandler({ is_complete: true, text: "" });
    });

    expect(useGameStore.getState().isAgentThinking).toBe(false);
    const messages = useGameStore.getState().messages;
    expect(messages[0].isStreaming).toBe(false);
  });

  it("onAgentResponse handler with is_complete=false appends chunk", () => {
    render(<PlayPage />);

    act(() => {
      useGameStore.getState().startAgentMessage();
      const agentHandler = wsInstance.onAgentResponse.mock.calls[0][0];
      agentHandler({ is_complete: false, text: "Hello" });
    });

    const messages = useGameStore.getState().messages;
    expect(messages[0].content).toBe("Hello");
    expect(messages[0].isStreaming).toBe(true);
  });
});
