import { render, screen, fireEvent } from "@testing-library/react";
import StoryPanel from "@/components/StoryPanel";
import type { StoryState } from "@/types/game";

const mockStory: StoryState = {
  outline: {
    premise: "A quest to save the kingdom from darkness.",
    setting: "Medieval Fantasy",
    beats: [
      { summary: "Arrive at the village", location: "Village", trigger_conditions: [], key_elements: [], player_objectives: [], possible_outcomes: [], flexibility: "flexible", status: "resolved" },
      { summary: "Meet the mysterious stranger", location: "Tavern", trigger_conditions: [], key_elements: [], player_objectives: [], possible_outcomes: [], flexibility: "flexible", status: "active" },
      { summary: "Enter the dungeon", location: "Dungeon", trigger_conditions: [], key_elements: [], player_objectives: [], possible_outcomes: [], flexibility: "fixed", status: "planned" },
      { summary: "Defeat the boss", location: "Throne Room", trigger_conditions: [], key_elements: [], player_objectives: [], possible_outcomes: [], flexibility: "optional", status: "planned" },
    ],
  },
  active_beat_index: 1,
  summary: "The hero arrived at the village and learned of dark forces.",
  adaptations: [],
};

describe("StoryPanel", () => {
  it("renders current beat summary", () => {
    render(<StoryPanel story={mockStory} />);
    // Appears in both Current Beat section and beat list
    const elements = screen.getAllByText("Meet the mysterious stranger");
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders progress indicator", () => {
    render(<StoryPanel story={mockStory} />);
    expect(screen.getByText("Chapter 2 of 4")).toBeInTheDocument();
  });

  it("renders beat list with all beats", () => {
    render(<StoryPanel story={mockStory} />);
    expect(screen.getByText("Arrive at the village")).toBeInTheDocument();
    expect(screen.getByText("Enter the dungeon")).toBeInTheDocument();
    expect(screen.getByText("Defeat the boss")).toBeInTheDocument();
  });

  it("renders premise when expanded", () => {
    render(<StoryPanel story={mockStory} />);
    const toggle = screen.getByText("Story Premise");
    fireEvent.click(toggle);
    expect(screen.getByText("A quest to save the kingdom from darkness.")).toBeInTheDocument();
  });

  it("renders null story gracefully", () => {
    render(<StoryPanel story={null} />);
    expect(screen.getByText("No story data")).toBeInTheDocument();
  });

  it("shows resolved status for completed beats", () => {
    render(<StoryPanel story={mockStory} />);
    const resolvedIndicators = screen.getAllByTestId("beat-status-resolved");
    expect(resolvedIndicators.length).toBe(1);
  });

  it("shows active status for current beat", () => {
    render(<StoryPanel story={mockStory} />);
    const activeIndicators = screen.getAllByTestId("beat-status-active");
    expect(activeIndicators.length).toBe(1);
  });

  it("shows planned status for future beats", () => {
    render(<StoryPanel story={mockStory} />);
    const pendingIndicators = screen.getAllByTestId("beat-status-planned");
    expect(pendingIndicators.length).toBe(2);
  });
});
