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
    expect(wsInstance.onConnected).toHaveBeenCalled();
    expect(wsInstance.onAgentResponse).toHaveBeenCalled();
    expect(wsInstance.onStateUpdate).toHaveBeenCalled();
    expect(wsInstance.onError).toHaveBeenCalled();
    expect(wsInstance.onClose).toHaveBeenCalled();
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
});
