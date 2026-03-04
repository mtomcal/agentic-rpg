import { render, screen } from "@testing-library/react";
import CharacterPanel from "@/components/CharacterPanel";
import type { Character } from "@/types/game";

const mockCharacter: Character = {
  id: "c-001",
  name: "Aldric",
  profession: "Knight",
  background: "A former soldier",
  stats: { health: 80, max_health: 100, energy: 30, max_energy: 50, money: 42 },
  status_effects: [
    { name: "Poisoned", duration: 3, description: "Taking damage each turn" },
  ],
  level: 3,
  experience: 250,
  location_id: "loc-001",
};

describe("CharacterPanel", () => {
  it("renders character name", () => {
    render(<CharacterPanel character={mockCharacter} />);
    expect(screen.getByText("Aldric")).toBeInTheDocument();
  });

  it("renders profession and level", () => {
    render(<CharacterPanel character={mockCharacter} />);
    expect(screen.getByText(/Level 3 Knight/)).toBeInTheDocument();
  });

  it("renders health bar with correct values", () => {
    render(<CharacterPanel character={mockCharacter} />);
    expect(screen.getByText("80 / 100")).toBeInTheDocument();
    expect(screen.getByTestId("health-bar")).toBeInTheDocument();
  });

  it("renders energy bar with correct values", () => {
    render(<CharacterPanel character={mockCharacter} />);
    expect(screen.getByText("30 / 50")).toBeInTheDocument();
    expect(screen.getByTestId("energy-bar")).toBeInTheDocument();
  });

  it("renders money", () => {
    render(<CharacterPanel character={mockCharacter} />);
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("renders status effects", () => {
    render(<CharacterPanel character={mockCharacter} />);
    expect(screen.getByText("Poisoned")).toBeInTheDocument();
    expect(screen.getByText("3 turns")).toBeInTheDocument();
  });

  it("renders experience", () => {
    render(<CharacterPanel character={mockCharacter} />);
    expect(screen.getByText(/XP: 250/)).toBeInTheDocument();
  });

  it("renders loading placeholder when character is null", () => {
    render(<CharacterPanel character={null} />);
    expect(screen.getByText("No character data")).toBeInTheDocument();
  });

  it("applies correct health bar color for high health", () => {
    const healthyChar = { ...mockCharacter, stats: { ...mockCharacter.stats, health: 90 } };
    render(<CharacterPanel character={healthyChar} />);
    const bar = screen.getByTestId("health-bar-fill");
    expect(bar.className).toContain("bg-green");
  });

  it("applies correct health bar color for medium health", () => {
    const medChar = { ...mockCharacter, stats: { ...mockCharacter.stats, health: 40 } };
    render(<CharacterPanel character={medChar} />);
    const bar = screen.getByTestId("health-bar-fill");
    expect(bar.className).toContain("bg-yellow");
  });

  it("applies correct health bar color for low health", () => {
    const lowChar = { ...mockCharacter, stats: { ...mockCharacter.stats, health: 20 } };
    render(<CharacterPanel character={lowChar} />);
    const bar = screen.getByTestId("health-bar-fill");
    expect(bar.className).toContain("bg-red");
  });
});
