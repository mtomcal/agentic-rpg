import type { GameState } from "./game";

/** Request body for POST /api/v1/sessions. */
export interface SessionCreateRequest {
  genre: string;
  character: {
    name: string;
    profession: string;
    background: string;
  };
}

/** Response from POST /api/v1/sessions. */
export interface SessionCreateResponse {
  session_id: string;
  game_state: GameState;
}

/** Summary of a session for listing. */
export interface SessionSummary {
  session_id: string;
  status: string;
  genre: string;
  character_name: string;
  created_at: string;
  updated_at: string;
}

/** Response from GET /api/v1/sessions. */
export interface SessionListResponse {
  sessions: SessionSummary[];
}

/** Generic WebSocket message envelope. */
export interface WSMessage {
  type: string;
  data: Record<string, any>;
  timestamp: string;
}

/** Client → server: player action. */
export interface PlayerActionMessage {
  type: "player_action";
  data: { text: string };
  timestamp: string;
}

/** Server → client: agent narrative response (may be streamed). */
export interface AgentResponseMessage {
  type: "agent_response";
  data: { text: string; is_complete: boolean };
  timestamp: string;
}

/** Server → client: game state change. */
export interface StateUpdateMessage {
  type: "state_update";
  data: {
    event_type: string;
    changes: Record<string, any>;
  };
  timestamp: string;
}

/** Server → client: initial connection message with session summary. */
export interface ConnectedMessage {
  type: "connected";
  data: {
    session_id: string;
    character: {
      name: string;
      profession: string;
      level: number;
    };
    location: {
      id: string;
      name: string;
      description: string;
    };
  };
  timestamp: string;
}

/** Server → client: error message. */
export interface ErrorMessage {
  type: "error";
  data: { code: string; message: string };
  timestamp: string;
}
