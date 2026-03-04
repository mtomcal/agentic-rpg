type ConnectionStatus = "connecting" | "connected" | "disconnected";

type MessageHandler<T = any> = (data: T) => void;

function getWsUrl(): string {
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
  return apiUrl.replace(/^http/, "ws");
}

export class GameWebSocket {
  private ws: WebSocket | null = null;
  private status: ConnectionStatus = "disconnected";
  private sessionId: string | null = null;
  private intentionalClose = false;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  private handlers = {
    connected: [] as MessageHandler[],
    agent_response: [] as MessageHandler[],
    state_update: [] as MessageHandler[],
    error: [] as MessageHandler[],
    close: [] as MessageHandler[],
  };

  connect(sessionId: string): void {
    this.sessionId = sessionId;
    this.intentionalClose = false;
    this.status = "connecting";

    const url = `${getWsUrl()}/api/v1/sessions/${sessionId}/ws`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.status = "connected";
      this.reconnectAttempt = 0;
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data);
        const type = message.type as keyof typeof this.handlers;
        if (type in this.handlers && type !== "close") {
          for (const handler of this.handlers[type]) {
            handler(message.data);
          }
        }
      } catch {
        // ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      this.status = "disconnected";
      for (const handler of this.handlers.close) {
        handler({});
      }
      if (!this.intentionalClose && this.sessionId) {
        this.attemptReconnect();
      }
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.status = "disconnected";
  }

  sendAction(text: string): void {
    if (!this.ws) return;
    const message = {
      type: "player_action",
      data: { text },
      timestamp: new Date().toISOString(),
    };
    this.ws.send(JSON.stringify(message));
  }

  onConnected(handler: MessageHandler): void {
    this.handlers.connected.push(handler);
  }

  onAgentResponse(handler: MessageHandler): void {
    this.handlers.agent_response.push(handler);
  }

  onStateUpdate(handler: MessageHandler): void {
    this.handlers.state_update.push(handler);
  }

  onError(handler: MessageHandler): void {
    this.handlers.error.push(handler);
  }

  onClose(handler: MessageHandler): void {
    this.handlers.close.push(handler);
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  private attemptReconnect(): void {
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempt), 30000);
    this.reconnectAttempt++;
    this.reconnectTimer = setTimeout(() => {
      if (this.sessionId && !this.intentionalClose) {
        this.connect(this.sessionId);
      }
    }, delay);
    // Set status to connecting immediately so tests can check
    this.status = "connecting";
  }
}
