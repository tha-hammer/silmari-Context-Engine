# Sprint 10: AI Chat Interface

**Phase:** 3 - Communication
**Focus:** Conversational AI agent
**Dependencies:** Sprint 01 (Schema), Sprint 06 (Vectors), Sprint 09 (Messaging)

---

## Testable Deliverable

**Human Test:**
1. Start new AI conversation
2. Send message "What can you help me with?"
3. Receive helpful AI response (streaming in real-time)
4. Ask follow-up questions
5. AI maintains context across messages
6. Conversation saved in history

**Test Flow:**
```
User: "Help me plan a marketing campaign"
AI: "I'd be happy to help! Let me ask a few questions..."

User: "It's for our Q2 product launch"
AI: "Great! For a Q2 product launch campaign, here are some key elements..."

User: "What budget should I consider?"
AI: "Based on typical B2B SaaS launches, I'd recommend..."
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_028 | Dedicated AI agent chat conversations | 18 |
| REQ_003 | Context-aware AI assistance | 17 |
| REQ_041 | Unlimited conversation context depth | 17 |

### Implementation Requirements

- REQ_028.2.1: Create AI chat interface
- REQ_028.2.2: Maintain conversation state
- REQ_003.2.1: Provide contextual responses
- REQ_041.2.1: Support long conversations
- REQ_041.2.2: Summarize older context

---

## Architecture

```
[User Message]
    |
    v
[Rate Limiter] -- Check per-user limits
    |
    v
[Conversation Service]
    |
    +-- [Context Builder] -- [Memory Search] -- [User Memories]
    |
    v
[Celery Task] (for long-running operations)
    |
    v
[LLM Service]
    |
    v
[AI Response] -- Streaming via SSE
    |
    +-- [WebSocket Hub] -- Push to connected clients (Sprint 09 integration)
    |
    v
[Save to Conversation]
    |
    +-- [sender_id: AI_ASSISTANT_USER_ID]
    +-- [is_ai_generated: true]
```

---

## AI Message Handling

### System User for AI Messages

AI messages are stored with a dedicated system user ID rather than NULL, providing consistency and queryability.

```python
from uuid import UUID

# AI System User Constants
AI_ASSISTANT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
AI_ASSISTANT_DISPLAY_NAME = "Tanka AI"

# Create system user record during database seeding (Sprint 01 migration)
# INSERT INTO users (id, email, display_name, is_active)
# VALUES ('00000000-0000-0000-0000-000000000001', 'ai@system.tanka.ai', 'Tanka AI', true);
```

### Message Schema Extension

Extends the `messages` table from Sprint 01 - no table redefinition needed.

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class Message(BaseModel):
    """Message model - extends Sprint 01 schema."""
    id: UUID
    conversation_id: UUID
    sender_id: UUID  # AI_ASSISTANT_USER_ID for AI messages, user UUID for humans
    content: str
    content_type: str  # "text", "file", "system", "ai"
    status: str  # "sent", "delivered", "read"

    # AI-specific fields (already in Sprint 01 schema)
    is_ai_generated: bool = False  # Replaces is_ai_response from Sprint 01
    ai_model: Optional[str] = None  # "claude-3-5-sonnet-20241022", "gpt-4", etc.

    # Timestamps
    created_at: datetime
    edited_at: Optional[datetime] = None


class AIMessageCreate(BaseModel):
    """Schema for creating AI response messages."""
    conversation_id: UUID
    content: str
    ai_model: str

    def to_message_create(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "sender_id": AI_ASSISTANT_USER_ID,
            "content": self.content,
            "content_type": "ai",
            "is_ai_generated": True,
            "ai_model": self.ai_model,
        }
```

### AI Message Storage & Retrieval

```python
async def save_ai_message(
    conversation_id: UUID,
    content: str,
    ai_model: str,
    memory_ids_used: list[UUID] = None
) -> Message:
    """Save an AI-generated message with proper attribution."""

    message = await db.messages.create(
        conversation_id=conversation_id,
        sender_id=AI_ASSISTANT_USER_ID,
        content=content,
        content_type="ai",
        is_ai_generated=True,
        ai_model=ai_model,
        status="sent"
    )

    # Track which memories were used for this response (RAG tracking)
    if memory_ids_used:
        for memory_id in memory_ids_used:
            await db.message_memory_usage.create(
                message_id=message.id,
                memory_id=memory_id,
                relevance_score=None  # Set during context building
            )

    return message


async def get_ai_conversations(user_id: UUID) -> list[Conversation]:
    """Get all AI chat conversations for a user."""
    return await db.conversations.find_many(
        where={
            "type": "ai_chat",
            "participants": {"some": {"user_id": user_id}}
        },
        order_by={"last_message_at": "desc"}
    )
```

---

## AI Configuration

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class AIConfig:
    # Model
    PROVIDER: Literal["anthropic", "openai"] = "anthropic"
    MODEL: str = "claude-3-5-sonnet-20241022"

    # Context
    MAX_CONTEXT_MESSAGES: int = 20
    MAX_CONTEXT_TOKENS: int = 8000  # Reserve tokens for response
    SYSTEM_PROMPT: str = """You are Tanka, an AI assistant integrated into a business messenger.
    You help users with:
    - Answering questions about their work
    - Organizing information and memories
    - Planning and task management
    - Writing and editing content

    Be helpful, concise, and professional. When relevant, reference
    the user's stored memories to provide personalized assistance."""

    # Streaming
    STREAM_RESPONSES: bool = True
    STREAM_CHUNK_SIZE: int = 10  # Characters per SSE event

    # Memory Integration
    INCLUDE_RELEVANT_MEMORIES: bool = True
    MAX_MEMORIES_IN_CONTEXT: int = 5
    MEMORY_RELEVANCE_THRESHOLD: float = 0.7  # Minimum similarity score

    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 10
    MAX_REQUESTS_PER_HOUR: int = 100
    MAX_TOKENS_PER_DAY: int = 100000
```

---

## Streaming Responses

### SSE (Server-Sent Events) Endpoint

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from uuid import UUID
import json
import asyncio

router = APIRouter()

@router.post("/api/v1/conversations/{conversation_id}/ai-reply")
async def ai_reply(
    conversation_id: UUID,
    request: AIReplyRequest,
    current_user: User = Depends(get_current_user)
):
    """Stream AI response using Server-Sent Events."""

    # Verify user is participant
    if not await is_participant(conversation_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not a participant")

    # Check rate limits
    if not await check_rate_limit(current_user.id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Save user message first
    user_message = await save_message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=request.content,
        content_type="text"
    )

    async def generate():
        """Generator for SSE stream."""
        full_response = ""
        memories_used = []

        try:
            # Build context with memories
            context, memories_used = await build_context_with_memories(
                conversation_id=conversation_id,
                user_message=request.content,
                user_id=current_user.id
            )

            # Send start event
            yield f"event: message_start\ndata: {json.dumps({'conversation_id': str(conversation_id)})}\n\n"

            # Stream from LLM
            async for chunk in ai_service.stream_response(context):
                full_response += chunk
                yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"

            # Save complete AI message
            ai_message = await save_ai_message(
                conversation_id=conversation_id,
                content=full_response,
                ai_model=AI_CONFIG.MODEL,
                memory_ids_used=[m.id for m in memories_used]
            )

            # Send end event with message ID
            yield f"event: message_end\ndata: {json.dumps({'message_id': str(ai_message.id), 'full_content': full_response})}\n\n"

            # Notify via WebSocket (Sprint 09 integration)
            await websocket_hub.broadcast_to_conversation(
                conversation_id=conversation_id,
                event="new_message",
                data=ai_message.dict()
            )

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

### Frontend SSE Consumption

```typescript
// Frontend - SSE consumption with typewriter effect
interface StreamingMessageProps {
  conversationId: string;
  userMessage: string;
  onComplete: (message: Message) => void;
}

async function streamAIResponse({ conversationId, userMessage, onComplete }: StreamingMessageProps) {
  const response = await fetch(`/api/v1/conversations/${conversationId}/ai-reply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: userMessage }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let fullContent = '';

  while (true) {
    const { done, value } = await reader!.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';  // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        const eventType = line.slice(7);
        continue;
      }
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        if (data.token) {
          fullContent += data.token;
          // Update UI with new token (typewriter effect)
          updateStreamingMessage(fullContent);
        }

        if (data.message_id) {
          // Stream complete
          onComplete({
            id: data.message_id,
            content: data.full_content,
            sender_id: AI_ASSISTANT_USER_ID,
            is_ai_generated: true
          });
        }

        if (data.error) {
          throw new Error(data.error);
        }
      }
    }
  }
}
```

---

## Context Management

### Memory Retrieval for AI Context

```python
from typing import Tuple

async def build_context_with_memories(
    conversation_id: UUID,
    user_message: str,
    user_id: UUID
) -> Tuple[list[dict], list[Memory]]:
    """Build context for AI request with relevant memories."""

    messages = []
    memories_used = []

    # 1. System prompt
    messages.append({
        "role": "system",
        "content": AI_CONFIG.SYSTEM_PROMPT
    })

    # 2. Retrieve relevant memories using vector similarity (Sprint 06)
    if AI_CONFIG.INCLUDE_RELEVANT_MEMORIES:
        memories = await memory_service.semantic_search(
            query=user_message,
            user_id=user_id,
            limit=AI_CONFIG.MAX_MEMORIES_IN_CONTEXT,
            min_score=AI_CONFIG.MEMORY_RELEVANCE_THRESHOLD
        )

        if memories:
            memories_used = memories
            memory_context = format_memories_for_context(memories)
            messages.append({
                "role": "system",
                "content": f"Relevant information from user's memories:\n{memory_context}"
            })

    # 3. Conversation history with token management
    history = await get_conversation_history(
        conversation_id,
        limit=AI_CONFIG.MAX_CONTEXT_MESSAGES
    )

    # Summarize older messages if needed
    if await estimate_tokens(history) > AI_CONFIG.MAX_CONTEXT_TOKENS:
        history = await summarize_older_context(history)

    for msg in history:
        role = "assistant" if msg.sender_id == AI_ASSISTANT_USER_ID else "user"
        messages.append({
            "role": role,
            "content": msg.content
        })

    # 4. Current user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    return messages, memories_used


def format_memories_for_context(memories: list[Memory]) -> str:
    """Format memories for inclusion in system prompt."""
    formatted = []
    for i, memory in enumerate(memories, 1):
        formatted.append(f"[Memory {i}] ({memory.memory_type}): {memory.content}")
    return "\n".join(formatted)


async def summarize_older_context(history: list[Message]) -> list[Message]:
    """Summarize older messages to fit within token limit."""

    if len(history) <= 4:
        return history  # Keep all if very short

    # Keep recent messages, summarize older ones
    recent = history[-4:]
    older = history[:-4]

    summary = await ai_service.generate(
        prompt=f"Summarize this conversation history concisely:\n{format_messages(older)}",
        max_tokens=500
    )

    # Create synthetic system message with summary
    summary_msg = Message(
        id=UUID("00000000-0000-0000-0000-000000000000"),  # Synthetic ID
        conversation_id=older[0].conversation_id,
        sender_id=AI_ASSISTANT_USER_ID,
        content=f"[Earlier conversation summary: {summary}]",
        is_ai_generated=True
    )

    return [summary_msg] + recent
```

---

## Rate Limiting

### Per-User AI Request Limits

```python
from datetime import datetime, timedelta
from redis import asyncio as aioredis

class AIRateLimiter:
    """Rate limiter for AI requests using Redis."""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def check_rate_limit(self, user_id: UUID) -> RateLimitResult:
        """Check if user is within rate limits."""

        now = datetime.utcnow()
        user_key = str(user_id)

        # Check per-minute limit
        minute_key = f"ai_rate:{user_key}:minute:{now.strftime('%Y%m%d%H%M')}"
        minute_count = await self.redis.incr(minute_key)
        await self.redis.expire(minute_key, 60)

        if minute_count > AI_CONFIG.MAX_REQUESTS_PER_MINUTE:
            return RateLimitResult(
                allowed=False,
                reason="Per-minute limit exceeded",
                retry_after=60 - now.second
            )

        # Check per-hour limit
        hour_key = f"ai_rate:{user_key}:hour:{now.strftime('%Y%m%d%H')}"
        hour_count = await self.redis.incr(hour_key)
        await self.redis.expire(hour_key, 3600)

        if hour_count > AI_CONFIG.MAX_REQUESTS_PER_HOUR:
            return RateLimitResult(
                allowed=False,
                reason="Per-hour limit exceeded",
                retry_after=3600 - (now.minute * 60 + now.second)
            )

        # Check daily token usage
        day_key = f"ai_tokens:{user_key}:day:{now.strftime('%Y%m%d')}"
        tokens_used = int(await self.redis.get(day_key) or 0)

        if tokens_used > AI_CONFIG.MAX_TOKENS_PER_DAY:
            return RateLimitResult(
                allowed=False,
                reason="Daily token limit exceeded",
                retry_after=None  # Reset at midnight
            )

        return RateLimitResult(allowed=True)

    async def record_token_usage(self, user_id: UUID, tokens: int):
        """Record token usage for daily tracking."""
        now = datetime.utcnow()
        day_key = f"ai_tokens:{str(user_id)}:day:{now.strftime('%Y%m%d')}"
        await self.redis.incrby(day_key, tokens)
        await self.redis.expire(day_key, 86400)


@dataclass
class RateLimitResult:
    allowed: bool
    reason: str = None
    retry_after: int = None  # Seconds
```

---

## Celery Tasks for Long-Running Operations

### Background AI Processing

```python
from celery import Celery
from uuid import UUID

celery_app = Celery('ai_tasks')

@celery_app.task(bind=True, max_retries=3)
def process_ai_request_background(
    self,
    conversation_id: str,
    user_id: str,
    user_message: str
):
    """
    Background task for long-running AI operations.
    Used when streaming is not required (e.g., batch processing, regeneration).
    """
    try:
        # Build context
        context, memories = asyncio.run(
            build_context_with_memories(
                UUID(conversation_id),
                user_message,
                UUID(user_id)
            )
        )

        # Generate response (non-streaming)
        response = asyncio.run(
            ai_service.generate(context)
        )

        # Save message
        message = asyncio.run(
            save_ai_message(
                conversation_id=UUID(conversation_id),
                content=response.content,
                ai_model=AI_CONFIG.MODEL,
                memory_ids_used=[m.id for m in memories]
            )
        )

        # Notify via WebSocket
        asyncio.run(
            websocket_hub.broadcast_to_conversation(
                conversation_id=UUID(conversation_id),
                event="ai_response_ready",
                data=message.dict()
            )
        )

        return {"message_id": str(message.id), "status": "completed"}

    except Exception as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task
def regenerate_ai_response(message_id: str, conversation_id: str, user_id: str):
    """Regenerate an AI response for a specific message."""

    # Get the user message that prompted the original response
    original_message = asyncio.run(db.messages.find_unique(id=UUID(message_id)))

    # Find the preceding user message
    user_message = asyncio.run(
        db.messages.find_first(
            where={
                "conversation_id": UUID(conversation_id),
                "created_at": {"lt": original_message.created_at},
                "is_ai_generated": False
            },
            order_by={"created_at": "desc"}
        )
    )

    if not user_message:
        return {"error": "No user message found to regenerate from"}

    # Mark original AI message as deleted
    asyncio.run(
        db.messages.update(
            where={"id": UUID(message_id)},
            data={"deleted_at": datetime.utcnow()}
        )
    )

    # Generate new response
    return process_ai_request_background(
        conversation_id,
        user_id,
        user_message.content
    )
```

---

## WebSocket Integration (Sprint 09)

### Real-time AI Response Notifications

```python
# Extends Sprint 09 WebSocket hub
class AIWebSocketEvents:
    """AI-specific WebSocket events."""

    AI_TYPING_START = "ai_typing_start"
    AI_TYPING_STOP = "ai_typing_stop"
    AI_RESPONSE_CHUNK = "ai_response_chunk"  # Alternative to SSE
    AI_RESPONSE_COMPLETE = "ai_response_complete"
    AI_ERROR = "ai_error"


async def notify_ai_typing(conversation_id: UUID, is_typing: bool):
    """Notify participants that AI is generating a response."""
    await websocket_hub.broadcast_to_conversation(
        conversation_id=conversation_id,
        event=AIWebSocketEvents.AI_TYPING_START if is_typing else AIWebSocketEvents.AI_TYPING_STOP,
        data={"conversation_id": str(conversation_id)}
    )
```

---

## API Endpoints

```yaml
# Start AI Conversation
POST /api/v1/conversations
  Request:
    type: "ai_chat"
    title: string (optional, auto-generated)
  Response: Conversation

# Send Message to AI (non-streaming)
POST /api/v1/conversations/{id}/messages
  Request:
    content: string
    include_memories: bool (default: true)
  Response:
    user_message: Message
    ai_response: Message

# Streaming AI Response (SSE)
POST /api/v1/conversations/{id}/ai-reply
  Request:
    content: string
    include_memories: bool (default: true)
  Response: Server-Sent Events
    event: message_start
    event: token (repeated)
    event: message_end

# Regenerate Response
POST /api/v1/conversations/{id}/messages/{message_id}/regenerate
  Response:
    task_id: uuid (Celery task)
    status: "processing"

# Get AI Conversations
GET /api/v1/conversations?type=ai_chat
  Response: Conversation[]

# Check Rate Limit Status
GET /api/v1/ai/rate-limit
  Response:
    requests_remaining_minute: int
    requests_remaining_hour: int
    tokens_remaining_day: int
    reset_times: { minute: datetime, hour: datetime, day: datetime }
```

---

## Tasks

### Backend - AI Service
- [ ] Create LLM service interface
- [ ] Implement Anthropic/OpenAI provider
- [ ] Design system prompt
- [ ] Implement streaming responses (SSE)
- [ ] Create AI system user in database seeding

### Backend - AI Message Handling
- [ ] Implement AI message creation with proper sender_id
- [ ] Add is_ai_generated flag handling
- [ ] Track ai_model for each response
- [ ] Implement message_memory_usage tracking

### Backend - Context Building
- [ ] Build conversation history formatter
- [ ] Implement context window management
- [ ] Integrate memory search for context (Sprint 06)
- [ ] Handle long conversations (summarization)

### Backend - Rate Limiting
- [ ] Implement Redis-based rate limiter
- [ ] Add per-minute request limits
- [ ] Add per-hour request limits
- [ ] Add daily token tracking

### Backend - Background Tasks
- [ ] Set up Celery worker for AI tasks
- [ ] Implement regenerate response task
- [ ] Add task status tracking
- [ ] Handle task failures and retries

### Backend - WebSocket Integration
- [ ] Extend Sprint 09 WebSocket hub
- [ ] Add AI typing indicators
- [ ] Push AI responses via WebSocket

### Frontend - AI Chat UI
- [ ] Create AI conversation view
- [ ] Implement SSE streaming display (typewriter effect)
- [ ] Show typing indicator during generation
- [ ] Markdown rendering for AI responses

### Frontend - Features
- [ ] New AI chat button
- [ ] Conversation title editing
- [ ] Regenerate response button
- [ ] Copy response button
- [ ] Rate limit status display

---

## Acceptance Criteria

1. Can start new AI conversation
2. AI responds to messages
3. Streaming shows response as it generates (typewriter effect)
4. Conversation history maintained
5. Can have multi-turn conversations
6. AI conversations appear in conversation list
7. Can rename AI conversations
8. Regenerate produces new response
9. AI messages stored with AI_ASSISTANT_USER_ID as sender
10. Rate limiting prevents abuse
11. Memories are retrieved and used in context

---

## Files to Create

```
# Backend
src/
  ai/
    __init__.py
    config.py           # AI configuration
    constants.py        # AI_ASSISTANT_USER_ID
    service.py          # Main AI service
    context.py          # Context building
    rate_limiter.py     # Rate limiting
    providers/
      base.py
      anthropic.py
      openai.py
    streaming.py        # SSE utilities
    tasks.py            # Celery tasks

# Frontend
frontend/src/
  components/
    ai/
      AIChat.tsx
      AIMessage.tsx
      StreamingMessage.tsx
      RegenerateButton.tsx
      RateLimitStatus.tsx
  hooks/
    useSSE.ts           # SSE hook for streaming
  constants/
    ai.ts               # AI_ASSISTANT_USER_ID constant
```

---

## Database Seeding (Sprint 01 Extension)

```sql
-- Add AI system user during database seeding
-- This should be added to Sprint 01 migration or a dedicated seed script

INSERT INTO users (id, email, display_name, is_active, is_verified, created_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'ai@system.tanka.ai',
    'Tanka AI',
    true,
    true,
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- Note: No organization_id for system user (it's global)
```

---

## Related Requirement Groups

- Group 003: Semantic: Question
- Group 012: Semantic: Machine Learning
- Context awareness domain
