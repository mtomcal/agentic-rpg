const PLAYER_ID_KEY = "agentic_rpg_player_id";

/** Generate a v4 UUID, using crypto.randomUUID() when available (secure contexts)
 *  and falling back to crypto.getRandomValues() otherwise (plain HTTP). */
function generateUUID(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // Fallback for non-secure contexts (HTTP over non-localhost)
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40; // version 4
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // variant 1
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

/** Returns the player's UUID, generating and persisting to localStorage on first call. */
export function getPlayerId(): string {
  if (typeof window === "undefined") {
    // SSR fallback — generate a fresh ID (won't persist)
    return generateUUID();
  }
  let id = localStorage.getItem(PLAYER_ID_KEY);
  if (!id) {
    id = generateUUID();
    localStorage.setItem(PLAYER_ID_KEY, id);
  }
  return id;
}
