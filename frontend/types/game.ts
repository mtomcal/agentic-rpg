/** Status effect on a character (buff, debuff, condition). */
export interface StatusEffect {
  name: string;
  effect_type: "buff" | "debuff" | "condition";
  duration: number | null;
  magnitude: number;
  description: string;
}

/** Record of a story adaptation. */
export interface AdaptationRecord {
  reason: string;
  changes: string;
  timestamp: string;
}

/** Player character. Matches backend Character Pydantic model. */
export interface Character {
  id: string;
  name: string;
  profession: string;
  background: string;
  stats: Record<string, number>;
  status_effects: StatusEffect[];
  level: number;
  experience: number;
  location_id: string;
}

/** An item in the game world or inventory. */
export interface Item {
  id: string;
  name: string;
  description: string;
  item_type: "weapon" | "armor" | "consumable" | "key" | "misc";
  quantity: number;
  properties: Record<string, any>;
}

/** Character inventory — items and equipment. */
export interface Inventory {
  items: Item[];
  equipment: Record<string, string | null>;
  capacity: number | null;
}

/** A location in the game world. */
export interface Location {
  id: string;
  name: string;
  description: string;
  connections: string[];
  npcs_present: string[];
  items_present: string[];
  visited: boolean;
}

/** World state — locations and flags. */
export interface World {
  locations: Record<string, Location>;
  current_location_id: string;
  discovered_locations: string[];
  world_flags: Record<string, any>;
}

/** A single story beat in the narrative outline. */
export interface StoryBeat {
  summary: string;
  location: string;
  trigger_conditions: string[];
  key_elements: string[];
  player_objectives: string[];
  possible_outcomes: string[];
  flexibility: "fixed" | "flexible" | "optional";
  status: "planned" | "active" | "resolved" | "skipped" | "adapted";
}

/** The overall story outline generated at session start. */
export interface StoryOutline {
  premise: string;
  setting: string;
  beats: StoryBeat[];
}

/** Story progression state. */
export interface StoryState {
  outline: StoryOutline | null;
  active_beat_index: number;
  summary: string;
  adaptations: AdaptationRecord[];
}

/** A single message in the conversation history. */
export interface Message {
  role: "player" | "agent" | "system";
  content: string;
  timestamp: string;
  metadata: Record<string, any>;
}

/** Conversation history with windowing. */
export interface Conversation {
  history: Message[];
  window_size: number;
  summary: string;
}

/** Game session metadata. */
export interface Session {
  session_id: string;
  player_id: string;
  created_at: string;
  updated_at: string;
  schema_version: number;
  status: "active" | "paused" | "completed" | "abandoned";
}

/** Top-level game state. Matches backend GameState Pydantic model. */
export interface GameState {
  session: Session;
  character: Character;
  inventory: Inventory;
  world: World;
  story: StoryState;
  conversation: Conversation;
  recent_events: any[];
}
