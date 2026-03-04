/**
 * Tests for lib/player.ts — player ID generation and persistence.
 */

import { getPlayerId } from "@/lib/player";

// Mock localStorage
const store: Record<string, string> = {};
const mockLocalStorage = {
  getItem: jest.fn((key: string) => store[key] ?? null),
  setItem: jest.fn((key: string, value: string) => {
    store[key] = value;
  }),
  removeItem: jest.fn((key: string) => {
    delete store[key];
  }),
  clear: jest.fn(() => {
    for (const key of Object.keys(store)) delete store[key];
  }),
  get length() {
    return Object.keys(store).length;
  },
  key: jest.fn(),
};

Object.defineProperty(global, "localStorage", { value: mockLocalStorage });

// Mock crypto.randomUUID
const mockRandomUUID = jest.fn(() => "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee");
Object.defineProperty(global, "crypto", {
  value: { randomUUID: mockRandomUUID },
});

beforeEach(() => {
  mockLocalStorage.clear();
  mockLocalStorage.getItem.mockClear();
  mockLocalStorage.setItem.mockClear();
  mockRandomUUID.mockClear();
});

describe("getPlayerId", () => {
  it("generates a UUID on first call", () => {
    const id = getPlayerId();
    expect(id).toBe("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee");
    expect(mockRandomUUID).toHaveBeenCalledTimes(1);
  });

  it("persists the UUID to localStorage", () => {
    getPlayerId();
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      "agentic_rpg_player_id",
      "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    );
  });

  it("returns the same UUID on subsequent calls", () => {
    const first = getPlayerId();
    const second = getPlayerId();
    expect(first).toBe(second);
    // randomUUID called once for first call, not again for second
    expect(mockRandomUUID).toHaveBeenCalledTimes(1);
  });

  it("returns existing UUID from localStorage without generating", () => {
    store["agentic_rpg_player_id"] = "existing-uuid-value";
    const id = getPlayerId();
    expect(id).toBe("existing-uuid-value");
    expect(mockRandomUUID).not.toHaveBeenCalled();
  });
});
