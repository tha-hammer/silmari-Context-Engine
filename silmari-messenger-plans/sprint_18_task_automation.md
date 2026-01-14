# Sprint 18: Task Automation

**Phase:** 5 - AI Enhancement
**Focus:** AI-driven task creation and tracking
**Dependencies:** Sprint 10 (AI Chat), Sprint 12 (Memory)

---

## Testable Deliverable

**Human Test:**
1. Tell AI "Create a task to review Q4 report by Friday"
2. Task appears in task list
3. AI confirms task creation
4. View task with due date
5. Mark task complete
6. AI extracts tasks from conversations automatically

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_004 | Automated workflows and task management | 17 |
| REQ_068 | Track and alert on approaching deadlines | 17 |

### Implementation Requirements
- REQ_004.2.1: Create tasks from AI commands
- REQ_004.2.2: Task tracking and status
- REQ_068.2.1: Due date tracking
- REQ_068.2.2: Deadline notifications

---

## Data Model

```python
class Task(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    due_time: time | None
    reminder_at: datetime | None

    # Source tracking
    source: TaskSource
    source_id: str | None    # conversation_id, memory_id, etc.

    # Organization
    project_id: UUID | None
    tags: List[str]

    # Recurrence
    recurrence_rule: str | None  # RRULE format

    # Completion
    completed_at: datetime | None

    created_at: datetime
    updated_at: datetime

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskSource(Enum):
    MANUAL = "manual"
    AI_CREATED = "ai_created"
    AI_EXTRACTED = "ai_extracted"
    INTEGRATION = "integration"

# Task reminder for notifications
class TaskReminder(BaseModel):
    id: UUID
    task_id: UUID
    user_id: UUID
    scheduled_for: datetime
    notification_type: str     # push, email, in_app
    status: str                # pending, sent, dismissed
    sent_at: datetime | None
    created_at: datetime
```

---

## Database Schema

```sql
-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'todo',
    priority VARCHAR(20) DEFAULT 'medium',
    due_date DATE,
    due_time TIME,
    reminder_at TIMESTAMP,

    -- Source tracking
    source VARCHAR(50) DEFAULT 'manual',
    source_id VARCHAR(255),       -- conversation_id, memory_id, etc.

    -- Organization (project_id deferred to future sprint)
    tags TEXT[] DEFAULT '{}',

    -- Recurrence
    recurrence_rule TEXT,          -- RRULE format

    -- Completion
    completed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_due ON tasks(user_id, due_date) WHERE status != 'done';
CREATE INDEX idx_tasks_source ON tasks(source, source_id);

-- Task reminders for notification scheduling
CREATE TABLE task_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_for TIMESTAMP NOT NULL,
    notification_type VARCHAR(20) DEFAULT 'in_app',
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(task_id, scheduled_for)
);

CREATE INDEX idx_reminders_pending ON task_reminders(scheduled_for)
    WHERE status = 'pending';
CREATE INDEX idx_reminders_user ON task_reminders(user_id);
```

---

## API Endpoints

```yaml
# Tasks CRUD
POST /api/v1/tasks
GET /api/v1/tasks
GET /api/v1/tasks/{id}
PATCH /api/v1/tasks/{id}
DELETE /api/v1/tasks/{id}

# Task Status
POST /api/v1/tasks/{id}/complete
POST /api/v1/tasks/{id}/reopen

# AI Task Operations
POST /api/v1/tasks/ai/create
  Request:
    instruction: string  # "Create task to review report by Friday"
  Response:
    task: Task
    interpretation: string  # How AI understood the request

POST /api/v1/tasks/ai/extract
  Request:
    text: string
  Response:
    extracted_tasks: [
      { title, due_date, confidence }
    ]

# Due Today / Upcoming
GET /api/v1/tasks/due-today
GET /api/v1/tasks/upcoming?days=7
GET /api/v1/tasks/overdue
```

---

## Tasks

### Backend - Task Model
- [ ] Create Task model
- [ ] Implement CRUD operations
- [ ] Add status transitions
- [ ] Due date queries

### Backend - AI Task Creation
- [ ] Parse natural language to task
- [ ] Extract due dates
- [ ] Extract priority
- [ ] Confirm task interpretation

### Backend - Task Extraction
- [ ] Extract tasks from text
- [ ] Integrate with conversation flow
- [ ] Handle extraction from memories

### Backend - Reminders
- [ ] Schedule reminder notifications
- [ ] Due date alerts
- [ ] Overdue task detection

### Frontend - Task List
- [ ] Task list view
- [ ] Filter by status/date
- [ ] Quick complete button
- [ ] Task detail modal

### Frontend - AI Integration
- [ ] "Create task" AI command
- [ ] Task extraction preview
- [ ] Confirm extracted tasks

---

## Acceptance Criteria

1. Can create task via AI command
2. Task has title, due date, priority
3. Task appears in task list
4. Can mark task complete
5. AI extracts tasks from text
6. Due dates are parsed correctly
7. Overdue tasks highlighted

---

## AI Task Parser

```python
class AITaskParser:
    def __init__(self, llm: LLMService):
        self.llm = llm

    async def parse_task_instruction(
        self,
        instruction: str,
        user_timezone: str = "UTC"
    ) -> ParsedTask:
        """Parse natural language into structured task."""

        prompt = f"""Parse this task instruction into structured data.
Current date: {datetime.now().strftime('%Y-%m-%d')}
User timezone: {user_timezone}

Instruction: "{instruction}"

Respond with JSON:
{{
    "title": "concise task title",
    "description": "additional details or null",
    "due_date": "YYYY-MM-DD or null",
    "due_time": "HH:MM or null",
    "priority": "low|medium|high|urgent",
    "confidence": 0.0-1.0
}}"""

        response = await self.llm.generate(prompt, json_mode=True)
        return ParsedTask(**json.loads(response))

    async def extract_tasks_from_text(
        self,
        text: str
    ) -> List[ExtractedTask]:
        """Extract multiple tasks from a block of text."""

        prompt = f"""Extract action items and tasks from this text.

Text:
{text}

For each task found, provide:
- title: what needs to be done
- due_date: if mentioned (YYYY-MM-DD)
- assignee: if mentioned
- confidence: how confident you are this is a task (0.0-1.0)

Respond with JSON array."""

        response = await self.llm.generate(prompt, json_mode=True)
        return [ExtractedTask(**t) for t in json.loads(response)]
```

---

## AI Function Calling

```python
# Define task creation as an AI tool
TASK_TOOLS = [
    {
        "name": "create_task",
        "description": "Create a new task for the user",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "due_date": {"type": "string", "format": "date"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "description": {"type": "string"}
            },
            "required": ["title"]
        }
    }
]

async def handle_ai_tool_call(tool_call, user_id: UUID):
    if tool_call.name == "create_task":
        task = await task_service.create(
            user_id=user_id,
            source=TaskSource.AI_CREATED,
            **tool_call.arguments
        )
        return f"Created task: {task.title}"
```

---

## UI Components

```typescript
// Task List
<TaskList>
  <TaskFilters
    status={statusFilter}
    dateRange={dateFilter}
    onFilterChange={setFilters}
  />

  {tasks.map(task => (
    <TaskItem
      key={task.id}
      task={task}
      onComplete={() => completeTask(task.id)}
      onClick={() => openTaskDetail(task)}
    />
  ))}
</TaskList>

// Task Item
<TaskItem>
  <Checkbox
    checked={task.status === 'done'}
    onChange={onComplete}
  />
  <TaskTitle strikethrough={task.status === 'done'}>
    {task.title}
  </TaskTitle>
  <DueDate date={task.due_date} isOverdue={isOverdue} />
  <PriorityBadge priority={task.priority} />
</TaskItem>
```

---

## Files to Create

```
src/
  tasks/
    __init__.py
    models.py
    schemas.py
    service.py
    router.py
    ai_parser.py
    reminders.py

frontend/src/
  app/dashboard/
    tasks/
      page.tsx
  components/
    tasks/
      TaskList.tsx
      TaskItem.tsx
      TaskDetail.tsx
      TaskForm.tsx
      DueDatePicker.tsx
```

---

## Related Requirement Groups

- REQ_004: Automated workflows
- REQ_068: Deadline tracking
- Task management domain

---

## Real-time Task Updates (WebSocket from Sprint 09)

```python
from src.websocket import WebSocketManager  # From Sprint 09

async def notify_task_created(task: Task, user_id: UUID):
    """Send real-time notification when AI creates a task."""
    await websocket_manager.send_to_user(
        user_id=user_id,
        message={
            "type": "task_created",
            "payload": {
                "task_id": str(task.id),
                "title": task.title,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "source": task.source,
            }
        }
    )

# Call this after AI tool creates a task
async def handle_ai_tool_call(tool_call, user_id: UUID):
    if tool_call.name == "create_task":
        task = await task_service.create(
            user_id=user_id,
            source=TaskSource.AI_CREATED,
            **tool_call.arguments
        )
        # Notify frontend in real-time
        await notify_task_created(task, user_id)
        return f"Created task: {task.title}"
```

---

## Reminder Scheduling (Celery from Sprint 03)

```python
from celery import Celery
from celery.schedules import crontab

celery = Celery('tasks')

# Periodic task to check for due reminders
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Check for reminders every minute
    sender.add_periodic_task(
        60.0,
        check_and_send_reminders.s(),
        name='check-reminders-every-minute'
    )

@celery.task
def check_and_send_reminders():
    """Check for pending reminders and send notifications."""
    now = datetime.utcnow()

    # Get pending reminders due now
    pending = db.query(TaskReminder).filter(
        TaskReminder.status == 'pending',
        TaskReminder.scheduled_for <= now
    ).all()

    for reminder in pending:
        send_reminder_notification(reminder)

def send_reminder_notification(reminder: TaskReminder):
    """Send reminder via appropriate channel."""
    task = get_task(reminder.task_id)

    if reminder.notification_type == 'in_app':
        # Send via WebSocket
        asyncio.run(websocket_manager.send_to_user(
            user_id=reminder.user_id,
            message={
                "type": "task_reminder",
                "payload": {
                    "task_id": str(task.id),
                    "title": task.title,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                }
            }
        ))

    elif reminder.notification_type == 'push':
        # Send push notification (requires Sprint 23 mobile setup)
        send_push_notification(
            user_id=reminder.user_id,
            title="Task Reminder",
            body=f"Don't forget: {task.title}"
        )

    elif reminder.notification_type == 'email':
        # Send email notification
        send_email(
            to=get_user_email(reminder.user_id),
            subject=f"Reminder: {task.title}",
            body=f"Your task '{task.title}' is due soon."
        )

    # Mark reminder as sent
    reminder.status = 'sent'
    reminder.sent_at = datetime.utcnow()
    db.commit()
```

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added complete SQL database schema for tasks and task_reminders tables
2. Added `TaskReminder` model for scheduling notifications
3. Added WebSocket notification for real-time task updates (using Sprint 09 infrastructure)
4. Added Celery periodic task for checking and sending reminders
5. Added multi-channel notification support (in_app, push, email)
6. Removed `project_id` FK (deferred to future sprint when Project model is defined)

**Cross-Sprint Dependencies:**
- Sprint 03: Celery infrastructure for periodic tasks
- Sprint 09: WebSocket for real-time notifications
- Sprint 23: Push notification infrastructure for mobile reminders

**Note:** The `project_id` field was removed from the Task model as no Project table is defined. This can be added in a future sprint when project/workspace organization is implemented.
