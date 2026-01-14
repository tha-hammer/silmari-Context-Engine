# Phase 2: Markdown Content Retrieval and Rendering

## Overview

Extend `DocsService` with a `getDocument()` method that retrieves a specific markdown file by category and slug, parses frontmatter, and renders markdown content to HTML with syntax highlighting.

**Human-Testable Function**: `DocsService.getDocument(category, slug)` returns rendered HTML with metadata.

## Dependencies

- **Requires**: Phase 1 (Discovery Service) - uses shared `DocsService` class
- **Blocks**: Phase 4 (Document Route)

## Changes Required

### Modified Files

| File | Lines | Purpose |
|------|-------|---------|
| `server/src/services/docs.service.ts:50-100` | Add getDocument method |
| `server/src/services/__tests__/docs.service.test.ts:50-100` | Add getDocument tests |

### New Dependencies
```bash
npm install marked marked-highlight highlight.js
npm install -D @types/marked
```

### Test Specification

**Given**: A documentation file exists at `delta-first/docs/concepts/overview.md`
**When**: Requesting the document content for `concepts/overview`
**Then**: Returns the markdown content rendered as HTML

**Edge Cases**:
- File not found returns null
- Malformed markdown still renders
- Frontmatter stripped from output
- Path traversal attempts blocked

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

  it('should block path traversal attempts', async () => {
    const service = new DocsService(path.join(__dirname, '../../../delta-first/docs'));

    const result = await service.getDocument('..', 'passwd');

    expect(result).toBeNull();
  });
});
```

#### 🟢 Green: Minimal Implementation
**File**: `server/src/services/docs.service.ts` (add to existing class)
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

#### 🔵 Refactor: Add Security and Syntax Highlighting
**File**: `server/src/services/docs.service.ts` (enhanced version)
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

## Success Criteria

### Automated
- [ ] Test fails initially (Red): `npm test -- docs.service.test.ts`
- [ ] Test passes after implementation (Green): `npm test -- docs.service.test.ts`
- [ ] All tests pass after refactor: `npm test`
- [ ] No path traversal vulnerabilities

### Manual
- [ ] Markdown renders correctly with formatting
- [ ] Code blocks have syntax highlighting
- [ ] Frontmatter not visible in output
- [ ] Returns null for non-existent files

### Verification Command
```bash
cd server && npm test -- docs.service.test.ts --verbose
```
