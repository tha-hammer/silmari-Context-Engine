# Sprint 08: Memory Search UI

**Phase:** 2 - Memory System
**Focus:** Web interface for memory management
**Dependencies:** Sprint 04 (UI Shell), Sprint 06 (Vector Search)

---

## Testable Deliverable

**Human Test:**
1. Navigate to Memories page in web app
2. See list of existing memories
3. Create a new memory via form
4. Search using natural language
5. Filter by type/date/tags
6. Click memory to view details
7. Edit and delete memories

**User Flow:**
```
[Dashboard] -> [Memories Page]
                    |
    +---------------+---------------+
    |               |               |
[List View]    [Search]       [Create New]
    |               |               |
[Memory Card] -> [Detail Modal] -> [Edit Mode]
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_019 | User Interface | 8 |
| REQ_014 | Folder organization | 8 |
| REQ_003 | Context-aware AI assistance | 17 |

### Implementation Requirements

**UI Components Domain (281 requirements)**
- REQ_007.3.1: Create dashboard layout
- REQ_019.2.1: Memory list view
- REQ_019.2.2: Memory search interface
- REQ_019.2.3: Memory detail view
- REQ_014.2.1: Folder/category organization

---

## Pages & Components

### Memories Page (`/dashboard/memories`)

```
+------------------------------------------+
|  Header                    [+ New Memory] |
+------------------------------------------+
|  Search: [_________________________] O    |
|                                          |
|  Filters: [Type v] [Date v] [Tags v]     |
+------------------------------------------+
|                                          |
|  Memory List                             |
|  +--------------------------------------+|
|  | [O] Meeting with John                ||
|  | Q4 budget discussion...              ||
|  | meeting - 2 days ago                 ||
|  +--------------------------------------+|
|  | [*] Revenue insight                  ||
|  | Q4 revenue up 15%...                 ||
|  | insight - 3 days ago                 ||
|  +--------------------------------------+|
|  | ... more memories ...                ||
|                                          |
|  [Infinite Scroll - Loading...]          |
+------------------------------------------+
```

### Components to Build

```typescript
// Page Components
<MemoriesPage>           // Main page wrapper
<MemoryList>             // List container with infinite scroll
<MemoryCard>             // Individual memory preview
<MemoryDetail>           // Full memory view (modal or side panel)
<MemoryForm>             // Create/edit form

// Search & Filter
<SearchBar>              // Natural language search input (debounced)
<FilterBar>              // Type, date, tag filters
<FilterChip>             // Active filter indicator
<DateRangePicker>        // Date filter component

// Organization
<TagInput>               // Add/remove tags
<MemoryTypeSelect>       // Type dropdown
<FolderTree>             // Future: folder organization

// Loading States
<MemoryCardSkeleton>     // Skeleton loader for memory cards
<SearchResultSkeleton>   // Skeleton for search results
```

---

## State Management

> **Pattern from Sprint 04:** Use React Query for server state (data fetching, caching, mutations) and Zustand for UI state (filters, query input, modal states).

### API Client Configuration

> **IMPORTANT:** The API client must be configured with the `/api/v1` base path to match Sprint 06's backend endpoints.

```typescript
// lib/api.ts
import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token interceptor (from Sprint 04)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

> **Note:** With `baseURL: '/api/v1'`, all API calls like `api.get('/memories')` will resolve to `/api/v1/memories`.

### React Query Hooks (Server State)

```typescript
// hooks/useMemorySearch.ts
import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query';

interface MemoryFilters {
  types: MemoryType[];
  dateRange: { start?: Date; end?: Date };
  tags: string[];
  embedding_status?: 'pending' | 'completed' | 'failed';
}

interface MemorySearchResult {
  items: Memory[];
  nextCursor: string | null;
  total: number;
}

/**
 * React Query hook for memory search with infinite scroll
 * Follows Sprint 04 patterns: TanStack Query with proper cache keys
 */
export const useMemorySearch = (query: string, filters: MemoryFilters) => {
  return useInfiniteQuery({
    queryKey: ['memories', 'search', query, filters],
    queryFn: async ({ pageParam = null }): Promise<MemorySearchResult> => {
      const response = await api.get('/memories/search', {
        params: {
          q: query,
          cursor: pageParam,
          limit: 20,
          ...filters,
        },
      });
      return response.data;
    },
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    staleTime: 1000 * 60 * 5, // 5 min cache for search results
    gcTime: 1000 * 60 * 30,   // Keep unused data for 30 min
    enabled: query.length > 0 || Object.values(filters).some(v => v?.length > 0),
  });
};

// hooks/useMemories.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export const useMemories = () => {
  const queryClient = useQueryClient();

  const memoriesQuery = useQuery({
    queryKey: ['memories'],
    queryFn: () => api.get('/memories').then(res => res.data),
    staleTime: 1000 * 60 * 2, // 2 min cache
  });

  const createMutation = useMutation({
    mutationFn: (data: MemoryInput) => api.post('/memories', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Memory> }) =>
      api.patch(`/memories/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/memories/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] });
    },
  });

  return {
    memories: memoriesQuery.data ?? [],
    isLoading: memoriesQuery.isLoading,
    error: memoriesQuery.error,
    createMemory: createMutation.mutateAsync,
    updateMemory: updateMutation.mutateAsync,
    deleteMemory: deleteMutation.mutateAsync,
  };
};
```

### Zustand Store (UI State)

```typescript
// stores/memorySearchStore.ts
import { create } from 'zustand';

interface MemoryFilters {
  types: MemoryType[];
  dateRange: { start?: Date; end?: Date };
  tags: string[];
}

interface MemorySearchState {
  // Search input
  query: string;
  debouncedQuery: string;  // Actual query sent to API (after debounce)

  // Filters
  filters: MemoryFilters;

  // UI State
  selectedMemoryId: string | null;
  isDetailOpen: boolean;
  isFormOpen: boolean;
  formMode: 'create' | 'edit';

  // Actions
  setQuery: (q: string) => void;
  setDebouncedQuery: (q: string) => void;
  setFilters: (f: Partial<MemoryFilters>) => void;
  clearFilters: () => void;
  selectMemory: (id: string | null) => void;
  openDetail: (id: string) => void;
  closeDetail: () => void;
  openForm: (mode: 'create' | 'edit', memoryId?: string) => void;
  closeForm: () => void;
}

const initialFilters: MemoryFilters = {
  types: [],
  dateRange: {},
  tags: [],
};

export const useMemorySearchStore = create<MemorySearchState>((set) => ({
  query: '',
  debouncedQuery: '',
  filters: initialFilters,
  selectedMemoryId: null,
  isDetailOpen: false,
  isFormOpen: false,
  formMode: 'create',

  setQuery: (q) => set({ query: q }),
  setDebouncedQuery: (q) => set({ debouncedQuery: q }),
  setFilters: (f) => set((state) => ({
    filters: { ...state.filters, ...f }
  })),
  clearFilters: () => set({ filters: initialFilters }),
  selectMemory: (id) => set({ selectedMemoryId: id }),
  openDetail: (id) => set({ selectedMemoryId: id, isDetailOpen: true }),
  closeDetail: () => set({ isDetailOpen: false }),
  openForm: (mode, memoryId) => set({
    formMode: mode,
    isFormOpen: true,
    selectedMemoryId: memoryId ?? null,
  }),
  closeForm: () => set({ isFormOpen: false }),
}));
```

### Zustand + React Query Integration

```typescript
// hooks/useMemorySearchWithState.ts
import { useEffect, useState } from 'react';
import { useMemorySearchStore } from '@/stores/memorySearchStore';
import { useMemorySearch } from './useMemorySearch';

// Custom debounce hook (avoids Mantine dependency)
function useDebouncedValue<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debouncedValue;
}

/**
 * Combines Zustand UI state with React Query server state
 * Pattern from Sprint 04: UI state drives server state queries
 */
export const useMemorySearchWithState = () => {
  const {
    query,
    filters,
    setDebouncedQuery,
    selectedMemoryId,
    isDetailOpen,
  } = useMemorySearchStore();

  // Debounce search input (300ms delay)
  const debouncedQuery = useDebouncedValue(query, 300);

  // Sync debounced value to store
  useEffect(() => {
    setDebouncedQuery(debouncedQuery);
  }, [debouncedQuery, setDebouncedQuery]);

  // React Query handles actual API calls
  const searchQuery = useMemorySearch(debouncedQuery, filters);

  return {
    ...searchQuery,
    query,
    filters,
    selectedMemoryId,
    isDetailOpen,
  };
};
```

---

## Search UX

### Debounced Search Input

```typescript
// components/memories/SearchBar.tsx
import { useCallback, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Search, X, Loader2 } from 'lucide-react';
import { useMemorySearchStore } from '@/stores/memorySearchStore';

interface SearchBarProps {
  isSearching?: boolean;
}

export function SearchBar({ isSearching }: SearchBarProps) {
  const { query, setQuery } = useMemorySearchStore();

  const handleClear = useCallback(() => {
    setQuery('');
  }, [setQuery]);

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        type="text"
        placeholder="Search memories..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="pl-10 pr-10"
        aria-label="Search memories"
      />
      <div className="absolute right-3 top-1/2 -translate-y-1/2">
        {isSearching ? (
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        ) : query.length > 0 ? (
          <button onClick={handleClear} aria-label="Clear search">
            <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
          </button>
        ) : null}
      </div>
    </div>
  );
}
```

### Loading States with Skeletons

```typescript
// components/memories/MemoryCardSkeleton.tsx
import { Skeleton } from '@/components/ui/skeleton';

export function MemoryCardSkeleton() {
  return (
    <div className="p-4 border rounded-lg space-y-3">
      <div className="flex items-center gap-2">
        <Skeleton className="h-5 w-5 rounded" />
        <Skeleton className="h-5 w-48" />
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <div className="flex gap-2">
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
    </div>
  );
}

// components/memories/MemoryListSkeleton.tsx
export function MemoryListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <MemoryCardSkeleton key={i} />
      ))}
    </div>
  );
}
```

### Empty States

```typescript
// components/memories/EmptyState.tsx
interface EmptyStateProps {
  type: 'no-memories' | 'no-results' | 'error';
  query?: string;
  onCreateNew?: () => void;
  onRetry?: () => void;
}

export function EmptyState({ type, query, onCreateNew, onRetry }: EmptyStateProps) {
  if (type === 'no-memories') {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium">No memories yet</h3>
        <p className="text-muted-foreground mt-1">
          Create your first memory to get started
        </p>
        <Button onClick={onCreateNew} className="mt-4">
          Create Memory
        </Button>
      </div>
    );
  }

  if (type === 'no-results') {
    return (
      <div className="text-center py-12">
        <Search className="h-12 w-12 mx-auto text-muted-foreground" />
        <h3 className="text-lg font-medium mt-4">No results found</h3>
        <p className="text-muted-foreground mt-1">
          No memories match "{query}"
        </p>
      </div>
    );
  }

  return (
    <div className="text-center py-12">
      <AlertCircle className="h-12 w-12 mx-auto text-destructive" />
      <h3 className="text-lg font-medium mt-4">Error loading memories</h3>
      <Button variant="outline" onClick={onRetry} className="mt-4">
        Retry
      </Button>
    </div>
  );
}
```

---

## Performance

### Virtualized List for Large Result Sets

```typescript
// components/memories/VirtualizedMemoryList.tsx
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef, useEffect } from 'react';

interface VirtualizedMemoryListProps {
  memories: Memory[];
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  fetchNextPage: () => void;
  onSelect: (memory: Memory) => void;
}

export function VirtualizedMemoryList({
  memories,
  hasNextPage,
  isFetchingNextPage,
  fetchNextPage,
  onSelect,
}: VirtualizedMemoryListProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: memories.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120, // Estimated card height
    overscan: 5,
  });

  const items = virtualizer.getVirtualItems();

  // Infinite scroll trigger
  useEffect(() => {
    const lastItem = items[items.length - 1];
    if (!lastItem) return;

    if (
      lastItem.index >= memories.length - 1 &&
      hasNextPage &&
      !isFetchingNextPage
    ) {
      fetchNextPage();
    }
  }, [items, hasNextPage, isFetchingNextPage, fetchNextPage, memories.length]);

  return (
    <div
      ref={parentRef}
      className="h-[600px] overflow-auto"
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {items.map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <MemoryCard
              memory={memories[virtualRow.index]}
              onSelect={() => onSelect(memories[virtualRow.index])}
            />
          </div>
        ))}
      </div>
      {isFetchingNextPage && (
        <div className="py-4 text-center">
          <Loader2 className="h-6 w-6 animate-spin mx-auto" />
        </div>
      )}
    </div>
  );
}
```

### Search Result Caching Strategy

```typescript
// lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Global defaults
      staleTime: 1000 * 60 * 2, // 2 minutes
      gcTime: 1000 * 60 * 10,   // 10 minutes garbage collection
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// Cache strategy notes:
// - ['memories', 'search', query, filters]: 5 min staleTime
//   Rationale: Search results unlikely to change frequently
// - ['memories']: 2 min staleTime
//   Rationale: List may update with new memories
// - ['memory', id]: 10 min staleTime
//   Rationale: Individual memory details rarely change

// Prefetching strategy for memory detail
export const prefetchMemoryDetail = (id: string) => {
  queryClient.prefetchQuery({
    queryKey: ['memory', id],
    queryFn: () => api.get(`/memories/${id}`).then(res => res.data),
    staleTime: 1000 * 60 * 10,
  });
};
```

---

## UI Specifications

### Memory Card with Embedding Status

```typescript
interface MemoryCardProps {
  memory: Memory;
  onSelect: () => void;
  onQuickDelete: () => void;
}

// Display:
// - Icon based on type (note, insight, task, etc.)
// - Title or first 50 chars of content
// - Content preview (100 chars)
// - Type badge
// - Embedding status indicator
// - Relative timestamp
// - Tags (max 3, +N more)

interface Memory {
  id: string;
  content: string;
  title?: string;
  type: MemoryType;
  tags: string[];
  embedding_status: 'pending' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}

// Embedding Status Indicator component
function EmbeddingStatusIndicator({ status }: { status: Memory['embedding_status'] }) {
  const statusConfig = {
    pending: { color: 'bg-yellow-500', label: 'Indexing...' },
    completed: { color: 'bg-green-500', label: 'Indexed' },
    failed: { color: 'bg-red-500', label: 'Index failed' },
  };

  const config = statusConfig[status];

  return (
    <span className="flex items-center gap-1 text-xs text-muted-foreground">
      <span className={`h-2 w-2 rounded-full ${config.color}`} />
      {config.label}
    </span>
  );
}
```

### Memory Detail Modal

```typescript
interface MemoryDetailProps {
  memory: Memory;
  onEdit: () => void;
  onDelete: () => void;
  onClose: () => void;
}

// Sections:
// - Full content (markdown rendered)
// - Metadata table
// - Tags (editable)
// - Embedding status with retry option
// - Related memories (from similarity search)
// - Source info (where it came from)
// - Timestamps
// - Edit/Delete buttons
```

### Create/Edit Form

```typescript
interface MemoryFormProps {
  memory?: Memory;  // undefined = create mode
  onSave: (data: MemoryInput) => void;
  onCancel: () => void;
}

// Fields:
// - Content (textarea, markdown support)
// - Type (select)
// - Tags (tag input)
// - Title (optional)
// - Metadata (JSON editor, advanced)
```

---

## Tasks

### Page Structure
- [ ] Create /dashboard/memories route
- [ ] Implement page layout with header
- [ ] Add "New Memory" button

### State Management (Sprint 04 Patterns)
- [ ] Set up React Query hooks for memory CRUD
- [ ] Implement useMemorySearch with useInfiniteQuery
- [ ] Create Zustand store for UI state
- [ ] Integrate debounced search (300ms)

### Memory List
- [ ] Build MemoryList component with React Query
- [ ] Implement MemoryCard with embedding_status indicator
- [ ] Add infinite scroll using useInfiniteQuery
- [ ] Implement virtualized list for performance
- [ ] Empty state when no memories

### Search & Filters
- [ ] Build SearchBar with 300ms debounce
- [ ] Implement FilterBar with Zustand state
- [ ] Connect to semantic search API via React Query
- [ ] Show search results with similarity scores
- [ ] Add filter chips for active filters

### Loading & Error States
- [ ] Create MemoryCardSkeleton component
- [ ] Implement MemoryListSkeleton
- [ ] Add loading indicator in search bar
- [ ] Error states with retry functionality
- [ ] Empty states for no-memories and no-results

### Memory Detail
- [ ] Create detail modal/panel
- [ ] Display all memory fields including embedding_status
- [ ] Show related memories
- [ ] Markdown rendering for content

### CRUD Operations
- [ ] Create memory form with React Query mutation
- [ ] Edit memory functionality
- [ ] Delete with confirmation
- [ ] Optimistic updates via React Query

### Performance
- [ ] Implement @tanstack/react-virtual for large lists
- [ ] Configure caching strategy (staleTime, gcTime)
- [ ] Add prefetching for memory detail on hover

### Polish
- [ ] Keyboard shortcuts (/, Esc)
- [ ] Responsive design
- [ ] Toast notifications for mutations

---

## Acceptance Criteria

1. Can view list of memories on dedicated page
2. Can create new memory via form
3. Search returns relevant results as user types (debounced 300ms)
4. Filters narrow down results correctly
5. Can click to view full memory details
6. Can edit existing memories
7. Can delete with confirmation
8. Related memories shown in detail view
9. Works on mobile viewport
10. Embedding status visible on memory cards
11. Infinite scroll works smoothly with virtualization
12. Skeleton loaders display during initial load and search

---

## Files to Create

```
frontend/
  src/
    app/
      dashboard/
        memories/
          page.tsx           # Memories page
          [id]/
            page.tsx         # Individual memory page (optional)

    components/
      memories/
        MemoryList.tsx
        MemoryCard.tsx
        MemoryCardSkeleton.tsx
        MemoryDetail.tsx
        MemoryForm.tsx
        SearchBar.tsx
        FilterBar.tsx
        TagInput.tsx
        EmbeddingStatusIndicator.tsx
        EmptyState.tsx
        VirtualizedMemoryList.tsx

    stores/
      memorySearchStore.ts

    hooks/
      useMemories.ts
      useMemorySearch.ts
      useMemorySearchWithState.ts
```

---

## API Integration

> **Note:** All endpoints below are relative to the API base path `/api/v1` (see API Client Configuration above).
> The frontend `api` client is pre-configured, so `api.get('/memories')` resolves to `/api/v1/memories`.

```typescript
// API endpoints used (all prefixed with /api/v1 by the axios client)
GET  /memories              - List all memories (paginated)
GET  /memories/search       - Semantic search with filters (Sprint 06)
GET  /memories/:id          - Get single memory
POST /memories              - Create memory
PATCH /memories/:id         - Update memory
DELETE /memories/:id        - Delete memory
POST /memories/:id/reindex  - Retry failed embedding
```

---

## Related Requirement Groups

- Group 003: Semantic: Question
- Group 014: Semantic: Folder
- Group 019: Semantic: User Interface
