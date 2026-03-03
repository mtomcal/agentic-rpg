"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createSession } from "@/lib/api";

export default function NewGamePage() {
  const router = useRouter();
  const [genre, setGenre] = useState("");
  const [name, setName] = useState("");
  const [profession, setProfession] = useState("");
  const [background, setBackground] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!genre.trim() || !name.trim() || !profession.trim() || !background.trim()) return;

    try {
      setLoading(true);
      setError(null);
      const result = await createSession(genre.trim(), {
        name: name.trim(),
        profession: profession.trim(),
        background: background.trim(),
      });
      router.push(`/play/${result.session_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create session");
      setLoading(false);
    }
  }

  return (
    <main className="max-w-lg mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">New Game</h1>
        <button
          onClick={() => router.back()}
          className="text-gray-400 hover:text-gray-200"
        >
          Back
        </button>
      </div>

      {error && (
        <p className="text-red-400 bg-red-900/20 rounded-lg px-4 py-2 mb-4">
          {error}
        </p>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="genre" className="block text-sm text-gray-400 mb-1">
            Genre / Setting
          </label>
          <input
            id="genre"
            type="text"
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            required
            className="w-full bg-gray-800 text-gray-100 rounded-lg px-4 py-2 border border-gray-600 focus:border-indigo-500 focus:outline-none"
            placeholder="e.g., Medieval Fantasy, Sci-Fi, Horror"
          />
        </div>

        <div>
          <label htmlFor="name" className="block text-sm text-gray-400 mb-1">
            Character Name
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full bg-gray-800 text-gray-100 rounded-lg px-4 py-2 border border-gray-600 focus:border-indigo-500 focus:outline-none"
            placeholder="e.g., Aldric, Zara, Rex"
          />
        </div>

        <div>
          <label htmlFor="profession" className="block text-sm text-gray-400 mb-1">
            Profession
          </label>
          <input
            id="profession"
            type="text"
            value={profession}
            onChange={(e) => setProfession(e.target.value)}
            required
            className="w-full bg-gray-800 text-gray-100 rounded-lg px-4 py-2 border border-gray-600 focus:border-indigo-500 focus:outline-none"
            placeholder="e.g., Knight, Mage, Rogue"
          />
        </div>

        <div>
          <label htmlFor="background" className="block text-sm text-gray-400 mb-1">
            Background
          </label>
          <textarea
            id="background"
            value={background}
            onChange={(e) => setBackground(e.target.value)}
            required
            rows={3}
            className="w-full bg-gray-800 text-gray-100 rounded-lg px-4 py-2 border border-gray-600 focus:border-indigo-500 focus:outline-none resize-none"
            placeholder="Tell us about your character's backstory..."
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-500 disabled:opacity-50"
        >
          {loading ? "Creating..." : "Start Adventure"}
        </button>
      </form>
    </main>
  );
}
