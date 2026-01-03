# Delta-First Documentation Express Integration TDD Implementation Plan

## Overview

Implement a documentation-first development workflow for the Express TypeScript server that converts 29 Delta-First documentation entries into a navigable documentation system. The system renders markdown files dynamically through an Express route, with an index page linking to individual documentation pages organized into sections/subsections.

**Key Behaviors:**
1. Index page displays all 29 docs organized by sections/subsections with links
2. Individual documentation pages render markdown dynamically
3. Navigation between docs via the index

## Current State Analysis

### Express Server Structure
- **Entry Point**: `server/src/index.ts:1-50` - Express app with middleware setup
- **Routes**: `server/src/routes/` - Modular route definitions
- **Static Files**: `server/src/public/` - Static asset serving configured
- **Views**: EJS templating available via `server/src/views/`

### Delta-First Documentation
- **Location**: `delta-first/docs/` - 29 markdown files
- **Categories**: Architecture (4), Concepts (6), Development (8), Getting Started (3), Reference (8)
- **Format**: Standard markdown with frontmatter metadata

### Key Discoveries:
- Express server uses EJS for templating: `server/src/index.ts:15`
- Static middleware configured: `server/src/index.ts:20`
- Route pattern: `server/src/routes/*.ts` with `Router()` exports
- No existing markdown rendering - need to add `marked` or similar
- Documentation files have consistent naming: `kebab-case.md`

## Desired End State

A `/docs` route in the Express server that:
1. `/docs` - Index page with all 29 docs organized into sections/subsections
2. `/docs/:category/:slug` - Individual doc pages rendering markdown dynamically

### Observable Behaviors:
1. **Index renders with sections**: Given docs exist, when visiting `/docs`, then see organized sections with links
2. **Doc page renders markdown**: Given a doc file exists, when visiting `/docs/concepts/overview`, then see rendered HTML
3. **404 for missing docs**: Given no file exists, when visiting `/docs/invalid/path`, then return 404
4. **Navigation works**: Given on a doc page, when clicking back to index, then return to organized index

## What We're NOT Doing

- Real-time documentation editing
- Documentation search functionality
- PDF export or other formats
- Documentation versioning
- Authentication/authorization for docs
- Caching layer (can be added later)

## Testing Strategy

- **Framework**: Jest with supertest for HTTP testing
- **Test Types**:
  - Unit: Markdown parsing, section organization logic
  - Integration: Express route handlers with supertest
  - E2E: Out of scope (manual browser verification)
- **Mocking**: Mock file system for unit tests, real files for integration

## Behavior 1: Documentation Discovery and Organization

### Test Specification
**Given**: Documentation files exist in `delta-first/docs/` with category subdirectories
**When**: The docs service scans for available documentation
**Then**: Returns organized structure with sections, subsections, titles, and paths

**Edge Cases**:
- Empty category directory
- File without frontmatter
- Nested subdirectories beyond category level

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `server/src/services/__tests__/docs.service.test.ts`
```typescript
import { DocsService } from '../docs.service';
import path from 'path';

describe('DocsService', () => {
  describe('getDocumentationIndex', () => {
    it('should return organized sections with document metadata', async () => {
      const service = new DocsService(path.join(__dirname, '../../../delta-first/docs'));

      const result = await service.getDocumentationIndex();

      expect(result.sections).toBeDefined();
      expect(Array.isArray(result.sections)).toBe(true);
      expect(result.sections.length).toBeGreaterThan(0);

      const section = result.sections[0];
      expect(section).toHaveProperty('name');
      expect(section).toHaveProperty('documents');
      expect(Array.isArray(section.documents)).toBe(true);
    });

    it('should include document title, slug, and category for each document', async () => {
      const service = new DocsService(path.join(__dirname, '../../../delta-first/docs'));

      const result = await service.getDocumentationIndex();

      const doc = result.sections[0].documents[0];
      expect(doc).toHaveProperty('title');
      expect(doc).toHaveProperty('slug');
      expect(doc).toHaveProperty('category');
      expect(typeof doc.title).toBe('string');
      expect(typeof doc.slug).toBe('string');
    });

    it('should organize 29 documents across sections', async () => {
      const service = new DocsService(path.join(__dirname, '../../../delta-first/docs'));

      const result = await service.getDocumentationIndex();

      const totalDocs = result.sections.reduce(
        (sum, section) => sum + section.documents.length,
        0
      );
      expect(totalDocs).toBe(29);
    });
  });
});
```

#### 🟢 Green: Minimal Implementation
**File**: `server/src/services/docs.service.ts`
```typescript
import fs from 'fs/promises';
import path from 'path';

export interface DocumentMeta {
  title: string;
  slug: string;
  category: string;
}

export interface DocumentSection {
  name: string;
  documents: DocumentMeta[];
}

export interface DocumentationIndex {
  sections: DocumentSection[];
}

export class DocsService {
  constructor(private docsPath: string) {}

  async getDocumentationIndex(): Promise<DocumentationIndex> {
    const sections: DocumentSection[] = [];

    const categories = await fs.readdir(this.docsPath, { withFileTypes: true });

    for (const category of categories) {
      if (!category.isDirectory()) continue;

      const categoryPath = path.join(this.docsPath, category.name);
      const files = await fs.readdir(categoryPath);

      const documents: DocumentMeta[] = [];

      for (const file of files) {
        if (!file.endsWith('.md')) continue;

        const slug = file.replace('.md', '');
        const title = this.slugToTitle(slug);

        documents.push({
          title,
          slug,
          category: category.name,
        });
      }

      if (documents.length > 0) {
        sections.push({
          name: this.slugToTitle(category.name),
          documents,
        });
      }
    }

    return { sections };
  }

  private slugToTitle(slug: string): string {
    return slug
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
}
```

#### 🔵 Refactor: Improve Code
**File**: `server/src/services/docs.service.ts`
```typescript
import fs from 'fs/promises';
import path from 'path';
import matter from 'gray-matter';

export interface DocumentMeta {
  title: string;
  slug: string;
  category: string;
  order?: number;
}

export interface DocumentSection {
  name: string;
  documents: DocumentMeta[];
}

export interface DocumentationIndex {
  sections: DocumentSection[];
}

export class DocsService {
  constructor(private docsPath: string) {}

  async getDocumentationIndex(): Promise<DocumentationIndex> {
    const categories = await this.getCategories();
    const sections = await Promise.all(
      categories.map(cat => this.buildSection(cat))
    );

    return {
      sections: sections
        .filter(s => s.documents.length > 0)
        .sort((a, b) => a.name.localeCompare(b.name))
    };
  }

  private async getCategories(): Promise<string[]> {
    const entries = await fs.readdir(this.docsPath, { withFileTypes: true });
    return entries
      .filter(e => e.isDirectory())
      .map(e => e.name);
  }

  private async buildSection(category: string): Promise<DocumentSection> {
    const categoryPath = path.join(this.docsPath, category);
    const files = await fs.readdir(categoryPath);

    const documents = await Promise.all(
      files
        .filter(f => f.endsWith('.md'))
        .map(f => this.extractDocMeta(category, f))
    );

    return {
      name: this.formatTitle(category),
      documents: documents.sort((a, b) =>
        (a.order ?? 999) - (b.order ?? 999) || a.title.localeCompare(b.title)
      ),
    };
  }

  private async extractDocMeta(category: string, filename: string): Promise<DocumentMeta> {
    const filePath = path.join(this.docsPath, category, filename);
    const content = await fs.readFile(filePath, 'utf-8');
    const { data } = matter(content);

    const slug = filename.replace('.md', '');

    return {
      title: data.title || this.formatTitle(slug),
      slug,
      category,
      order: data.order,
    };
  }

  private formatTitle(slug: string): string {
    return slug
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
}
```

### Success Criteria
**Automated:**
- [ ] Test fails initially (Red): `npm test -- docs.service.test.ts`
- [ ] Test passes after implementation (Green): `npm test -- docs.service.test.ts`
- [ ] All tests pass after refactor: `npm test`
- [ ] TypeScript compiles: `npm run build`

**Manual:**
- [ ] Service discovers all 29 documentation files
- [ ] Categories map correctly to sections
- [ ] Titles are human-readable

---

## Behavior 2: Markdown Content Retrieval and Rendering

### Test Specification
**Given**: A documentation file exists at `delta-first/docs/concepts/overview.md`
**When**: Requesting the document content for `concepts/overview`
**Then**: Returns the markdown content rendered as HTML

**Edge Cases**:
- File not found returns null/throws
- Malformed markdown still renders
- Frontmatter stripped from output

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `server/src/services/__tests__/docs.service.test.ts`
```typescript
describe('getDocument', () => {
  it('should return rendered HTML for valid document path', async () => {
    const service = new DocsService(path.join(__dirname, '../../../delta-first/docs'));

    const result = await service.getDocument('concepts', 'overview');

    expect(result).toBeDefined();
    expect(result?.html).toBeDefined();
    expect(result?.html).toContain('<'); // Contains HTML tags
    expect(result?.title).toBeDefined();
  });

  it('should return null for non-existent document', async () => {
    const service = new DocsService(path.join(__dirname, '../../../delta-first/docs'));

    const result = await service.getDocument('invalid', 'nonexistent');

    expect(result).toBeNull();
  });

  it('should strip frontmatter from rendered content', async () => {
    const service = new DocsService(path.join(__dirname, '../../../delta-first/docs'));

    const result = await service.getDocument('concepts', 'overview');

    expect(result?.html).not.toContain('---');
    expect(result?.html).not.toMatch(/^title:/m);
  });

  it('should include document metadata', async () => {
    const service = new DocsService(path.join(__dirname, '../../../delta-first/docs'));

    const result = await service.getDocument('concepts', 'overview');

    expect(result).toHaveProperty('title');
    expect(result).toHaveProperty('category');
    expect(result?.category).toBe('concepts');
  });
});
```

#### 🟢 Green: Minimal Implementation
**File**: `server/src/services/docs.service.ts`
```typescript
import { marked } from 'marked';

export interface DocumentContent {
  title: string;
  category: string;
  slug: string;
  html: string;
}

// Add to DocsService class:
async getDocument(category: string, slug: string): Promise<DocumentContent | null> {
  const filePath = path.join(this.docsPath, category, `${slug}.md`);

  try {
    const content = await fs.readFile(filePath, 'utf-8');
    const { data, content: markdown } = matter(content);

    const html = await marked(markdown);

    return {
      title: data.title || this.formatTitle(slug),
      category,
      slug,
      html,
    };
  } catch (error) {
    return null;
  }
}
```

#### 🔵 Refactor: Improve Code
**File**: `server/src/services/docs.service.ts`
```typescript
import { marked } from 'marked';
import { markedHighlight } from 'marked-highlight';
import hljs from 'highlight.js';

// Configure marked with syntax highlighting
marked.use(markedHighlight({
  langPrefix: 'hljs language-',
  highlight(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  }
}));

export interface DocumentContent {
  title: string;
  category: string;
  slug: string;
  html: string;
  description?: string;
  lastModified?: Date;
}

// Add to DocsService class:
async getDocument(category: string, slug: string): Promise<DocumentContent | null> {
  // Prevent path traversal attacks
  if (category.includes('..') || slug.includes('..')) {
    return null;
  }

  const filePath = path.join(this.docsPath, category, `${slug}.md`);

  try {
    const [content, stats] = await Promise.all([
      fs.readFile(filePath, 'utf-8'),
      fs.stat(filePath),
    ]);

    const { data, content: markdown } = matter(content);
    const html = await marked(markdown);

    return {
      title: data.title || this.formatTitle(slug),
      category,
      slug,
      html,
      description: data.description,
      lastModified: stats.mtime,
    };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      return null;
    }
    throw error;
  }
}
```

### Success Criteria
**Automated:**
- [ ] Test fails initially (Red): `npm test -- docs.service.test.ts`
- [ ] Test passes after implementation (Green): `npm test -- docs.service.test.ts`
- [ ] All tests pass after refactor: `npm test`
- [ ] No path traversal vulnerabilities

**Manual:**
- [ ] Markdown renders correctly with formatting
- [ ] Code blocks have syntax highlighting
- [ ] Frontmatter not visible in output

---

## Behavior 3: Index Route Returns Organized Documentation

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

#### 🔵 Refactor: Improve Code
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

### Success Criteria
**Automated:**
- [ ] Test fails initially (Red): `npm test -- docs.routes.test.ts`
- [ ] Test passes after implementation (Green): `npm test -- docs.routes.test.ts`
- [ ] All tests pass after refactor: `npm test`

**Manual:**
- [ ] Page displays all 5 sections (Architecture, Concepts, Development, Getting Started, Reference)
- [ ] All 29 documents appear as links
- [ ] Links are properly formatted

---

## Behavior 4: Individual Document Route Renders Markdown

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
**File**: `server/src/routes/docs.routes.ts`
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

#### 🔵 Refactor: Improve Code
**File**: `server/src/routes/docs.routes.ts`
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

### Success Criteria
**Automated:**
- [ ] Test fails initially (Red): `npm test -- docs.routes.test.ts`
- [ ] Test passes after implementation (Green): `npm test -- docs.routes.test.ts`
- [ ] All tests pass after refactor: `npm test`
- [ ] Path traversal tests pass

**Manual:**
- [ ] Document renders with proper formatting
- [ ] Code blocks have syntax highlighting
- [ ] Back link works
- [ ] 404 page displays for invalid paths

---

## Behavior 5: Server Integration

### Test Specification
**Given**: The Express server is configured
**When**: The docs router is mounted at `/docs`
**Then**: Documentation is accessible at `/docs` and `/docs/:category/:slug`

**Edge Cases**:
- Router conflicts with existing routes
- Middleware order affects rendering

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

#### 🔵 Refactor: Improve Code
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

// ... rest of existing routes

export { app };
```

### Success Criteria
**Automated:**
- [ ] Integration tests pass: `npm test -- integration.test.ts`
- [ ] All existing tests still pass: `npm test`
- [ ] Server starts without errors: `npm run dev`

**Manual:**
- [ ] Documentation accessible in browser at `/docs`
- [ ] Navigation between pages works
- [ ] No conflicts with existing routes

---

## Behavior 6: CSS Styling for Documentation

### Test Specification
**Given**: Documentation pages are rendered
**When**: CSS file is requested
**Then**: Proper styling is applied for readability

**Edge Cases**:
- CSS file not found returns 404
- Syntax highlighting styles load correctly

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `server/src/routes/__tests__/docs.routes.test.ts`
```typescript
describe('Documentation Styling', () => {
  it('should reference docs.css stylesheet', async () => {
    const response = await request(app).get('/docs');
    expect(response.text).toContain('href="/css/docs.css"');
  });

  it('should serve docs.css file', async () => {
    const response = await request(app).get('/css/docs.css');
    expect(response.status).toBe(200);
    expect(response.headers['content-type']).toMatch(/text\/css/);
  });

  it('should reference highlight.css for code blocks', async () => {
    const response = await request(app).get('/docs/concepts/overview');
    expect(response.text).toContain('href="/css/highlight.css"');
  });
});
```

#### 🟢 Green: Minimal Implementation
**File**: `server/src/public/css/docs.css`
```css
/* Documentation Base Styles */
.docs-index,
.docs-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
}

.docs-section {
  margin-bottom: 2rem;
}

.docs-section h2 {
  color: #333;
  border-bottom: 2px solid #eee;
  padding-bottom: 0.5rem;
}

.docs-list {
  list-style: none;
  padding: 0;
}

.docs-list li {
  margin: 0.5rem 0;
}

.docs-list a {
  color: #0066cc;
  text-decoration: none;
}

.docs-list a:hover {
  text-decoration: underline;
}

.docs-nav {
  padding: 1rem 2rem;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.docs-nav a {
  color: #666;
  text-decoration: none;
}

.docs-body {
  margin-top: 2rem;
}

.docs-body pre {
  background: #f8f8f8;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
}

.docs-body code {
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
}

.docs-meta {
  color: #666;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.docs-meta .category {
  text-transform: capitalize;
  background: #e8e8e8;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  margin-right: 1rem;
}
```

**File**: `server/src/public/css/highlight.css`
```css
/* Syntax highlighting - GitHub style */
.hljs {
  background: #f8f8f8;
  color: #333;
}

.hljs-comment,
.hljs-quote {
  color: #998;
  font-style: italic;
}

.hljs-keyword,
.hljs-selector-tag {
  color: #d73a49;
}

.hljs-string,
.hljs-attr {
  color: #032f62;
}

.hljs-number,
.hljs-literal {
  color: #005cc5;
}

.hljs-function .hljs-title {
  color: #6f42c1;
}

.hljs-built_in,
.hljs-builtin-name {
  color: #005cc5;
}
```

### Success Criteria
**Automated:**
- [ ] CSS file tests pass: `npm test -- docs.routes.test.ts`
- [ ] Static files served correctly

**Manual:**
- [ ] Documentation pages are visually readable
- [ ] Code blocks have syntax highlighting
- [ ] Navigation is clear and accessible
- [ ] Mobile responsive (basic)

---

## Dependencies and Installation

### Required npm packages:
```bash
npm install marked gray-matter marked-highlight highlight.js
npm install -D @types/marked
```

### File structure:
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

## Implementation Order

1. **Behavior 1**: Documentation Discovery - Foundation for all other behaviors
2. **Behavior 2**: Markdown Rendering - Core content functionality
3. **Behavior 3**: Index Route - Entry point for users
4. **Behavior 4**: Document Route - Individual page viewing
5. **Behavior 5**: Server Integration - Wire everything together
6. **Behavior 6**: CSS Styling - Polish and usability

## References

- Research: `thoughts/searchable/shared/research/2026-01-02-delta-first-docs-express-integration.md`
- Express Server: `server/src/index.ts`
- Delta-First Docs: `delta-first/docs/`
- EJS Views: `server/src/views/`
