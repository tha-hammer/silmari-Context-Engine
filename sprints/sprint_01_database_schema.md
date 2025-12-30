# Sprint 01: Database & Schema Foundation

**Phase:** 1 - Foundation
**Focus:** Database infrastructure and comprehensive schema
**Dependencies:** None (first sprint)

---

## Testable Deliverable

**Human Test:** Connect to the database and verify:
1. PostgreSQL server is running and accepting connections
2. All core tables exist (users, organizations, memories, messages, etc.)
3. Can INSERT and SELECT test data
4. Indexes are in place and performant
5. Foreign key constraints work correctly

**Test Script:**
```bash
# Connect to database
psql -h localhost -U tanka_user -d tanka_ai

# Verify tables exist
\dt

# Insert test organization
INSERT INTO organizations (name) VALUES ('Test Org') RETURNING id;

# Insert test user
INSERT INTO users (email, organization_id, created_at)
VALUES ('test@example.com', '<org_id>', NOW());

# Query test user
SELECT * FROM users WHERE email = 'test@example.com';

# Verify foreign keys
SELECT * FROM conversations c
JOIN conversation_participants cp ON c.id = cp.conversation_id;
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_173 | PostgreSQL for structured data storage | 18 |
| REQ_169 | Vector database for memory storage | 18 |
| REQ_006 | EverMemOS memory framework | 17 |

### Implementation Requirements (from groups)

**Group 009 - Database Schema (8 requirements)**
- REQ_006.2.1: Define core memory architecture, data model, storage engine
- REQ_006.2.3: Create data model for storing memories
- REQ_013.2.1: Configure secure cloud storage infrastructure
- REQ_013.4.1: Establish secure cloud infrastructure
- REQ_013.4.2: Configure storage for user data, memory, assets
- REQ_173.2.1: Design PostgreSQL schema for structured data
- REQ_173.2.2: Implement database connection pooling
- REQ_173.2.3: Create database migration scripts

---

## Complete Database Schema

### Core Tables - Organizations & Users

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector for embeddings

-- Organizations (Multi-tenancy foundation)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE,
    plan_type VARCHAR(50) DEFAULT 'free',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),

    -- Profile fields
    display_name VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);

-- User Preferences
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,

    -- Memory settings
    auto_include_memories BOOLEAN DEFAULT true,
    max_memories_per_request INT DEFAULT 5,
    auto_extract_from_chat BOOLEAN DEFAULT false,
    excluded_memory_types TEXT[],

    -- Notification settings
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true,

    -- UI preferences
    theme VARCHAR(20) DEFAULT 'system',
    language VARCHAR(10) DEFAULT 'en',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
```

### Memory System Tables

```sql
-- Memories
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Content
    content TEXT NOT NULL,
    title VARCHAR(500),
    memory_type VARCHAR(50) NOT NULL DEFAULT 'note',
    source VARCHAR(50) NOT NULL DEFAULT 'manual',
    source_id VARCHAR(255),

    -- Organization
    tags TEXT[],
    metadata JSONB DEFAULT '{}',

    -- Vector embedding
    embedding VECTOR(1536),
    embedding_status VARCHAR(20) DEFAULT 'pending',
    embedding_model VARCHAR(100),
    embedding_updated_at TIMESTAMP,

    -- Relationships
    conversation_id UUID,  -- FK added after conversations table

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    accessed_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,

    CONSTRAINT memories_content_check CHECK (char_length(content) <= 50000)
);

CREATE INDEX idx_memories_user ON memories(user_id);
CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_source ON memories(source);
CREATE INDEX idx_memories_created ON memories(created_at DESC);
CREATE INDEX idx_memories_tags ON memories USING GIN(tags);
CREATE INDEX idx_memories_metadata ON memories USING GIN(metadata);
CREATE INDEX idx_memories_embedding ON memories
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_memories_deleted ON memories(deleted_at) WHERE deleted_at IS NULL;
```

### Communication Tables

```sql
-- Conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Type: 'direct', 'group', 'ai_chat'
    type VARCHAR(20) NOT NULL DEFAULT 'direct',

    -- Group-specific fields
    name VARCHAR(255),
    description TEXT,
    avatar_url VARCHAR(500),
    is_private BOOLEAN DEFAULT true,

    -- Ownership
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_conversations_org ON conversations(organization_id);
CREATE INDEX idx_conversations_type ON conversations(type);
CREATE INDEX idx_conversations_created_by ON conversations(created_by);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);

-- Conversation Participants
CREATE TABLE conversation_participants (
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member',  -- owner, admin, member
    joined_at TIMESTAMP DEFAULT NOW(),
    last_read_at TIMESTAMP,
    is_muted BOOLEAN DEFAULT false,
    PRIMARY KEY (conversation_id, user_id)
);

CREATE INDEX idx_participants_user ON conversation_participants(user_id);
CREATE INDEX idx_participants_role ON conversation_participants(role);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- NULL for AI/system messages

    -- Content
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text',  -- text, file, system, ai

    -- Status
    status VARCHAR(20) DEFAULT 'sent',  -- sent, delivered, read
    is_edited BOOLEAN DEFAULT false,

    -- AI-specific
    is_ai_response BOOLEAN DEFAULT false,
    ai_model VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    edited_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_content_search ON messages USING GIN(to_tsvector('english', content));

-- Message Memory Usage (for RAG tracking)
CREATE TABLE message_memory_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    relevance_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_message_memory_message ON message_memory_usage(message_id);
CREATE INDEX idx_message_memory_memory ON message_memory_usage(memory_id);

-- Add FK from memories to conversations
ALTER TABLE memories
ADD CONSTRAINT fk_memories_conversation
FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL;
```

### Task Management Tables

```sql
-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Content
    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- Status & Priority
    status VARCHAR(20) DEFAULT 'todo',  -- todo, in_progress, done, cancelled
    priority VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, urgent

    -- Dates
    due_date DATE,
    due_time TIME,
    reminder_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Source tracking
    source VARCHAR(50) DEFAULT 'manual',  -- manual, ai_created, ai_extracted, integration
    source_id UUID,  -- conversation_id, memory_id, etc.
    source_type VARCHAR(50),

    -- Organization
    project_id UUID,
    tags TEXT[],

    -- Recurrence
    recurrence_rule VARCHAR(255),  -- RRULE format

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_priority ON tasks(priority);
```

### Integration Tables

```sql
-- Integrations (OAuth connections)
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Provider info
    provider VARCHAR(50) NOT NULL,  -- google, microsoft, slack, notion
    status VARCHAR(20) DEFAULT 'pending',  -- pending, active, expired, error, disconnected

    -- Tokens (encrypted)
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMP,

    -- Permissions
    scopes TEXT[],

    -- Sync state
    last_sync_at TIMESTAMP,
    sync_cursor TEXT,  -- For incremental sync

    -- Metadata
    provider_user_id VARCHAR(255),
    provider_email VARCHAR(255),
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    connected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, provider)
);

CREATE INDEX idx_integrations_user ON integrations(user_id);
CREATE INDEX idx_integrations_provider ON integrations(provider);
CREATE INDEX idx_integrations_status ON integrations(status);

-- Gmail Messages (synced)
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

    labels TEXT[],
    is_read BOOLEAN DEFAULT false,

    received_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, gmail_id)
);

CREATE INDEX idx_gmail_user ON gmail_messages(user_id);
CREATE INDEX idx_gmail_received ON gmail_messages(received_at DESC);
CREATE INDEX idx_gmail_search ON gmail_messages USING GIN(to_tsvector('english', subject || ' ' || COALESCE(body_text, '')));

-- Calendar Events (synced - Google & Microsoft)
CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,

    provider VARCHAR(20) NOT NULL,  -- google, microsoft
    provider_event_id VARCHAR(255) NOT NULL,
    calendar_id VARCHAR(255),

    title VARCHAR(500),
    description TEXT,
    location TEXT,

    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    is_all_day BOOLEAN DEFAULT false,
    timezone VARCHAR(50),

    attendees JSONB DEFAULT '[]',

    -- Online meeting
    is_online_meeting BOOLEAN DEFAULT false,
    online_meeting_url TEXT,

    -- Recurrence
    recurrence_rule VARCHAR(255),

    synced_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, provider, provider_event_id)
);

CREATE INDEX idx_calendar_user ON calendar_events(user_id);
CREATE INDEX idx_calendar_time ON calendar_events(start_time, end_time);

-- Drive/OneDrive Files (synced)
CREATE TABLE drive_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,

    provider VARCHAR(20) NOT NULL,  -- google, microsoft
    provider_file_id VARCHAR(255) NOT NULL,

    name VARCHAR(500) NOT NULL,
    mime_type VARCHAR(255),
    size_bytes BIGINT,

    web_url TEXT,
    parent_path TEXT,

    modified_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, provider, provider_file_id)
);

CREATE INDEX idx_drive_user ON drive_files(user_id);
CREATE INDEX idx_drive_name ON drive_files(name);
```

### Knowledge Graph Tables

```sql
-- Entities (extracted from content)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    entity_type VARCHAR(50) NOT NULL,  -- person, organization, project, location, etc.
    name VARCHAR(255) NOT NULL,
    aliases TEXT[],
    description TEXT,

    metadata JSONB DEFAULT '{}',
    mention_count INT DEFAULT 1,

    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, entity_type, name)
);

CREATE INDEX idx_entities_user ON entities(user_id);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_name ON entities(name);

-- Entity Relationships
CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,

    relationship_type VARCHAR(50) NOT NULL,  -- works_at, knows, manages, part_of
    strength FLOAT DEFAULT 0.5,
    context TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_entity_rel_source ON entity_relationships(source_entity_id);
CREATE INDEX idx_entity_rel_target ON entity_relationships(target_entity_id);

-- Entity Mentions
CREATE TABLE entity_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,

    source_type VARCHAR(50) NOT NULL,  -- memory, message, email, file
    source_id UUID NOT NULL,
    context TEXT,
    position INT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_entity_mentions_entity ON entity_mentions(entity_id);
CREATE INDEX idx_entity_mentions_source ON entity_mentions(source_type, source_id);
```

### RBAC & Audit Tables

```sql
-- Roles
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT false,
    permissions TEXT[] NOT NULL DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_roles_org ON roles(organization_id);

-- User Roles
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    granted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,

    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Action details
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),

    -- Context
    ip_address INET,
    user_agent TEXT,
    session_id UUID,

    -- Changes
    old_value JSONB,
    new_value JSONB,

    -- Status
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_org ON audit_logs(organization_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
```

### Document & Template Tables

```sql
-- Generated Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    document_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    outline TEXT[],

    template_id UUID,
    status VARCHAR(20) DEFAULT 'draft',  -- draft, generating, ready, exported

    context_memory_ids UUID[],

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_documents_type ON documents(document_type);

-- Document Templates
CREATE TABLE document_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    outline TEXT[],
    instructions TEXT,

    is_system BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_templates_org ON document_templates(organization_id);
CREATE INDEX idx_templates_type ON document_templates(document_type);
```

### Mobile & Notification Tables

```sql
-- Devices (for push notifications)
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    device_token TEXT NOT NULL,
    platform VARCHAR(20) NOT NULL,  -- ios, android, web
    device_name VARCHAR(255),

    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP DEFAULT NOW(),

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, device_token)
);

CREATE INDEX idx_devices_user ON devices(user_id);
CREATE INDEX idx_devices_active ON devices(is_active) WHERE is_active = true;

-- Notifications
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    body TEXT,
    data JSONB DEFAULT '{}',

    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,

    -- Related resource
    resource_type VARCHAR(50),
    resource_id UUID,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = false;
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
```

---

## Tasks

### Infrastructure Setup
- [ ] Install PostgreSQL 15+
- [ ] Install pgvector extension for vector operations
- [ ] Create database and user with appropriate permissions
- [ ] Configure connection pooling (PgBouncer or native)

### Schema Design
- [ ] Run all migration scripts in order
- [ ] Verify all indexes created
- [ ] Set up foreign key constraints
- [ ] Configure JSONB columns for flexible metadata

### Migration System
- [ ] Set up migration tool (Alembic for Python)
- [ ] Create versioned migration scripts
- [ ] Document rollback procedures
- [ ] Set up migration CI/CD

### Verification
- [ ] Write schema validation tests
- [ ] Verify connection pooling works
- [ ] Test basic CRUD operations on all tables
- [ ] Benchmark query performance
- [ ] Test cascade deletes

---

## Acceptance Criteria

1. PostgreSQL server running with pgvector extension
2. All tables created with proper constraints
3. Connection pooling handles 100+ concurrent connections
4. Basic queries execute in < 10ms
5. Migration scripts run without errors
6. All indexes verified with EXPLAIN ANALYZE
7. Foreign key cascades work correctly

---

## Files to Create

```
src/
  database/
    __init__.py
    connection.py      # Database connection management
    models/
      __init__.py
      base.py          # SQLAlchemy base
      user.py
      organization.py
      memory.py
      conversation.py
      message.py
      task.py
      integration.py
      entity.py
      role.py
      audit.py
      document.py
      device.py
    migrations/
      versions/
        001_initial_schema.py
        002_add_indexes.py
      env.py
      alembic.ini
```

---

## Related Requirement Groups

- Group 001: Implementation (backend, frontend, middleware, shared_objects)
- Group 009: Semantic: Database Schema
- Group 015: Semantic: Data Storage
