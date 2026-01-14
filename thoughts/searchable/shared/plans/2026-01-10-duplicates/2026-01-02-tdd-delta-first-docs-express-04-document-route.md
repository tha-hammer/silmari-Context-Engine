# Phase 4: Individual Document Route

## Overview

Add a route handler for `GET /docs/:category/:slug` that uses `DocsService.getDocument()` to render individual documentation pages with markdown converted to HTML, including navigation back to the index.

**Human-Testable Function**: `GET /docs/:category/:slug` renders document with HTML content and back navigation.

## Dependencies

- **Requires**: Phase 2 (Markdown Rendering) - uses `getDocument()`
- **Requires**: Phase 3 (Index Route) - shares router
- **Blocks**: Phase 5 (Server Integration)

## Changes Required

### Modified Files

| File | Lines | Purpose |
|------|-------|---------|
| `server/src/routes/docs.routes.ts:30-60` | Add document route handler |
| `server/src/routes/__tests__/docs.routes.test.ts:50-100` | Add document route tests |

### New Files

| File | Purpose |
|------|---------|
| `server/src/views/docs/show.ejs:1-40` | EJS template for document page |

### Test Specification

**Given**: A document exists at `concepts/overview.md`
**When**: GET request to `/docs/concepts/overview`
**Then**: Returns 200 with rendered markdown HTML

**Edge Cases**:
- Non-existent document returns 404
- Invalid category returns 404
- Path traversal attempt returns 404

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `server/src/routes/__tests__/docs.routes.test.ts`
```typescript
describe('GET /docs/:category/:slug', () => {
  it('should return 200 for valid document', async () => {
    const response = await request(app).get('/docs/concepts/overview');
    expect(response.status).toBe(200);
  });

  it('should return HTML content', async () => {
    const response = await request(app).get('/docs/concepts/overview');
    expect(response.headers['content-type']).toMatch(/text\/html/);
  });

  it('should contain the document title', async () => {
    const response = await request(app).get('/docs/concepts/overview');
    expect(response.text).toMatch(/<h1[^>]*>.*Overview/i);
  });

  it('should return 404 for non-existent document', async () => {
    const response = await request(app).get('/docs/invalid/nonexistent');
    expect(response.status).toBe(404);
  });

  it('should return 404 for path traversal attempts', async () => {
    const response = await request(app).get('/docs/../../../etc/passwd');
    expect(response.status).toBe(404);
  });

  it('should contain back link to index', async () => {
    const response = await request(app).get('/docs/concepts/overview');
    expect(response.text).toContain('href="/docs"');
  });
});
```

#### 🟢 Green: Minimal Implementation
**File**: `server/src/routes/docs.routes.ts` (add to existing router)
```typescript
docsRouter.get('/:category/:slug', asyncHandler(async (req, res) => {
  const { category, slug } = req.params;

  const doc = await docsService.getDocument(category, slug);

  if (!doc) {
    res.status(404).render('error', {
      message: 'Documentation not found',
      status: 404
    });
    return;
  }

  res.render('docs/show', {
    title: doc.title,
    doc,
    breadcrumbs: [
      { name: 'Docs', path: '/docs' },
      { name: doc.title, path: `/docs/${category}/${slug}` }
    ]
  });
}));
```

**File**: `server/src/views/docs/show.ejs`
```ejs
<!DOCTYPE html>
<html>
<head>
  <title><%= title %> - Documentation</title>
  <link rel="stylesheet" href="/css/docs.css">
  <link rel="stylesheet" href="/css/highlight.css">
</head>
<body>
  <nav class="docs-nav">
    <a href="/docs">&larr; Back to Documentation</a>
  </nav>

  <main class="docs-content">
    <article>
      <h1><%= doc.title %></h1>
      <div class="docs-meta">
        <span class="category"><%= doc.category %></span>
        <% if (doc.lastModified) { %>
          <span class="modified">Last updated: <%= doc.lastModified.toLocaleDateString() %></span>
        <% } %>
      </div>
      <div class="docs-body">
        <%- doc.html %>
      </div>
    </article>
  </main>
</body>
</html>
```

#### 🔵 Refactor: Factory Function for Testability
**File**: `server/src/routes/docs.routes.ts` (complete refactored version)
```typescript
import { Router, Request, Response, NextFunction } from 'express';
import { DocsService } from '../services/docs.service';
import path from 'path';

export const createDocsRouter = (docsPath?: string): Router => {
  const router = Router();
  const service = new DocsService(
    docsPath || path.join(__dirname, '../../../delta-first/docs')
  );

  const asyncHandler = (fn: (req: Request, res: Response, next: NextFunction) => Promise<void>) =>
    (req: Request, res: Response, next: NextFunction) =>
      Promise.resolve(fn(req, res, next)).catch(next);

  router.get('/', asyncHandler(async (req, res) => {
    const index = await service.getDocumentationIndex();
    res.render('docs/index', {
      title: 'Documentation',
      sections: index.sections,
      breadcrumbs: [{ name: 'Docs', path: '/docs' }]
    });
  }));

  router.get('/:category/:slug', asyncHandler(async (req, res) => {
    const { category, slug } = req.params;

    const doc = await service.getDocument(category, slug);

    if (!doc) {
      res.status(404).render('error', {
        message: 'Documentation not found',
        status: 404
      });
      return;
    }

    res.render('docs/show', {
      title: doc.title,
      doc,
      breadcrumbs: [
        { name: 'Docs', path: '/docs' },
        { name: doc.title, path: `/docs/${category}/${slug}` }
      ]
    });
  }));

  return router;
};

// Default export for backward compatibility
export const docsRouter = createDocsRouter();
```

## Success Criteria

### Automated
- [x] Test fails initially (Red): `npm test -- docs.routes.test.ts`
- [x] Test passes after implementation (Green): `npm test -- docs.routes.test.ts`
- [x] All tests pass after refactor: `npm test`
- [x] Path traversal tests pass

### Manual
- [ ] Document renders with proper formatting
- [ ] Code blocks have syntax highlighting
- [ ] Back link works and returns to index
- [ ] 404 page displays for invalid paths
- [ ] Category badge displays correctly

### Verification Command
```bash
cd server && npm test -- docs.routes.test.ts --verbose
```

## Implementation Notes (2026-01-02)

**Files Modified:**
- `server/src/routes/docs.routes.ts` - Added document route handler
- `server/src/routes/__tests__/docs.routes.test.ts` - Added 6 new tests
- `server/src/views/docs/show.ejs` - Created document template

**Files Created:**
- `jest.config.js` - Jest configuration for ESM support
- `package.json` - Added test script

**Files Updated:**
- `tsconfig.json` - Added `isolatedModules: true` for ts-jest compatibility

**Test Results:**
- 21 tests passing (11 service tests + 10 route tests)
- 6 new tests for document route (valid document, HTML content type, document title, 404 for non-existent, path traversal protection, back link)
