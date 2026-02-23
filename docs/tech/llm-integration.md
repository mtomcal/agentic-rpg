# Technology Choice: Direct LLM API Integration

## Decision

Call LLM APIs (Anthropic Claude, OpenAI) directly using their HTTP APIs. No LLM frameworks.

## Rationale

- **Learning goal**: This project exists to learn custom agent development. Frameworks hide the mechanics. Direct API calls expose everything.
- **Transparency**: Every prompt, every tool call, every response is visible and debuggable. No framework magic.
- **Simplicity**: The agent loop is a simple loop (send message → get response → execute tools → repeat). A framework adds complexity without proportional value for a single-agent system.
- **Control**: We decide exactly how context is assembled, how tools are formatted, how streaming works, and how errors are handled.
- **No lock-in**: Switching LLM providers means changing one HTTP client, not migrating an entire framework.

## LLM API Client

A thin Go client that wraps the LLM provider's HTTP API:

### Responsibilities

- Send messages with tools to the LLM API
- Parse responses (text content, tool calls, or both)
- Handle streaming responses (SSE for Anthropic, SSE for OpenAI)
- Retry on transient errors (429, 500, 503) with exponential backoff
- Track token usage for cost monitoring
- Support multiple providers behind a common interface

### Interface

```
LLMClient interface:
  SendMessage(request) → response
  SendMessageStream(request) → stream of chunks
```

The request includes:
- System prompt
- Messages (conversation history)
- Tools (name, description, parameter schema)
- Model selection
- Temperature and other parameters

The response includes:
- Content blocks (text and/or tool calls)
- Token usage (input, output)
- Stop reason (end_turn, tool_use, max_tokens)

### Provider Abstraction

A common interface with provider-specific implementations:

- `AnthropicClient` — Calls the Anthropic Messages API
- `OpenAIClient` — Calls the OpenAI Chat Completions API (future)

The agent system programs against the interface, not the implementation. Switching providers is a configuration change.

## Tool Use Format

Tools are sent to the LLM in the provider's native format:

**Anthropic format:**
```json
{
  "name": "move_character",
  "description": "Move the player character to a connected location",
  "input_schema": {
    "type": "object",
    "properties": {
      "location_id": { "type": "string", "description": "ID of the target location" }
    },
    "required": ["location_id"]
  }
}
```

**OpenAI format:**
```json
{
  "type": "function",
  "function": {
    "name": "move_character",
    "description": "Move the player character to a connected location",
    "parameters": {
      "type": "object",
      "properties": {
        "location_id": { "type": "string", "description": "ID of the target location" }
      },
      "required": ["location_id"]
    }
  }
}
```

The tool registry provides tools in a neutral format. The LLM client translates to the provider's format.

## Streaming

Agent responses are streamed to the frontend via WebSocket. The flow:

1. Agent sends request to LLM with `stream: true`
2. LLM returns an SSE stream of chunks
3. Go client reads chunks, parsing text content and tool calls
4. Text chunks are forwarded to the WebSocket immediately (for typewriter effect)
5. Tool call chunks are accumulated until complete, then executed
6. After tool execution, the agent sends another request (with tool results) and continues streaming

## Cost and Token Management

- Log token usage for every LLM call (input tokens, output tokens, model, timestamp)
- Set a per-session token budget (configurable, with a sensible default)
- Warn the player when approaching the budget
- Hard stop at the budget limit

## Error Handling

- **Rate limiting (429)**: Retry with exponential backoff, up to 3 retries
- **Server errors (500, 503)**: Retry once, then return error to the agent
- **Timeout**: 60-second timeout on LLM calls. On timeout, return error to the agent.
- **Invalid response**: If the LLM returns unparseable JSON in a tool call, send the error back as a tool result and let it try again (up to 3 retries)
- **Content filtering**: If the LLM refuses a request, return the refusal text as the agent response

## Configuration

- **Provider**: Which LLM provider to use (anthropic, openai)
- **Model**: Which model (claude-sonnet-4-20250514, gpt-4o, etc.)
- **API key**: From environment variable (never in code or config files)
- **Temperature**: Default 0.7 for narrative, 0.2 for structured output (tool calls, outline generation)
- **Max tokens**: Per-request output token limit
- **Token budget**: Per-session total token budget

## Future Extensions

- **Multiple providers**: Fall back to a secondary provider if the primary is down
- **Model routing**: Use cheaper/faster models for simple tasks (inventory checks), expensive models for narrative
- **Prompt caching**: Cache system prompts and tool definitions for reduced token usage (Anthropic prompt caching)
- **Fine-tuning**: Use fine-tuned models for specific agent roles (combat narration, NPC dialogue)
