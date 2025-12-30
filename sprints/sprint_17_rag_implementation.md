# Sprint 17: RAG Implementation

**Phase:** 5 - AI Enhancement
**Focus:** Retrieval Augmented Generation
**Dependencies:** Sprint 06 (Vectors), Sprint 12 (Chat Memory)

---

## Testable Deliverable

**Human Test:**
1. Ask AI about something in your memories
2. AI response cites specific memories
3. See [Source: Memory #123] citations
4. Click citation to view source
5. Response accuracy improved with context

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_182 | RAG for memory-enhanced responses | 18 |
| REQ_003 | Context-aware AI assistance | 17 |

### Implementation Requirements
- REQ_182.2.1: Retrieve relevant context
- REQ_182.2.2: Inject context into prompts
- REQ_182.2.3: Generate cited responses

---

## RAG Pipeline

```
[User Query]
      |
      v
[Query Analysis]
      |
      +--> [Identify Intent]
      |
      +--> [Extract Keywords]
      |
      v
[Multi-Source Retrieval]
      |
      +--> [Vector Search (Memories)]
      |
      +--> [Keyword Search (Messages)]
      |
      +--> [Recent Context (Conversation)]
      |
      v
[Re-Ranking]
      |
      v
[Context Assembly]
      |
      v
[LLM Generation with Citations]
      |
      v
[Post-Process Citations]
```

---

## API Enhancements

```yaml
# Enhanced AI Chat
POST /api/v1/conversations/{id}/messages
  Request:
    content: string
    rag_config: {
      enable_rag: bool (default: true)
      max_sources: int (default: 5)
      include_citations: bool (default: true)
      source_types: string[] (memories, messages, integrations)
    }
  Response:
    ai_response: Message
    sources: [
      {
        id: uuid
        type: string
        content_snippet: string
        relevance_score: float
        citation_id: string  # e.g., [1], [2]
      }
    ]

# Get Sources for Message
GET /api/v1/messages/{id}/sources
  Response: Source[]
```

---

## Tasks

### Backend - Query Analysis
- [ ] Implement query intent detection
- [ ] Extract key entities and keywords
- [ ] Determine optimal retrieval strategy

### Backend - Multi-Source Retrieval
- [ ] Enhance memory vector search
- [ ] Add message keyword search
- [ ] Include integration data search
- [ ] Implement hybrid search (vector + keyword)

### Backend - Re-Ranking
- [ ] Score relevance across sources
- [ ] Apply diversity penalty
- [ ] Consider recency
- [ ] Deduplicate similar content

### Backend - Citation Generation
- [ ] Prompt engineering for citations
- [ ] Parse LLM output for citations
- [ ] Map citations to sources
- [ ] Store citation metadata

### Frontend - Citation UI
- [ ] Inline citation markers [1]
- [ ] Citation hover preview
- [ ] Click to view source
- [ ] Sources panel in chat

---

## Acceptance Criteria

1. AI responses include citations
2. Citations map to real sources
3. Multiple source types supported
4. Click citation shows source
5. RAG can be toggled off
6. Response quality measurably better

---

## RAG Service

```python
class RAGService:
    def __init__(self):
        self.memory_retriever = MemoryRetriever()
        self.message_retriever = MessageRetriever()
        self.reranker = CrossEncoderReranker()

    async def retrieve_context(
        self,
        query: str,
        user_id: UUID,
        config: RAGConfig
    ) -> List[RetrievedSource]:
        """Retrieve relevant context from multiple sources."""

        # 1. Query analysis
        query_info = await self.analyze_query(query)

        # 2. Parallel retrieval
        tasks = []
        if "memories" in config.source_types:
            tasks.append(self.memory_retriever.search(
                query, user_id, limit=config.max_sources * 2
            ))
        if "messages" in config.source_types:
            tasks.append(self.message_retriever.search(
                query, user_id, limit=config.max_sources * 2
            ))

        raw_results = await asyncio.gather(*tasks)

        # 3. Combine and flatten
        all_sources = []
        for results in raw_results:
            all_sources.extend(results)

        # 4. Re-rank with cross-encoder
        ranked = await self.reranker.rerank(query, all_sources)

        # 5. Select top sources
        return ranked[:config.max_sources]

    async def generate_with_citations(
        self,
        query: str,
        sources: List[RetrievedSource],
        conversation_history: List[Message]
    ) -> Tuple[str, List[Citation]]:
        """Generate response with inline citations."""

        # Format sources for prompt
        source_context = self.format_sources(sources)

        prompt = f"""Based on the following sources, answer the user's question.
Include citations in your response using [1], [2], etc. to reference sources.

Sources:
{source_context}

User question: {query}

Provide a helpful response with citations where relevant."""

        response = await self.llm.generate(prompt)

        # Parse citations from response
        citations = self.parse_citations(response, sources)

        return response, citations

    def format_sources(self, sources: List[RetrievedSource]) -> str:
        formatted = ""
        for i, source in enumerate(sources, 1):
            formatted += f"[{i}] {source.type.upper()}: {source.content[:500]}\n\n"
        return formatted
```

---

## Database Schema for Citations

```sql
-- Store citations for each AI message
CREATE TABLE message_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    citation_marker VARCHAR(10) NOT NULL,  -- "[1]", "[2]", etc.
    position_in_response INT,
    source_type VARCHAR(50) NOT NULL,      -- memory, gmail, outlook, etc.
    source_id UUID NOT NULL,               -- FK to the source table
    relevance_score FLOAT,
    content_snippet TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_citations_message ON message_citations(message_id);
CREATE INDEX idx_citations_source ON message_citations(source_type, source_id);
```

---

## Re-Ranking with Cross-Encoder

```python
from sentence_transformers import CrossEncoder

class CrossEncoderReranker:
    """Re-rank search results using a cross-encoder model for better relevance."""

    def __init__(self):
        # Use MS-MARCO trained model for passage ranking
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    async def rerank(
        self,
        query: str,
        sources: List[RetrievedSource],
        top_k: int = 5
    ) -> List[RetrievedSource]:
        """Re-rank sources by relevance to query."""
        if not sources:
            return []

        # Prepare pairs for cross-encoder
        pairs = [(query, source.content) for source in sources]

        # Score all pairs
        scores = self.model.predict(pairs)

        # Attach scores and sort
        for source, score in zip(sources, scores):
            source.relevance_score = float(score)

        ranked = sorted(sources, key=lambda x: x.relevance_score, reverse=True)
        return ranked[:top_k]
```

---

## Citation Parsing

```python
import re

def parse_citations(response: str, sources: List[RetrievedSource]) -> List[Citation]:
    """Extract citation markers from response and map to sources."""
    citations = []

    # Find all [N] patterns
    pattern = r'\[(\d+)\]'
    matches = re.finditer(pattern, response)

    for match in matches:
        citation_num = int(match.group(1))
        if 1 <= citation_num <= len(sources):
            source = sources[citation_num - 1]
            citations.append(Citation(
                marker=f"[{citation_num}]",
                position=match.start(),
                source_id=source.id,
                source_type=source.type,
                content_snippet=source.content[:200]
            ))

    return citations
```

---

## UI Components

```typescript
// Chat message with citations
<AIMessage content={message.content} sources={message.sources}>
  {/* Render with inline citations */}
  <CitedContent
    text={message.content}
    citations={message.sources}
    onCitationClick={showSourcePanel}
  />

  {/* Source list */}
  <SourcesPanel sources={message.sources}>
    {sources.map((source, i) => (
      <SourceCard
        key={source.id}
        number={i + 1}
        type={source.type}
        snippet={source.content_snippet}
        onClick={() => openSource(source)}
      />
    ))}
  </SourcesPanel>
</AIMessage>

// Citation marker component
<CitationMarker number={1} onClick={() => scrollToSource(1)}>
  [1]
</CitationMarker>
```

---

## Files to Create

```
src/
  rag/
    __init__.py
    service.py
    retrievers/
      __init__.py
      memory.py
      message.py
      hybrid.py
    reranker.py
    citation.py
    prompts.py

frontend/src/
  components/
    ai/
      CitedContent.tsx
      CitationMarker.tsx
      SourcesPanel.tsx
      SourceCard.tsx
```

---

## Related Requirement Groups

- Group 008: Semantic Search
- Group 012: Machine Learning
- AI context domain

---

## Integration Data Retrievers

```python
# Additional retrievers for integration data (referenced in RAGConfig.source_types)

class IntegrationRetriever:
    """Base class for integration-sourced retrieval."""

    def __init__(self, search_service: UnifiedSearchService):
        self.search_service = search_service

    async def search(
        self,
        query: str,
        user_id: UUID,
        limit: int = 10
    ) -> List[RetrievedSource]:
        # Use unified search from Sprint 16
        results = await self.search_service.search(
            query=query,
            user_id=user_id,
            filters=SearchFilters(
                sources=[
                    SearchSource.GMAIL,
                    SearchSource.OUTLOOK,
                    SearchSource.GOOGLE_CALENDAR,
                    SearchSource.OUTLOOK_CALENDAR,
                ],
                limit=limit
            )
        )

        # Convert to RetrievedSource format
        sources = []
        for source_type, items in results.items():
            for item in items:
                sources.append(RetrievedSource(
                    id=item.source_id,
                    type=source_type,
                    content=f"{item.title}\n{item.snippet}",
                    relevance_score=item.score,
                    metadata=item.metadata
                ))

        return sources
```

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added `message_citations` database schema for storing citation references
2. Added `CrossEncoderReranker` with specific model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
3. Added `IntegrationRetriever` class for Gmail/Outlook/Calendar data retrieval
4. Connected to Sprint 16 UnifiedSearchService for integration data search
5. Citations now persist to database for later retrieval via `/api/v1/messages/{id}/sources`

**Cross-Sprint Dependencies:**
- Sprint 06: Vector DB for memory semantic search
- Sprint 10: AI chat LLM service for generation
- Sprint 16: UnifiedSearchService for integration data retrieval
- Sprint 14/15: Gmail and Outlook tables as citation sources

**Model Requirements:**
- `sentence-transformers` library for CrossEncoder
- Model download: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~80MB)
