# Phase 1: Documentation Discovery Service

## Overview

Create a `DocsService` class that scans the `delta-first/docs/` directory structure and returns an organized index of all 29 documentation files grouped by category/section.

**Human-Testable Function**: `DocsService.getDocumentationIndex()` returns organized sections with document metadata.

## Dependencies

- **Requires**: None (foundation phase)
- **Blocks**: Phase 2 (Markdown Rendering), Phase 3 (Index Route)

## Changes Required

### New Files

| File | Purpose |
|------|---------|
| `server/src/services/docs.service.ts:1-100` | DocsService class with getDocumentationIndex method |
| `server/src/services/__tests__/docs.service.test.ts:1-50` | Unit tests for discovery functionality |

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

#### 🔵 Refactor: Add Frontmatter Parsing
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

## Success Criteria

### Automated
- [x] Test fails initially (Red): `npm test -- docs.service.test.ts`
- [x] Test passes after implementation (Green): `npm test -- docs.service.test.ts`
- [x] All tests pass after refactor: `npm test`
- [x] TypeScript compiles: `npx tsc --noEmit`

### Manual
- [x] Service discovers all 29 documentation files
- [x] Categories map correctly to sections
- [x] Titles are human-readable

### Verification Command
```bash
cd /home/maceo/Dev/Cosmic-intranet/express-js-on-vercel && NODE_OPTIONS='--experimental-vm-modules' npx jest --config server/jest.config.js --verbose
```

## Implementation Notes (2026-01-02)

- Created `server/` directory structure within express-js-on-vercel project
- Used Jest with ts-jest ESM preset for testing
- DocsService handles both root-level docs and category subdirectories
- Root docs placed in "Overview" section, categories sorted alphabetically
- 4 tests passing: sections structure, doc metadata, 29 docs count, root docs inclusion
