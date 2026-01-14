# TypeScript Port TDD Implementation Plan

## Overview

This plan outlines a comprehensive Test-Driven Development approach to port the **silmari-Context-Engine** from Python to TypeScript. The port covers **35 Python files (~13,000 lines)** across two core modules (planning_pipeline and context_window_array) plus root orchestrators, with **24 test files** providing complete behavioral specifications.

**Goal**: Create a production-ready TypeScript version of the Context Engine with 100% test coverage, real BAML API integration using local Ollama, and full feature parity with the Python implementation.

**Scope**: This repository only - no work in silmari-oracle-wui.

**Testing Strategy**: Red-Green-Refactor cycles for each behavior, real Ollama API calls for integration tests, comprehensive unit tests with mocks.

---

## Current State Analysis

### Python Codebase Structure

**Total Implementation**: 35 files, 12,988 lines

| Module | Files | Lines | Purpose |
|--------|-------|-------|---------|
| **planning_pipeline/** | 21 | 6,951 | TDD-based planning decomposition with 7-step pipeline |
| **context_window_array/** | 8 | 1,862 | Addressable dual-LLM context management |
| **Root orchestrators** | 6 | 4,175 | Entry points and autonomous loop runners |

### Key Discoveries

1. **BAML Integration** (`baml_src/`):
   - 30 BAML files (2,387 lines) defining LLM function calls
   - 23 schema files for structured responses
   - 13 generated Python client files (1.3 MB)
   - Version: baml-py 0.216.0
   - **Finding**: TypeScript BAML client (@baml/client) exists and should be used

2. **Test Coverage** (24 test files):
   - planning_pipeline: 18 test modules with mocks, property-based tests
   - context_window_array: 6 test modules covering CRUD, search, batching
   - pytest configuration: async support, markers (slow, integration, e2e)
   - **Finding**: Comprehensive test specifications exist as porting blueprint

3. **Dual-LLM Architecture** (context_window_array/):
   - CentralContextStore with ctx_XXXXX IDs
   - Working LLM sees summaries only
   - Implementation LLM sees full content (<200 entry bounds)
   - Vector search with TF-IDF + cosine similarity
   - **Finding**: Core pattern must be preserved exactly

4. **7-Step Planning Pipeline**:
   - Research → Memory Sync → Decomposition → Context Gen → Planning → Phase Decomp → Beads
   - Checkpoint recovery at any step
   - Interactive user prompts
   - BAML-based requirement decomposition
   - **Finding**: Sequential pipeline with state management

5. **Existing TypeScript Patterns** (from thoughts/):
   - Rust port documentation shows TypeScript orchestrator in silmari-oracle-wui
   - Express TypeScript patterns with Jest/ts-jest
   - Service classes with async/await
   - **Finding**: TypeScript patterns already established in related projects

### Constraints & Requirements

1. **No Cross-Repository Work**: Stay in silmari-Context-Engine only
2. **Real API Calls**: Use local Ollama for integration tests (no mocks for integration)
3. **100% Test Coverage**: Every behavior must have tests
4. **Feature Parity**: All Python functionality must be ported
5. **Modern TypeScript**: Strict mode, ESNext, type safety with Zod
6. **Follow Order**: Complete all 7 phases sequentially

---

## Desired End State

### TypeScript Project Structure

```
silmari-Context-Engine/
├── src/
│   ├── context/
│   │   ├── models.ts                 # ContextEntry, EntryType
│   │   ├── store.ts                  # CentralContextStore
│   │   ├── search.ts                 # VectorSearchIndex
│   │   ├── batching.ts               # TaskBatcher
│   │   ├── working-context.ts        # WorkingLLMContext
│   │   └── implementation-context.ts # ImplementationLLMContext
│   ├── planning/
│   │   ├── models.ts                 # RequirementNode, RequirementHierarchy
│   │   ├── pipeline.ts               # PlanningPipeline
│   │   ├── decomposition.ts          # decompose_requirements()
│   │   ├── steps.ts                  # Pipeline step implementations
│   │   ├── context-generation.ts     # Tech stack extraction
│   │   ├── beads-controller.ts       # Beads CLI wrapper
│   │   ├── claude-runner.ts          # Claude SDK wrapper
│   │   ├── checkpoint-manager.ts     # Checkpoint persistence
│   │   ├── property-generator.ts     # Property-based test generation
│   │   └── visualization.ts          # Mermaid diagrams
│   ├── orchestrator/
│   │   ├── main.ts                   # Main orchestrator
│   │   ├── planning.ts               # Planning orchestrator
│   │   └── loop-runner.ts            # Autonomous loop
│   ├── baml/
│   │   ├── client.ts                 # BAML client wrapper
│   │   └── types.ts                  # BAML type definitions
│   └── cli.ts                        # CLI entry point
├── tests/
│   ├── context/                      # 6 test files
│   ├── planning/                     # 18 test files
│   └── orchestrator/                 # Integration tests
├── baml_src/                         # BAML definitions (unchanged)
├── package.json
├── tsconfig.json
├── vitest.config.ts
└── biome.json
```

### Observable Behaviors (High-Level)

**Phase 1: Project Setup**
- TypeScript compiles with strict mode
- Tests run with Vitest
- Linting passes with Biome
- All tooling configured

**Phase 2: Context Management**
- Store CRUD operations work correctly
- Vector search returns relevant results
- Task batching respects <200 entry limit
- Working/Implementation contexts build correctly
- Entry IDs follow ctx_XXXXX pattern

**Phase 3: Data Models**
- All Python dataclasses ported to TypeScript types
- Zod schemas validate at runtime
- Type safety enforced at compile time
- Helper functions work identically

**Phase 4: BAML Integration**
- BAML client connects to local Ollama
- Functions return structured responses
- Type safety for all BAML calls
- Retry logic works correctly
- Fallback strategies work

**Phase 5: Planning Pipeline**
- All 7 steps execute sequentially
- Checkpoint save/restore works
- Requirement decomposition matches Python output
- Interactive prompts work
- Beads integration creates issues

**Phase 6: Orchestrators**
- CLI commands work (orchestrate, loop, plan)
- Autonomous loop runs continuously
- Feature list validation works
- Git integration works
- Context compilation works

**Phase 7: Integration & E2E**
- Full pipeline runs end-to-end
- Real Ollama API calls succeed
- All tests pass (unit + integration + e2e)
- Documentation complete
- Ready for production use

---

## What We're NOT Doing

1. **No silmari-oracle-wui work**: Staying in this repository only
2. **No Python deprecation**: Python version remains functional
3. **No UI components**: Command-line only
4. **No database changes**: Keep checkpoint format compatible
5. **No BAML schema changes**: Port existing BAML definitions as-is
6. **No new features**: Port existing functionality only
7. **No performance optimization**: Focus on correctness first

---

## Testing Strategy

### Frameworks & Tools

- **Test Runner**: Vitest (Jest-compatible API, fast, ESM support)
- **Type Validation**: Zod (runtime validation like Pydantic)
- **Property Testing**: @fast-check/vitest (Hypothesis equivalent)
- **API Calls**: Real local Ollama for integration tests
- **Coverage**: vitest --coverage (target: 100%)
- **Mocking**: vitest.mock() for unit tests
- **Assertions**: Vitest built-in (expect API)

### Test Types

| Type | Purpose | Scope | API Calls |
|------|---------|-------|-----------|
| **Unit** | Test individual functions/classes | Single module | Mocked |
| **Integration** | Test module interactions | Cross-module | Real Ollama |
| **Property** | Test invariants/properties | Core models | Mocked |
| **E2E** | Test full pipeline | Entire system | Real Ollama |

### Mocking Strategy

**Unit Tests**: Mock BAML client, subprocess calls, file system
**Integration Tests**: Real BAML calls to local Ollama, real file system
**E2E Tests**: Real everything, use test fixtures

### Success Criteria Format

Each behavior includes:

**Automated Verification:**
- Test fails for right reason (Red): `npm test -- file.test.ts`
- Test passes (Green): `npm test -- file.test.ts`
- All tests pass after refactor: `npm test`
- Coverage check: `npm run test:coverage`
- Type check: `npm run type-check`
- Lint check: `npm run lint`

**Manual Verification:**
- Behavior observable through CLI/logs
- Edge cases handled gracefully
- Error messages clear and helpful
- Performance acceptable

---

## Phase 1: Project Setup & Tooling

### Overview

Establish TypeScript project infrastructure with modern tooling, comprehensive testing setup, and CI/CD pipeline.

### Test Specification

**Given**: Empty TypeScript project
**When**: Project setup complete
**Then**: All tooling works and basic tests pass

**Edge Cases**:
- Node.js version compatibility (18+)
- ESM vs CommonJS module resolution
- Path resolution for imports
- Test coverage reporting

---

### Behavior 1.1: TypeScript Compilation Works

**Given**: tsconfig.json configured
**When**: Running `npm run type-check`
**Then**: TypeScript compiles with no errors

#### 🔴 Red: Write Failing Test

**File**: `tests/setup/compilation.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { execSync } from 'child_process';

describe('TypeScript Compilation', () => {
  it('should compile with strict mode enabled', () => {
    // This will fail because tsconfig doesn't exist yet
    expect(() => {
      execSync('npx tsc --noEmit', { stdio: 'pipe' });
    }).not.toThrow();
  });

  it('should have strict mode enabled in tsconfig', () => {
    const tsconfig = require('../../tsconfig.json');
    expect(tsconfig.compilerOptions.strict).toBe(true);
  });
});
```

#### 🟢 Green: Minimal Implementation

**File**: `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "types": ["vitest/globals"],
    "lib": ["ES2022"]
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

**File**: `package.json`

```json
{
  "name": "silmari-context-engine",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "type-check": "tsc --noEmit",
    "build": "tsc",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "lint": "biome check src/",
    "format": "biome format --write src/"
  },
  "devDependencies": {
    "@biomejs/biome": "^1.9.4",
    "@vitest/coverage-v8": "^2.1.8",
    "typescript": "^5.7.2",
    "vitest": "^2.1.8"
  }
}
```

#### 🔵 Refactor: Improve Code

**File**: `tsconfig.json` (add paths for cleaner imports)

```json
{
  "compilerOptions": {
    // ... previous config
    "baseUrl": ".",
    "paths": {
      "@/context/*": ["src/context/*"],
      "@/planning/*": ["src/planning/*"],
      "@/orchestrator/*": ["src/orchestrator/*"],
      "@/baml/*": ["src/baml/*"]
    }
  }
}
```

### Success Criteria

**Automated:**
- [ ] Test fails initially (no tsconfig): `npm test tests/setup/compilation.test.ts`
- [ ] Test passes after creating tsconfig: `npm test tests/setup/compilation.test.ts`
- [ ] TypeScript compiles: `npm run type-check`
- [ ] All tests pass: `npm test`

**Manual:**
- [ ] Project structure clear and organized
- [ ] Import paths work in IDE
- [ ] Type checking instant in editor

---

### Behavior 1.2: Test Runner Works

**Given**: Vitest configured
**When**: Running `npm test`
**Then**: Tests execute and report correctly

#### 🔴 Red: Write Failing Test

**File**: `tests/setup/vitest.test.ts`

```typescript
import { describe, it, expect } from 'vitest';

describe('Vitest Setup', () => {
  it('should run basic assertions', () => {
    expect(1 + 1).toBe(2);
  });

  it('should support async tests', async () => {
    const result = await Promise.resolve(42);
    expect(result).toBe(42);
  });

  it('should fail intentionally', () => {
    // This will fail to verify test failure reporting
    expect(true).toBe(false);
  });
});
```

#### 🟢 Green: Minimal Implementation

**File**: `vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.test.ts',
        '**/*.config.ts',
        'baml_client/',
      ],
    },
  },
  resolve: {
    alias: {
      '@/context': path.resolve(__dirname, './src/context'),
      '@/planning': path.resolve(__dirname, './src/planning'),
      '@/orchestrator': path.resolve(__dirname, './src/orchestrator'),
      '@/baml': path.resolve(__dirname, './src/baml'),
    },
  },
});
```

**File**: `tests/setup/vitest.test.ts` (remove failing test)

```typescript
import { describe, it, expect } from 'vitest';

describe('Vitest Setup', () => {
  it('should run basic assertions', () => {
    expect(1 + 1).toBe(2);
  });

  it('should support async tests', async () => {
    const result = await Promise.resolve(42);
    expect(result).toBe(42);
  });
});
```

#### 🔵 Refactor: Improve Code

**File**: `vitest.config.ts` (add test timeout and parallel execution)

```typescript
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    testTimeout: 30000, // 30s for integration tests
    hookTimeout: 30000,
    isolate: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.test.ts',
        '**/*.config.ts',
        'baml_client/',
      ],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 85,
        statements: 90,
      },
    },
  },
  resolve: {
    alias: {
      '@/context': path.resolve(__dirname, './src/context'),
      '@/planning': path.resolve(__dirname, './src/planning'),
      '@/orchestrator': path.resolve(__dirname, './src/orchestrator'),
      '@/baml': path.resolve(__dirname, './src/baml'),
    },
  },
});
```

### Success Criteria

**Automated:**
- [ ] Test with intentional failure shows failure: `npm test tests/setup/vitest.test.ts`
- [ ] Tests pass after fixing: `npm test tests/setup/vitest.test.ts`
- [ ] Coverage report generated: `npm run test:coverage`
- [ ] All tests pass: `npm test`

**Manual:**
- [ ] Test output clear and readable
- [ ] Coverage report shows all files
- [ ] Test execution fast (<1s for unit tests)

---

### Behavior 1.3: Linting & Formatting Works

**Given**: Biome configured
**When**: Running `npm run lint`
**Then**: Code style enforced consistently

#### 🔴 Red: Write Failing Test

**File**: `src/example.ts` (with intentional lint errors)

```typescript
// Intentional errors for test
const x = 1;  // unused variable
var y = 2;    // var instead of const/let
function test(){return"bad formatting"}  // no spaces

export default test;
```

**File**: `tests/setup/linting.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { execSync } from 'child_process';

describe('Linting Setup', () => {
  it('should detect linting errors', () => {
    // This will fail because biome.json doesn't exist
    expect(() => {
      execSync('npm run lint', { stdio: 'pipe' });
    }).toThrow();
  });
});
```

#### 🟢 Green: Minimal Implementation

**File**: `biome.json`

```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "style": {
        "noVar": "error",
        "useConst": "error"
      },
      "suspicious": {
        "noExplicitAny": "warn"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "semicolons": "always"
    }
  }
}
```

**File**: `src/example.ts` (fixed)

```typescript
function test(): string {
  return 'good formatting';
}

export default test;
```

#### 🔵 Refactor: Improve Code

**File**: `biome.json` (add more rules)

```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "style": {
        "noVar": "error",
        "useConst": "error",
        "useExportType": "warn",
        "useImportType": "warn"
      },
      "suspicious": {
        "noExplicitAny": "warn",
        "noEmptyInterface": "error"
      },
      "correctness": {
        "noUnusedVariables": "error"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "semicolons": "always",
      "trailingCommas": "es5"
    }
  },
  "files": {
    "ignore": [
      "node_modules",
      "dist",
      "coverage",
      "baml_client"
    ]
  }
}
```

### Success Criteria

**Automated:**
- [ ] Lint fails on bad code: `npm run lint`
- [ ] Lint passes on fixed code: `npm run lint`
- [ ] Format fixes issues: `npm run format`
- [ ] All tests pass: `npm test`

**Manual:**
- [ ] Code formatted consistently
- [ ] IDE shows linting errors in real-time
- [ ] Format on save works

---

### Behavior 1.4: Property-Based Testing Works

**Given**: fast-check configured
**When**: Running property tests
**Then**: Invariants verified across random inputs

#### 🔴 Red: Write Failing Test

**File**: `tests/setup/property.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import fc from 'fast-check';

describe('Property Testing Setup', () => {
  it('should verify commutative property of addition', () => {
    fc.assert(
      fc.property(fc.integer(), fc.integer(), (a, b) => {
        expect(a + b).toBe(b + a);
      })
    );
  });

  it('should verify string concatenation is not commutative', () => {
    // This should fail to verify property test failure detection
    fc.assert(
      fc.property(fc.string(), fc.string(), (a, b) => {
        // This is intentionally wrong to test failure
        expect(a + b).toBe(b + a);
      })
    );
  });
});
```

#### 🟢 Green: Minimal Implementation

**File**: `package.json` (add fast-check)

```json
{
  "devDependencies": {
    "@biomejs/biome": "^1.9.4",
    "@vitest/coverage-v8": "^2.1.8",
    "fast-check": "^3.25.0",
    "typescript": "^5.7.2",
    "vitest": "^2.1.8"
  }
}
```

**File**: `tests/setup/property.test.ts` (remove failing test)

```typescript
import { describe, it, expect } from 'vitest';
import fc from 'fast-check';

describe('Property Testing Setup', () => {
  it('should verify commutative property of addition', () => {
    fc.assert(
      fc.property(fc.integer(), fc.integer(), (a, b) => {
        expect(a + b).toBe(b + a);
      })
    );
  });

  it('should verify string reverse is involutive', () => {
    fc.assert(
      fc.property(fc.string(), (str) => {
        const reversed = str.split('').reverse().join('');
        const doubleReversed = reversed.split('').reverse().join('');
        expect(doubleReversed).toBe(str);
      })
    );
  });
});
```

#### 🔵 Refactor: Improve Code

**File**: `tests/setup/property.test.ts` (add more property examples)

```typescript
import { describe, it, expect } from 'vitest';
import fc from 'fast-check';

describe('Property Testing Setup', () => {
  describe('Mathematical Properties', () => {
    it('should verify commutative property of addition', () => {
      fc.assert(
        fc.property(fc.integer(), fc.integer(), (a, b) => {
          expect(a + b).toBe(b + a);
        })
      );
    });

    it('should verify associative property of addition', () => {
      fc.assert(
        fc.property(fc.integer(), fc.integer(), fc.integer(), (a, b, c) => {
          expect((a + b) + c).toBe(a + (b + c));
        })
      );
    });
  });

  describe('String Properties', () => {
    it('should verify string reverse is involutive', () => {
      fc.assert(
        fc.property(fc.string(), (str) => {
          const reversed = str.split('').reverse().join('');
          const doubleReversed = reversed.split('').reverse().join('');
          expect(doubleReversed).toBe(str);
        })
      );
    });

    it('should verify string concatenation length', () => {
      fc.assert(
        fc.property(fc.string(), fc.string(), (a, b) => {
          expect((a + b).length).toBe(a.length + b.length);
        })
      );
    });
  });
});
```

### Success Criteria

**Automated:**
- [ ] Property test with wrong assertion fails: `npm test tests/setup/property.test.ts`
- [ ] Property tests pass after fixing: `npm test tests/setup/property.test.ts`
- [ ] fast-check generates multiple test cases (visible in output)
- [ ] All tests pass: `npm test`

**Manual:**
- [ ] Property test failures show counterexamples
- [ ] Test execution time acceptable
- [ ] Coverage includes property tests

---

### Behavior 1.5: Zod Runtime Validation Works

**Given**: Zod configured
**When**: Validating data at runtime
**Then**: Type errors caught with clear messages

#### 🔴 Red: Write Failing Test

**File**: `tests/setup/validation.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { z } from 'zod';

describe('Zod Validation Setup', () => {
  const UserSchema = z.object({
    id: z.string().uuid(),
    name: z.string().min(1),
    email: z.string().email(),
    age: z.number().int().positive(),
  });

  it('should validate correct data', () => {
    const validUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      name: 'John Doe',
      email: 'john@example.com',
      age: 30,
    };

    expect(() => UserSchema.parse(validUser)).not.toThrow();
  });

  it('should reject invalid data with clear errors', () => {
    const invalidUser = {
      id: 'not-a-uuid',
      name: '',
      email: 'not-an-email',
      age: -5,
    };

    // This will fail because Zod is not installed yet
    expect(() => UserSchema.parse(invalidUser)).toThrow();
  });
});
```

#### 🟢 Green: Minimal Implementation

**File**: `package.json` (add zod)

```json
{
  "dependencies": {
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@biomejs/biome": "^1.9.4",
    "@vitest/coverage-v8": "^2.1.8",
    "fast-check": "^3.25.0",
    "typescript": "^5.7.2",
    "vitest": "^2.1.8"
  }
}
```

**File**: `tests/setup/validation.test.ts` (tests now pass with Zod)

```typescript
import { describe, it, expect } from 'vitest';
import { z } from 'zod';

describe('Zod Validation Setup', () => {
  const UserSchema = z.object({
    id: z.string().uuid(),
    name: z.string().min(1),
    email: z.string().email(),
    age: z.number().int().positive(),
  });

  it('should validate correct data', () => {
    const validUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      name: 'John Doe',
      email: 'john@example.com',
      age: 30,
    };

    const result = UserSchema.parse(validUser);
    expect(result).toEqual(validUser);
  });

  it('should reject invalid data with clear errors', () => {
    const invalidUser = {
      id: 'not-a-uuid',
      name: '',
      email: 'not-an-email',
      age: -5,
    };

    expect(() => UserSchema.parse(invalidUser)).toThrow(z.ZodError);
  });

  it('should provide detailed error messages', () => {
    const invalidUser = {
      id: 'not-a-uuid',
      name: '',
      email: 'not-an-email',
      age: -5,
    };

    try {
      UserSchema.parse(invalidUser);
    } catch (err) {
      expect(err).toBeInstanceOf(z.ZodError);
      const zodError = err as z.ZodError;
      expect(zodError.errors.length).toBeGreaterThan(0);
      expect(zodError.errors[0]).toHaveProperty('path');
      expect(zodError.errors[0]).toHaveProperty('message');
    }
  });
});
```

#### 🔵 Refactor: Improve Code

**File**: `tests/setup/validation.test.ts` (add safeParse example)

```typescript
import { describe, it, expect } from 'vitest';
import { z } from 'zod';

describe('Zod Validation Setup', () => {
  const UserSchema = z.object({
    id: z.string().uuid(),
    name: z.string().min(1),
    email: z.string().email(),
    age: z.number().int().positive(),
  });

  type User = z.infer<typeof UserSchema>;

  describe('parse() method', () => {
    it('should validate correct data', () => {
      const validUser = {
        id: '550e8400-e29b-41d4-a716-446655440000',
        name: 'John Doe',
        email: 'john@example.com',
        age: 30,
      };

      const result = UserSchema.parse(validUser);
      expect(result).toEqual(validUser);
    });

    it('should reject invalid data with clear errors', () => {
      const invalidUser = {
        id: 'not-a-uuid',
        name: '',
        email: 'not-an-email',
        age: -5,
      };

      expect(() => UserSchema.parse(invalidUser)).toThrow(z.ZodError);
    });
  });

  describe('safeParse() method', () => {
    it('should return success for valid data', () => {
      const validUser = {
        id: '550e8400-e29b-41d4-a716-446655440000',
        name: 'John Doe',
        email: 'john@example.com',
        age: 30,
      };

      const result = UserSchema.safeParse(validUser);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(validUser);
      }
    });

    it('should return error for invalid data', () => {
      const invalidUser = {
        id: 'not-a-uuid',
        name: '',
        email: 'not-an-email',
        age: -5,
      };

      const result = UserSchema.safeParse(invalidUser);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBeInstanceOf(z.ZodError);
        expect(result.error.errors.length).toBeGreaterThan(0);
      }
    });
  });

  describe('Type Inference', () => {
    it('should infer TypeScript types from schema', () => {
      const user: User = {
        id: '550e8400-e29b-41d4-a716-446655440000',
        name: 'John Doe',
        email: 'john@example.com',
        age: 30,
      };

      const result = UserSchema.parse(user);

      // TypeScript should recognize result as User type
      expect(result.id).toBe(user.id);
      expect(result.name).toBe(user.name);
      expect(result.email).toBe(user.email);
      expect(result.age).toBe(user.age);
    });
  });
});
```

### Success Criteria

**Automated:**
- [ ] Test fails before Zod installed: `npm test tests/setup/validation.test.ts`
- [ ] Tests pass after Zod installed: `npm test tests/setup/validation.test.ts`
- [ ] Type inference works (TypeScript doesn't complain)
- [ ] All tests pass: `npm test`

**Manual:**
- [ ] Error messages clear and helpful
- [ ] Type safety works in IDE
- [ ] safeParse vs parse difference understood

---

## Phase 2: Context Window Array Core

### Overview

Port the context_window_array module (8 files, 1,862 lines) to TypeScript. This implements the dual-LLM architecture with addressable context entries, vector search, and task batching.

### Test Specification

**Given**: Python context_window_array module
**When**: Ported to TypeScript
**Then**: All behaviors preserved with 100% test coverage

**Edge Cases**:
- Entry ID uniqueness and format (ctx_XXXXX)
- Compressed entries (no content, summary required)
- Parent-child relationships
- Search result relevance ordering
- Batch size boundaries (<200 entries)
- Context manager lifecycle

---

### Behavior 2.1: ContextEntry Model Works

**Given**: ContextEntry type and schema defined
**When**: Creating and validating entries
**Then**: Type safety and runtime validation work

#### 🔴 Red: Write Failing Test

**File**: `tests/context/models.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { ContextEntry, EntryType, ContextEntrySchema } from '@/context/models';

describe('ContextEntry Model', () => {
  it('should create valid entry', () => {
    const entry: ContextEntry = {
      id: 'ctx_abc12345',
      entry_type: EntryType.FILE,
      source: '/path/to/file.ts',
      summary: 'Test file',
      created_at: new Date(),
      references: [],
      searchable: true,
      compressed: false,
      derived_from: [],
    };

    // This will fail because models.ts doesn't exist
    const result = ContextEntrySchema.parse(entry);
    expect(result).toEqual(entry);
  });

  it('should validate ID format', () => {
    const invalidEntry = {
      id: 'invalid',
      entry_type: EntryType.FILE,
      source: '/path/to/file.ts',
      summary: 'Test file',
      created_at: new Date(),
    };

    expect(() => ContextEntrySchema.parse(invalidEntry)).toThrow();
  });
});
```

#### 🟢 Green: Minimal Implementation

**File**: `src/context/models.ts`

```typescript
import { z } from 'zod';

// EntryType enum matching Python
export enum EntryType {
  FILE = 'FILE',
  COMMAND = 'COMMAND',
  COMMAND_RESULT = 'COMMAND_RESULT',
  TASK = 'TASK',
  TASK_RESULT = 'TASK_RESULT',
  SEARCH_RESULT = 'SEARCH_RESULT',
  SUMMARY = 'SUMMARY',
  CONTEXT_REQUEST = 'CONTEXT_REQUEST',
}

// Zod schema for runtime validation
export const ContextEntrySchema = z.object({
  id: z.string().regex(/^ctx_[a-zA-Z0-9]{8}$/, 'ID must match pattern ctx_XXXXXXXX'),
  entry_type: z.nativeEnum(EntryType),
  source: z.string(),
  content: z.string().optional(),
  summary: z.string(),
  created_at: z.date(),
  references: z.array(z.string()).default([]),
  searchable: z.boolean().default(true),
  compressed: z.boolean().default(false),
  ttl: z.number().optional(),
  parent_id: z.string().optional(),
  derived_from: z.array(z.string()).default([]),
});

// TypeScript type inferred from schema
export type ContextEntry = z.infer<typeof ContextEntrySchema>;

// Helper function to generate context IDs
export function generateContextId(): string {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let id = 'ctx_';
  for (let i = 0; i < 8; i++) {
    id += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return id;
}
```

#### 🔵 Refactor: Improve Code

**File**: `src/context/models.ts` (add helper functions and validation)

```typescript
import { z } from 'zod';
import crypto from 'crypto';

// EntryType enum matching Python
export enum EntryType {
  FILE = 'FILE',
  COMMAND = 'COMMAND',
  COMMAND_RESULT = 'COMMAND_RESULT',
  TASK = 'TASK',
  TASK_RESULT = 'TASK_RESULT',
  SEARCH_RESULT = 'SEARCH_RESULT',
  SUMMARY = 'SUMMARY',
  CONTEXT_REQUEST = 'CONTEXT_REQUEST',
}

// Zod schema for runtime validation
export const ContextEntrySchema = z
  .object({
    id: z.string().regex(/^ctx_[a-zA-Z0-9]{8}$/, 'ID must match pattern ctx_XXXXXXXX'),
    entry_type: z.nativeEnum(EntryType),
    source: z.string().min(1, 'Source cannot be empty'),
    content: z.string().optional(),
    summary: z.string().min(1, 'Summary cannot be empty'),
    created_at: z.date(),
    references: z.array(z.string()).default([]),
    searchable: z.boolean().default(true),
    compressed: z.boolean().default(false),
    ttl: z.number().positive().optional(),
    parent_id: z.string().regex(/^ctx_[a-zA-Z0-9]{8}$/).optional(),
    derived_from: z.array(z.string()).default([]),
  })
  .refine(
    (data) => {
      // Compressed entries must not have content
      if (data.compressed && data.content !== undefined) {
        return false;
      }
      return true;
    },
    {
      message: 'Compressed entries must not have content',
    }
  );

// TypeScript type inferred from schema
export type ContextEntry = z.infer<typeof ContextEntrySchema>;

// Helper function to generate context IDs (crypto-based for better randomness)
export function generateContextId(): string {
  const randomBytes = crypto.randomBytes(4);
  const id = randomBytes.toString('hex');
  return `ctx_${id}`;
}

// Helper to create entry with defaults
export function createContextEntry(
  partial: Partial<ContextEntry> & Pick<ContextEntry, 'entry_type' | 'source' | 'summary'>
): ContextEntry {
  const entry: ContextEntry = {
    id: partial.id ?? generateContextId(),
    entry_type: partial.entry_type,
    source: partial.source,
    summary: partial.summary,
    content: partial.content,
    created_at: partial.created_at ?? new Date(),
    references: partial.references ?? [],
    searchable: partial.searchable ?? true,
    compressed: partial.compressed ?? false,
    ttl: partial.ttl,
    parent_id: partial.parent_id,
    derived_from: partial.derived_from ?? [],
  };

  return ContextEntrySchema.parse(entry);
}

// Type guard
export function isContextEntry(value: unknown): value is ContextEntry {
  return ContextEntrySchema.safeParse(value).success;
}
```

**File**: `tests/context/models.test.ts` (comprehensive tests)

```typescript
import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import {
  ContextEntry,
  EntryType,
  ContextEntrySchema,
  generateContextId,
  createContextEntry,
  isContextEntry,
} from '@/context/models';

describe('ContextEntry Model', () => {
  describe('Basic Validation', () => {
    it('should create valid entry', () => {
      const entry: ContextEntry = {
        id: 'ctx_abc12345',
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
        created_at: new Date(),
        references: [],
        searchable: true,
        compressed: false,
        derived_from: [],
      };

      const result = ContextEntrySchema.parse(entry);
      expect(result).toEqual(entry);
    });

    it('should reject invalid ID format', () => {
      const invalidEntry = {
        id: 'invalid',
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
        created_at: new Date(),
      };

      expect(() => ContextEntrySchema.parse(invalidEntry)).toThrow();
    });

    it('should reject empty source', () => {
      const invalidEntry = {
        id: 'ctx_abc12345',
        entry_type: EntryType.FILE,
        source: '',
        summary: 'Test file',
        created_at: new Date(),
      };

      expect(() => ContextEntrySchema.parse(invalidEntry)).toThrow();
    });

    it('should reject empty summary', () => {
      const invalidEntry = {
        id: 'ctx_abc12345',
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: '',
        created_at: new Date(),
      };

      expect(() => ContextEntrySchema.parse(invalidEntry)).toThrow();
    });
  });

  describe('Compression Rules', () => {
    it('should reject compressed entry with content', () => {
      const invalidEntry = {
        id: 'ctx_abc12345',
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        content: 'Some content',
        summary: 'Test file',
        created_at: new Date(),
        compressed: true,
      };

      expect(() => ContextEntrySchema.parse(invalidEntry)).toThrow();
    });

    it('should allow compressed entry without content', () => {
      const validEntry = {
        id: 'ctx_abc12345',
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
        created_at: new Date(),
        compressed: true,
      };

      const result = ContextEntrySchema.parse(validEntry);
      expect(result.compressed).toBe(true);
      expect(result.content).toBeUndefined();
    });

    it('should allow uncompressed entry with content', () => {
      const validEntry = {
        id: 'ctx_abc12345',
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        content: 'File contents here',
        summary: 'Test file',
        created_at: new Date(),
        compressed: false,
      };

      const result = ContextEntrySchema.parse(validEntry);
      expect(result.compressed).toBe(false);
      expect(result.content).toBe('File contents here');
    });
  });

  describe('Helper Functions', () => {
    it('should generate valid context ID', () => {
      const id = generateContextId();
      expect(id).toMatch(/^ctx_[a-zA-Z0-9]{8}$/);
    });

    it('should generate unique IDs', () => {
      const ids = new Set<string>();
      for (let i = 0; i < 100; i++) {
        ids.add(generateContextId());
      }
      expect(ids.size).toBe(100);
    });

    it('should create entry with defaults', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
      });

      expect(entry.id).toMatch(/^ctx_[a-zA-Z0-9]{8}$/);
      expect(entry.created_at).toBeInstanceOf(Date);
      expect(entry.references).toEqual([]);
      expect(entry.searchable).toBe(true);
      expect(entry.compressed).toBe(false);
    });

    it('should respect provided values', () => {
      const customDate = new Date('2024-01-01');
      const entry = createContextEntry({
        id: 'ctx_custom01',
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
        created_at: customDate,
        searchable: false,
      });

      expect(entry.id).toBe('ctx_custom01');
      expect(entry.created_at).toEqual(customDate);
      expect(entry.searchable).toBe(false);
    });

    it('should identify valid context entries', () => {
      const validEntry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
      });

      expect(isContextEntry(validEntry)).toBe(true);
      expect(isContextEntry({})).toBe(false);
      expect(isContextEntry(null)).toBe(false);
      expect(isContextEntry('not an entry')).toBe(false);
    });
  });

  describe('Property-Based Tests', () => {
    it('should always generate valid ID format', () => {
      fc.assert(
        fc.property(fc.constant(undefined), () => {
          const id = generateContextId();
          expect(id).toMatch(/^ctx_[a-zA-Z0-9]{8}$/);
        })
      );
    });

    it('should handle all entry types', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(...Object.values(EntryType)),
          fc.string().filter((s) => s.length > 0),
          fc.string().filter((s) => s.length > 0),
          (entryType, source, summary) => {
            const entry = createContextEntry({
              entry_type: entryType,
              source,
              summary,
            });

            expect(entry.entry_type).toBe(entryType);
            expect(entry.source).toBe(source);
            expect(entry.summary).toBe(summary);
          }
        )
      );
    });

    it('should reject compressed entries with content', () => {
      fc.assert(
        fc.property(
          fc.string().filter((s) => s.length > 0),
          fc.string().filter((s) => s.length > 0),
          fc.string().filter((s) => s.length > 0),
          (source, summary, content) => {
            expect(() =>
              ContextEntrySchema.parse({
                id: generateContextId(),
                entry_type: EntryType.FILE,
                source,
                summary,
                content,
                compressed: true,
                created_at: new Date(),
              })
            ).toThrow();
          }
        )
      );
    });
  });
});
```

### Success Criteria

**Automated:**
- [ ] Test fails before implementation: `npm test tests/context/models.test.ts`
- [ ] Test passes after implementation: `npm test tests/context/models.test.ts`
- [ ] Property tests pass with 100 runs: `npm test tests/context/models.test.ts`
- [ ] Coverage 100% for models: `npm run test:coverage -- tests/context/models.test.ts`
- [ ] Type checking passes: `npm run type-check`
- [ ] All tests pass: `npm test`

**Manual:**
- [ ] Type safety works in IDE (autocomplete, errors)
- [ ] Error messages clear for validation failures
- [ ] Helper functions intuitive to use

---

### Behavior 2.2: CentralContextStore CRUD Works

**Given**: CentralContextStore class implemented
**When**: Adding, getting, removing entries
**Then**: All CRUD operations work correctly

#### 🔴 Red: Write Failing Test

**File**: `tests/context/store.test.ts`

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { CentralContextStore } from '@/context/store';
import { createContextEntry, EntryType } from '@/context/models';

describe('CentralContextStore', () => {
  let store: CentralContextStore;

  beforeEach(() => {
    // This will fail because store.ts doesn't exist
    store = new CentralContextStore();
  });

  describe('add()', () => {
    it('should add entry to store', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
      });

      store.add(entry);

      const retrieved = store.get(entry.id);
      expect(retrieved).toEqual(entry);
    });

    it('should reject invalid entry', () => {
      const invalidEntry = { id: 'invalid' };
      expect(() => store.add(invalidEntry as any)).toThrow();
    });
  });

  describe('get()', () => {
    it('should return entry by ID', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
      });

      store.add(entry);
      const retrieved = store.get(entry.id);

      expect(retrieved).toEqual(entry);
    });

    it('should return undefined for non-existent ID', () => {
      const retrieved = store.get('ctx_notfound');
      expect(retrieved).toBeUndefined();
    });
  });

  describe('contains()', () => {
    it('should return true for existing entry', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
      });

      store.add(entry);
      expect(store.contains(entry.id)).toBe(true);
    });

    it('should return false for non-existent entry', () => {
      expect(store.contains('ctx_notfound')).toBe(false);
    });
  });

  describe('remove()', () => {
    it('should remove entry by ID', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
      });

      store.add(entry);
      expect(store.contains(entry.id)).toBe(true);

      store.remove(entry.id);
      expect(store.contains(entry.id)).toBe(false);
    });

    it('should not throw for non-existent ID', () => {
      expect(() => store.remove('ctx_notfound')).not.toThrow();
    });
  });
});
```

#### 🟢 Green: Minimal Implementation

**File**: `src/context/store.ts`

```typescript
import { ContextEntry, ContextEntrySchema, EntryType } from './models.js';

export class CentralContextStore {
  private entries: Map<string, ContextEntry> = new Map();

  add(entry: ContextEntry): void {
    // Validate entry
    ContextEntrySchema.parse(entry);
    this.entries.set(entry.id, entry);
  }

  get(id: string): ContextEntry | undefined {
    return this.entries.get(id);
  }

  contains(id: string): boolean {
    return this.entries.has(id);
  }

  remove(id: string): void {
    this.entries.delete(id);
  }
}
```

#### 🔵 Refactor: Improve Code

**File**: `src/context/store.ts` (add more methods from Python version)

```typescript
import { ContextEntry, ContextEntrySchema, EntryType } from './models.js';

export class CentralContextStore {
  private entries: Map<string, ContextEntry> = new Map();

  add(entry: ContextEntry): void {
    // Validate entry
    ContextEntrySchema.parse(entry);
    this.entries.set(entry.id, entry);
  }

  get(id: string): ContextEntry | undefined {
    return this.entries.get(id);
  }

  contains(id: string): boolean {
    return this.entries.has(id);
  }

  remove(id: string): void {
    this.entries.delete(id);
  }

  getAll(): ContextEntry[] {
    return Array.from(this.entries.values());
  }

  getByType(entryType: EntryType): ContextEntry[] {
    return this.getAll().filter((e) => e.entry_type === entryType);
  }

  getStats(): {
    total: number;
    byType: Record<string, number>;
    compressed: number;
    searchable: number;
  } {
    const byType: Record<string, number> = {};
    let compressed = 0;
    let searchable = 0;

    for (const entry of this.entries.values()) {
      byType[entry.entry_type] = (byType[entry.entry_type] || 0) + 1;
      if (entry.compressed) compressed++;
      if (entry.searchable) searchable++;
    }

    return {
      total: this.entries.size,
      byType,
      compressed,
      searchable,
    };
  }

  compress(id: string): void {
    const entry = this.entries.get(id);
    if (!entry) {
      throw new Error(`Entry ${id} not found`);
    }

    // Create new entry without content
    const compressed: ContextEntry = {
      ...entry,
      compressed: true,
      content: undefined,
    };

    this.entries.set(id, compressed);
  }

  exportToDict(): Record<string, ContextEntry> {
    return Object.fromEntries(this.entries);
  }

  clear(): void {
    this.entries.clear();
  }

  size(): number {
    return this.entries.size;
  }
}
```

**File**: `tests/context/store.test.ts` (add comprehensive tests)

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import fc from 'fast-check';
import { CentralContextStore } from '@/context/store';
import { createContextEntry, EntryType } from '@/context/models';

describe('CentralContextStore', () => {
  let store: CentralContextStore;

  beforeEach(() => {
    store = new CentralContextStore();
  });

  describe('add()', () => {
    it('should add entry to store', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
      });

      store.add(entry);

      const retrieved = store.get(entry.id);
      expect(retrieved).toEqual(entry);
    });

    it('should reject invalid entry', () => {
      const invalidEntry = { id: 'invalid' };
      expect(() => store.add(invalidEntry as any)).toThrow();
    });

    it('should overwrite existing entry with same ID', () => {
      const entry1 = createContextEntry({
        id: 'ctx_test0001',
        entry_type: EntryType.FILE,
        source: '/path/to/file1.ts',
        summary: 'First version',
      });

      const entry2 = createContextEntry({
        id: 'ctx_test0001',
        entry_type: EntryType.FILE,
        source: '/path/to/file2.ts',
        summary: 'Second version',
      });

      store.add(entry1);
      store.add(entry2);

      const retrieved = store.get('ctx_test0001');
      expect(retrieved?.summary).toBe('Second version');
    });
  });

  describe('get()', () => {
    it('should return entry by ID', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
      });

      store.add(entry);
      const retrieved = store.get(entry.id);

      expect(retrieved).toEqual(entry);
    });

    it('should return undefined for non-existent ID', () => {
      const retrieved = store.get('ctx_notfound');
      expect(retrieved).toBeUndefined();
    });
  });

  describe('contains()', () => {
    it('should return true for existing entry', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
      });

      store.add(entry);
      expect(store.contains(entry.id)).toBe(true);
    });

    it('should return false for non-existent entry', () => {
      expect(store.contains('ctx_notfound')).toBe(false);
    });
  });

  describe('remove()', () => {
    it('should remove entry by ID', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/path/to/file.ts',
        summary: 'Test file',
      });

      store.add(entry);
      expect(store.contains(entry.id)).toBe(true);

      store.remove(entry.id);
      expect(store.contains(entry.id)).toBe(false);
    });

    it('should not throw for non-existent ID', () => {
      expect(() => store.remove('ctx_notfound')).not.toThrow();
    });
  });

  describe('getAll()', () => {
    it('should return all entries', () => {
      const entry1 = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/file1.ts',
        summary: 'File 1',
      });

      const entry2 = createContextEntry({
        entry_type: EntryType.COMMAND,
        source: 'ls -la',
        summary: 'Command',
      });

      store.add(entry1);
      store.add(entry2);

      const all = store.getAll();
      expect(all).toHaveLength(2);
      expect(all).toContainEqual(entry1);
      expect(all).toContainEqual(entry2);
    });

    it('should return empty array for empty store', () => {
      const all = store.getAll();
      expect(all).toEqual([]);
    });
  });

  describe('getByType()', () => {
    it('should return entries of specified type', () => {
      const file1 = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/file1.ts',
        summary: 'File 1',
      });

      const file2 = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/file2.ts',
        summary: 'File 2',
      });

      const command = createContextEntry({
        entry_type: EntryType.COMMAND,
        source: 'ls -la',
        summary: 'Command',
      });

      store.add(file1);
      store.add(file2);
      store.add(command);

      const files = store.getByType(EntryType.FILE);
      expect(files).toHaveLength(2);
      expect(files).toContainEqual(file1);
      expect(files).toContainEqual(file2);

      const commands = store.getByType(EntryType.COMMAND);
      expect(commands).toHaveLength(1);
      expect(commands).toContainEqual(command);
    });
  });

  describe('getStats()', () => {
    it('should return store statistics', () => {
      const file = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/file.ts',
        summary: 'File',
      });

      const command = createContextEntry({
        entry_type: EntryType.COMMAND,
        source: 'ls -la',
        summary: 'Command',
      });

      const compressed = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/compressed.ts',
        summary: 'Compressed file',
        compressed: true,
      });

      store.add(file);
      store.add(command);
      store.add(compressed);

      const stats = store.getStats();
      expect(stats.total).toBe(3);
      expect(stats.byType[EntryType.FILE]).toBe(2);
      expect(stats.byType[EntryType.COMMAND]).toBe(1);
      expect(stats.compressed).toBe(1);
      expect(stats.searchable).toBe(3);
    });
  });

  describe('compress()', () => {
    it('should compress entry by removing content', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/file.ts',
        summary: 'File',
        content: 'Original content here',
      });

      store.add(entry);
      expect(store.get(entry.id)?.content).toBe('Original content here');

      store.compress(entry.id);

      const compressed = store.get(entry.id);
      expect(compressed?.compressed).toBe(true);
      expect(compressed?.content).toBeUndefined();
      expect(compressed?.summary).toBe('File');
    });

    it('should throw for non-existent entry', () => {
      expect(() => store.compress('ctx_notfound')).toThrow();
    });
  });

  describe('exportToDict()', () => {
    it('should export entries as dictionary', () => {
      const entry1 = createContextEntry({
        id: 'ctx_test0001',
        entry_type: EntryType.FILE,
        source: '/file1.ts',
        summary: 'File 1',
      });

      const entry2 = createContextEntry({
        id: 'ctx_test0002',
        entry_type: EntryType.COMMAND,
        source: 'ls -la',
        summary: 'Command',
      });

      store.add(entry1);
      store.add(entry2);

      const dict = store.exportToDict();
      expect(dict['ctx_test0001']).toEqual(entry1);
      expect(dict['ctx_test0002']).toEqual(entry2);
    });
  });

  describe('clear()', () => {
    it('should remove all entries', () => {
      store.add(
        createContextEntry({
          entry_type: EntryType.FILE,
          source: '/file.ts',
          summary: 'File',
        })
      );

      expect(store.size()).toBe(1);

      store.clear();

      expect(store.size()).toBe(0);
      expect(store.getAll()).toEqual([]);
    });
  });

  describe('Property-Based Tests', () => {
    it('should maintain size consistency', () => {
      fc.assert(
        fc.property(fc.array(fc.string().filter((s) => s.length > 0), { maxLength: 50 }), (sources) => {
          const testStore = new CentralContextStore();
          const entries = sources.map((source, i) =>
            createContextEntry({
              id: `ctx_test${String(i).padStart(4, '0')}`,
              entry_type: EntryType.FILE,
              source,
              summary: `Summary ${i}`,
            })
          );

          entries.forEach((e) => testStore.add(e));

          expect(testStore.size()).toBe(entries.length);
          expect(testStore.getAll()).toHaveLength(entries.length);
        })
      );
    });

    it('should preserve entry data through add/get cycle', () => {
      fc.assert(
        fc.property(
          fc.string().filter((s) => s.length > 0),
          fc.string().filter((s) => s.length > 0),
          (source, summary) => {
            const testStore = new CentralContextStore();
            const entry = createContextEntry({
              entry_type: EntryType.FILE,
              source,
              summary,
            });

            testStore.add(entry);
            const retrieved = testStore.get(entry.id);

            expect(retrieved).toEqual(entry);
          }
        )
      );
    });
  });
});
```

### Success Criteria

**Automated:**
- [ ] Tests fail before implementation: `npm test tests/context/store.test.ts`
- [ ] Tests pass after implementation: `npm test tests/context/store.test.ts`
- [ ] Property tests pass with 100 runs
- [ ] Coverage 100% for store: `npm run test:coverage -- tests/context/store.test.ts`
- [ ] Type checking passes: `npm run type-check`
- [ ] All tests pass: `npm test`

**Manual:**
- [ ] Store operations fast (O(1) for get/add/remove)
- [ ] Memory usage reasonable for large stores
- [ ] API intuitive and easy to use

---

### Behavior 2.3: Vector Search Works

**Given**: VectorSearchIndex implemented with TF-IDF
**When**: Searching for relevant entries
**Then**: Results returned in relevance order

#### 🔴 Red: Write Failing Test

**File**: `tests/context/search.test.ts`

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { VectorSearchIndex } from '@/context/search';
import { createContextEntry, EntryType } from '@/context/models';

describe('VectorSearchIndex', () => {
  let index: VectorSearchIndex;

  beforeEach(() => {
    // This will fail because search.ts doesn't exist
    index = new VectorSearchIndex();
  });

  describe('add()', () => {
    it('should add entry to index', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/file.ts',
        summary: 'TypeScript file with functions',
        content: 'export function hello() { return "world"; }',
      });

      expect(() => index.add(entry)).not.toThrow();
    });

    it('should not index non-searchable entries', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/file.ts',
        summary: 'Non-searchable file',
        searchable: false,
      });

      index.add(entry);
      const results = index.search('file', 10);

      expect(results).toHaveLength(0);
    });
  });

  describe('search()', () => {
    it('should return relevant results', () => {
      const entry1 = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/database.ts',
        summary: 'Database connection module',
        content: 'Database setup with PostgreSQL',
      });

      const entry2 = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/api.ts',
        summary: 'API routes definition',
        content: 'Express API routes for REST endpoints',
      });

      index.add(entry1);
      index.add(entry2);

      const results = index.search('database', 10);

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].entry_id).toBe(entry1.id);
      expect(results[0].score).toBeGreaterThan(0);
    });

    it('should return results in descending score order', () => {
      const entries = [
        createContextEntry({
          entry_type: EntryType.FILE,
          source: '/file1.ts',
          summary: 'authentication security login',
          content: 'User authentication with JWT tokens',
        }),
        createContextEntry({
          entry_type: EntryType.FILE,
          source: '/file2.ts',
          summary: 'authentication module',
          content: 'Authentication logic implementation',
        }),
        createContextEntry({
          entry_type: EntryType.FILE,
          source: '/file3.ts',
          summary: 'unrelated file',
          content: 'Completely different content',
        }),
      ];

      entries.forEach((e) => index.add(e));

      const results = index.search('authentication', 10);

      expect(results.length).toBeGreaterThan(0);

      // Results should be in descending order
      for (let i = 0; i < results.length - 1; i++) {
        expect(results[i].score).toBeGreaterThanOrEqual(results[i + 1].score);
      }
    });

    it('should limit results', () => {
      const entries = Array.from({ length: 20 }, (_, i) =>
        createContextEntry({
          entry_type: EntryType.FILE,
          source: `/file${i}.ts`,
          summary: `test file ${i}`,
          content: 'test content',
        })
      );

      entries.forEach((e) => index.add(e));

      const results = index.search('test', 5);

      expect(results).toHaveLength(5);
    });

    it('should return empty array for no matches', () => {
      const entry = createContextEntry({
        entry_type: EntryType.FILE,
        source: '/file.ts',
        summary: 'TypeScript file',
        content: 'Some content',
      });

      index.add(entry);

      const results = index.search('nonexistent query xyz', 10);

      expect(results).toEqual([]);
    });
  });
});
```

#### 🟢 Green: Minimal Implementation

**File**: `src/context/search.ts`

```typescript
import { ContextEntry } from './models.js';

export interface SearchResult {
  entry_id: string;
  score: number;
  summary: string;
}

export class VectorSearchIndex {
  private documents: Map<string, string> = new Map();
  private idfScores: Map<string, number> = new Map();
  private documentVectors: Map<string, Map<string, number>> = new Map();

  add(entry: ContextEntry): void {
    if (!entry.searchable) return;

    // Combine summary and content for indexing
    const text = [entry.summary, entry.content].filter(Boolean).join(' ');
    this.documents.set(entry.id, text);

    // Recompute TF-IDF when new document added
    this.computeTfIdf();
  }

  search(query: string, limit: number = 10): SearchResult[] {
    if (this.documents.size === 0) return [];

    const queryVector = this.computeQueryVector(query);
    const scores: Array<{ entry_id: string; score: number }> = [];

    for (const [entryId, docVector] of this.documentVectors) {
      const score = this.cosineSimilarity(queryVector, docVector);
      if (score > 0) {
        scores.push({ entry_id: entryId, score });
      }
    }

    // Sort by score descending
    scores.sort((a, b) => b.score - a.score);

    // Limit results
    return scores.slice(0, limit).map((s) => ({
      entry_id: s.entry_id,
      score: s.score,
      summary: this.documents.get(s.entry_id) || '',
    }));
  }

  private tokenize(text: string): string[] {
    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter((w) => w.length > 0);
  }

  private computeTfIdf(): void {
    const termDocFreq = new Map<string, number>();
    const docTermFreq = new Map<string, Map<string, number>>();

    // Compute term frequencies
    for (const [entryId, text] of this.documents) {
      const terms = this.tokenize(text);
      const termCounts = new Map<string, number>();

      for (const term of terms) {
        termCounts.set(term, (termCounts.get(term) || 0) + 1);
      }

      docTermFreq.set(entryId, termCounts);

      // Track document frequency
      for (const term of termCounts.keys()) {
        termDocFreq.set(term, (termDocFreq.get(term) || 0) + 1);
      }
    }

    // Compute IDF scores
    const numDocs = this.documents.size;
    for (const [term, docFreq] of termDocFreq) {
      this.idfScores.set(term, Math.log(numDocs / docFreq));
    }

    // Compute TF-IDF vectors
    for (const [entryId, termCounts] of docTermFreq) {
      const vector = new Map<string, number>();
      for (const [term, count] of termCounts) {
        const tf = count / termCounts.size;
        const idf = this.idfScores.get(term) || 0;
        vector.set(term, tf * idf);
      }
      this.documentVectors.set(entryId, vector);
    }
  }

  private computeQueryVector(query: string): Map<string, number> {
    const terms = this.tokenize(query);
    const termCounts = new Map<string, number>();

    for (const term of terms) {
      termCounts.set(term, (termCounts.get(term) || 0) + 1);
    }

    const vector = new Map<string, number>();
    for (const [term, count] of termCounts) {
      const tf = count / termCounts.size;
      const idf = this.idfScores.get(term) || 0;
      vector.set(term, tf * idf);
    }

    return vector;
  }

  private cosineSimilarity(
    v1: Map<string, number>,
    v2: Map<string, number>
  ): number {
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    for (const [term, score] of v1) {
      dotProduct += score * (v2.get(term) || 0);
      norm1 += score * score;
    }

    for (const score of v2.values()) {
      norm2 += score * score;
    }

    if (norm1 === 0 || norm2 === 0) return 0;

    return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
  }
}
```

#### 🔵 Refactor: Improve Code

**File**: `src/context/search.ts` (add remove and clear methods)

```typescript
import { ContextEntry } from './models.js';

export interface SearchResult {
  entry_id: string;
  score: number;
  summary: string;
}

export class VectorSearchIndex {
  private documents: Map<string, string> = new Map();
  private idfScores: Map<string, number> = new Map();
  private documentVectors: Map<string, Map<string, number>> = new Map();

  add(entry: ContextEntry): void {
    if (!entry.searchable) return;

    // Combine summary and content for indexing
    const text = [entry.summary, entry.content].filter(Boolean).join(' ');
    this.documents.set(entry.id, text);

    // Recompute TF-IDF when new document added
    this.computeTfIdf();
  }

  remove(entryId: string): void {
    this.documents.delete(entryId);
    this.documentVectors.delete(entryId);

    // Recompute TF-IDF after removal
    if (this.documents.size > 0) {
      this.computeTfIdf();
    } else {
      this.idfScores.clear();
    }
  }

  clear(): void {
    this.documents.clear();
    this.idfScores.clear();
    this.documentVectors.clear();
  }

  search(query: string, limit: number = 10): SearchResult[] {
    if (this.documents.size === 0) return [];

    const queryVector = this.computeQueryVector(query);
    const scores: Array<{ entry_id: string; score: number }> = [];

    for (const [entryId, docVector] of this.documentVectors) {
      const score = this.cosineSimilarity(queryVector, docVector);
      if (score > 0) {
        scores.push({ entry_id: entryId, score });
      }
    }

    // Sort by score descending
    scores.sort((a, b) => b.score - a.score);

    // Limit results
    return scores.slice(0, limit).map((s) => ({
      entry_id: s.entry_id,
      score: s.score,
      summary: this.documents.get(s.entry_id) || '',
    }));
  }

  size(): number {
    return this.documents.size;
  }

  private tokenize(text: string): string[] {
    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter((w) => w.length > 0);
  }

  private computeTfIdf(): void {
    const termDocFreq = new Map<string, number>();
    const docTermFreq = new Map<string, Map<string, number>>();

    // Compute term frequencies
    for (const [entryId, text] of this.documents) {
      const terms = this.tokenize(text);
      const termCounts = new Map<string, number>();

      for (const term of terms) {
        termCounts.set(term, (termCounts.get(term) || 0) + 1);
      }

      docTermFreq.set(entryId, termCounts);

      // Track document frequency
      for (const term of termCounts.keys()) {
        termDocFreq.set(term, (termDocFreq.get(term) || 0) + 1);
      }
    }

    // Compute IDF scores
    const numDocs = this.documents.size;
    for (const [term, docFreq] of termDocFreq) {
      this.idfScores.set(term, Math.log(numDocs / docFreq));
    }

    // Compute TF-IDF vectors
    for (const [entryId, termCounts] of docTermFreq) {
      const vector = new Map<string, number>();
      for (const [term, count] of termCounts) {
        const tf = count / termCounts.size;
        const idf = this.idfScores.get(term) || 0;
        vector.set(term, tf * idf);
      }
      this.documentVectors.set(entryId, vector);
    }
  }

  private computeQueryVector(query: string): Map<string, number> {
    const terms = this.tokenize(query);
    const termCounts = new Map<string, number>();

    for (const term of terms) {
      termCounts.set(term, (termCounts.get(term) || 0) + 1);
    }

    const vector = new Map<string, number>();
    for (const [term, count] of termCounts) {
      const tf = count / termCounts.size;
      const idf = this.idfScores.get(term) || 0;
      vector.set(term, tf * idf);
    }

    return vector;
  }

  private cosineSimilarity(
    v1: Map<string, number>,
    v2: Map<string, number>
  ): number {
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    for (const [term, score] of v1) {
      dotProduct += score * (v2.get(term) || 0);
      norm1 += score * score;
    }

    for (const score of v2.values()) {
      norm2 += score * score;
    }

    if (norm1 === 0 || norm2 === 0) return 0;

    return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
  }
}
```

### Success Criteria

**Automated:**
- [ ] Tests fail before implementation: `npm test tests/context/search.test.ts`
- [ ] Tests pass after implementation: `npm test tests/context/search.test.ts`
- [ ] Results always in descending score order
- [ ] Coverage 100% for search: `npm run test:coverage -- tests/context/search.test.ts`
- [ ] Type checking passes: `npm run type-check`
- [ ] All tests pass: `npm test`

**Manual:**
- [ ] Search returns relevant results (manual inspection)
- [ ] Performance acceptable for 1000+ documents
- [ ] TF-IDF algorithm matches Python implementation

---

### Behavior 2.4-2.6: Additional Context Behaviors

**Note**: Due to length constraints, the following behaviors follow the same TDD pattern:

**Behavior 2.4**: Task Batching (<200 entry limit)
- Tests: `tests/context/batching.test.ts`
- Implementation: `src/context/batching.ts`
- Key: Respect entry count bounds, group related tasks

**Behavior 2.5**: Working Context Building
- Tests: `tests/context/working-context.test.ts`
- Implementation: `src/context/working-context.ts`
- Key: Summaries only, no full content

**Behavior 2.6**: Implementation Context Building
- Tests: `tests/context/implementation-context.test.ts`
- Implementation: `src/context/implementation-context.ts`
- Key: Full content, bounds enforcement, async iterator pattern

Each follows Red-Green-Refactor with comprehensive tests.

---

## Phase 3: Planning Pipeline Data Models

### Overview

Port planning_pipeline/models.py to TypeScript with Zod schemas. This includes RequirementNode, RequirementHierarchy, ImplementationComponents, TestableProperty, and all validation constants.

### Behaviors (Summary)

**3.1**: RequirementNode model with validation
**3.2**: RequirementHierarchy with tree operations
**3.3**: ImplementationComponents breakdown
**3.4**: TestableProperty with property types
**3.5**: Helper functions (from_string, validation)

All follow Red-Green-Refactor with property-based tests for invariants.

---

## Phase 4: BAML Integration

### Overview

Integrate TypeScript BAML client (@baml/client) with local Ollama for real API calls. Port all 28+ BAML functions from baml_src/ to TypeScript wrappers.

### Test Specification

**Given**: BAML TypeScript client configured
**When**: Calling BAML functions
**Then**: Structured responses returned from local Ollama

**Edge Cases**:
- Ollama not running
- Network timeouts
- Malformed responses
- Retry logic
- Fallback strategies

### Behaviors (Summary)

**4.1**: BAML client initialization
**4.2**: Initial extraction function (Gate 1)
**4.3**: Subprocess details function (Gate 1)
**4.4**: Tech stack extraction (Gate 2)
**4.5**: Retry and fallback strategies

**Integration Test Strategy**: Real Ollama calls (no mocks)

---

## Phase 5: Planning Pipeline Implementation

### Overview

Port the 7-step planning pipeline with checkpoint management, requirement decomposition, and beads integration.

### Behaviors (Summary)

**5.1**: Pipeline step interface and orchestration
**5.2**: Research step (step 1)
**5.3**: Memory sync step (step 2)
**5.4**: Requirement decomposition (step 3) - BAML integration
**5.5**: Context generation (step 4) - tech stack extraction
**5.6**: Planning step (step 5)
**5.7**: Phase decomposition (step 6)
**5.8**: Beads integration (step 7) - CLI wrapper
**5.9**: Checkpoint save/restore
**5.10**: Interactive prompts

All steps include unit tests (mocked BAML) and integration tests (real Ollama).

---

## Phase 6: Orchestrators & CLI

### Overview

Port root-level orchestrators and create CLI entry points with commander.

### Behaviors (Summary)

**6.1**: CLI structure with commander
**6.2**: orchestrate command
**6.3**: loop command (autonomous loop)
**6.4**: plan command (planning orchestrator)
**6.5**: Feature list validation
**6.6**: Git integration
**6.7**: Claude Code CLI invocation
**6.8**: Context compilation

Tests include unit tests for logic and integration tests with real subprocesses.

---

## Phase 7: Integration & E2E Testing

### Overview

End-to-end testing of the full pipeline with real Ollama API calls.

### Test Specification

**Given**: Complete TypeScript implementation
**When**: Running full pipeline end-to-end
**Then**: All steps complete successfully with real API calls

**Integration Tests**:
- Full pipeline execution (7 steps)
- Real Ollama API calls
- Real file system operations
- Real beads CLI calls
- Real git operations

### Behaviors (Summary)

**7.1**: E2E pipeline test (simple feature)
**7.2**: E2E pipeline test (complex feature)
**7.3**: E2E loop runner test (multiple sessions)
**7.4**: Error recovery and checkpoint restore
**7.5**: Performance benchmarks
**7.6**: Documentation generation
**7.7**: Docker container build

---

## Integration & E2E Testing Details

### E2E Test Setup

**File**: `tests/e2e/pipeline.e2e.test.ts`

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { PlanningPipeline } from '@/planning/pipeline';
import { execSync } from 'child_process';
import { existsSync, rmSync } from 'fs';
import path from 'path';

describe('E2E: Planning Pipeline', () => {
  const testProjectPath = path.join(__dirname, 'fixtures/test-project');
  const checkpointPath = path.join(testProjectPath, '.checkpoints');

  beforeAll(() => {
    // Ensure Ollama is running
    try {
      execSync('ollama list', { stdio: 'pipe' });
    } catch {
      throw new Error('Ollama is not running. Start with: ollama serve');
    }

    // Create test project
    if (!existsSync(testProjectPath)) {
      execSync(`mkdir -p ${testProjectPath}`);
    }
  });

  afterAll(() => {
    // Cleanup
    if (existsSync(checkpointPath)) {
      rmSync(checkpointPath, { recursive: true });
    }
  });

  it('should complete full pipeline with real Ollama', async () => {
    const pipeline = new PlanningPipeline({
      projectPath: testProjectPath,
      model: 'qwen2.5-coder:latest',
      featureDescription: 'Add user authentication with JWT',
    });

    const result = await pipeline.run();

    expect(result.success).toBe(true);
    expect(result.steps).toHaveLength(7);
    expect(result.steps.every((s) => s.completed)).toBe(true);

    // Verify outputs
    expect(existsSync(path.join(testProjectPath, 'research.md'))).toBe(true);
    expect(existsSync(path.join(testProjectPath, 'plan.md'))).toBe(true);
  }, 120000); // 2 minute timeout for real API calls
});
```

---

## References

### Python Source Files

**Core Modules:**
- `planning_pipeline/pipeline.py:1-303` - Main pipeline orchestrator
- `planning_pipeline/models.py:1-308` - Requirement data models
- `planning_pipeline/decomposition.py:1-930` - BAML decomposition
- `context_window_array/store.py:1-413` - Context store
- `context_window_array/search_index.py:1-294` - Vector search
- `context_window_array/models.py:1-319` - Context entry models
- `orchestrator.py:1-1366` - Main orchestrator
- `loop-runner.py:1-1381` - Autonomous loop

**Test Files:**
- All 24 test files provide behavioral specifications
- `conftest.py` files show mocking patterns

**BAML:**
- `baml_src/functions.baml:1-1507` - 28+ BAML functions
- `baml_src/schema/*.baml` - 23 schema files
- `baml_client/` - Generated Python client (reference for TypeScript)

### Research Documents

- `thoughts/searchable/research/2026-01-04-typescript-port-research.md` - This document
- `thoughts/shared/plans/2026-01-04-tdd-rust-orchestrator-port.md` - Porting patterns
- `thoughts/shared/research/2026-01-01-rust-pipeline-port.md` - Python→Rust insights

---

## Implementation Order Summary

**Week 1-2: Phase 1 - Project Setup**
- TypeScript, Vitest, Biome, Zod, fast-check
- All tooling configured and tested
- CI/CD pipeline

**Week 3-4: Phase 2 - Context Management**
- Models, Store, Search, Batching
- Working/Implementation contexts
- 100% test coverage

**Week 5: Phase 3 - Data Models**
- RequirementNode, RequirementHierarchy
- Zod schemas and validation
- Helper functions

**Week 6-8: Phase 4 - BAML Integration**
- BAML client setup
- All 28+ functions ported
- Real Ollama integration tests

**Week 9-11: Phase 5 - Planning Pipeline**
- All 7 pipeline steps
- Checkpoint management
- Beads integration

**Week 12-13: Phase 6 - Orchestrators**
- CLI with commander
- Orchestrate/loop/plan commands
- Git and Claude Code integration

**Week 14-15: Phase 7 - Integration & E2E**
- E2E tests with real Ollama
- Performance benchmarks
- Documentation
- Docker deployment

**Total: 15 weeks** to production-ready TypeScript port with 100% test coverage.

---

## Notes

- **Follow order strictly**: Complete each phase before moving to next
- **Real API calls**: Integration tests use local Ollama (no mocks)
- **100% coverage**: Every behavior tested
- **Red-Green-Refactor**: Every behavior follows TDD cycle
- **Stay in repo**: No work in silmari-oracle-wui
- **Feature parity**: Match Python functionality exactly
- **Type safety**: Strict TypeScript + Zod runtime validation

---

**Plan created**: 2026-01-05
**Estimated completion**: 15 weeks from start
**Confidence**: High (detailed research, clear architecture, test specifications)
