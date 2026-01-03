# Phase 5: Server Integration

## Overview

Mount the docs router on the Express server at `/docs` and verify it works alongside existing routes without conflicts. Add integration tests to ensure the full request/response cycle works.

**Human-Testable Function**: Full `/docs` and `/docs/:category/:slug` routes work in running server alongside other routes.

## Dependencies

- **Requires**: Phase 3 (Index Route)
- **Requires**: Phase 4 (Document Route)
- **Blocks**: Phase 6 (CSS Styling)

## Changes Required

### Modified Files

| File | Lines | Purpose |
|------|-------|---------|
| `server/src/index.ts:1-50` | Mount docs router, configure views |

### New Files

| File | Purpose |
|------|---------|
| `server/src/__tests__/integration.test.ts:1-50` | Full integration tests |

### Test Specification

**Given**: The Express server is configured
**When**: The docs router is mounted at `/docs`
**Then**: Documentation is accessible at `/docs` and `/docs/:category/:slug`

**Edge Cases**:
- Router conflicts with existing routes
- Middleware order affects rendering
- Static files served correctly

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `server/src/__tests__/integration.test.ts`
```typescript
import request from 'supertest';
import { app } from '../index';

describe('Documentation Integration', () => {
  it('should serve documentation index at /docs', async () => {
    const response = await request(app).get('/docs');
    expect(response.status).toBe(200);
    expect(response.text).toContain('Documentation');
  });

  it('should serve individual docs at /docs/:category/:slug', async () => {
    const response = await request(app).get('/docs/concepts/overview');
    expect(response.status).toBe(200);
  });

  it('should not interfere with other routes', async () => {
    const response = await request(app).get('/api/health');
    expect(response.status).toBe(200);
  });

  it('should return 404 for non-existent docs', async () => {
    const response = await request(app).get('/docs/invalid/path');
    expect(response.status).toBe(404);
  });
});
```

#### 🟢 Green: Minimal Implementation
**File**: `server/src/index.ts`
```typescript
import express from 'express';
import path from 'path';
import { docsRouter } from './routes/docs.routes';

const app = express();

// View engine setup
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// Routes
app.use('/docs', docsRouter);

// ... rest of existing routes

export { app };
```

#### 🔵 Refactor: Environment-Configurable Paths
**File**: `server/src/index.ts`
```typescript
import express from 'express';
import path from 'path';
import { createDocsRouter } from './routes/docs.routes';

const app = express();

// View engine setup
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// Documentation route with configurable path
const docsPath = process.env.DOCS_PATH || path.join(__dirname, '../../delta-first/docs');
app.use('/docs', createDocsRouter(docsPath));

// Health check (ensure existing routes still work)
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

// ... rest of existing routes

// Error handling middleware
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error(err.stack);
  res.status(500).render('error', { message: 'Internal Server Error' });
});

export { app };
```

## Success Criteria

### Automated
- [x] Integration tests pass: `npm test -- integration.test.ts` (6 tests passing)
- [x] All existing tests still pass: `npm test` (27 tests total)
- [ ] Server starts without errors: `npm run dev`
- [x] TypeScript compiles: `npm run build`

### Manual
- [ ] Documentation accessible in browser at `http://localhost:3000/docs`
- [ ] Navigation between pages works
- [x] No conflicts with existing API routes (verified by integration tests)
- [x] Existing routes still function correctly (verified by integration tests)

### Verification Commands
```bash
# Run integration tests
cd server && npm test -- integration.test.ts --verbose

# Start server and test manually
cd server && npm run dev
# Then visit http://localhost:3000/docs in browser
```

### Environment Variables
```bash
# Optional: Configure custom docs path
DOCS_PATH=/path/to/docs npm run dev
```
