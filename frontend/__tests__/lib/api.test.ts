/**
 * Tests for lib/api.ts — API client functions.
 */

// Mock the player module before importing api
jest.mock("@/lib/player", () => ({
  getPlayerId: jest.fn(() => "test-player-uuid"),
}));

import {
  getApiUrl,
  createSession,
  listSessions,
  getSession,
  deleteSession,
} from "@/lib/api";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

describe("getApiUrl", () => {
  const originalEnv = process.env;

  afterEach(() => {
    process.env = originalEnv;
  });

  it("returns NEXT_PUBLIC_API_URL when set", () => {
    process.env = { ...originalEnv, NEXT_PUBLIC_API_URL: "http://myhost:9000" };
    expect(getApiUrl()).toBe("http://myhost:9000");
  });

  it("defaults to http://localhost:8080 when env var not set", () => {
    process.env = { ...originalEnv };
    delete process.env.NEXT_PUBLIC_API_URL;
    expect(getApiUrl()).toBe("http://localhost:8080");
  });
});

describe("createSession", () => {
  it("sends POST to /api/v1/sessions with correct body", async () => {
    const responseData = {
      session_id: "sess-001",
      game_state: { session: { session_id: "sess-001" } },
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => responseData,
    });

    const result = await createSession("fantasy", {
      name: "Aldric",
      profession: "Knight",
      background: "A soldier",
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toContain("/api/v1/sessions");
    expect(options.method).toBe("POST");
    expect(options.headers["Content-Type"]).toBe("application/json");
    expect(options.headers["X-Player-ID"]).toBe("test-player-uuid");
    const body = JSON.parse(options.body);
    expect(body.genre).toBe("fantasy");
    expect(body.character.name).toBe("Aldric");
    expect(body.character.profession).toBe("Knight");
    expect(result.session_id).toBe("sess-001");
  });

  it("throws on non-2xx response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ error: { message: "Invalid request" } }),
    });

    await expect(
      createSession("fantasy", { name: "A", profession: "B", background: "C" })
    ).rejects.toThrow("Invalid request");
  });
});

describe("listSessions", () => {
  it("sends GET to /api/v1/sessions", async () => {
    const responseData = {
      sessions: [
        {
          session_id: "sess-001",
          status: "active",
          character_name: "Aldric",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        },
      ],
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => responseData,
    });

    const result = await listSessions();

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toContain("/api/v1/sessions");
    expect(options.headers["X-Player-ID"]).toBe("test-player-uuid");
    expect(result.sessions).toHaveLength(1);
    expect(result.sessions[0].character_name).toBe("Aldric");
  });

  it("throws on error response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ error: { message: "Internal error" } }),
    });

    await expect(listSessions()).rejects.toThrow("Internal error");
  });
});

describe("getSession", () => {
  it("sends GET to /api/v1/sessions/{id}", async () => {
    const responseData = {
      game_state: {
        session: { session_id: "sess-001" },
        character: { name: "Aldric" },
      },
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => responseData,
    });

    const result = await getSession("sess-001");

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toContain("/api/v1/sessions/sess-001");
    expect(options.headers["X-Player-ID"]).toBe("test-player-uuid");
    expect(result.game_state.character.name).toBe("Aldric");
  });

  it("throws on 404 response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ error: { message: "Session not found" } }),
    });

    await expect(getSession("nonexistent")).rejects.toThrow("Session not found");
  });
});

describe("deleteSession", () => {
  it("sends DELETE to /api/v1/sessions/{id}", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    const result = await deleteSession("sess-001");

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toContain("/api/v1/sessions/sess-001");
    expect(options.method).toBe("DELETE");
    expect(options.headers["X-Player-ID"]).toBe("test-player-uuid");
    expect(result.success).toBe(true);
  });

  it("throws on error response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ error: { message: "Delete failed" } }),
    });

    await expect(deleteSession("sess-001")).rejects.toThrow("Delete failed");
  });
});
