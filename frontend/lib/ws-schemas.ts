import { z } from "zod";

// --- Client -> Server ---

export const PlayerActionDataSchema = z.object({
  text: z.string().min(1),
});

export const PlayerActionMessageSchema = z.object({
  type: z.literal("player_action"),
  data: PlayerActionDataSchema,
  timestamp: z.string(),
});

// --- Server -> Client ---

export const ConnectedMessageSchema = z.object({
  type: z.literal("connected"),
  data: z.object({
    session_id: z.string(),
    game_state: z.record(z.string(), z.any()),
  }),
  timestamp: z.string(),
});

export const AgentResponseMessageSchema = z.object({
  type: z.literal("agent_response"),
  data: z.object({
    text: z.string(),
    is_complete: z.boolean(),
  }),
  timestamp: z.string(),
});

export const StateUpdateMessageSchema = z.object({
  type: z.literal("state_update"),
  data: z.object({
    event_type: z.string(),
    changes: z.record(z.string(), z.any()),
  }),
  timestamp: z.string(),
});

export const StateSnapshotMessageSchema = z.object({
  type: z.literal("state_snapshot"),
  data: z.object({
    game_state: z.record(z.string(), z.any()),
  }),
  timestamp: z.string(),
});

export const ErrorMessageSchema = z.object({
  type: z.literal("error"),
  data: z.object({
    code: z.string(),
    message: z.string(),
  }),
  timestamp: z.string(),
});

export const InboundMessageSchema = z.discriminatedUnion("type", [
  ConnectedMessageSchema,
  AgentResponseMessageSchema,
  StateUpdateMessageSchema,
  StateSnapshotMessageSchema,
  ErrorMessageSchema,
]);

// --- Inferred types ---
export type PlayerActionMessage = z.infer<typeof PlayerActionMessageSchema>;
export type ConnectedMessage = z.infer<typeof ConnectedMessageSchema>;
export type AgentResponseMessage = z.infer<typeof AgentResponseMessageSchema>;
export type StateUpdateMessage = z.infer<typeof StateUpdateMessageSchema>;
export type StateSnapshotMessage = z.infer<typeof StateSnapshotMessageSchema>;
export type ErrorMessage = z.infer<typeof ErrorMessageSchema>;
export type InboundMessage = z.infer<typeof InboundMessageSchema>;
