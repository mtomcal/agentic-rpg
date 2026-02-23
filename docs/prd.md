# Agentic RPG — Product Requirements Document

## Vision

A browser-based, single-player role-playing game where narrative, world state, and character interactions are dynamically generated and managed by LLM agents using direct API tool-use. The game is genre-agnostic — players can experience sci-fi, fantasy, space pirate, or any other setting. Multiple players can each run their own independent stories on the same server.

## Goals

- **Primary**: Build a working agentic RPG with persistent state, dynamic narrative generation, and meaningful player agency
- **Learning**: Deeply understand custom agent development by building against raw LLM APIs with tool use — no frameworks
- **Infrastructure**: Gain experience with PostgreSQL, Docker Compose, and Kubernetes deployment
- **Architecture**: Create a modular system where each subsystem is independently specified and testable

## Core Principles

### Design Principles

- **Player Agency**: The player should feel in control. The story adapts to their choices, not the other way around.
- **Narrative Coherence**: A loose story outline provides direction without railroading. The outline adapts when the player diverges.
- **Genre Agnostic**: The systems themselves know nothing about genre. Setting, tone, and theme come from prompts and configuration.
- **Single Agent First**: Start with one agent that does everything via tools. Add specialized agents later only when complexity demands it.

### Technical Principles

- **Spec-Driven Development**: Stack-agnostic system specs define behavior. Technology choices are separate documents.
- **Direct LLM Integration**: No abstraction frameworks (LangChain, LangGraph). Direct API calls with tool use for transparency and learning.
- **Shared Schema as Source of Truth**: JSON Schema defines all data contracts. Both server and client types are generated from it.
- **Event-Driven Communication**: Components communicate via an event bus with schema-validated events.
- **WebSocket Real-Time**: The client receives game updates in real-time over WebSockets.

## Non-Goals (For Now)

- Multiplayer (shared worlds between players)
- Voice input/output
- Mobile native clients
- LLM framework integration (LangChain, LangGraph, etc.)

## Target User

A single player in a browser who wants a dynamic, AI-driven narrative RPG experience. They pick a genre/setting, create a character, and play through a story that adapts to their choices.

## High-Level Architecture

```
┌─────────────────────────────────┐
│       Next.js Frontend          │
│    (TypeScript, WebSocket)      │
└──────────────┬──────────────────┘
               │ HTTP / WebSocket
┌──────────────▼──────────────────┐
│         Go API Server           │
│   (HTTP routes, WS hub, auth)   │
└──────┬───────────────┬──────────┘
       │               │
┌──────▼──────┐  ┌─────▼─────────┐
│   Agent     │  │  PostgreSQL   │
│   Engine    │  │  (state,      │
│ (LLM API + │  │   sessions,   │
│  tool use)  │  │   events)     │
└──────┬──────┘  └───────────────┘
       │
┌──────▼──────┐
│  Event Bus  │
│ (in-process │
│  pub/sub)   │
└─────────────┘
```

## Document Index

See [docs/README.md](README.md) for the full specification library and navigation guide.
