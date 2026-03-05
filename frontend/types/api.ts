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

export type {
  PlayerActionMessage,
  AgentResponseMessage,
  StateUpdateMessage,
  StateSnapshotMessage,
  ConnectedMessage,
  ErrorMessage,
  InboundMessage,
} from "@/lib/ws-schemas";
