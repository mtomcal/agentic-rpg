"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listSessions, deleteSession } from "@/lib/api";
import type { SessionSummary } from "@/types/api";

export default function HomePage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  async function loadSessions() {
    try {
      setLoading(true);
      setError(null);
      const data = await listSessions();
      setSessions(data.sessions);
    } catch (err: any) {
      setError(err.message || "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(e: React.MouseEvent, sessionId: string) {
    e.stopPropagation();
    if (!window.confirm("Delete this session?")) return;
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
    } catch (err: any) {
      setError(err.message || "Failed to delete session");
    }
  }

  return (
    <main className="max-w-2xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Agentic RPG</h1>
        <button
          onClick={() => router.push("/new")}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-500"
        >
          New Game
        </button>
      </div>

      {loading && <p className="text-gray-400">Loading...</p>}

      {error && (
        <p className="text-red-400 bg-red-900/20 rounded-lg px-4 py-2 mb-4">
          {error}
        </p>
      )}

      {!loading && !error && sessions.length === 0 && (
        <p className="text-gray-500 italic text-center mt-8">
          No sessions yet. Start a new game!
        </p>
      )}

      {!loading && sessions.length > 0 && (
        <div className="space-y-3">
          {sessions.map((session) => (
            <div
              key={session.session_id}
              onClick={() => router.push(`/play/${session.session_id}`)}
              className="bg-gray-800 rounded-lg p-4 cursor-pointer hover:bg-gray-700 flex items-center justify-between"
            >
              <div>
                <h2 className="font-semibold">{session.character_name}</h2>
                <p className="text-sm text-gray-400">
                  Status: {session.status} &middot;{" "}
                  {new Date(session.updated_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={(e) => handleDelete(e, session.session_id)}
                aria-label="Delete session"
                className="text-gray-500 hover:text-red-400 px-2"
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
