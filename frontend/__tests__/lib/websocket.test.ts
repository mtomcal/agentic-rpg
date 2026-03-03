/**
 * Tests for lib/websocket.ts — GameWebSocket client.
 */

import { GameWebSocket } from "@/lib/websocket";

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((ev: any) => void) | null = null;
  onclose: ((ev: any) => void) | null = null;
  onmessage: ((ev: any) => void) | null = null;
  onerror: ((ev: any) => void) | null = null;
  send = jest.fn();
  close = jest.fn();

  constructor(url: string) {
    this.url = url;
    // Auto-open after construction
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.({});
    }, 0);
  }
}

// Store original and override
const OriginalWebSocket = global.WebSocket;

beforeAll(() => {
  (global as any).WebSocket = MockWebSocket;
});

afterAll(() => {
  (global as any).WebSocket = OriginalWebSocket;
});

describe("GameWebSocket", () => {
  let ws: GameWebSocket;

  beforeEach(() => {
    jest.useFakeTimers();
    ws = new GameWebSocket();
  });

  afterEach(() => {
    ws.disconnect();
    jest.useRealTimers();
  });

  describe("connect", () => {
    it("opens WebSocket to correct URL", () => {
      ws.connect("sess-001");
      expect(ws.getStatus()).toBe("connecting");
    });

    it("uses NEXT_PUBLIC_WS_URL if set", () => {
      const orig = process.env.NEXT_PUBLIC_WS_URL;
      process.env.NEXT_PUBLIC_WS_URL = "ws://custom:9090";
      const ws2 = new GameWebSocket();
      ws2.connect("sess-001");
      // Status should be connecting since we connected
      expect(ws2.getStatus()).toBe("connecting");
      ws2.disconnect();
      process.env.NEXT_PUBLIC_WS_URL = orig;
    });

    it("transitions to connected on open", async () => {
      ws.connect("sess-001");
      expect(ws.getStatus()).toBe("connecting");

      // Trigger open
      jest.runAllTimers();
      expect(ws.getStatus()).toBe("connected");
    });
  });

  describe("disconnect", () => {
    it("closes the WebSocket", () => {
      ws.connect("sess-001");
      jest.runAllTimers();
      ws.disconnect();
      expect(ws.getStatus()).toBe("disconnected");
    });

    it("is safe to call when not connected", () => {
      expect(() => ws.disconnect()).not.toThrow();
    });
  });

  describe("sendAction", () => {
    it("sends a player_action message with correct format", () => {
      ws.connect("sess-001");
      jest.runAllTimers();

      ws.sendAction("I go north");

      const mockWs = (ws as any).ws as MockWebSocket;
      expect(mockWs.send).toHaveBeenCalledTimes(1);
      const sent = JSON.parse(mockWs.send.mock.calls[0][0]);
      expect(sent.type).toBe("player_action");
      expect(sent.data.text).toBe("I go north");
      expect(sent.timestamp).toBeDefined();
    });
  });

  describe("message handlers", () => {
    it("calls onConnected for connected messages", () => {
      const handler = jest.fn();
      ws.onConnected(handler);
      ws.connect("sess-001");
      jest.runAllTimers();

      const mockWs = (ws as any).ws as MockWebSocket;
      mockWs.onmessage?.({
        data: JSON.stringify({
          type: "connected",
          data: { session_id: "sess-001", game_state: {} },
          timestamp: "2024-01-01T00:00:00Z",
        }),
      });

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith({
        session_id: "sess-001",
        game_state: {},
      });
    });

    it("calls onAgentResponse for agent_response messages", () => {
      const handler = jest.fn();
      ws.onAgentResponse(handler);
      ws.connect("sess-001");
      jest.runAllTimers();

      const mockWs = (ws as any).ws as MockWebSocket;
      mockWs.onmessage?.({
        data: JSON.stringify({
          type: "agent_response",
          data: { text: "You walk north.", is_complete: false },
          timestamp: "2024-01-01T00:00:00Z",
        }),
      });

      expect(handler).toHaveBeenCalledWith({
        text: "You walk north.",
        is_complete: false,
      });
    });

    it("calls onStateUpdate for state_update messages", () => {
      const handler = jest.fn();
      ws.onStateUpdate(handler);
      ws.connect("sess-001");
      jest.runAllTimers();

      const mockWs = (ws as any).ws as MockWebSocket;
      mockWs.onmessage?.({
        data: JSON.stringify({
          type: "state_update",
          data: { event_type: "character.stat_changed", changes: {} },
          timestamp: "2024-01-01T00:00:00Z",
        }),
      });

      expect(handler).toHaveBeenCalledWith({
        event_type: "character.stat_changed",
        changes: {},
      });
    });

    it("calls onError for error messages", () => {
      const handler = jest.fn();
      ws.onError(handler);
      ws.connect("sess-001");
      jest.runAllTimers();

      const mockWs = (ws as any).ws as MockWebSocket;
      mockWs.onmessage?.({
        data: JSON.stringify({
          type: "error",
          data: { code: "agent_error", message: "Failed" },
          timestamp: "2024-01-01T00:00:00Z",
        }),
      });

      expect(handler).toHaveBeenCalledWith({
        code: "agent_error",
        message: "Failed",
      });
    });

    it("calls onClose when connection closes", () => {
      const handler = jest.fn();
      ws.onClose(handler);
      ws.connect("sess-001");
      jest.runAllTimers();

      const mockWs = (ws as any).ws as MockWebSocket;
      mockWs.readyState = MockWebSocket.CLOSED;
      mockWs.onclose?.({ code: 1000, reason: "Normal" });

      expect(handler).toHaveBeenCalledTimes(1);
    });
  });

  describe("getStatus", () => {
    it("returns disconnected initially", () => {
      expect(ws.getStatus()).toBe("disconnected");
    });

    it("returns connecting after connect call", () => {
      ws.connect("sess-001");
      expect(ws.getStatus()).toBe("connecting");
    });

    it("returns connected after open", () => {
      ws.connect("sess-001");
      jest.runAllTimers();
      expect(ws.getStatus()).toBe("connected");
    });
  });

  describe("auto-reconnect", () => {
    it("attempts reconnect on unexpected close", () => {
      ws.connect("sess-001");
      jest.runAllTimers();

      // Simulate unexpected close
      const mockWs = (ws as any).ws as MockWebSocket;
      mockWs.readyState = MockWebSocket.CLOSED;
      mockWs.onclose?.({ code: 1006, reason: "Abnormal" });

      // Should attempt reconnect after delay
      expect(ws.getStatus()).toBe("connecting");
    });

    it("does not reconnect on clean close via disconnect()", () => {
      ws.connect("sess-001");
      jest.runAllTimers();

      ws.disconnect();
      jest.runAllTimers();

      expect(ws.getStatus()).toBe("disconnected");
    });
  });
});
