# Sprint 16: Unified Search

**Phase:** 4 - Business Tools
**Focus:** Search across all data sources
**Dependencies:** Sprint 06 (Vectors), Sprint 14-15 (Integrations)

---

## Testable Deliverable

**Human Test:**
1. Open universal search (Cmd/Ctrl + K)
2. Type a search query
3. See results from: memories, messages, Gmail, Calendar, Drive
4. Results grouped by source
5. Click result to navigate
6. Filter by source type

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_275 | Unified search across integrations | 19 |
| REQ_062 | Aggregate insights from all data sources | 19 |

### Implementation Requirements
- REQ_275.2.1: Cross-source search
- REQ_275.2.2: Result ranking
- REQ_062.2.1: Data aggregation

---

## Architecture

```
[Search Query]
      |
      v
[Query Router]
      |
      +--> [Memory Search] --> [Vector DB]
      |
      +--> [Message Search] --> [PostgreSQL FTS]
      |
      +--> [Gmail Search] --> [Local Index / Gmail API]
      |
      +--> [Calendar Search] --> [Local Index]
      |
      +--> [Drive Search] --> [Local Index / Drive API]
      |
      v
[Result Aggregator]
      |
      v
[Ranked Results]
```

---

## Data Model

```python
class UnifiedSearchResult(BaseModel):
    id: str
    source: SearchSource
    source_id: str
    title: str
    snippet: str
    url: str | None
    score: float
    timestamp: datetime
    metadata: Dict

class SearchSource(Enum):
    MEMORY = "memory"
    MESSAGE = "message"
    # Google sources
    GMAIL = "gmail"
    GOOGLE_CALENDAR = "google_calendar"
    DRIVE = "drive"
    # Microsoft sources (from Sprint 15)
    OUTLOOK = "outlook"
    OUTLOOK_CALENDAR = "outlook_calendar"
    ONEDRIVE = "onedrive"
    # Aggregate
    ALL = "all"

class SearchFilters(BaseModel):
    sources: List[SearchSource] = [SearchSource.ALL]
    date_from: datetime | None
    date_to: datetime | None
    types: List[str] = []  # memory_type, file_type, etc.
```

---

## API Endpoints

```yaml
# Unified Search
GET /api/v1/search
  Query:
    q: string (required)
    sources: string[] (default: all)
    date_from: datetime
    date_to: datetime
    limit: int (default: 20)
  Response:
    query: string
    total_results: int
    results: [
      {
        source: string
        results: UnifiedSearchResult[]
      }
    ]
    facets: {
      sources: { memory: 10, gmail: 5, ... }
    }

# Quick Search (for command palette)
GET /api/v1/search/quick
  Query: ?q=project&limit=5
  Response: UnifiedSearchResult[] (top results only)

# Search Suggestions
GET /api/v1/search/suggestions
  Query: ?q=proj
  Response: string[] (autocomplete suggestions)
```

---

## Tasks

### Backend - Search Aggregator
- [ ] Create unified search service
- [ ] Implement source-specific searchers
- [ ] Build result aggregator
- [ ] Implement ranking algorithm

### Backend - Source Searchers
- [ ] Memory semantic search
- [ ] Message full-text search
- [ ] Gmail search (local/API hybrid)
- [ ] Calendar event search
- [ ] Drive file search

### Backend - Indexing
- [ ] Create local search indexes
- [ ] Background index updates
- [ ] Index sync status tracking

### Frontend - Search UI
- [ ] Command palette (Cmd+K)
- [ ] Full search page
- [ ] Result components per source
- [ ] Filter controls

### Frontend - Navigation
- [ ] Click to open result
- [ ] Preview panel
- [ ] Keyboard navigation

---

## Acceptance Criteria

1. Cmd/Ctrl+K opens search
2. Results from all sources appear
3. Results grouped by source
4. Can filter by source
5. Results are relevance-ranked
6. Click navigates to item
7. Search is fast (<500ms)

---

## Search Implementation

```python
class UnifiedSearchService:
    def __init__(self, integration_service: IntegrationService):
        self.integration_service = integration_service
        self.searchers = {
            SearchSource.MEMORY: MemorySearcher(),
            SearchSource.MESSAGE: MessageSearcher(),
            SearchSource.GMAIL: GmailSearcher(),
            SearchSource.GOOGLE_CALENDAR: GoogleCalendarSearcher(),
            SearchSource.DRIVE: DriveSearcher(),
            SearchSource.OUTLOOK: OutlookSearcher(),
            SearchSource.OUTLOOK_CALENDAR: OutlookCalendarSearcher(),
            SearchSource.ONEDRIVE: OneDriveSearcher(),
        }

        # Map sources to required integrations
        self.integration_requirements = {
            SearchSource.GMAIL: "google",
            SearchSource.GOOGLE_CALENDAR: "google",
            SearchSource.DRIVE: "google",
            SearchSource.OUTLOOK: "microsoft",
            SearchSource.OUTLOOK_CALENDAR: "microsoft",
            SearchSource.ONEDRIVE: "microsoft",
        }

    async def get_available_sources(self, user_id: UUID) -> List[SearchSource]:
        """Get sources available based on user's connected integrations."""
        available = [SearchSource.MEMORY, SearchSource.MESSAGE]  # Always available

        user_integrations = await self.integration_service.get_user_integrations(user_id)
        connected_providers = {
            i.provider for i in user_integrations
            if i.status == IntegrationStatus.ACTIVE
        }

        for source, provider in self.integration_requirements.items():
            if provider in connected_providers:
                available.append(source)

        return available

    async def search(
        self,
        query: str,
        user_id: UUID,
        filters: SearchFilters
    ) -> Dict[str, List[UnifiedSearchResult]]:

        # Get available sources for this user
        available_sources = await self.get_available_sources(user_id)

        sources = filters.sources
        if SearchSource.ALL in sources:
            sources = available_sources
        else:
            # Filter to only available sources
            sources = [s for s in sources if s in available_sources]

        # Search all sources in parallel
        tasks = [
            self.searchers[source].search(query, user_id, filters)
            for source in sources
            if source in self.searchers
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        aggregated = {}
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                aggregated[source.value] = []
            else:
                aggregated[source.value] = result

        return aggregated

    def rank_results(
        self,
        results: Dict[str, List[UnifiedSearchResult]]
    ) -> List[UnifiedSearchResult]:
        """Interleave and rank results from all sources."""
        all_results = []
        for source_results in results.values():
            all_results.extend(source_results)

        # Sort by score, with recency boost
        return sorted(
            all_results,
            key=lambda r: r.score * recency_boost(r.timestamp),
            reverse=True
        )
```

---

## UI Components

```typescript
// Command Palette
<CommandPalette open={isOpen} onClose={close}>
  <CommandInput
    value={query}
    onChange={setQuery}
    placeholder="Search everything..."
  />

  <CommandResults>
    {Object.entries(groupedResults).map(([source, results]) => (
      <CommandGroup key={source} heading={source}>
        {results.map(result => (
          <CommandItem
            key={result.id}
            onSelect={() => navigateTo(result)}
          >
            <SourceIcon source={result.source} />
            <ResultTitle>{result.title}</ResultTitle>
            <ResultSnippet>{result.snippet}</ResultSnippet>
          </CommandItem>
        ))}
      </CommandGroup>
    ))}
  </CommandResults>
</CommandPalette>
```

---

## Files to Create

```
src/
  search/
    __init__.py
    service.py
    router.py
    schemas.py
    searchers/
      __init__.py
      base.py
      memory.py
      message.py
      gmail.py
      calendar.py
      drive.py
    ranking.py
    indexer.py

frontend/src/
  components/
    search/
      CommandPalette.tsx
      SearchPage.tsx
      SearchResult.tsx
      SourceFilter.tsx
```

---

## Related Requirement Groups

- Group 008: Semantic Search
- Group 010: Query Processing
- Integration domain

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added Microsoft sources to SearchSource enum (OUTLOOK, OUTLOOK_CALENDAR, ONEDRIVE)
2. Renamed CALENDAR to GOOGLE_CALENDAR for clarity
3. Added `get_available_sources()` method to check user's connected integrations
4. Added `integration_requirements` mapping to know which provider each source needs
5. Search now only queries sources the user has actually connected
6. Added all corresponding searcher classes (OutlookSearcher, OneDriveSearcher, etc.)

**Cross-Sprint Dependencies:**
- Sprint 13: Integration status check for connected providers
- Sprint 14: Gmail/Calendar/Drive FTS indexes for search
- Sprint 15: Outlook/OneDrive FTS indexes for search
- Sprint 06: Vector DB for memory semantic search

**Note:** The FTS indexes on gmail_messages and outlook_messages tables (created in Sprints 14/15) enable fast full-text search without additional configuration.
