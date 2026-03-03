# Agentic RPG — Product Requirements Document

## Vision

A browser-based, single-player role-playing game where narrative, world state, and character interactions are dynamically generated and managed by LangChain-powered LLM agents orchestrated with LangGraph. The game is genre-agnostic — players can experience sci-fi, fantasy, space pirate, or any other setting. Multiple players can each run their own independent stories on the same server.

## Goals

- **Primary**: Build a working agentic RPG with persistent state, dynamic narrative generation, and meaningful player agency
- **Learning**: Deeply understand LangChain and LangGraph by building a real, complex agent system — tools, state graphs, streaming, and observability
- **Observability**: Integrate LangSmith for full tracing, debugging, and evaluation of agent behavior in production
- **Infrastructure**: Gain experience with PostgreSQL, Docker Compose, and Kubernetes deployment
- **Architecture**: Create a modular system where each subsystem is independently specified and testable

## Core Principles

### Design Principles

- **Player Agency**: The player should feel in control. The story adapts to their choices, not the other way around.
- **Narrative Coherence**: A loose story outline provides direction without railroading. The outline adapts when the player diverges.
- **Genre Agnostic**: The systems themselves know nothing about genre. Setting, tone, and theme come from prompts and configuration.
- **Single Agent First**: Start with one LangGraph agent that does everything via tools. Add specialized agents later only when complexity demands it.

### Technical Principles

- **Spec-Driven Development**: Stack-agnostic system specs define behavior. Technology choices are separate documents.
- **LangChain/LangGraph Integration**: Use LangChain for tool definitions and LLM interaction, LangGraph for agent workflow orchestration, and LangSmith for observability and tracing.
- **Pydantic Models as Source of Truth**: Pydantic v2 models define all data contracts. TypeScript types for the frontend are generated from them.
- **Event-Driven Communication**: Components communicate via an event bus with schema-validated events.
- **WebSocket Real-Time**: The client receives game updates in real-time over WebSockets.

## Non-Goals (For Now)

- Multiplayer (shared worlds between players)
- Voice input/output
- Mobile native clients

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
│     Python / FastAPI Server     │
│   (HTTP routes, WS hub, auth)   │
└──────┬───────────────┬──────────┘
       │               │
┌──────▼──────┐  ┌─────▼─────────┐
│  LangGraph  │  │  PostgreSQL   │
│   Agent     │  │  (state,      │
│  Engine     │  │   sessions,   │
│ (LangChain  │  │   events)     │
│  tools +    │  └───────────────┘
│  LangSmith  │
│  tracing)   │
└──────┬──────┘
       │
┌──────▼──────┐
│  Event Bus  │
│ (in-process │
│  pub/sub)   │
└─────────────┘
```

## Document Index

See [docs/README.md](README.md) for the full specification library and navigation guide.
