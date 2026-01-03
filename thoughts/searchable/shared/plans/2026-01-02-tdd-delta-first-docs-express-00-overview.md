# Delta-First Documentation Express Integration - TDD Implementation Plan

## Overview

Implement a documentation-first development workflow for the Express TypeScript server that converts 29 Delta-First documentation entries into a navigable documentation system. The system renders markdown files dynamically through an Express route, with an index page linking to individual documentation pages organized into sections/subsections.

**Installation Directory**
/home/maceo/Dev/Cosmic-intranet/express-js-on-vercel/server

**Key Behaviors:**
1. Index page displays all 29 docs organized by sections/subsections with links
2. Individual documentation pages render markdown dynamically
3. Navigation between docs via the index

## Implementation Progress

| Phase | Status | Date | Notes |
|-------|--------|------|-------|
| Phase 1 | ✅ Complete | 2026-01-02 | DocsService implemented with 4 passing tests |
| Phase 2 | ✅ Complete | 2026-01-02 | getDocument method with syntax highlighting, 11 passing tests |
| Phase 3 | ✅ Complete | 2026-01-02 | Index route with EJS template, 4 passing tests (15 total) |
| Phase 4 | ✅ Complete | 2026-01-02 | Document route with show.ejs template, 6 new tests (21 total) |
| Phase 5 | ⏳ Pending | - | - |
| Phase 6 | ⏳ Pending | - | - |

## Phase Files

| Phase | Description | Human-Testable Function |
|-------|-------------|------------------------|
| [Phase 1](2026-01-02-tdd-delta-first-docs-express-01-discovery-service.md) | Documentation Discovery Service | `DocsService.getDocumentationIndex()` returns organized sections |
| [Phase 2](2026-01-02-tdd-delta-first-docs-express-02-markdown-rendering.md) | Markdown Content Retrieval | `DocsService.getDocument()` returns rendered HTML |
| [Phase 3](2026-01-02-tdd-delta-first-docs-express-03-index-route.md) | Index Route | `GET /docs` returns organized documentation page |
| [Phase 4](2026-01-02-tdd-delta-first-docs-express-04-document-route.md) | Individual Document Route | `GET /docs/:category/:slug` renders document |
| [Phase 5](2026-01-02-tdd-delta-first-docs-express-05-server-integration.md) | Server Integration | Full `/docs` routes work in running server |
| [Phase 6](2026-01-02-tdd-delta-first-docs-express-06-css-styling.md) | CSS Styling | Documentation pages styled and readable |

## Dependency Graph

```
Phase 1 (Discovery Service)
    ↓
Phase 2 (Markdown Rendering)
    ↓
Phase 3 (Index Route) ────┐
    ↓                     │
Phase 4 (Document Route) ←┘
    ↓
Phase 5 (Server Integration)
    ↓
Phase 6 (CSS Styling)
```

## Required Dependencies

```bash
npm install marked gray-matter marked-highlight highlight.js
npm install -D @types/marked
```

## File Structure

```
server/
├── src/
│   ├── index.ts                    # Add docs router
│   ├── services/
│   │   ├── docs.service.ts         # NEW
│   │   └── __tests__/
│   │       └── docs.service.test.ts # NEW
│   ├── routes/
│   │   ├── docs.routes.ts          # NEW
│   │   └── __tests__/
│   │       └── docs.routes.test.ts # NEW
│   ├── views/
│   │   └── docs/
│   │       ├── index.ejs           # NEW
│   │       └── show.ejs            # NEW
│   └── public/
│       └── css/
│           ├── docs.css            # NEW
│           └── highlight.css       # NEW
```

## References

- Research: `thoughts/searchable/shared/research/2026-01-02-delta-first-docs-express-integration.md`
- Express Server: `server/src/index.ts`
- Delta-First Docs: `delta-first/docs/`
- EJS Views: `server/src/views/`
