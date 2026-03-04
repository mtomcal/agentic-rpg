/**
 * Tests for types/game.ts
 *
 * These tests verify that the TypeScript interfaces match the backend
 * Pydantic models from docs/specs/schema-registry.md and game-state.md.
 * We test by creating objects that conform to the interfaces and verifying
 * their shape.
 */

import type {
  StatusEffect,
  AdaptationRecord,
  Character,
  Item,
  Inventory,
  Location,
  World,
  StoryBeat,
  StoryOutline,
  StoryState,
  Message,
  Conversation,
  Session,
  GameState,
} from "@/types/game";

describe("Game Types", () => {
  describe("StatusEffect", () => {
    it("has required fields", () => {
      const effect: StatusEffect = {
        name: "Poisoned",
        effect_type: "debuff",
        duration: 3,
        magnitude: 5,
        description: "Losing health each turn",
      };
      expect(effect.name).toBe("Poisoned");
      expect(effect.effect_type).toBe("debuff");
      expect(effect.duration).toBe(3);
      expect(effect.magnitude).toBe(5);
      expect(effect.description).toBe("Losing health each turn");
    });

    it("supports all effect_type values", () => {
      const types: StatusEffect["effect_type"][] = ["buff", "debuff", "condition"];
      expect(types).toHaveLength(3);
    });

    it("allows null duration", () => {
      const effect: StatusEffect = {
        name: "Blessed",
        effect_type: "buff",
        duration: null,
        magnitude: 10,
        description: "Permanent blessing",
      };
      expect(effect.duration).toBeNull();
    });
  });

  describe("AdaptationRecord", () => {
    it("has required fields", () => {
      const record: AdaptationRecord = {
        reason: "Player went off-script",
        changes: "Added new story beat for unexpected cave",
        timestamp: "2024-06-15T10:30:00Z",
      };
      expect(record.reason).toBe("Player went off-script");
      expect(record.changes).toBe("Added new story beat for unexpected cave");
      expect(record.timestamp).toBe("2024-06-15T10:30:00Z");
    });
  });

  describe("Character", () => {
    it("has all required fields matching Pydantic model", () => {
      const character: Character = {
        id: "char-001",
        name: "Aldric",
        profession: "Knight",
        background: "A former soldier",
        stats: { health: 100, max_health: 100, energy: 50, max_energy: 50, money: 10 },
        status_effects: [],
        level: 1,
        experience: 0,
        location_id: "loc-001",
      };
      expect(character.id).toBe("char-001");
      expect(character.name).toBe("Aldric");
      expect(character.profession).toBe("Knight");
      expect(character.background).toBe("A former soldier");
      expect(character.stats.health).toBe(100);
      expect(character.stats.max_health).toBe(100);
      expect(character.status_effects).toHaveLength(0);
      expect(character.level).toBe(1);
      expect(character.experience).toBe(0);
      expect(character.location_id).toBe("loc-001");
    });

    it("supports status effects", () => {
      const character: Character = {
        id: "char-001",
        name: "Aldric",
        profession: "Knight",
        background: "A former soldier",
        stats: { health: 80 },
        status_effects: [{ name: "Poisoned", effect_type: "debuff", duration: 3, magnitude: 5, description: "Taking damage" }],
        level: 2,
        experience: 150,
        location_id: "loc-002",
      };
      expect(character.status_effects).toHaveLength(1);
      expect(character.status_effects[0].name).toBe("Poisoned");
      expect(character.status_effects[0].effect_type).toBe("debuff");
    });
  });

  describe("Item", () => {
    it("has all required fields matching Pydantic model", () => {
      const item: Item = {
        id: "item-001",
        name: "Iron Sword",
        description: "A sturdy blade",
        item_type: "weapon",
        quantity: 1,
        properties: { damage: 10 },
      };
      expect(item.id).toBe("item-001");
      expect(item.name).toBe("Iron Sword");
      expect(item.description).toBe("A sturdy blade");
      expect(item.item_type).toBe("weapon");
      expect(item.quantity).toBe(1);
      expect(item.properties.damage).toBe(10);
    });

    it("supports all item types", () => {
      const types: Item["item_type"][] = ["weapon", "armor", "consumable", "key", "misc"];
      expect(types).toHaveLength(5);
      expect(types).toContain("weapon");
      expect(types).toContain("armor");
      expect(types).toContain("consumable");
      expect(types).toContain("key");
      expect(types).toContain("misc");
    });
  });

  describe("Inventory", () => {
    it("has all required fields", () => {
      const inventory: Inventory = {
        items: [
          {
            id: "item-001",
            name: "Iron Sword",
            description: "A blade",
            item_type: "weapon",
            quantity: 1,
            properties: {},
          },
        ],
        equipment: { weapon: "item-001", armor: null },
        capacity: 20,
      };
      expect(inventory.items).toHaveLength(1);
      expect(inventory.items[0].name).toBe("Iron Sword");
      expect(inventory.equipment.weapon).toBe("item-001");
      expect(inventory.equipment.armor).toBeNull();
      expect(inventory.capacity).toBe(20);
    });

    it("allows null capacity", () => {
      const inventory: Inventory = {
        items: [],
        equipment: {},
        capacity: null,
      };
      expect(inventory.capacity).toBeNull();
    });
  });

  describe("Location", () => {
    it("has all required fields", () => {
      const location: Location = {
        id: "loc-001",
        name: "Town Square",
        description: "A bustling marketplace",
        connections: ["loc-002", "loc-003"],
        npcs_present: ["npc-001"],
        items_present: ["item-002"],
        visited: true,
      };
      expect(location.id).toBe("loc-001");
      expect(location.name).toBe("Town Square");
      expect(location.description).toBe("A bustling marketplace");
      expect(location.connections).toHaveLength(2);
      expect(location.npcs_present).toContain("npc-001");
      expect(location.items_present).toContain("item-002");
      expect(location.visited).toBe(true);
    });
  });

  describe("World", () => {
    it("has all required fields", () => {
      const world: World = {
        locations: {
          "loc-001": {
            id: "loc-001",
            name: "Town Square",
            description: "A bustling marketplace",
            connections: [],
            npcs_present: [],
            items_present: [],
            visited: true,
          },
        },
        current_location_id: "loc-001",
        discovered_locations: ["loc-001"],
        world_flags: { bridge_destroyed: true },
      };
      expect(world.locations["loc-001"].name).toBe("Town Square");
      expect(world.current_location_id).toBe("loc-001");
      expect(world.discovered_locations).toContain("loc-001");
      expect(world.world_flags.bridge_destroyed).toBe(true);
    });
  });

  describe("StoryBeat", () => {
    it("has all required fields matching Pydantic model", () => {
      const beat: StoryBeat = {
        summary: "The hero arrives at the village",
        location: "Village",
        trigger_conditions: ["enter_village"],
        key_elements: ["mysterious stranger"],
        player_objectives: ["talk to villagers"],
        possible_outcomes: ["learn about the quest"],
        flexibility: "flexible",
        status: "active",
      };
      expect(beat.summary).toBe("The hero arrives at the village");
      expect(beat.location).toBe("Village");
      expect(beat.trigger_conditions).toContain("enter_village");
      expect(beat.key_elements).toContain("mysterious stranger");
      expect(beat.player_objectives).toContain("talk to villagers");
      expect(beat.possible_outcomes).toContain("learn about the quest");
      expect(beat.flexibility).toBe("flexible");
      expect(beat.status).toBe("active");
    });

    it("supports all flexibility values", () => {
      const values: StoryBeat["flexibility"][] = ["fixed", "flexible", "optional"];
      expect(values).toHaveLength(3);
    });

    it("supports all status values", () => {
      const values: StoryBeat["status"][] = ["planned", "active", "resolved", "skipped", "adapted"];
      expect(values).toHaveLength(5);
    });
  });

  describe("StoryOutline", () => {
    it("has all required fields", () => {
      const outline: StoryOutline = {
        premise: "A quest to save the kingdom",
        setting: "Medieval fantasy",
        beats: [],
      };
      expect(outline.premise).toBe("A quest to save the kingdom");
      expect(outline.setting).toBe("Medieval fantasy");
      expect(outline.beats).toHaveLength(0);
    });
  });

  describe("StoryState", () => {
    it("has all required fields", () => {
      const storyState: StoryState = {
        outline: {
          premise: "Save the kingdom",
          setting: "Fantasy",
          beats: [],
        },
        active_beat_index: 0,
        summary: "The adventure begins",
        adaptations: [],
      };
      expect(storyState.outline?.premise).toBe("Save the kingdom");
      expect(storyState.active_beat_index).toBe(0);
      expect(storyState.summary).toBe("The adventure begins");
      expect(storyState.adaptations).toHaveLength(0);
    });

    it("allows null outline", () => {
      const storyState: StoryState = {
        outline: null,
        active_beat_index: 0,
        summary: "",
        adaptations: [],
      };
      expect(storyState.outline).toBeNull();
    });

    it("supports adaptation records", () => {
      const storyState: StoryState = {
        outline: null,
        active_beat_index: 0,
        summary: "",
        adaptations: [
          { reason: "Player went off-script", changes: "Added cave beat", timestamp: "2024-01-01T00:00:00Z" },
        ],
      };
      expect(storyState.adaptations).toHaveLength(1);
      expect(storyState.adaptations[0].reason).toBe("Player went off-script");
    });
  });

  describe("Message", () => {
    it("has all required fields", () => {
      const message: Message = {
        role: "player",
        content: "I go north",
        timestamp: "2024-01-01T00:00:00Z",
        metadata: {},
      };
      expect(message.role).toBe("player");
      expect(message.content).toBe("I go north");
      expect(message.timestamp).toBe("2024-01-01T00:00:00Z");
      expect(message.metadata).toEqual({});
    });

    it("supports all role values", () => {
      const roles: Message["role"][] = ["player", "agent", "system"];
      expect(roles).toHaveLength(3);
    });
  });

  describe("Conversation", () => {
    it("has all required fields", () => {
      const conversation: Conversation = {
        history: [],
        window_size: 20,
        summary: "",
      };
      expect(conversation.history).toHaveLength(0);
      expect(conversation.window_size).toBe(20);
      expect(conversation.summary).toBe("");
    });
  });

  describe("Session", () => {
    it("has all required fields matching Pydantic model", () => {
      const session: Session = {
        session_id: "sess-001",
        player_id: "player-001",
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T01:00:00Z",
        schema_version: 1,
        status: "active",
      };
      expect(session.session_id).toBe("sess-001");
      expect(session.player_id).toBe("player-001");
      expect(session.created_at).toBe("2024-01-01T00:00:00Z");
      expect(session.updated_at).toBe("2024-01-01T01:00:00Z");
      expect(session.schema_version).toBe(1);
      expect(session.status).toBe("active");
    });

    it("supports all status values", () => {
      const statuses: Session["status"][] = ["active", "paused", "completed", "abandoned"];
      expect(statuses).toHaveLength(4);
    });
  });

  describe("GameState", () => {
    it("has all top-level fields matching Pydantic GameState model", () => {
      const gameState: GameState = {
        session: {
          session_id: "sess-001",
          player_id: "player-001",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T01:00:00Z",
          schema_version: 1,
          status: "active",
        },
        character: {
          id: "char-001",
          name: "Aldric",
          profession: "Knight",
          background: "A soldier",
          stats: { health: 100 },
          status_effects: [],
          level: 1,
          experience: 0,
          location_id: "loc-001",
        },
        inventory: {
          items: [],
          equipment: {},
          capacity: null,
        },
        world: {
          locations: {},
          current_location_id: "loc-001",
          discovered_locations: [],
          world_flags: {},
        },
        story: {
          outline: { premise: "Quest", setting: "Fantasy", beats: [] },
          active_beat_index: 0,
          summary: "",
          adaptations: [],
        },
        conversation: {
          history: [],
          window_size: 20,
          summary: "",
        },
        recent_events: [],
      };
      expect(gameState.session.session_id).toBe("sess-001");
      expect(gameState.character.name).toBe("Aldric");
      expect(gameState.inventory.items).toHaveLength(0);
      expect(gameState.world.current_location_id).toBe("loc-001");
      expect(gameState.story.outline?.premise).toBe("Quest");
      expect(gameState.conversation.history).toHaveLength(0);
      expect(gameState.recent_events).toHaveLength(0);
    });
  });
});
