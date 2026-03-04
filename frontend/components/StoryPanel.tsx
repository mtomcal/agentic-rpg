"use client";

import { useState } from "react";
import type { StoryState, StoryBeat } from "@/types/game";

interface StoryPanelProps {
  story: StoryState | null;
}

function BeatStatusIcon({ status }: { status: StoryBeat["status"] }) {
  switch (status) {
    case "resolved":
      return <span data-testid="beat-status-resolved" className="text-green-400">&#10003;</span>;
    case "active":
      return <span data-testid="beat-status-active" className="text-yellow-400 animate-pulse">&#9679;</span>;
    case "skipped":
      return <span data-testid="beat-status-skipped" className="text-gray-500">&mdash;</span>;
    default:
      return <span data-testid="beat-status-pending" className="text-gray-600">&#9675;</span>;
  }
}

export default function StoryPanel({ story }: StoryPanelProps) {
  const [premiseOpen, setPremiseOpen] = useState(false);

  if (!story) {
    return <div className="p-4 text-gray-500 italic">No story data</div>;
  }

  const activeBeat = story.outline.beats[story.active_beat_index];
  const totalBeats = story.outline.beats.length;

  return (
    <div className="p-4 space-y-4">
      <div>
        <button
          onClick={() => setPremiseOpen(!premiseOpen)}
          className="text-sm text-gray-400 hover:text-gray-200 flex items-center gap-1"
        >
          <span>{premiseOpen ? "▼" : "▶"}</span>
          <span>Story Premise</span>
        </button>
        {premiseOpen && (
          <p className="text-sm text-gray-300 mt-2 pl-4">{story.outline.premise}</p>
        )}
      </div>

      {activeBeat && (
        <div>
          <h3 className="text-sm text-gray-400 mb-1">Current Beat</h3>
          <p className="text-sm bg-gray-800 rounded px-3 py-2">{activeBeat.summary}</p>
        </div>
      )}

      <div className="text-sm text-gray-400">
        Chapter {story.active_beat_index + 1} of {totalBeats}
      </div>

      <div>
        <h3 className="text-sm text-gray-400 mb-2">Beats</h3>
        <ul className="space-y-1">
          {story.outline.beats.map((beat, i) => (
            <li key={i} className="flex items-center gap-2 text-sm">
              <BeatStatusIcon status={beat.status} />
              <span className={beat.status === "active" ? "text-gray-100" : "text-gray-400"}>
                {beat.summary}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
