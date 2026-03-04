import { render, screen } from "@testing-library/react";
import InventoryPanel from "@/components/InventoryPanel";
import type { Inventory } from "@/types/game";

const mockInventory: Inventory = {
  items: [
    { id: "i1", name: "Iron Sword", description: "A blade", item_type: "weapon", quantity: 1, properties: {} },
    { id: "i2", name: "Leather Armor", description: "Basic armor", item_type: "armor", quantity: 1, properties: {} },
    { id: "i3", name: "Health Potion", description: "Heals 50 HP", item_type: "consumable", quantity: 3, properties: {} },
    { id: "i4", name: "Dungeon Key", description: "Opens the dungeon", item_type: "key", quantity: 1, properties: {} },
    { id: "i5", name: "Old Coin", description: "Shiny", item_type: "misc", quantity: 5, properties: {} },
  ],
  equipment: { weapon: "i1", armor: "i2", accessory: null },
  capacity: 20,
};

describe("InventoryPanel", () => {
  it("renders item names in the items list", () => {
    render(<InventoryPanel inventory={mockInventory} />);
    // Items appear in both equipment and items list, use getAllByText
    expect(screen.getAllByText("Iron Sword").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Leather Armor").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Health Potion")).toBeInTheDocument();
  });

  it("renders item quantities", () => {
    render(<InventoryPanel inventory={mockInventory} />);
    expect(screen.getByText("x3")).toBeInTheDocument();
    expect(screen.getByText("x5")).toBeInTheDocument();
  });

  it("renders item type badges in items section", () => {
    render(<InventoryPanel inventory={mockInventory} />);
    // Type badges appear in both equipment slot names and item badges
    const weaponBadges = screen.getAllByText("weapon");
    expect(weaponBadges.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("consumable")).toBeInTheDocument();
    expect(screen.getByText("key")).toBeInTheDocument();
    expect(screen.getByText("misc")).toBeInTheDocument();
  });

  it("renders equipment section heading", () => {
    render(<InventoryPanel inventory={mockInventory} />);
    expect(screen.getByText("Equipment")).toBeInTheDocument();
  });

  it("shows Empty for unequipped slots", () => {
    render(<InventoryPanel inventory={mockInventory} />);
    expect(screen.getByText("Empty")).toBeInTheDocument();
  });

  it("renders empty inventory message", () => {
    const empty: Inventory = { items: [], equipment: {}, capacity: null };
    render(<InventoryPanel inventory={empty} />);
    expect(screen.getByText("Your inventory is empty")).toBeInTheDocument();
  });

  it("renders null inventory gracefully", () => {
    render(<InventoryPanel inventory={null} />);
    expect(screen.getByText("No inventory data")).toBeInTheDocument();
  });

  it("applies correct color for weapon type badge", () => {
    render(<InventoryPanel inventory={mockInventory} />);
    // Find the badge in items section (has the bg-red class)
    const weaponElements = screen.getAllByText("weapon");
    const badge = weaponElements.find((el) => el.className.includes("red"));
    expect(badge).toBeDefined();
    expect(badge!.className).toContain("red");
  });

  it("applies correct color for armor type badge", () => {
    render(<InventoryPanel inventory={mockInventory} />);
    const armorElements = screen.getAllByText("armor");
    const badge = armorElements.find((el) => el.className.includes("blue"));
    expect(badge).toBeDefined();
    expect(badge!.className).toContain("blue");
  });

  it("applies correct color for consumable type", () => {
    render(<InventoryPanel inventory={mockInventory} />);
    const badge = screen.getByText("consumable");
    expect(badge.className).toContain("green");
  });

  it("applies correct color for key type", () => {
    render(<InventoryPanel inventory={mockInventory} />);
    const badge = screen.getByText("key");
    expect(badge.className).toContain("yellow");
  });
});
