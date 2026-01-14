# Phase 6: CSS Styling

## Overview

Add CSS styling for documentation pages including base styles, code syntax highlighting, and responsive layout. Ensure static CSS files are served correctly and referenced in templates.

**Human-Testable Function**: Documentation pages display with proper styling, readable typography, syntax highlighting, and responsive layout.

## Dependencies

- **Requires**: Phase 5 (Server Integration) - static file serving must work
- **Blocks**: None (final phase)

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `server/src/public/css/docs.css:1-100` | Base documentation styles |
| `server/src/public/css/highlight.css:1-50` | Syntax highlighting theme |

### Modified Files

| File | Lines | Purpose |
|------|-------|---------|
| `server/src/routes/__tests__/docs.routes.test.ts:100-120` | Add CSS serving tests |

### Test Specification

**Given**: Documentation pages are rendered
**When**: CSS files are requested
**Then**: Proper styling is applied for readability

**Edge Cases**:
- CSS file not found returns 404
- Syntax highlighting styles load correctly
- Styles don't break on mobile

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

  it('should serve highlight.css file', async () => {
    const response = await request(app).get('/css/highlight.css');
    expect(response.status).toBe(200);
    expect(response.headers['content-type']).toMatch(/text\/css/);
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

#### 🔵 Refactor: Add Responsive Styles
**File**: `server/src/public/css/docs.css` (enhanced version)
```css
/* Documentation Base Styles */
:root {
  --color-primary: #0066cc;
  --color-text: #333;
  --color-text-muted: #666;
  --color-bg: #fff;
  --color-bg-secondary: #f5f5f5;
  --color-border: #ddd;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'Fira Code', 'Monaco', 'Consolas', monospace;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: var(--font-sans);
  color: var(--color-text);
  background: var(--color-bg);
}

.docs-index,
.docs-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  line-height: 1.6;
}

/* Navigation */
.docs-nav {
  padding: 1rem 2rem;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
}

.docs-nav a {
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color 0.2s;
}

.docs-nav a:hover {
  color: var(--color-primary);
}

/* Index Page */
.docs-section {
  margin-bottom: 2rem;
}

.docs-section h2 {
  color: var(--color-text);
  border-bottom: 2px solid var(--color-border);
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.docs-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.docs-list li {
  margin: 0.5rem 0;
}

.docs-list a {
  color: var(--color-primary);
  text-decoration: none;
  padding: 0.25rem 0;
  display: inline-block;
}

.docs-list a:hover {
  text-decoration: underline;
}

/* Document Page */
.docs-meta {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.docs-meta .category {
  text-transform: capitalize;
  background: var(--color-bg-secondary);
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
}

.docs-body {
  margin-top: 2rem;
}

.docs-body h1,
.docs-body h2,
.docs-body h3,
.docs-body h4 {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.docs-body p {
  margin: 1em 0;
}

.docs-body ul,
.docs-body ol {
  padding-left: 1.5em;
}

.docs-body pre {
  background: #f8f8f8;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  margin: 1em 0;
}

.docs-body code {
  font-family: var(--font-mono);
  font-size: 0.9em;
}

.docs-body p code,
.docs-body li code {
  background: var(--color-bg-secondary);
  padding: 0.1em 0.3em;
  border-radius: 3px;
}

.docs-body blockquote {
  border-left: 4px solid var(--color-border);
  margin: 1em 0;
  padding-left: 1em;
  color: var(--color-text-muted);
}

.docs-body table {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

.docs-body th,
.docs-body td {
  border: 1px solid var(--color-border);
  padding: 0.5rem;
  text-align: left;
}

.docs-body th {
  background: var(--color-bg-secondary);
}

/* Responsive */
@media (max-width: 768px) {
  .docs-index,
  .docs-content {
    padding: 1rem;
  }

  .docs-nav {
    padding: 1rem;
  }

  .docs-body pre {
    padding: 0.75rem;
    font-size: 0.85em;
  }
}
```

## Success Criteria

### Automated
- [x] CSS file tests pass: `npm test -- docs.routes.test.ts`
- [x] Static files served with correct content-type
- [x] All tests pass: `npm test` (31 passing)

### Manual
- [ ] Documentation pages are visually readable
- [ ] Code blocks have syntax highlighting with colors
- [ ] Navigation is clear and accessible
- [ ] Mobile responsive - content readable on phone width
- [ ] Tables render with proper borders
- [ ] Blockquotes have visual distinction

### Verification Commands
```bash
# Run styling tests
cd server && npm test -- docs.routes.test.ts --verbose

# Manual verification
cd server && npm run dev
# Visit http://localhost:3000/docs in browser
# Resize browser window to test responsive layout
```

### Visual Checklist
- [ ] Headings have proper hierarchy
- [ ] Links are visible and clickable
- [ ] Code has monospace font
- [ ] Inline code has background highlight
- [ ] Pre blocks have horizontal scroll on overflow
- [ ] Category badges have subtle styling
- [ ] Back navigation is visible
