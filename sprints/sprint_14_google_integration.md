# Sprint 14: Google Workspace Integration

**Phase:** 4 - Business Tools
**Focus:** Gmail, Calendar, Drive sync
**Dependencies:** Sprint 13 (OAuth)

---

## Testable Deliverable

**Human Test:**
1. Connect Google account (from Sprint 13)
2. Navigate to Integrations dashboard
3. See recent emails from Gmail
4. See upcoming calendar events
5. Browse connected Drive files
6. Data syncs automatically

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_005 | Business tools integration | 17 |
| REQ_064 | Continuous sync from integrated tools | 19 |

### Implementation Requirements
- REQ_005.3.2: Gmail data synchronization
- REQ_050.2.1: Google Calendar integration
- REQ_053.2.1: Google Drive file access

---

## Sync Architecture

```
[Sync Scheduler] --> [Google API]
      |                  |
      v                  v
[Sync Job Queue]    [Rate Limiter]
      |                  |
      v                  v
[Process Batch]  <------+
      |
      v
[Transform Data]
      |
      v
[Store in DB] --> [Create Memories]
```

---

## Data Models

```python
class GmailMessage(BaseModel):
    id: UUID
    user_id: UUID
    integration_id: UUID    # FK to integrations table
    gmail_id: str           # Google's message ID
    thread_id: str
    subject: str
    from_email: str
    to_emails: List[str]
    snippet: str            # Preview text
    body_text: str | None   # Full body (if synced)
    received_at: datetime
    labels: List[str]
    is_read: bool
    synced_at: datetime

class CalendarEvent(BaseModel):
    id: UUID
    user_id: UUID
    integration_id: UUID    # FK to integrations table
    google_event_id: str
    calendar_id: str
    title: str
    description: str | None
    start_time: datetime
    end_time: datetime
    location: str | None
    attendees: List[str]
    is_all_day: bool
    synced_at: datetime

class DriveFile(BaseModel):
    id: UUID
    user_id: UUID
    integration_id: UUID    # FK to integrations table
    google_file_id: str
    name: str
    mime_type: str
    size_bytes: int
    web_link: str
    parent_folder: str | None
    modified_at: datetime
    synced_at: datetime

# Sync state tracking for incremental sync
class SyncState(BaseModel):
    id: UUID
    integration_id: UUID
    resource_type: str      # gmail, calendar, drive
    sync_token: str | None  # Google's sync token for incremental
    last_sync_at: datetime
    items_synced: int
    status: str             # idle, syncing, error
    error_message: str | None
    created_at: datetime
    updated_at: datetime
```

---

## Database Schema

```sql
-- Gmail messages table
CREATE TABLE gmail_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    gmail_id VARCHAR(255) NOT NULL,
    thread_id VARCHAR(255),
    subject TEXT,
    from_email VARCHAR(255),
    to_emails TEXT[],
    snippet TEXT,
    body_text TEXT,
    received_at TIMESTAMP,
    labels TEXT[],
    is_read BOOLEAN DEFAULT false,
    synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(integration_id, gmail_id)
);

CREATE INDEX idx_gmail_user ON gmail_messages(user_id);
CREATE INDEX idx_gmail_integration ON gmail_messages(integration_id);
CREATE INDEX idx_gmail_received ON gmail_messages(user_id, received_at DESC);
CREATE INDEX idx_gmail_fts ON gmail_messages USING GIN (
    to_tsvector('english', coalesce(subject, '') || ' ' || coalesce(body_text, ''))
);

-- Calendar events table
CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    google_event_id VARCHAR(255) NOT NULL,
    calendar_id VARCHAR(255),
    title TEXT,
    description TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    location TEXT,
    attendees JSONB DEFAULT '[]',
    is_all_day BOOLEAN DEFAULT false,
    synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(integration_id, google_event_id)
);

CREATE INDEX idx_calendar_user ON calendar_events(user_id);
CREATE INDEX idx_calendar_time ON calendar_events(user_id, start_time);

-- Drive files table
CREATE TABLE drive_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    google_file_id VARCHAR(255) NOT NULL,
    name TEXT,
    mime_type VARCHAR(255),
    size_bytes BIGINT,
    web_link TEXT,
    parent_folder VARCHAR(255),
    modified_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(integration_id, google_file_id)
);

CREATE INDEX idx_drive_user ON drive_files(user_id);
CREATE INDEX idx_drive_parent ON drive_files(integration_id, parent_folder);

-- Sync state tracking
CREATE TABLE sync_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    sync_token TEXT,
    last_sync_at TIMESTAMP,
    items_synced INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'idle',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(integration_id, resource_type)
);
```

---

## API Endpoints

```yaml
# Gmail
GET /api/v1/integrations/google/gmail/messages
  Query: ?page=1&per_page=20&label=INBOX
  Response: GmailMessage[]

GET /api/v1/integrations/google/gmail/messages/{id}
  Response: GmailMessage with full body

POST /api/v1/integrations/google/gmail/sync
  Response: { synced_count: int, status: string }

# Calendar
GET /api/v1/integrations/google/calendar/events
  Query: ?start=2024-01-01&end=2024-01-31
  Response: CalendarEvent[]

GET /api/v1/integrations/google/calendar/upcoming
  Query: ?limit=10
  Response: CalendarEvent[]

POST /api/v1/integrations/google/calendar/sync
  Response: { synced_count: int }

# Drive
GET /api/v1/integrations/google/drive/files
  Query: ?folder_id=root&page=1
  Response: DriveFile[]

GET /api/v1/integrations/google/drive/search
  Query: ?q=project%20report
  Response: DriveFile[]
```

---

## Tasks

### Backend - Gmail Sync
- [ ] Implement Gmail API client
- [ ] Fetch message list with pagination
- [ ] Fetch message details
- [ ] Store synced messages
- [ ] Handle labels and categories

### Backend - Calendar Sync
- [ ] Implement Calendar API client
- [ ] Fetch events in date range
- [ ] Store calendar events
- [ ] Handle recurring events
- [ ] Track event updates

### Backend - Drive Sync
- [ ] Implement Drive API client
- [ ] List files and folders
- [ ] File metadata extraction
- [ ] Search files
- [ ] Handle file permissions

### Backend - Sync Jobs
- [ ] Create sync scheduler
- [ ] Implement incremental sync
- [ ] Handle rate limiting
- [ ] Error recovery

### Frontend - Integration Dashboard
- [ ] Gmail messages view
- [ ] Calendar events view
- [ ] Drive file browser
- [ ] Sync status indicators

---

## Acceptance Criteria

1. Gmail messages sync and display
2. Calendar events sync and display
3. Drive files browsable
4. Incremental sync works
5. Manual sync trigger works
6. Rate limits respected
7. Sync errors handled gracefully

---

## Sync Implementation

```python
class GoogleSyncService:
    def __init__(self, integration: Integration):
        self.credentials = get_google_credentials(integration)
        self.gmail = build('gmail', 'v1', credentials=self.credentials)
        self.calendar = build('calendar', 'v3', credentials=self.credentials)
        self.drive = build('drive', 'v3', credentials=self.credentials)

    async def sync_gmail(self, user_id: UUID, since: datetime = None):
        """Sync Gmail messages."""
        query = f"after:{since.strftime('%Y/%m/%d')}" if since else ""

        results = self.gmail.users().messages().list(
            userId='me',
            q=query,
            maxResults=100
        ).execute()

        messages = results.get('messages', [])

        for msg in messages:
            full_message = self.gmail.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            await self.store_message(user_id, full_message)

    async def sync_calendar(self, user_id: UUID, days_ahead: int = 30):
        """Sync calendar events."""
        now = datetime.utcnow().isoformat() + 'Z'
        end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'

        events_result = self.calendar.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        for event in events:
            await self.store_event(user_id, event)
```

---

## Memory Extraction (Integration with Sprint 07)

```python
from src.memories.ingestion import MemoryIngestionService  # From Sprint 07

async def extract_memories_from_gmail(
    message: GmailMessage,
    user_id: UUID,
    ingestion_service: MemoryIngestionService
) -> List[Memory]:
    """Extract memories from email content using Sprint 07 pipeline."""

    # Use the memory ingestion service from Sprint 07
    memories = await ingestion_service.ingest_text(
        text=f"Subject: {message.subject}\n\n{message.body_text}",
        user_id=user_id,
        source="gmail",
        source_id=str(message.id),
        metadata={
            "from_email": message.from_email,
            "to_emails": message.to_emails,
            "received_at": message.received_at.isoformat(),
            "thread_id": message.thread_id,
        }
    )

    return memories


# Celery task for background extraction after sync
@celery.task
def extract_memories_from_synced_emails(integration_id: UUID, message_ids: List[UUID]):
    """Background task to extract memories from newly synced emails."""
    from src.memories.ingestion import MemoryIngestionService

    ingestion_service = MemoryIngestionService()
    integration = get_integration(integration_id)

    for message_id in message_ids:
        message = get_gmail_message(message_id)
        asyncio.run(extract_memories_from_gmail(
            message=message,
            user_id=integration.user_id,
            ingestion_service=ingestion_service
        ))
```

---

## Files to Create

```
src/
  integrations/
    google/
      __init__.py
      client.py          # Google API wrapper
      gmail_sync.py
      calendar_sync.py
      drive_sync.py
      router.py
      schemas.py

  models/
    gmail_message.py
    calendar_event.py
    drive_file.py

frontend/src/
  components/
    integrations/
      google/
        GmailList.tsx
        CalendarView.tsx
        DriveExplorer.tsx
```

---

## Rate Limiting

```python
# Google API quotas
GMAIL_QUOTA = {
    "per_user_per_second": 10,
    "per_user_per_day": 10_000
}

CALENDAR_QUOTA = {
    "per_user_per_second": 10,
    "per_user_per_day": 10_000
}

# Rate limiter implementation
from asyncio import Semaphore
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, calls_per_second: int):
        self.semaphore = Semaphore(calls_per_second)
        self.last_reset = datetime.now()

    async def acquire(self):
        async with self.semaphore:
            yield
            await asyncio.sleep(1 / self.calls_per_second)
```

---

## Related Requirement Groups

- Integration domain
- REQ_050: Outlook Calendar
- REQ_053: OneDrive

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added `integration_id` FK to all data models (GmailMessage, CalendarEvent, DriveFile)
2. Added complete SQL database schema with proper indexes and constraints
3. Added `SyncState` model for tracking incremental sync progress with sync tokens
4. Added `sync_states` table for persistent sync state storage
5. Connected memory extraction to Sprint 07 ingestion pipeline
6. Added Celery task for background memory extraction after sync
7. Added full-text search (FTS) index on gmail_messages for unified search (Sprint 16)

**Cross-Sprint Dependencies:**
- Sprint 07: Memory ingestion pipeline for extracting memories from emails
- Sprint 13: Integration model and OAuth tokens
- Sprint 16: FTS indexes enable unified search across synced data
