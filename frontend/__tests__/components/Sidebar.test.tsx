import { render, screen, fireEvent } from "@testing-library/react";
import Sidebar from "@/components/Sidebar";
import type { GameState } from "@/types/game";

const mockGameState: GameState = {
  session: { session_id: "s1", player_id: "p1", created_at: "", updated_at: "", schema_version: 1, status: "active" },
  character: { id: "c1", name: "Aldric", profession: "Knight", background: "", stats: { health: 100, max_health: 100, energy: 50, max_energy: 50, money: 10 }, status_effects: [], level: 1, experience: 0, location_id: "loc-001" },
  inventory: { items: [{ id: "i1", name: "Sword", description: "", item_type: "weapon", quantity: 1, properties: {} }], equipment: {}, capacity: null },
  world: { locations: { "loc-001": { id: "loc-001", name: "Village", description: "A small village", connections: [], npcs_present: [], items_present: [], visited: true } }, current_location_id: "loc-001", discovered_locations: ["loc-001"], world_flags: {} },
  story: { outline: { premise: "Save the kingdom", setting: "Fantasy", beats: [{ summary: "Begin", location: "Village", trigger_conditions: [], key_elements: [], player_objectives: [], possible_outcomes: [], flexibility: "flexible", status: "active" }] }, active_beat_index: 0, summary: "", adaptation_history: [] },
  conversation: { history: [], window_size: 20, summary: "" },
  recent_events: [],
};

describe("Sidebar", () => {
  it("renders all tab buttons", () => {
    render(<Sidebar gameState={mockGameState} />);
    expect(screen.getByText("Character")).toBeInTheDocument();
    expect(screen.getByText("Inventory")).toBeInTheDocument();
    expect(screen.getByText("Location")).toBeInTheDocument();
    expect(screen.getByText("Story")).toBeInTheDocument();
  });

  it("defaults to Character tab", () => {
    render(<Sidebar gameState={mockGameState} />);
    expect(screen.getByText("Aldric")).toBeInTheDocument();
  });

  it("switches to Inventory tab", () => {
    render(<Sidebar gameState={mockGameState} />);
    fireEvent.click(screen.getByText("Inventory"));
    expect(screen.getByText("Sword")).toBeInTheDocument();
  });

  it("switches to Location tab", () => {
    render(<Sidebar gameState={mockGameState} />);
    fireEvent.click(screen.getByText("Location"));
    expect(screen.getByText("Village")).toBeInTheDocument();
    expect(screen.getByText("A small village")).toBeInTheDocument();
  });

  it("switches to Story tab", () => {
    render(<Sidebar gameState={mockGameState} />);
    fireEvent.click(screen.getByText("Story"));
    expect(screen.getByText("Chapter 1 of 1")).toBeInTheDocument();
  });

  it("highlights the active tab", () => {
    render(<Sidebar gameState={mockGameState} />);
    const charTab = screen.getByText("Character");
    expect(charTab.closest("button")?.className).toContain("border-indigo");
  });

  it("renders with null game state", () => {
    render(<Sidebar gameState={null} />);
    expect(screen.getByText("No character data")).toBeInTheDocument();
  });
});
