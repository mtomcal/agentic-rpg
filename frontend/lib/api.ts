import type {
  SessionCreateRequest,
  SessionCreateResponse,
  SessionListResponse,
} from "@/types/api";
import type { GameState } from "@/types/game";
import { getPlayerId } from "./player";

/** Returns common headers for all API requests. */
function apiHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-Player-ID": getPlayerId(),
  };
}

/** Returns the base API URL from env or defaults to localhost:8080. */
export function getApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body?.error?.message) {
        message = body.error.message;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(message);
  }
  return response.json();
}

/** POST /api/v1/sessions — create a new game session. */
export async function createSession(
  genre: string,
  character: { name: string; profession: string; background: string }
): Promise<SessionCreateResponse> {
  const body: SessionCreateRequest = { genre, character };
  const response = await fetch(`${getApiUrl()}/api/v1/sessions`, {
    method: "POST",
    headers: apiHeaders(),
    body: JSON.stringify(body),
  });
  return handleResponse<SessionCreateResponse>(response);
}

/** GET /api/v1/sessions — list all sessions. */
export async function listSessions(): Promise<SessionListResponse> {
  const response = await fetch(`${getApiUrl()}/api/v1/sessions`, {
    headers: apiHeaders(),
  });
  return handleResponse<SessionListResponse>(response);
}

/** GET /api/v1/sessions/{id} — get full game state. */
export async function getSession(
  sessionId: string
): Promise<{ game_state: GameState }> {
  const response = await fetch(`${getApiUrl()}/api/v1/sessions/${sessionId}`, {
    headers: apiHeaders(),
  });
  return handleResponse<{ game_state: GameState }>(response);
}

/** DELETE /api/v1/sessions/{id} — delete a session. */
export async function deleteSession(
  sessionId: string
): Promise<{ success: boolean }> {
  const response = await fetch(`${getApiUrl()}/api/v1/sessions/${sessionId}`, {
    method: "DELETE",
    headers: apiHeaders(),
  });
  return handleResponse<{ success: boolean }>(response);
}
