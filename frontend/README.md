# Agentic RPG - Frontend

Next.js 16 (React 19) frontend for the Agentic RPG game with TypeScript, Tailwind CSS v4, and comprehensive testing.

## Project Overview

This frontend application is built with the Next.js App Router architecture and designed to integrate with the FastAPI backend through a type-safe API client. It features a modern testing setup with both unit and end-to-end tests.

## Technology Stack

### Core Framework
- **Next.js 16.0.3** - React framework with App Router
- **React 19.2.0** - UI library with latest features
- **TypeScript 5** - Type safety across the codebase
- **Tailwind CSS 4** - Utility-first CSS framework

### State Management
- **Zustand 5.0.8** - Lightweight state management library

### Testing
- **Vitest 4.0.9** - Unit and component testing framework
- **@testing-library/react 16.3.0** - React testing utilities
- **@testing-library/jest-dom 6.9.1** - Custom jest matchers
- **Playwright 1.56.1** - End-to-end testing framework
- **jsdom 27.2.0** - DOM implementation for Node.js

### Type Generation
- **openapi-typescript 7.10.1** - Generate TypeScript types from OpenAPI specs
- **openapi-typescript-codegen 0.29.0** - Generate API client code

## Project Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── layout.tsx             # Root layout component
│   ├── page.tsx               # Home page
│   ├── globals.css            # Global styles
│   └── __tests__/             # Page/layout tests
│       ├── layout.test.tsx
│       └── page.test.tsx
├── lib/                       # Core utilities and API
│   ├── api/
│   │   ├── client.ts         # API client implementation
│   │   └── client.test.ts    # API client tests
│   ├── config.ts             # Application configuration
│   └── config.test.ts        # Config tests
├── scripts/
│   └── generate-types.sh     # OpenAPI type generation script
├── public/                    # Static assets
├── e2e/                      # Playwright E2E tests (to be added)
├── vitest.config.ts          # Vitest configuration
├── vitest.setup.ts           # Test setup file
├── playwright.config.ts      # Playwright configuration
├── next.config.ts            # Next.js configuration
├── tsconfig.json             # TypeScript configuration
└── package.json              # Dependencies and scripts
```

## Getting Started

### Prerequisites

- Node.js 20+ (specified in package.json)
- npm or yarn
- Running backend server at `http://localhost:8000` (for type generation)

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Available Scripts

#### Development
```bash
npm run dev          # Start development server (localhost:3000)
npm run build        # Build for production
npm run start        # Start production server
```

#### Code Quality
```bash
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler checks
```

#### Testing
```bash
npm run test         # Run unit tests with Vitest
npm run test:e2e     # Run end-to-end tests with Playwright
```

#### Type Generation
```bash
npm run generate-types  # Generate TypeScript types from backend OpenAPI spec
```

This requires the backend server to be running at `http://localhost:8000`.

## Configuration

### Environment Variables

Create a `.env.local` file for local development:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Application Configuration

The application configuration is centralized in `lib/config.ts`:

```typescript
const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
    timeout: 30000,
    version: 'v1',
  },
  game: {
    maxMessageLength: 500,
    autosaveInterval: 60000,
    maxHistoryMessages: 100,
  },
  ui: {
    enableAnimations: true,
    theme: 'dark',
    debugMode: process.env.NODE_ENV === 'development',
  },
} as const;
```

## API Client

The `GameAPIClient` class provides type-safe methods for interacting with the backend API.

### Basic Usage

```typescript
import { apiClient } from '@/lib/api/client';

// Health check
const health = await apiClient.healthCheck();
console.log(health); // { status: "ok", timestamp: "2024-11-15T..." }
```

### Client Configuration

The client uses the configuration from `lib/config.ts` by default, but can be instantiated with a custom base URL:

```typescript
import { GameAPIClient } from '@/lib/api/client';

const customClient = new GameAPIClient('https://api.example.com');
```

## Testing

The project includes comprehensive testing infrastructure:

### Unit Testing with Vitest

- **Framework**: Vitest with React plugin
- **Environment**: jsdom for DOM simulation
- **Location**: Tests are co-located with source files using `*.test.ts` or `*.test.tsx` naming
- **Coverage**: 31 total tests covering configuration, API client, and components

Run unit tests:
```bash
npm run test
```

#### Test Structure

```typescript
// lib/api/client.test.ts
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { GameAPIClient } from './client';

describe('GameAPIClient', () => {
  it('should make health check request', async () => {
    // Test implementation
  });
});
```

### End-to-End Testing with Playwright

- **Framework**: Playwright
- **Browsers**: Chromium, Firefox, WebKit
- **Configuration**: Located in `playwright.config.ts`
- **Auto-start**: Dev server automatically starts for tests

Run E2E tests:
```bash
npm run test:e2e
```

Playwright will:
1. Start the Next.js dev server
2. Run tests across all configured browsers
3. Generate HTML report on failures

## Type Safety

### Generated Types

Types are automatically generated from the backend's OpenAPI specification:

```bash
npm run generate-types
```

This script:
1. Checks if backend is running
2. Fetches OpenAPI spec from `http://localhost:8000/openapi.json`
3. Generates TypeScript types in `lib/api/generated/schema.ts`
4. Generates API client in `lib/api/generated/client/`

### Type-Safe Development

All API interactions are type-safe:

```typescript
import type { GameState, Character } from '@/lib/api/generated/schema';

// TypeScript ensures you're using the correct types
const character: Character = {
  id: "char_123",
  name: "Hero",
  // ... other required fields
};
```

## Development Workflow

### TDD Approach

Following project guidelines, always write tests first:

1. **Write failing test**
   ```bash
   # Create test file
   touch lib/api/new-feature.test.ts

   # Write test and watch it fail
   npm run test
   ```

2. **Implement feature**
   ```bash
   # Create implementation
   touch lib/api/new-feature.ts

   # Watch tests pass
   npm run test
   ```

3. **Verify quality**
   ```bash
   npm run lint
   npm run type-check
   npm run test
   ```

### Before Committing

Run all checks:
```bash
npm run lint && npm run type-check && npm run test && npm run build
```

## Integration with Backend

### API Contract

The frontend expects the backend to expose:

- **Health Check**: `GET /api/health/`
  ```json
  { "status": "ok", "timestamp": "2024-11-15T..." }
  ```

- **OpenAPI Spec**: `GET /openapi.json`
  - Used for automatic type generation
  - Must be valid JSON
  - Should follow OpenAPI 3.0+ specification

### Type Synchronization

To keep types in sync:

1. Start backend server: `cd ../backend && poetry run poe dev`
2. Generate types: `npm run generate-types`
3. Review generated files in `lib/api/generated/`
4. Update imports in your code if needed

## Troubleshooting

### Type Generation Fails

**Error**: `Backend is not running`

**Solution**: Ensure backend is running:
```bash
cd ../backend
poetry run poe dev
# Backend should start at http://localhost:8000
```

### Build Errors

**Error**: `Type error: Cannot find module '@/lib/api/generated/schema'`

**Solution**: Generate types from backend:
```bash
npm run generate-types
```

### Test Failures

**Error**: `ECONNREFUSED` during E2E tests

**Solution**: Playwright will auto-start dev server. Ensure port 3000 is available:
```bash
lsof -ti:3000 | xargs kill -9  # Kill any process on port 3000
npm run test:e2e
```

## Next Steps

This Phase 6 setup provides the foundation for:

- **Phase 7**: Character creation UI and state management
- **Phase 8**: Chat interface and real-time messaging
- **Phase 9**: WebSocket integration for live updates
- **Phase 10**: Game system UIs (inventory, location, combat)

## Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React 19 Documentation](https://react.dev)
- [Tailwind CSS v4 Documentation](https://tailwindcss.com/docs)
- [Vitest Documentation](https://vitest.dev)
- [Playwright Documentation](https://playwright.dev)
- [Zustand Documentation](https://zustand.docs.pmnd.rs)

## Team Ownership

- **Owner**: @team-frontend
- **Code Path**: `/frontend/`
- **Related Teams**: @team-api (for API contract), @team-core (for type generation)

For questions or issues, refer to the main project PRD.md and CLAUDE.md for development guidelines.
