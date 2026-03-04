import { render, screen } from "@testing-library/react";
import LocationPanel from "@/components/LocationPanel";
import type { Location } from "@/types/game";

const mockLocation: Location = {
  id: "loc-001",
  name: "Town Square",
  description: "A bustling marketplace in the heart of town.",
  connections: ["loc-002", "loc-003"],
  npcs_present: ["Guard Captain", "Merchant"],
  items_present: ["Rusty Key"],
  visited: true,
};

const mockLocations: Record<string, Location> = {
  "loc-001": mockLocation,
  "loc-002": { id: "loc-002", name: "Tavern", description: "A cozy inn", connections: [], npcs_present: [], items_present: [], visited: true },
  "loc-003": { id: "loc-003", name: "Blacksmith", description: "Hot forge", connections: [], npcs_present: [], items_present: [], visited: false },
};

describe("LocationPanel", () => {
  it("renders location name", () => {
    render(<LocationPanel location={mockLocation} locations={mockLocations} />);
    expect(screen.getByText("Town Square")).toBeInTheDocument();
  });

  it("renders location description", () => {
    render(<LocationPanel location={mockLocation} locations={mockLocations} />);
    expect(screen.getByText("A bustling marketplace in the heart of town.")).toBeInTheDocument();
  });

  it("renders connected locations", () => {
    render(<LocationPanel location={mockLocation} locations={mockLocations} />);
    expect(screen.getByText("Tavern")).toBeInTheDocument();
    expect(screen.getByText("Blacksmith")).toBeInTheDocument();
  });

  it("renders NPCs present", () => {
    render(<LocationPanel location={mockLocation} locations={mockLocations} />);
    expect(screen.getByText("Guard Captain")).toBeInTheDocument();
    expect(screen.getByText("Merchant")).toBeInTheDocument();
  });

  it("renders items present", () => {
    render(<LocationPanel location={mockLocation} locations={mockLocations} />);
    expect(screen.getByText("Rusty Key")).toBeInTheDocument();
  });

  it("renders null location gracefully", () => {
    render(<LocationPanel location={null} locations={{}} />);
    expect(screen.getByText("No location data")).toBeInTheDocument();
  });

  it("hides NPCs section when none present", () => {
    const noNpcs = { ...mockLocation, npcs_present: [] };
    render(<LocationPanel location={noNpcs} locations={mockLocations} />);
    expect(screen.queryByText("NPCs")).not.toBeInTheDocument();
  });

  it("hides Items section when none present", () => {
    const noItems = { ...mockLocation, items_present: [] };
    render(<LocationPanel location={noItems} locations={mockLocations} />);
    expect(screen.queryByText("Items Here")).not.toBeInTheDocument();
  });
});
