"use client";

import { useState } from "react";
import type { GameState } from "@/types/game";
import CharacterPanel from "./CharacterPanel";
import InventoryPanel from "./InventoryPanel";
import LocationPanel from "./LocationPanel";
import StoryPanel from "./StoryPanel";

interface SidebarProps {
  gameState: GameState | null;
}

const tabs = ["Character", "Inventory", "Location", "Story"] as const;
type Tab = (typeof tabs)[number];

export default function Sidebar({ gameState }: SidebarProps) {
  const [activeTab, setActiveTab] = useState<Tab>("Character");

  const currentLocation = gameState?.world.locations[gameState.world.current_location_id] ?? null;

  return (
    <div className="w-80 flex flex-col h-full border-l border-gray-700">
      <div className="flex border-b border-gray-700">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-2 py-2 text-sm ${
              activeTab === tab
                ? "border-b-2 border-indigo-500 text-indigo-400"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto">
        {activeTab === "Character" && (
          <CharacterPanel character={gameState?.character ?? null} />
        )}
        {activeTab === "Inventory" && (
          <InventoryPanel inventory={gameState?.inventory ?? null} />
        )}
        {activeTab === "Location" && (
          <LocationPanel
            location={currentLocation}
            locations={gameState?.world.locations ?? {}}
          />
        )}
        {activeTab === "Story" && (
          <StoryPanel story={gameState?.story ?? null} />
        )}
      </div>
    </div>
  );
}
