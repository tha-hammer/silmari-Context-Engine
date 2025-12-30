# Sprint 07: Memory Ingestion Pipeline

**Phase:** 2 - Memory System
**Focus:** Automatic memory extraction from text
**Dependencies:** Sprint 01 (Database Schema), Sprint 03 (Celery Task Queue), Sprint 05 (Storage), Sprint 06 (Vectors)

---

## Testable Deliverable

**Human Test:**
1. Paste a long meeting transcript into the UI
2. Click "Extract Memories"
3. See AI-generated memories appear
4. Review and approve/edit extracted memories
5. Memories are saved with proper types

**Test Flow:**
```bash
# Submit text for memory extraction
curl -X POST http://localhost:8000/api/v1/memories/extract \
  -H "Authorization: Bearer <token>" \
  -d '{
    "text": "Meeting Notes - Jan 15, 2024\n\nAttendees: John, Sarah, Mike\n\nDiscussed Q4 results. Revenue up 15%. Decided to expand to European market in Q2. John will lead the expansion. Action item: Sarah to prepare market research by Feb 1.",
    "source": "manual",
    "extract_types": ["decision", "task", "insight"]
  }'

# Response
{
  "extracted_memories": [
    {
      "content": "Q4 revenue increased by 15%",
      "memory_type": "insight",
      "confidence": 0.95,
      "metadata": {"metric": "revenue", "change": "+15%"}
    },
    {
      "content": "Decision: Expand to European market in Q2",
      "memory_type": "decision",
      "confidence": 0.92,
      "metadata": {"timeline": "Q2", "lead": "John"}
    },
    {
      "content": "Action: Sarah to prepare market research by Feb 1",
      "memory_type": "task",
      "confidence": 0.98,
      "metadata": {"assignee": "Sarah", "due_date": "2024-02-01"}
    }
  ],
  "status": "pending_review"
}
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_014 | Extract memories from conversations automatically | 17 |
| REQ_015 | Extract memories from uploaded files | 19 |
| REQ_060 | Extract knowledge from integrated tool data | 19 |

### Implementation Requirements

- REQ_001.2.2: Ingest data from chat messages
- REQ_014.2.1: Extract memories from conversations
- REQ_014.2.2: Identify key entities in text
- REQ_014.2.3: Categorize extracted information
- REQ_015.2.1: Parse document content
- REQ_015.2.2: Extract structured data from files

---

## Extraction Types

```python
class ExtractionType(Enum):
    DECISION = "decision"      # Choices made, conclusions
    TASK = "task"              # Action items, todos
    INSIGHT = "insight"        # Key learnings, metrics
    CONTACT = "contact"        # People mentioned
    DATE = "date"              # Important dates, deadlines
    TOPIC = "topic"            # Main subjects discussed
    SENTIMENT = "sentiment"    # Emotional context
    ALL = "all"                # Extract everything
```

---

## Celery Task Definitions

Leveraging Sprint 03's Celery infrastructure with Redis broker for async processing.

```python
from celery import shared_task, group, chain
from celery.exceptions import MaxRetriesExceededError
from src.core.celery_app import celery_app
from src.core.rate_limiter import RateLimiter

# Rate limiter for LLM API calls
llm_rate_limiter = RateLimiter(
    max_requests=60,      # Max requests per window
    window_seconds=60,    # 1 minute window
    provider="openai"
)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
    acks_late=True,
    track_started=True
)
def extract_memories_from_message(self, message_id: str, user_id: str):
    """
    Extract memories from a chat message.

    Workflow:
    1. Fetch message content from database
    2. Apply rate limiting for LLM calls
    3. Call LLM for memory extraction
    4. Parse and validate extracted memories
    5. Queue embedding generation
    """
    try:
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'fetching', 'progress': 10}
        )

        # Fetch message (references Sprint 01 messages table)
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise ValueError(f"Message {message_id} not found")

        # Rate limit check
        self.update_state(state='PROGRESS', meta={'stage': 'rate_limiting', 'progress': 20})
        llm_rate_limiter.acquire()

        # Extract memories via LLM
        self.update_state(state='PROGRESS', meta={'stage': 'extracting', 'progress': 40})
        extracted = llm_service.extract_memories(
            text=message.content,
            types=['decision', 'task', 'insight', 'contact']
        )

        # Store pending extractions
        self.update_state(state='PROGRESS', meta={'stage': 'storing', 'progress': 70})
        extraction_id = store_pending_extraction(
            user_id=user_id,
            memories=extracted,
            source='message',
            source_id=message_id
        )

        # Queue embedding generation
        batch_embed_memories.delay([m['temp_id'] for m in extracted])

        self.update_state(state='PROGRESS', meta={'stage': 'complete', 'progress': 100})

        return {
            'extraction_id': extraction_id,
            'memory_count': len(extracted),
            'status': 'pending_review'
        }

    except Exception as exc:
        # Log to dead letter queue on final failure
        if self.request.retries >= self.max_retries:
            send_to_dead_letter_queue(
                task_name='extract_memories_from_message',
                args={'message_id': message_id, 'user_id': user_id},
                error=str(exc)
            )
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    acks_late=True,
    track_started=True
)
def process_file_for_memories(self, file_id: str, user_id: str):
    """
    Process uploaded file and extract memories.

    Supported formats: PDF, DOCX, TXT, MD
    Uses chunking for large files.
    """
    try:
        self.update_state(state='PROGRESS', meta={'stage': 'loading', 'progress': 5})

        # Load file metadata (references Sprint 01 drive_files table pattern)
        file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not file_record:
            raise ValueError(f"File {file_id} not found")

        # Parse file content based on type
        self.update_state(state='PROGRESS', meta={'stage': 'parsing', 'progress': 15})
        parser = get_parser_for_type(file_record.mime_type)
        content = parser.extract_text(file_record.storage_path)

        # Chunk large documents
        self.update_state(state='PROGRESS', meta={'stage': 'chunking', 'progress': 25})
        chunks = chunk_text(content, max_chunk_size=4000, overlap=200)

        all_memories = []
        total_chunks = len(chunks)

        for idx, chunk in enumerate(chunks):
            # Rate limit for each LLM call
            llm_rate_limiter.acquire()

            progress = 25 + int((idx / total_chunks) * 60)
            self.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'extracting',
                    'progress': progress,
                    'chunk': idx + 1,
                    'total_chunks': total_chunks
                }
            )

            extracted = llm_service.extract_memories(text=chunk, types=['all'])
            all_memories.extend(extracted)

        # Deduplicate similar memories
        self.update_state(state='PROGRESS', meta={'stage': 'deduplicating', 'progress': 90})
        unique_memories = deduplicate_memories(all_memories, similarity_threshold=0.85)

        # Store extraction results
        extraction_id = store_pending_extraction(
            user_id=user_id,
            memories=unique_memories,
            source='file',
            source_id=file_id
        )

        # Queue batch embedding
        batch_embed_memories.delay([m['temp_id'] for m in unique_memories])

        self.update_state(state='PROGRESS', meta={'stage': 'complete', 'progress': 100})

        return {
            'extraction_id': extraction_id,
            'memory_count': len(unique_memories),
            'chunks_processed': total_chunks,
            'status': 'pending_review'
        }

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            send_to_dead_letter_queue(
                task_name='process_file_for_memories',
                args={'file_id': file_id, 'user_id': user_id},
                error=str(exc)
            )
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    rate_limit='100/m',  # Celery built-in rate limiting
    acks_late=True
)
def batch_embed_memories(self, memory_ids: list[str], batch_size: int = 50):
    """
    Generate embeddings for multiple memories.

    Uses batched API calls for efficiency.
    Stores embeddings in memories table (Sprint 01 schema).
    """
    try:
        self.update_state(state='PROGRESS', meta={'stage': 'loading', 'progress': 10})

        memories = db.query(Memory).filter(Memory.id.in_(memory_ids)).all()
        if not memories:
            return {'embedded_count': 0, 'status': 'no_memories_found'}

        total_batches = (len(memories) + batch_size - 1) // batch_size
        embedded_count = 0

        for batch_idx in range(0, len(memories), batch_size):
            batch = memories[batch_idx:batch_idx + batch_size]
            current_batch = batch_idx // batch_size + 1

            progress = 10 + int((current_batch / total_batches) * 80)
            self.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'embedding',
                    'progress': progress,
                    'batch': current_batch,
                    'total_batches': total_batches
                }
            )

            # Rate limit embedding API calls
            llm_rate_limiter.acquire()

            # Batch embedding call
            texts = [m.content for m in batch]
            embeddings = embedding_service.embed_batch(texts)

            # Update memories with embeddings (Sprint 01 memories table)
            for memory, embedding in zip(batch, embeddings):
                memory.embedding = embedding
                memory.embedding_status = 'completed'
                memory.embedding_model = embedding_service.model_name
                memory.embedding_updated_at = datetime.utcnow()
                embedded_count += 1

            db.commit()

        self.update_state(state='PROGRESS', meta={'stage': 'complete', 'progress': 100})

        return {
            'embedded_count': embedded_count,
            'status': 'completed'
        }

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            send_to_dead_letter_queue(
                task_name='batch_embed_memories',
                args={'memory_ids': memory_ids},
                error=str(exc)
            )
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2)
def bulk_ingest_memories(self, items: list[dict], user_id: str):
    """
    Batch process multiple items for memory extraction.

    Used for bulk imports and integration syncs.
    Creates sub-tasks for each item.
    """
    task_group = group([
        extract_memories_from_message.s(item['id'], user_id)
        if item['type'] == 'message'
        else process_file_for_memories.s(item['id'], user_id)
        for item in items
    ])

    result = task_group.apply_async()

    return {
        'group_id': result.id,
        'total_items': len(items),
        'status': 'processing'
    }
```

---

## Ingestion Pipeline

### Step-by-Step Async Workflow

```
                    ┌─────────────────┐
                    │   User Request  │
                    │  (API Endpoint) │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Validate Input │
                    │  & Auth Check   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Queue Task to  │
                    │  Redis Broker   │
                    │ (Sprint 03 Celery)
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
           ┌────────────────┐ ┌────────────────┐
           │ Message Task   │ │  File Task     │
           │ extract_memories│ │ process_file   │
           │ _from_message  │ │ _for_memories  │
           └───────┬────────┘ └───────┬────────┘
                   │                  │
                   │    ┌─────────────┤
                   │    │             │
                   ▼    ▼             ▼
           ┌────────────────┐ ┌────────────────┐
           │  Rate Limiter  │ │  File Parser   │
           │  (LLM API)     │ │  (PDF/DOCX)    │
           └───────┬────────┘ └───────┬────────┘
                   │                  │
                   ▼                  ▼
           ┌─────────────────────────────────────┐
           │         LLM Extraction Service      │
           │    (OpenAI/Anthropic structured)    │
           └─────────────────┬───────────────────┘
                             │
                             ▼
           ┌─────────────────────────────────────┐
           │   Store Pending Extractions         │
           │   (pending_extractions table)       │
           └─────────────────┬───────────────────┘
                             │
                             ▼
           ┌─────────────────────────────────────┐
           │      batch_embed_memories           │
           │   (Generate vector embeddings)      │
           └─────────────────┬───────────────────┘
                             │
                             ▼
           ┌─────────────────────────────────────┐
           │    User Review & Confirmation       │
           │   (Approve/Reject/Edit memories)    │
           └─────────────────┬───────────────────┘
                             │
                             ▼
           ┌─────────────────────────────────────┐
           │   Save to memories table            │
           │   (Sprint 01 PostgreSQL schema)     │
           └─────────────────────────────────────┘
```

### Pipeline Stages

1. **Receive** - API endpoint receives extraction request
2. **Validate** - Check auth, rate limits, input validation
3. **Queue** - Submit to Celery via Redis broker (Sprint 03)
4. **Parse** - Extract text from files if needed
5. **Chunk** - Split large documents into processable chunks
6. **Extract** - LLM-based memory extraction with rate limiting
7. **Dedupe** - Remove duplicate/similar extractions
8. **Embed** - Generate vector embeddings (batch processing)
9. **Review** - User confirms/rejects extracted memories
10. **Store** - Save confirmed memories to Sprint 01 schema

---

## Error Handling

### Dead Letter Queue

Failed tasks after max retries are sent to a dead letter queue for manual inspection.

```python
# Dead letter queue configuration
DEAD_LETTER_QUEUE = 'ingestion_dead_letter'

def send_to_dead_letter_queue(task_name: str, args: dict, error: str):
    """
    Send failed task to dead letter queue for manual review.
    """
    dlq_entry = {
        'task_name': task_name,
        'args': args,
        'error': error,
        'failed_at': datetime.utcnow().isoformat(),
        'retry_count': 0
    }

    redis_client.lpush(DEAD_LETTER_QUEUE, json.dumps(dlq_entry))

    # Alert monitoring
    logger.error(
        f"Task {task_name} sent to DLQ",
        extra={'task_args': args, 'error': error}
    )


# DLQ processing endpoint
@celery_app.task
def process_dead_letter_queue():
    """
    Periodically process dead letter queue.
    Retry or escalate failed tasks.
    """
    while True:
        entry = redis_client.rpop(DEAD_LETTER_QUEUE)
        if not entry:
            break

        task_data = json.loads(entry)

        if task_data['retry_count'] < 3:
            # Attempt retry with exponential backoff
            task_data['retry_count'] += 1
            delay = 60 * (2 ** task_data['retry_count'])

            if task_data['task_name'] == 'extract_memories_from_message':
                extract_memories_from_message.apply_async(
                    args=[task_data['args']['message_id'], task_data['args']['user_id']],
                    countdown=delay
                )
            # ... handle other task types
        else:
            # Escalate to admin notification
            notify_admin_dlq_escalation(task_data)
```

### Retry Strategies

```python
# Retry configuration by task type
RETRY_CONFIGS = {
    'extraction': {
        'max_retries': 3,
        'retry_backoff': True,
        'retry_backoff_max': 300,  # 5 minutes max
        'retry_jitter': True,       # Add randomness to prevent thundering herd
    },
    'embedding': {
        'max_retries': 5,
        'retry_backoff': True,
        'retry_backoff_max': 600,  # 10 minutes max
        'retry_jitter': True,
    },
    'file_processing': {
        'max_retries': 2,
        'retry_backoff': True,
        'retry_backoff_max': 120,  # 2 minutes max
        'retry_jitter': False,
    }
}
```

---

## Rate Limiting

### LLM API Rate Limiting

```python
from redis import Redis
from time import sleep
import threading

class RateLimiter:
    """
    Token bucket rate limiter using Redis for distributed coordination.
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        provider: str,
        redis_client: Redis = None
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.provider = provider
        self.redis = redis_client or Redis()
        self.key = f"rate_limit:{provider}"
        self._lock = threading.Lock()

    def acquire(self, timeout: int = 60) -> bool:
        """
        Acquire a rate limit token. Blocks until available or timeout.
        """
        deadline = time.time() + timeout

        while time.time() < deadline:
            with self._lock:
                current = self.redis.get(self.key)
                current_count = int(current) if current else 0

                if current_count < self.max_requests:
                    pipe = self.redis.pipeline()
                    pipe.incr(self.key)
                    pipe.expire(self.key, self.window_seconds)
                    pipe.execute()
                    return True

            # Wait before retry
            sleep(0.5)

        raise RateLimitExceeded(
            f"Rate limit exceeded for {self.provider}"
        )

    def get_remaining(self) -> int:
        """Get remaining requests in current window."""
        current = self.redis.get(self.key)
        current_count = int(current) if current else 0
        return max(0, self.max_requests - current_count)

    def get_reset_time(self) -> int:
        """Get seconds until rate limit resets."""
        ttl = self.redis.ttl(self.key)
        return max(0, ttl)


# Provider-specific rate limiters
rate_limiters = {
    'openai': RateLimiter(max_requests=60, window_seconds=60, provider='openai'),
    'anthropic': RateLimiter(max_requests=50, window_seconds=60, provider='anthropic'),
    'embedding': RateLimiter(max_requests=100, window_seconds=60, provider='embedding'),
}
```

---

## Monitoring

### Celery Flower Dashboard Integration

```python
# docker-compose.yml additions for monitoring
"""
services:
  flower:
    image: mher/flower:0.9.7
    command: celery --broker=redis://redis:6379/0 flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - FLOWER_BASIC_AUTH=admin:password
    depends_on:
      - redis
      - celery_worker
"""

# Custom task events for monitoring
from celery import signals

@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, **kwargs):
    """Log task start for monitoring."""
    metrics.increment('celery.task.started', tags={'task': task.name})

@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, state=None, **kwargs):
    """Log task completion for monitoring."""
    metrics.increment('celery.task.completed', tags={'task': task.name, 'state': state})

@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log task failures for alerting."""
    metrics.increment('celery.task.failed', tags={'task': sender.name})
    logger.error(f"Task {sender.name} failed: {exception}")
```

### Progress Tracking API

```python
from celery.result import AsyncResult

@router.get("/api/v1/memories/extract/{task_id}/progress")
async def get_extraction_progress(task_id: str):
    """
    Get progress of an extraction task.
    Polls Celery task state.
    """
    result = AsyncResult(task_id)

    if result.state == 'PENDING':
        return {
            'task_id': task_id,
            'state': 'pending',
            'progress': 0,
            'stage': 'queued'
        }
    elif result.state == 'PROGRESS':
        return {
            'task_id': task_id,
            'state': 'processing',
            'progress': result.info.get('progress', 0),
            'stage': result.info.get('stage', 'unknown'),
            'chunk': result.info.get('chunk'),
            'total_chunks': result.info.get('total_chunks')
        }
    elif result.state == 'SUCCESS':
        return {
            'task_id': task_id,
            'state': 'completed',
            'progress': 100,
            'result': result.result
        }
    elif result.state == 'FAILURE':
        return {
            'task_id': task_id,
            'state': 'failed',
            'progress': 0,
            'error': str(result.info)
        }

    return {
        'task_id': task_id,
        'state': result.state,
        'progress': 0
    }


# WebSocket for real-time progress (optional enhancement)
@router.websocket("/api/v1/memories/extract/{task_id}/ws")
async def extraction_progress_ws(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time progress updates.
    """
    await websocket.accept()

    result = AsyncResult(task_id)

    while not result.ready():
        state_info = {
            'state': result.state,
            'progress': result.info.get('progress', 0) if result.info else 0,
            'stage': result.info.get('stage', 'unknown') if result.info else 'unknown'
        }
        await websocket.send_json(state_info)
        await asyncio.sleep(1)

    # Send final result
    final_state = {
        'state': 'completed' if result.successful() else 'failed',
        'progress': 100,
        'result': result.result if result.successful() else str(result.info)
    }
    await websocket.send_json(final_state)
    await websocket.close()
```

### Metrics Dashboard

```python
# Key metrics to track
INGESTION_METRICS = {
    'ingestion.tasks.queued': 'Tasks waiting in queue',
    'ingestion.tasks.processing': 'Tasks currently processing',
    'ingestion.tasks.completed': 'Tasks completed successfully',
    'ingestion.tasks.failed': 'Tasks that failed',
    'ingestion.memories.extracted': 'Total memories extracted',
    'ingestion.memories.confirmed': 'Memories confirmed by users',
    'ingestion.memories.rejected': 'Memories rejected by users',
    'ingestion.api.rate_limited': 'Requests rate limited',
    'ingestion.processing_time.avg': 'Average processing time (seconds)',
    'ingestion.dlq.size': 'Dead letter queue size',
}
```

---

## API Endpoints

```yaml
# Extract Memories from Text
POST /api/v1/memories/extract
  Request:
    text: string (required, max 50000 chars)
    source: string (manual, file, integration)
    source_id: string (optional)
    extract_types: string[] (optional, default: all)
    auto_save: bool (default: false)
    async: bool (default: true)  # Use Celery for async processing
  Response:
    task_id: uuid (if async)
    extraction_id: uuid
    extracted_memories: [
      {
        temp_id: uuid
        content: string
        memory_type: string
        confidence: float (0-1)
        metadata: object
        suggested_tags: string[]
      }
    ]
    status: string (pending_review, auto_saved, processing)

# Get Extraction Progress (async tasks)
GET /api/v1/memories/extract/{task_id}/progress
  Response:
    task_id: uuid
    state: string (pending, processing, completed, failed)
    progress: int (0-100)
    stage: string
    result: object (if completed)
    error: string (if failed)

# Confirm Extracted Memories
POST /api/v1/memories/extract/{extraction_id}/confirm
  Request:
    confirmed_ids: uuid[]       # Accept these
    rejected_ids: uuid[]        # Discard these
    edits: [                    # Modify before saving
      { temp_id: uuid, content: string, memory_type: string }
    ]
  Response:
    saved_count: int
    memory_ids: uuid[]

# Extract from File
POST /api/v1/memories/extract/file
  Content-Type: multipart/form-data
  Request:
    file: File (pdf, txt, docx, md)
    extract_types: string[]
  Response:
    task_id: uuid
    status: processing

# Get Extraction Status
GET /api/v1/memories/extract/{extraction_id}
  Response:
    status: string (processing, completed, failed)
    extracted_memories: Memory[] (if completed)
    error: string (if failed)

# Bulk Ingest
POST /api/v1/memories/extract/bulk
  Request:
    items: [
      { type: string (message|file), id: uuid }
    ]
  Response:
    group_id: uuid
    total_items: int
    status: processing
```

---

## Tasks

### LLM Integration
- [ ] Create LLM service interface
- [ ] Implement OpenAI/Anthropic provider
- [ ] Design extraction prompts
- [ ] Handle structured output parsing

### Extraction Pipeline
- [ ] Build text preprocessing (chunking, cleaning)
- [ ] Implement extraction by type
- [ ] Calculate confidence scores
- [ ] Extract metadata and entities

### File Processing
- [ ] PDF text extraction (PyPDF2/pdfplumber)
- [ ] DOCX parsing (python-docx)
- [ ] Markdown parsing
- [ ] Plain text handling

### Review Workflow
- [ ] Store pending extractions temporarily
- [ ] Implement confirm/reject flow
- [ ] Allow edits before saving
- [ ] Auto-expire unconfirmed extractions (24h)

### Celery Integration (Sprint 03)
- [ ] Define extraction task with retry logic
- [ ] Define file processing task
- [ ] Define batch embedding task
- [ ] Implement bulk ingestion workflow
- [ ] Configure rate limiting for LLM calls
- [ ] Set up dead letter queue
- [ ] Implement progress tracking

### Monitoring & Observability
- [ ] Configure Celery Flower dashboard
- [ ] Implement progress tracking endpoint
- [ ] Add WebSocket support for real-time updates
- [ ] Define key metrics and alerts
- [ ] Set up DLQ monitoring

---

## Acceptance Criteria

1. Can extract memories from pasted text
2. Each extracted memory has type and confidence score
3. User can review before saving
4. User can edit extracted content
5. File upload extracts text content
6. Long documents are processed asynchronously via Celery
7. Failed extractions report clear errors
8. Retry logic handles transient failures
9. Rate limiting prevents API quota exhaustion
10. Progress tracking available for long-running jobs
11. Dead letter queue captures failed tasks for review
12. Flower dashboard shows task status and metrics

---

## Extraction Prompt Design

```python
EXTRACTION_PROMPT = """
Analyze the following text and extract structured memories.

For each piece of important information, create a memory with:
- content: The key information (concise, self-contained)
- type: One of [decision, task, insight, contact, date, topic]
- confidence: How confident you are (0.0-1.0)
- metadata: Relevant structured data

Text to analyze:
{text}

Respond with JSON array of extracted memories.
"""

# Example structured output
[
  {
    "content": "Revenue increased 15% in Q4",
    "type": "insight",
    "confidence": 0.95,
    "metadata": {
      "metric": "revenue",
      "period": "Q4",
      "change_percent": 15
    }
  }
]
```

---

## Files to Create

```
src/
  ingestion/
    __init__.py
    service.py           # Main ingestion service
    router.py            # API endpoints
    schemas.py           # Request/response schemas
    tasks.py             # Celery task definitions (NEW)
    rate_limiter.py      # Rate limiting utilities (NEW)
    dead_letter.py       # DLQ handling (NEW)
    extractors/
      __init__.py
      base.py            # Extractor interface
      llm_extractor.py   # LLM-based extraction
      rule_extractor.py  # Rule-based (dates, emails)
    parsers/
      __init__.py
      pdf.py
      docx.py
      text.py
    prompts/
      extraction.py      # Prompt templates
    monitoring/
      __init__.py
      metrics.py         # Metrics collection (NEW)
      progress.py        # Progress tracking (NEW)
```

---

## LLM Service Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMService(ABC):
    @abstractmethod
    async def extract_memories(
        self,
        text: str,
        types: List[str]
    ) -> List[Dict[str, Any]]:
        """Extract structured memories from text."""
        pass

class OpenAILLMService(LLMService):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def extract_memories(self, text: str, types: List[str]):
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract {types} from:\n{text}"}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
```

---

## Memory Storage Destination (Sprint 01 Reference)

Extracted memories are stored in the `memories` table defined in Sprint 01:

```sql
-- Target table for confirmed memories (from Sprint 01)
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    title VARCHAR(500),
    memory_type VARCHAR(50) NOT NULL DEFAULT 'note',
    source VARCHAR(50) NOT NULL DEFAULT 'manual',
    source_id VARCHAR(255),
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    embedding_status VARCHAR(20) DEFAULT 'pending',
    embedding_model VARCHAR(100),
    embedding_updated_at TIMESTAMP,
    conversation_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    accessed_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);
```

---

## Related Requirement Groups

- Group 012: Semantic: Machine Learning
- Group 013: Semantic: User Input
- Group 020: Semantic: Market Analysis (entity extraction patterns)
