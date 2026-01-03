# Phase 3: Index Route

## Overview

Create an Express route handler for `GET /docs` that uses `DocsService.getDocumentationIndex()` to render an EJS template displaying all 29 documentation files organized by category sections with links to individual documents.

**Human-Testable Function**: `GET /docs` returns HTML page with organized documentation sections and links.

## Dependencies

- **Requires**: Phase 1 (Discovery Service) - uses `getDocumentationIndex()`
- **Blocks**: Phase 5 (Server Integration)

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `server/src/routes/docs.routes.ts:1-30` | Express router with index route |
| `server/src/routes/__tests__/docs.routes.test.ts:1-50` | Route integration tests |
| `server/src/views/docs/index.ejs:1-40` | EJS template for index page |

### Test Specification

**Given**: The Express server is running with docs route
**When**: GET request to `/docs`
**Then**: Returns 200 with HTML page containing organized documentation sections

**Edge Cases**:
- Empty docs directory returns empty sections
- Server error returns 500

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `server/src/routes/__tests__/docs.routes.test.ts`
```typescript
import request from 'supertest';
import express from 'express';
import path from 'path';
import { docsRouter } from '../docs.routes';

describe('GET /docs', () => {
  let app: express.Application;

  beforeAll(() => {
    app = express();
    app.set('view engine', 'ejs');
    app.set('views', path.join(__dirname, '../../views'));
    app.use('/docs', docsRouter);
  });

  it('should return 200 status', async () => {
    const response = await request(app).get('/docs');
    expect(response.status).toBe(200);
  });

  it('should return HTML content type', async () => {
    const response = await request(app).get('/docs');
    expect(response.headers['content-type']).toMatch(/text\/html/);
  });

  it('should contain documentation sections', async () => {
    const response = await request(app).get('/docs');
    expect(response.text).toContain('Documentation');
    expect(response.text).toContain('Concepts');
    expect(response.text).toContain('Architecture');
  });

  it('should contain links to individual documents', async () => {
    const response = await request(app).get('/docs');
    expect(response.text).toMatch(/href="\/docs\/concepts\/[^"]+"/);
  });
});
```

#### 🟢 Green: Minimal Implementation
**File**: `server/src/routes/docs.routes.ts`
```typescript
import { Router } from 'express';
import { DocsService } from '../services/docs.service';
import path from 'path';

export const docsRouter = Router();

const docsService = new DocsService(
  path.join(__dirname, '../../../delta-first/docs')
);

docsRouter.get('/', async (req, res) => {
  try {
    const index = await docsService.getDocumentationIndex();
    res.render('docs/index', {
      title: 'Documentation',
      sections: index.sections
    });
  } catch (error) {
    res.status(500).render('error', { message: 'Failed to load documentation' });
  }
});
```

**File**: `server/src/views/docs/index.ejs`
```ejs
<!DOCTYPE html>
<html>
<head>
  <title><%= title %></title>
  <link rel="stylesheet" href="/css/docs.css">
</head>
<body>
  <main class="docs-index">
    <h1><%= title %></h1>

    <% sections.forEach(section => { %>
      <section class="docs-section">
        <h2><%= section.name %></h2>
        <ul class="docs-list">
          <% section.documents.forEach(doc => { %>
            <li>
              <a href="/docs/<%= doc.category %>/<%= doc.slug %>">
                <%= doc.title %>
              </a>
            </li>
          <% }); %>
        </ul>
      </section>
    <% }); %>
  </main>
</body>
</html>
```

#### 🔵 Refactor: Add Error Handling Wrapper
**File**: `server/src/routes/docs.routes.ts`
```typescript
import { Router, Request, Response, NextFunction } from 'express';
import { DocsService } from '../services/docs.service';
import path from 'path';

export const docsRouter = Router();

const docsService = new DocsService(
  path.join(__dirname, '../../../delta-first/docs')
);

// Async error handler wrapper
const asyncHandler = (fn: (req: Request, res: Response, next: NextFunction) => Promise<void>) =>
  (req: Request, res: Response, next: NextFunction) =>
    Promise.resolve(fn(req, res, next)).catch(next);

docsRouter.get('/', asyncHandler(async (req, res) => {
  const index = await docsService.getDocumentationIndex();
  res.render('docs/index', {
    title: 'Documentation',
    sections: index.sections,
    breadcrumbs: [{ name: 'Docs', path: '/docs' }]
  });
}));
```

## Success Criteria

### Automated
- [ ] Test fails initially (Red): `npm test -- docs.routes.test.ts`
- [ ] Test passes after implementation (Green): `npm test -- docs.routes.test.ts`
- [ ] All tests pass after refactor: `npm test`

### Manual
- [ ] Page displays all 5 sections (Architecture, Concepts, Development, Getting Started, Reference)
- [ ] All 29 documents appear as links
- [ ] Links are properly formatted (`/docs/category/slug`)
- [ ] Page renders without errors

### Verification Command
```bash
cd server && npm test -- docs.routes.test.ts --verbose
```
