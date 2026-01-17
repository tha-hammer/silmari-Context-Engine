# Sprint 12: Chat Memory Integration

**Phase:** 3 - Communication
**Focus:** AI responses enriched with user memories
**Dependencies:** Sprint 01 (Data Foundation), Sprint 06 (Vectors), Sprint 10 (AI Chat)

---

## Testable Deliverable

**Human Test:**
1. Create several memories about a project
2. Start AI chat and ask about the project
3. AI response references your stored memories
4. See which memories were used in response
5. Toggle memory inclusion on/off
6. Auto-extract memories from conversations

**Test Flow:**
```
# Previously stored memory:
"Project Alpha launch date: March 15, 2024. Budget: $50,000"

# User asks AI:
"What's the budget for Project Alpha?"

# AI responds:
"Based on your notes, Project Alpha has a budget of $50,000,
with a launch date of March 15, 2024."

# UI shows:
[Memory Used: "Project Alpha launch date..."]
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_182 | RAG for memory-enhanced responses | 18 |
| REQ_003 | Context-aware AI assistance | 17 |
| REQ_014 | Extract memories from conversations | 17 |

### Implementation Requirements

- REQ_182.2.1: Retrieve relevant memories for context
- REQ_182.2.2: Format memories for LLM consumption
- REQ_182.2.3: Track which memories were used
- REQ_014.2.1: Auto-extract from chat conversations
- REQ_003.2.1: Personalized responses

---

## Database Schema Reference

> **Note:** The `message_memory_usage` junction table is defined in **Sprint 01 (Data Foundation)**:
> ```sql
> CREATE TABLE message_memory_usage (
>     message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
>     memory_id UUID REFERENCES memories(id) ON DELETE CASCADE,
>     relevance_score FLOAT,
>     created_at TIMESTAMPTZ DEFAULT NOW(),
>     PRIMARY KEY (message_id, memory_id)
> );
> ```
> This sprint implements the services and logic that utilize this table.

---

## Architecture

```
[User Message]
    |
    v
[Memory Search]----> [Top N Relevant Memories]
    |                         |
    v                         v
[Context Builder] <-----------+
    |
    v
[LLM Request with Memory Context]
    |
    v
[AI Response]
    |
    +----> [Track Memory Usage]
    |
    +----> [Extract New Memories (optional)]
    |
    +----> [Memory Citations in Response]
```

---

## Memory Retrieval Pipeline

The memory retrieval pipeline selects the most relevant memories to include in AI context.

```python
from uuid import UUID
from typing import Optional
from pydantic import BaseModel

class RetrievedMemory(BaseModel):
    """Memory with relevance scoring for AI context."""
    memory: Memory
    relevance_score: float
    snippet: str  # Truncated for display


class MemoryContextService:
    """Service for retrieving relevant memories for AI context."""

    def __init__(
        self,
        vector_store: VectorStore,
        memory_repository: MemoryRepository,
        max_context_tokens: int = 2000
    ):
        self.vector_store = vector_store
        self.memory_repository = memory_repository
        self.max_context_tokens = max_context_tokens

    async def get_relevant_memories(
        self,
        conversation_id: UUID,
        query: str,
        user_id: UUID,
        limit: int = 10,
        min_relevance: float = 0.5,
        memory_types: Optional[list[str]] = None
    ) -> list[RetrievedMemory]:
        """
        Retrieve memories relevant to the current conversation context.

        Pipeline:
        1. Get recent conversation context for query expansion
        2. Vector search for semantically similar memories
        3. Apply relevance scoring and filtering
        4. Rank by recency + relevance combination
        5. Return top memories within token budget
        """
        # Step 1: Get recent conversation for context expansion
        recent_messages = await self._get_recent_context(conversation_id, limit=5)
        expanded_query = self._expand_query(query, recent_messages)

        # Step 2: Vector search for candidate memories
        candidates = await self.vector_store.similarity_search(
            query=expanded_query,
            user_id=user_id,
            limit=limit * 2,  # Fetch extra for filtering
            memory_types=memory_types
        )

        # Step 3: Score and filter candidates
        scored_memories = []
        for memory, vector_score in candidates:
            relevance_score = self._compute_relevance_score(
                memory=memory,
                vector_score=vector_score,
                query=query,
                recent_messages=recent_messages
            )

            if relevance_score >= min_relevance:
                scored_memories.append(RetrievedMemory(
                    memory=memory,
                    relevance_score=relevance_score,
                    snippet=memory.content[:200] + "..." if len(memory.content) > 200 else memory.content
                ))

        # Step 4: Rank by combined score (relevance + recency)
        scored_memories.sort(key=lambda m: m.relevance_score, reverse=True)

        # Step 5: Fit within token budget
        return self._fit_to_token_budget(scored_memories[:limit])

    def _compute_relevance_score(
        self,
        memory: Memory,
        vector_score: float,
        query: str,
        recent_messages: list[Message]
    ) -> float:
        """
        Compute combined relevance score.

        Factors:
        - Vector similarity (semantic match): 50%
        - Recency boost: 20%
        - Memory type priority: 15%
        - Usage frequency: 15%
        """
        # Base vector similarity
        score = vector_score * 0.5

        # Recency boost (memories from last 7 days get boost)
        days_old = (datetime.utcnow() - memory.created_at).days
        recency_boost = max(0, 1 - (days_old / 30)) * 0.2
        score += recency_boost

        # Memory type priority (facts > notes > ideas)
        type_weights = {"fact": 0.15, "note": 0.10, "idea": 0.05}
        score += type_weights.get(memory.memory_type, 0.05)

        # Usage frequency boost
        if memory.metadata and memory.metadata.get("usage_count", 0) > 0:
            usage_boost = min(0.15, memory.metadata["usage_count"] * 0.03)
            score += usage_boost

        return min(1.0, score)

    def _fit_to_token_budget(
        self,
        memories: list[RetrievedMemory]
    ) -> list[RetrievedMemory]:
        """Select memories that fit within token budget."""
        selected = []
        current_tokens = 0

        for memory in memories:
            # Estimate tokens (rough approximation)
            memory_tokens = len(memory.memory.content.split()) * 1.3

            if current_tokens + memory_tokens <= self.max_context_tokens:
                selected.append(memory)
                current_tokens += memory_tokens
            else:
                break

        return selected
```

---

## Memory Usage Tracking

Track which memories influenced each AI response using the Sprint 01 junction table.

```python
from uuid import UUID
from typing import List, Tuple

class MemoryUsageService:
    """Track memory usage in AI responses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_ai_response_with_memories(
        self,
        message: Message,
        used_memories: list[tuple[Memory, float]]  # (memory, relevance_score)
    ) -> None:
        """
        Record which memories were used to generate an AI response.

        Args:
            message: The AI response message
            used_memories: List of (Memory, relevance_score) tuples
        """
        for memory, score in used_memories:
            await self.db.execute(
                """
                INSERT INTO message_memory_usage
                    (message_id, memory_id, relevance_score)
                VALUES (:message_id, :memory_id, :relevance_score)
                ON CONFLICT (message_id, memory_id) DO UPDATE
                SET relevance_score = :relevance_score
                """,
                {
                    "message_id": message.id,
                    "memory_id": memory.id,
                    "relevance_score": score
                }
            )

        await self.db.commit()

    async def get_memories_for_message(
        self,
        message_id: UUID
    ) -> list[dict]:
        """Retrieve memories used for a specific message."""
        result = await self.db.execute(
            """
            SELECT
                m.id, m.content, m.memory_type, m.metadata,
                mmu.relevance_score, mmu.created_at as used_at
            FROM message_memory_usage mmu
            JOIN memories m ON m.id = mmu.memory_id
            WHERE mmu.message_id = :message_id
            ORDER BY mmu.relevance_score DESC
            """,
            {"message_id": message_id}
        )
        return [dict(row) for row in result.fetchall()]

    async def increment_memory_usage_count(
        self,
        memory_ids: list[UUID]
    ) -> None:
        """Increment usage count for memories (for relevance scoring)."""
        await self.db.execute(
            """
            UPDATE memories
            SET metadata = jsonb_set(
                COALESCE(metadata, '{}'::jsonb),
                '{usage_count}',
                (COALESCE(metadata->>'usage_count', '0')::int + 1)::text::jsonb
            )
            WHERE id = ANY(:memory_ids)
            """,
            {"memory_ids": memory_ids}
        )
        await self.db.commit()
```

---

## Memory Citations

Show users which memories influenced AI responses.

```python
class MemoryCitationFormatter:
    """Format memory citations in AI responses."""

    @staticmethod
    def format_inline_citations(
        response: str,
        used_memories: list[RetrievedMemory]
    ) -> str:
        """
        Add inline citations to AI response.

        Example output:
        "The project budget is $50,000 [1] with a March deadline [2]."
        """
        # Simple citation format - AI can reference by number
        citation_map = {i+1: m.memory.id for i, m in enumerate(used_memories)}
        return response  # AI should include [1], [2] references naturally

    @staticmethod
    def format_citation_footer(
        used_memories: list[RetrievedMemory]
    ) -> list[dict]:
        """
        Generate citation footer for display.

        Returns structured data for UI to render.
        """
        return [
            {
                "citation_number": i + 1,
                "memory_id": str(m.memory.id),
                "snippet": m.snippet,
                "memory_type": m.memory.memory_type,
                "relevance_score": round(m.relevance_score, 2),
                "created_at": m.memory.created_at.isoformat()
            }
            for i, m in enumerate(used_memories)
        ]


def get_system_prompt_with_citations(memories: list[RetrievedMemory]) -> str:
    """
    Build system prompt that instructs AI to cite memories.
    """
    if not memories:
        return "You are a helpful AI assistant."

    prompt = """You are a helpful AI assistant with access to the user's stored memories.

When using information from the provided memories, cite them using [1], [2], etc.
Only cite memories that directly support your response.

User's relevant memories:
"""

    for i, retrieved in enumerate(memories, 1):
        memory = retrieved.memory
        prompt += f"\n[{i}] ({memory.memory_type.upper()}) {memory.content[:500]}"
        if memory.metadata:
            prompt += f"\n    Context: {memory.metadata}"
        prompt += f"\n    (Saved: {memory.created_at.strftime('%Y-%m-%d')})\n"

    prompt += """
---
Use these memories to provide personalized, accurate responses.
Cite relevant memories using their numbers [1], [2], etc.
"""

    return prompt
```

---

## Automatic Memory Extraction

Extract new memories from conversations using Celery for async processing.

```python
from celery import shared_task
from uuid import UUID

@shared_task(bind=True, max_retries=3)
def extract_memories_from_conversation(
    self,
    conversation_id: str,
    user_id: str,
    message_range: dict = None
):
    """
    Celery task to extract memories from conversation.

    Runs asynchronously after conversation ends or on-demand.
    """
    try:
        service = MemoryExtractionService()
        extracted = service.extract_memories(
            conversation_id=UUID(conversation_id),
            user_id=UUID(user_id),
            start_message_id=message_range.get("start_id") if message_range else None,
            end_message_id=message_range.get("end_id") if message_range else None
        )

        # Store extracted memories (pending user approval if configured)
        for memory in extracted:
            service.save_extracted_memory(memory, pending_approval=True)

        return {"status": "success", "extracted_count": len(extracted)}

    except Exception as e:
        self.retry(exc=e, countdown=60)


class MemoryExtractionService:
    """Extract memories from chat conversations."""

    def __init__(self, llm_client: LLMClient, memory_repository: MemoryRepository):
        self.llm_client = llm_client
        self.memory_repository = memory_repository

    async def extract_memories(
        self,
        conversation_id: UUID,
        user_id: UUID,
        start_message_id: Optional[UUID] = None,
        end_message_id: Optional[UUID] = None
    ) -> list[ExtractedMemory]:
        """
        Use LLM to extract memorable information from conversation.

        Extraction targets:
        - Facts mentioned by user
        - Preferences expressed
        - Decisions made
        - Important dates/deadlines
        - Project information
        """
        messages = await self._get_messages(
            conversation_id, start_message_id, end_message_id
        )

        if not messages:
            return []

        # Format conversation for LLM
        conversation_text = self._format_conversation(messages)

        # Call LLM for extraction
        extraction_prompt = self._build_extraction_prompt(conversation_text)
        result = await self.llm_client.complete(extraction_prompt)

        # Parse extracted memories
        extracted = self._parse_extraction_result(result, user_id)

        # Deduplicate against existing memories
        deduplicated = await self._deduplicate(extracted, user_id)

        return deduplicated

    def _build_extraction_prompt(self, conversation: str) -> str:
        return f"""Analyze this conversation and extract memorable information.

Focus on:
1. FACTS: Specific information mentioned (dates, numbers, names, places)
2. PREFERENCES: User preferences or opinions expressed
3. DECISIONS: Choices or decisions made during conversation
4. PROJECTS: Information about ongoing projects or tasks
5. CONTACTS: People mentioned and their roles

For each extracted memory, provide:
- Type: fact/preference/decision/project/contact
- Content: The memory itself (clear, standalone statement)
- Confidence: How certain (0.0-1.0)

Conversation:
{conversation}

Extract memories in JSON format:
[{{"type": "...", "content": "...", "confidence": 0.0}}]
"""

    async def _deduplicate(
        self,
        extracted: list[ExtractedMemory],
        user_id: UUID
    ) -> list[ExtractedMemory]:
        """Remove memories that duplicate existing ones."""
        unique = []

        for memory in extracted:
            # Search for similar existing memories
            similar = await self.memory_repository.find_similar(
                content=memory.content,
                user_id=user_id,
                threshold=0.85
            )

            if not similar:
                unique.append(memory)

        return unique


# Celery beat schedule for periodic extraction
CELERY_BEAT_SCHEDULE = {
    'extract-memories-from-idle-conversations': {
        'task': 'tasks.extract_idle_conversations',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'args': ()
    }
}


@shared_task
def extract_idle_conversations():
    """Extract memories from conversations idle for >1 hour."""
    conversations = get_idle_conversations(idle_minutes=60)

    for conv in conversations:
        if not conv.memories_extracted:
            extract_memories_from_conversation.delay(
                str(conv.id),
                str(conv.user_id)
            )
```

---

## Memory Feedback Loop

Allow users to provide feedback on memory usefulness.

```python
from enum import Enum

class MemoryFeedback(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"
    OUTDATED = "outdated"


class MemoryFeedbackService:
    """Handle user feedback on memory usage."""

    async def record_feedback(
        self,
        message_id: UUID,
        memory_id: UUID,
        feedback: MemoryFeedback,
        user_id: UUID,
        comment: Optional[str] = None
    ) -> None:
        """
        Record user feedback on a memory's usefulness.

        This feedback is used to:
        1. Adjust relevance scoring weights
        2. Flag incorrect/outdated memories for review
        3. Improve memory extraction quality
        """
        await self.db.execute(
            """
            INSERT INTO memory_feedback
                (message_id, memory_id, user_id, feedback, comment, created_at)
            VALUES (:message_id, :memory_id, :user_id, :feedback, :comment, NOW())
            """,
            {
                "message_id": message_id,
                "memory_id": memory_id,
                "user_id": user_id,
                "feedback": feedback.value,
                "comment": comment
            }
        )

        # Handle specific feedback types
        if feedback == MemoryFeedback.INCORRECT:
            await self._flag_memory_for_review(memory_id, "incorrect")
        elif feedback == MemoryFeedback.OUTDATED:
            await self._flag_memory_for_review(memory_id, "outdated")
        elif feedback == MemoryFeedback.HELPFUL:
            await self._boost_memory_relevance(memory_id)
        elif feedback == MemoryFeedback.NOT_HELPFUL:
            await self._decrease_memory_relevance(memory_id)

        await self.db.commit()

    async def _boost_memory_relevance(self, memory_id: UUID) -> None:
        """Increase memory's relevance weight based on positive feedback."""
        await self.db.execute(
            """
            UPDATE memories
            SET metadata = jsonb_set(
                COALESCE(metadata, '{}'::jsonb),
                '{helpful_count}',
                (COALESCE(metadata->>'helpful_count', '0')::int + 1)::text::jsonb
            )
            WHERE id = :memory_id
            """,
            {"memory_id": memory_id}
        )

    async def _decrease_memory_relevance(self, memory_id: UUID) -> None:
        """Decrease memory's relevance weight based on negative feedback."""
        await self.db.execute(
            """
            UPDATE memories
            SET metadata = jsonb_set(
                COALESCE(metadata, '{}'::jsonb),
                '{not_helpful_count}',
                (COALESCE(metadata->>'not_helpful_count', '0')::int + 1)::text::jsonb
            )
            WHERE id = :memory_id
            """,
            {"memory_id": memory_id}
        )

    async def _flag_memory_for_review(
        self,
        memory_id: UUID,
        reason: str
    ) -> None:
        """Flag memory for user review."""
        await self.db.execute(
            """
            UPDATE memories
            SET metadata = jsonb_set(
                jsonb_set(
                    COALESCE(metadata, '{}'::jsonb),
                    '{needs_review}',
                    'true'::jsonb
                ),
                '{review_reason}',
                :reason::jsonb
            )
            WHERE id = :memory_id
            """,
            {"memory_id": memory_id, "reason": f'"{reason}"'}
        )

    async def get_feedback_stats(
        self,
        user_id: UUID
    ) -> dict:
        """Get aggregated feedback statistics for a user."""
        result = await self.db.execute(
            """
            SELECT
                feedback,
                COUNT(*) as count
            FROM memory_feedback
            WHERE user_id = :user_id
            GROUP BY feedback
            """,
            {"user_id": user_id}
        )
        return {row["feedback"]: row["count"] for row in result.fetchall()}
```

**Additional Schema (extends Sprint 01):**
```sql
-- Memory feedback tracking
CREATE TABLE memory_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    memory_id UUID REFERENCES memories(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    feedback VARCHAR(20) NOT NULL,  -- helpful, not_helpful, incorrect, outdated
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memory_feedback_memory ON memory_feedback(memory_id);
CREATE INDEX idx_memory_feedback_user ON memory_feedback(user_id);
```

---

## API Enhancements

```yaml
# Send Message (Enhanced)
POST /api/v1/conversations/{id}/messages
  Request:
    content: string
    use_memories: bool (default: true)
    memory_types: string[] (optional filter)
  Response:
    user_message: Message
    ai_response: Message
    memories_used: [
      {
        memory_id: uuid
        relevance_score: float
        snippet: string
        citation_number: int
      }
    ]

# Get Message Context
GET /api/v1/messages/{id}/context
  Response:
    memories_used: Memory[]
    conversation_context: Message[]

# Extract Memories from Conversation
POST /api/v1/conversations/{id}/extract-memories
  Request:
    message_range: { start_id?, end_id? }
    auto_save: bool
  Response:
    task_id: uuid  # Celery task ID for async tracking
    status: string

# Check Extraction Status
GET /api/v1/tasks/{task_id}/status
  Response:
    status: pending | processing | completed | failed
    result: { extracted_count: int, memories: Memory[] }

# Memory Feedback
POST /api/v1/messages/{message_id}/memories/{memory_id}/feedback
  Request:
    feedback: helpful | not_helpful | incorrect | outdated
    comment: string (optional)
  Response:
    status: success

# Memory Usage Settings
GET /api/v1/users/me/memory-settings
PATCH /api/v1/users/me/memory-settings
  Request:
    auto_include_memories: bool
    max_memories_per_request: int
    auto_extract_from_chat: bool
    excluded_memory_types: string[]
```

---

## Tasks

### Backend - Memory Retrieval Pipeline
- [ ] Implement MemoryContextService
- [ ] Add query expansion from conversation context
- [ ] Implement multi-factor relevance scoring
- [ ] Add token budget management for context

### Backend - Memory Usage Tracking
- [ ] Implement MemoryUsageService
- [ ] Store memory usage per AI message (uses Sprint 01 table)
- [ ] Track usage count for relevance boosting
- [ ] Return memories_used in response

### Backend - Memory Citations
- [ ] Implement citation formatting in system prompt
- [ ] Add citation numbers to response metadata
- [ ] Create citation footer generator

### Backend - Automatic Extraction
- [ ] Create Celery task for extraction
- [ ] Implement LLM-based memory extraction
- [ ] Add deduplication against existing memories
- [ ] Set up periodic extraction for idle conversations
- [ ] Create extraction status endpoint

### Backend - Feedback Loop
- [ ] Implement MemoryFeedbackService
- [ ] Create feedback API endpoint
- [ ] Add relevance adjustment based on feedback
- [ ] Flag memories for review on negative feedback

### Frontend - Memory Indicators
- [ ] Show "Using X memories" indicator
- [ ] Expandable list of used memories with citations
- [ ] Link to full memory view
- [ ] Toggle to disable memory use

### Frontend - Feedback UI
- [ ] Add helpful/not helpful buttons per memory
- [ ] Flag incorrect/outdated option
- [ ] Feedback confirmation toast

### Frontend - Extraction UI
- [ ] "Extract Memories" button on conversation
- [ ] Preview extracted memories
- [ ] Confirm/edit before saving
- [ ] Settings for auto-extraction
- [ ] Extraction progress indicator

### Performance
- [ ] Cache frequent memory searches (5 min TTL)
- [ ] Limit memory context size
- [ ] Parallel memory search and history fetch
- [ ] Batch memory usage inserts

---

## Acceptance Criteria

1. AI responses are contextually relevant to user's memories
2. UI shows which memories influenced the response with citation numbers
3. User can toggle memory inclusion per conversation
4. Can manually extract memories from chat (async with Celery)
5. Auto-extraction works in background (if enabled)
6. Response time remains acceptable (<5s)
7. Memory usage is logged for debugging
8. Users can provide feedback on memory helpfulness
9. Feedback influences future memory relevance scoring

---

## Memory Context Format

```python
def format_memories_for_context(memories: List[Memory]) -> str:
    """Format memories for inclusion in LLM context."""

    if not memories:
        return ""

    formatted = "Relevant information from user's memory:\n\n"

    for i, memory in enumerate(memories, 1):
        formatted += f"{i}. [{memory.memory_type.upper()}] "
        formatted += f"{memory.content[:500]}\n"
        if memory.metadata:
            formatted += f"   Metadata: {json.dumps(memory.metadata)}\n"
        formatted += f"   (Created: {memory.created_at.strftime('%Y-%m-%d')})\n\n"

    formatted += "---\n"
    formatted += "Use this information to provide personalized, accurate responses.\n"

    return formatted
```

---

## UI Components

### Memory Usage Indicator
```typescript
<MemoryUsageIndicator
  count={usedMemories.length}
  expanded={showMemories}
  onToggle={() => setShowMemories(!showMemories)}
>
  {showMemories && (
    <UsedMemoryList memories={usedMemories}>
      {memories.map(m => (
        <UsedMemoryItem
          key={m.memory_id}
          citationNumber={m.citation_number}
          content={m.snippet}
          score={m.relevance_score}
          onClick={() => openMemory(m.memory_id)}
        >
          <FeedbackButtons
            onHelpful={() => submitFeedback(m.memory_id, 'helpful')}
            onNotHelpful={() => submitFeedback(m.memory_id, 'not_helpful')}
          />
        </UsedMemoryItem>
      ))}
    </UsedMemoryList>
  )}
</MemoryUsageIndicator>
```

### Memory Toggle
```typescript
<ChatControls>
  <Toggle
    label="Include Memories"
    checked={useMemories}
    onChange={setUseMemories}
  />
  <Tooltip content="AI will use your stored memories to personalize responses" />
</ChatControls>
```

### Memory Feedback
```typescript
<MemoryFeedbackDialog
  isOpen={showFeedback}
  memory={selectedMemory}
  onSubmit={async (feedback, comment) => {
    await submitFeedback(message.id, selectedMemory.id, feedback, comment);
    setShowFeedback(false);
  }}
  options={[
    { value: 'helpful', label: 'This was helpful', icon: ThumbsUp },
    { value: 'not_helpful', label: 'Not relevant', icon: ThumbsDown },
    { value: 'incorrect', label: 'Information is wrong', icon: AlertCircle },
    { value: 'outdated', label: 'Outdated information', icon: Clock }
  ]}
/>
```

---

## Files to Create

```
# Backend
src/
  ai/
    memory_context.py        # MemoryContextService, retrieval pipeline
    memory_tracking.py       # MemoryUsageService, usage tracking
    memory_citations.py      # Citation formatting

  conversations/
    extraction.py            # MemoryExtractionService

  feedback/
    memory_feedback.py       # MemoryFeedbackService

  tasks/
    memory_extraction.py     # Celery tasks for async extraction

# Frontend
frontend/src/
  components/
    ai/
      MemoryUsageIndicator.tsx
      UsedMemoryList.tsx
      MemoryToggle.tsx
      ExtractMemoriesModal.tsx
      MemoryFeedbackButtons.tsx
      MemoryFeedbackDialog.tsx
      ExtractionProgress.tsx
```

---

## Performance Considerations

```python
# Parallel fetching
async def build_enhanced_context(
    conversation_id: UUID,
    user_message: str,
    user_id: UUID
):
    # Fetch in parallel
    history_task = get_conversation_history(conversation_id)
    memory_task = search_relevant_memories(user_message, user_id)

    history, memories = await asyncio.gather(history_task, memory_task)

    # Build context
    return {
        "history": history,
        "memories": memories,
        "system_prompt": get_system_prompt_with_citations(memories)
    }

# Caching
@cache(ttl=300)  # 5 minute cache
async def search_relevant_memories(query: str, user_id: UUID):
    # Memory search is expensive, cache results
    pass

# Batch inserts for memory usage
async def batch_save_memory_usage(
    message_id: UUID,
    memory_scores: list[tuple[UUID, float]]
):
    """Batch insert memory usage records for efficiency."""
    values = [
        {"message_id": message_id, "memory_id": mid, "relevance_score": score}
        for mid, score in memory_scores
    ]
    await db.execute(
        message_memory_usage.insert(),
        values
    )
```

---

## Related Requirement Groups

- Group 008: Semantic: Semantic Search
- Group 012: Semantic: Machine Learning
- Group 016: Semantic: Memory
