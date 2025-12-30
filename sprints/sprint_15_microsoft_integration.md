# Sprint 15: Microsoft 365 Integration

**Phase:** 4 - Business Tools
**Focus:** Outlook, Teams, OneDrive sync
**Dependencies:** Sprint 13 (OAuth)

---

## Testable Deliverable

**Human Test:**
1. Connect Microsoft 365 account
2. See recent Outlook emails
3. See calendar events
4. Browse OneDrive files
5. Data syncs from Microsoft

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_050 | Outlook Calendar integration | 19 |
| REQ_053 | OneDrive integration | 17 |

### Implementation Requirements
- REQ_050.2.1-2.3: Calendar sync implementation
- REQ_053.2.1-2.3: OneDrive file access

---

## Microsoft Graph API

```python
MICROSOFT_GRAPH_BASE = "https://graph.microsoft.com/v1.0"

ENDPOINTS = {
    "me": "/me",
    "messages": "/me/messages",
    "calendar_events": "/me/calendar/events",
    "drive_files": "/me/drive/root/children",
    "drive_search": "/me/drive/root/search(q='{query}')"
}
```

---

## Data Models

```python
class OutlookMessage(BaseModel):
    id: UUID
    user_id: UUID
    integration_id: UUID    # FK to integrations table
    outlook_id: str
    conversation_id: str
    subject: str
    from_email: str
    to_emails: List[str]
    preview: str
    body_text: str | None
    received_at: datetime
    is_read: bool
    importance: str
    synced_at: datetime

class OutlookEvent(BaseModel):
    id: UUID
    user_id: UUID
    integration_id: UUID    # FK to integrations table
    outlook_event_id: str
    title: str
    body: str | None
    start_time: datetime
    end_time: datetime
    location: str | None
    attendees: List[Dict]
    is_all_day: bool
    is_online_meeting: bool
    online_meeting_url: str | None
    synced_at: datetime

class OneDriveFile(BaseModel):
    id: UUID
    user_id: UUID
    integration_id: UUID    # FK to integrations table
    onedrive_id: str
    name: str
    mime_type: str
    size_bytes: int
    web_url: str
    parent_path: str
    modified_at: datetime
    synced_at: datetime

# Microsoft uses delta links for incremental sync
class MicrosoftSyncState(BaseModel):
    id: UUID
    integration_id: UUID
    resource_type: str      # mail, calendar, onedrive
    delta_link: str | None  # Microsoft Graph delta URL for incremental sync
    last_sync_at: datetime
    items_synced: int
    status: str             # idle, syncing, error
    error_message: str | None
```

---

## Database Schema

```sql
-- Outlook messages table
CREATE TABLE outlook_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    outlook_id VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255),
    subject TEXT,
    from_email VARCHAR(255),
    to_emails TEXT[],
    preview TEXT,
    body_text TEXT,
    received_at TIMESTAMP,
    is_read BOOLEAN DEFAULT false,
    importance VARCHAR(20),
    synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(integration_id, outlook_id)
);

CREATE INDEX idx_outlook_msg_user ON outlook_messages(user_id);
CREATE INDEX idx_outlook_msg_integration ON outlook_messages(integration_id);
CREATE INDEX idx_outlook_msg_received ON outlook_messages(user_id, received_at DESC);
CREATE INDEX idx_outlook_msg_fts ON outlook_messages USING GIN (
    to_tsvector('english', coalesce(subject, '') || ' ' || coalesce(body_text, ''))
);

-- Outlook calendar events table
CREATE TABLE outlook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    outlook_event_id VARCHAR(255) NOT NULL,
    title TEXT,
    body TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    location TEXT,
    attendees JSONB DEFAULT '[]',
    is_all_day BOOLEAN DEFAULT false,
    is_online_meeting BOOLEAN DEFAULT false,
    online_meeting_url TEXT,
    synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(integration_id, outlook_event_id)
);

CREATE INDEX idx_outlook_evt_user ON outlook_events(user_id);
CREATE INDEX idx_outlook_evt_time ON outlook_events(user_id, start_time);

-- OneDrive files table
CREATE TABLE onedrive_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    onedrive_id VARCHAR(255) NOT NULL,
    name TEXT,
    mime_type VARCHAR(255),
    size_bytes BIGINT,
    web_url TEXT,
    parent_path TEXT,
    modified_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(integration_id, onedrive_id)
);

CREATE INDEX idx_onedrive_user ON onedrive_files(user_id);
CREATE INDEX idx_onedrive_parent ON onedrive_files(integration_id, parent_path);

-- Note: Microsoft sync states use the same sync_states table from Sprint 14
-- The delta_link is stored in the sync_token column
```

---

## API Endpoints

```yaml
# Outlook Mail
GET /api/v1/integrations/microsoft/mail/messages
GET /api/v1/integrations/microsoft/mail/messages/{id}
POST /api/v1/integrations/microsoft/mail/sync

# Outlook Calendar
GET /api/v1/integrations/microsoft/calendar/events
GET /api/v1/integrations/microsoft/calendar/upcoming
POST /api/v1/integrations/microsoft/calendar/sync

# OneDrive
GET /api/v1/integrations/microsoft/onedrive/files
GET /api/v1/integrations/microsoft/onedrive/search
```

---

## Tasks

### Backend - Microsoft Graph Client
- [ ] Create Graph API wrapper
- [ ] Implement token refresh
- [ ] Handle API errors

### Backend - Outlook Mail Sync
- [ ] Fetch messages list
- [ ] Fetch message content
- [ ] Store messages
- [ ] Handle folders/categories

### Backend - Calendar Sync
- [ ] Fetch events in range
- [ ] Store events
- [ ] Handle recurring events
- [ ] Teams meeting detection

### Backend - OneDrive Sync
- [ ] List files and folders
- [ ] Search files
- [ ] File metadata

### Frontend - Microsoft Dashboard
- [ ] Mail messages view
- [ ] Calendar events
- [ ] OneDrive browser

---

## Acceptance Criteria

1. Microsoft OAuth works
2. Outlook emails display
3. Calendar events sync
4. OneDrive files accessible
5. Sync errors handled
6. Teams meeting links shown

---

## Graph API Client

```python
class MicrosoftGraphClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"

    async def get(self, endpoint: str, params: dict = None):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def get_messages(self, top: int = 50, skip: int = 0):
        return await self.get("/me/messages", {
            "$top": top,
            "$skip": skip,
            "$orderby": "receivedDateTime desc"
        })

    async def get_calendar_events(
        self,
        start: datetime,
        end: datetime
    ):
        return await self.get("/me/calendar/events", {
            "$filter": f"start/dateTime ge '{start.isoformat()}' and end/dateTime le '{end.isoformat()}'",
            "$orderby": "start/dateTime"
        })

    async def get_drive_files(self, folder_id: str = "root"):
        if folder_id == "root":
            return await self.get("/me/drive/root/children")
        return await self.get(f"/me/drive/items/{folder_id}/children")
```

---

## Files to Create

```
src/
  integrations/
    microsoft/
      __init__.py
      client.py
      mail_sync.py
      calendar_sync.py
      onedrive_sync.py
      router.py
      schemas.py

frontend/src/
  components/
    integrations/
      microsoft/
        OutlookList.tsx
        OutlookCalendar.tsx
        OneDriveExplorer.tsx
```

---

## Related Requirement Groups

- REQ_050: Outlook Calendar
- REQ_053: OneDrive
- Integration domain

---

## Memory Extraction (Integration with Sprint 07)

```python
from src.memories.ingestion import MemoryIngestionService  # From Sprint 07

# Celery task for background extraction after sync
@celery.task
def extract_memories_from_synced_outlook(integration_id: UUID, message_ids: List[UUID]):
    """Background task to extract memories from newly synced Outlook emails."""
    from src.memories.ingestion import MemoryIngestionService

    ingestion_service = MemoryIngestionService()
    integration = get_integration(integration_id)

    for message_id in message_ids:
        message = get_outlook_message(message_id)
        asyncio.run(ingestion_service.ingest_text(
            text=f"Subject: {message.subject}\n\n{message.body_text}",
            user_id=integration.user_id,
            source="outlook",
            source_id=str(message.id),
            metadata={
                "from_email": message.from_email,
                "to_emails": message.to_emails,
                "received_at": message.received_at.isoformat(),
            }
        ))
```

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added `integration_id` FK to all data models (OutlookMessage, OutlookEvent, OneDriveFile)
2. Added complete SQL database schema with proper indexes and constraints
3. Added `MicrosoftSyncState` model with delta_link for Microsoft Graph incremental sync
4. Added FTS indexes on outlook_messages for unified search (Sprint 16)
5. Added memory extraction Celery task connected to Sprint 07 pipeline

**Cross-Sprint Dependencies:**
- Sprint 07: Memory ingestion pipeline for extracting memories from emails
- Sprint 13: Integration model and OAuth tokens
- Sprint 14: Shares sync_states table structure
- Sprint 16: FTS indexes enable unified search across synced data
