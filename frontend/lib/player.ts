const PLAYER_ID_KEY = "agentic_rpg_player_id";

/** Returns the player's UUID, generating and persisting to localStorage on first call. */
export function getPlayerId(): string {
  if (typeof window === "undefined") {
    // SSR fallback — generate a fresh ID (won't persist)
    return crypto.randomUUID();
  }
  let id = localStorage.getItem(PLAYER_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(PLAYER_ID_KEY, id);
  }
  return id;
}
