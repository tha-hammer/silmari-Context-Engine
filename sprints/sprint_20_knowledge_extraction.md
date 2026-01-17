# Sprint 20: Knowledge Extraction

**Phase:** 5 - AI Enhancement
**Focus:** Automatic entity and relationship extraction
**Dependencies:** Sprint 07 (Ingestion), Sprint 17 (RAG)

---

## Testable Deliverable

**Human Test:**
1. Upload a document or paste text
2. System extracts people, companies, dates
3. Entities appear as tags/connections
4. Relationships visualized (who knows whom)
5. Search by entity works
6. Knowledge graph view available

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_060 | Extract knowledge from integrated data | 19 |
| REQ_014 | Extract memories from conversations | 17 |

### Implementation Requirements
- REQ_014.2.2: Identify key entities
- REQ_060.2.1: Entity extraction
- REQ_060.2.2: Relationship mapping

---

## Entity Types

```python
class EntityType(Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    PROJECT = "project"
    PRODUCT = "product"
    LOCATION = "location"
    DATE = "date"
    MONEY = "money"
    EVENT = "event"
    TOPIC = "topic"
    CUSTOM = "custom"

class Entity(BaseModel):
    id: UUID
    user_id: UUID
    entity_type: EntityType
    name: str
    aliases: List[str]        # Alternative names
    description: str | None
    metadata: Dict            # Type-specific data
    mention_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    source_ids: List[UUID]    # Where this entity was found

class EntityRelationship(BaseModel):
    id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str    # "works_at", "knows", "manages", etc.
    strength: float           # 0-1 based on co-occurrence
    context: str | None       # Example sentence showing relationship
    created_at: datetime

class EntityMention(BaseModel):
    id: UUID
    entity_id: UUID
    source_type: str          # memory, message, email, etc.
    source_id: UUID
    context: str              # Surrounding text
    position: int             # Character position
    created_at: datetime
```

---

## API Endpoints

```yaml
# Entities
GET /api/v1/entities
  Query: ?type=person&limit=50
  Response: Entity[]

GET /api/v1/entities/{id}
  Response: Entity with mentions and relationships

POST /api/v1/entities/extract
  Request:
    text: string
    source_type: string
    source_id: uuid
  Response:
    entities: Entity[]
    relationships: EntityRelationship[]

# Relationships
GET /api/v1/entities/{id}/relationships
  Response: EntityRelationship[]

# Knowledge Graph
GET /api/v1/knowledge/graph
  Query: ?center_entity_id=uuid&depth=2
  Response:
    nodes: Entity[]
    edges: EntityRelationship[]

# Entity Search
GET /api/v1/entities/search
  Query: ?q=john
  Response: Entity[]
```

---

## Tasks

### Backend - Entity Extraction
- [ ] NER (Named Entity Recognition) service
- [ ] LLM-based extraction for complex entities
- [ ] Entity deduplication/merging
- [ ] Alias management

### Backend - Relationship Extraction
- [ ] Co-occurrence analysis
- [ ] LLM relationship inference
- [ ] Relationship strength calculation
- [ ] Relationship type classification

### Backend - Entity Management
- [ ] CRUD operations
- [ ] Mention tracking
- [ ] Entity merging UI support
- [ ] Bulk extraction jobs

### Backend - Knowledge Graph
- [ ] Graph query API
- [ ] Subgraph extraction
- [ ] Path finding between entities

### Frontend - Entity Views
- [ ] Entity list/search
- [ ] Entity detail page
- [ ] Mention list per entity
- [ ] Entity quick-add/edit

### Frontend - Knowledge Graph
- [ ] Graph visualization (D3/vis.js)
- [ ] Interactive node exploration
- [ ] Filter by entity type
- [ ] Zoom and pan

---

## Acceptance Criteria

1. Entities extracted from text
2. People, orgs, dates recognized
3. Relationships detected
4. Entity search works
5. Knowledge graph displays
6. Can navigate relationships
7. Duplicate detection works

---

## Extraction Service

```python
class KnowledgeExtractionService:
    def __init__(self):
        self.ner = NERService()  # spaCy or similar
        self.llm = LLMService()

    async def extract_entities(
        self,
        text: str,
        source_type: str,
        source_id: UUID,
        user_id: UUID
    ) -> ExtractionResult:
        """Extract entities and relationships from text."""

        # 1. Basic NER extraction
        ner_entities = await self.ner.extract(text)

        # 2. LLM enhancement for context
        llm_result = await self.llm_extract(text, ner_entities)

        # 3. Deduplicate against existing entities
        merged_entities = await self.deduplicate(
            llm_result.entities,
            user_id
        )

        # 4. Extract relationships
        relationships = await self.extract_relationships(
            text,
            merged_entities
        )

        # 5. Store mentions
        for entity in merged_entities:
            await self.store_mention(
                entity_id=entity.id,
                source_type=source_type,
                source_id=source_id,
                context=self.get_context(text, entity.name)
            )

        return ExtractionResult(
            entities=merged_entities,
            relationships=relationships
        )

    async def llm_extract(
        self,
        text: str,
        ner_hints: List[NEREntity]
    ) -> LLMExtractionResult:
        """Use LLM for deeper entity extraction."""

        prompt = f"""Analyze this text and extract entities.

Text: {text}

Already detected: {[e.name for e in ner_hints]}

For each entity, provide:
- name: Primary name
- type: person/organization/project/product/location/date/event/topic
- aliases: Other names used
- description: Brief description if inferable

Also identify relationships between entities:
- source: entity name
- target: entity name
- type: works_at/knows/manages/part_of/created/mentioned_with

Respond with JSON."""

        response = await self.llm.generate(prompt, json_mode=True)
        return LLMExtractionResult(**json.loads(response))
```

---

## Knowledge Graph Visualization

```typescript
// Using D3.js or vis.js
import { Network } from 'vis-network';

function KnowledgeGraph({ entities, relationships }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const nodes = entities.map(e => ({
      id: e.id,
      label: e.name,
      group: e.entity_type,
      title: e.description,
    }));

    const edges = relationships.map(r => ({
      from: r.source_entity_id,
      to: r.target_entity_id,
      label: r.relationship_type,
      width: r.strength * 3,
    }));

    const network = new Network(containerRef.current, { nodes, edges }, {
      nodes: {
        shape: 'dot',
        size: 20,
      },
      edges: {
        arrows: 'to',
      },
      physics: {
        stabilization: true,
      },
    });

    network.on('click', (params) => {
      if (params.nodes.length > 0) {
        onEntityClick(params.nodes[0]);
      }
    });
  }, [entities, relationships]);

  return <div ref={containerRef} style={{ height: '500px' }} />;
}
```

---

## Files to Create

```
src/
  knowledge/
    __init__.py
    models.py
    schemas.py
    service.py
    router.py
    extraction/
      __init__.py
      ner.py
      llm_extractor.py
      deduplication.py
      relationship.py
    graph.py

frontend/src/
  app/dashboard/
    knowledge/
      page.tsx
      entities/
        [id]/
          page.tsx
  components/
    knowledge/
      EntityList.tsx
      EntityCard.tsx
      EntityDetail.tsx
      KnowledgeGraph.tsx
      RelationshipList.tsx
```

---

## Related Requirement Groups

- REQ_060: Knowledge extraction
- REQ_014: Memory extraction
- Data processing domain

---

## Database Schema

```sql
-- Entities table
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    name VARCHAR(500) NOT NULL,
    aliases TEXT[] DEFAULT '{}',
    description TEXT,
    metadata JSONB DEFAULT '{}',
    mention_count INT DEFAULT 1,
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_entities_user ON entities(user_id);
CREATE INDEX idx_entities_type ON entities(user_id, entity_type);
CREATE INDEX idx_entities_name ON entities(user_id, lower(name));

-- Entity sources (many-to-many - where entity was found)
CREATE TABLE entity_sources (
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,  -- memory, gmail, outlook, conversation
    source_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (entity_id, source_type, source_id)
);

CREATE INDEX idx_entity_sources_source ON entity_sources(source_type, source_id);

-- Entity mentions (specific occurrences in text)
CREATE TABLE entity_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,
    source_id UUID NOT NULL,
    context TEXT,              -- Surrounding text
    position INT,              -- Character position in source
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mentions_entity ON entity_mentions(entity_id);
CREATE INDEX idx_mentions_source ON entity_mentions(source_type, source_id);

-- Entity relationships
CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    strength FLOAT DEFAULT 0.5,
    context TEXT,              -- Example sentence showing relationship
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(source_entity_id, target_entity_id, relationship_type)
);

CREATE INDEX idx_relationships_source ON entity_relationships(source_entity_id);
CREATE INDEX idx_relationships_target ON entity_relationships(target_entity_id);
```

---

## Automatic Extraction Triggers

```python
# Celery tasks for automatic entity extraction from various sources

@celery.task
def extract_entities_from_memory(memory_id: UUID):
    """Triggered when a new memory is created (Sprint 07)."""
    memory = get_memory(memory_id)
    extraction_service = KnowledgeExtractionService()

    asyncio.run(extraction_service.extract_entities(
        text=memory.content,
        source_type="memory",
        source_id=memory_id,
        user_id=memory.user_id
    ))


@celery.task
def extract_entities_from_email(message_id: UUID, provider: str):
    """Triggered when emails are synced (Sprint 14/15)."""
    if provider == "google":
        message = get_gmail_message(message_id)
    else:
        message = get_outlook_message(message_id)

    extraction_service = KnowledgeExtractionService()

    asyncio.run(extraction_service.extract_entities(
        text=f"{message.subject}\n{message.body_text}",
        source_type=f"{provider}_email",
        source_id=message_id,
        user_id=message.user_id
    ))


@celery.task
def extract_entities_from_conversation(conversation_id: UUID):
    """Triggered periodically for active conversations."""
    messages = get_recent_messages(conversation_id, limit=10)
    user_id = messages[0].sender_id if messages else None

    if not user_id:
        return

    combined_text = "\n".join([m.content for m in messages])
    extraction_service = KnowledgeExtractionService()

    asyncio.run(extraction_service.extract_entities(
        text=combined_text,
        source_type="conversation",
        source_id=conversation_id,
        user_id=user_id
    ))


# Hook into memory creation (Sprint 07)
async def on_memory_created(memory: Memory):
    """Called after memory is saved."""
    extract_entities_from_memory.delay(memory.id)


# Hook into email sync (Sprint 14/15)
async def on_emails_synced(integration_id: UUID, message_ids: List[UUID]):
    """Called after emails are synced."""
    integration = get_integration(integration_id)
    for message_id in message_ids:
        extract_entities_from_email.delay(message_id, integration.provider)
```

---

## NER Service Configuration

```python
import spacy

class NERService:
    """Named Entity Recognition using spaCy."""

    def __init__(self):
        # Load the large English model for better accuracy
        # Install: python -m spacy download en_core_web_lg
        self.nlp = spacy.load("en_core_web_lg")

    async def extract(self, text: str) -> List[NEREntity]:
        """Extract named entities from text."""
        doc = self.nlp(text)

        entities = []
        for ent in doc.ents:
            entity_type = self._map_spacy_type(ent.label_)
            if entity_type:
                entities.append(NEREntity(
                    name=ent.text,
                    type=entity_type,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.8  # spaCy doesn't provide confidence, use fixed
                ))

        return entities

    def _map_spacy_type(self, spacy_label: str) -> str | None:
        """Map spaCy labels to our EntityType enum."""
        mapping = {
            "PERSON": "person",
            "ORG": "organization",
            "GPE": "location",      # Geopolitical entity
            "LOC": "location",
            "DATE": "date",
            "MONEY": "money",
            "EVENT": "event",
            "PRODUCT": "product",
            "WORK_OF_ART": "topic",
        }
        return mapping.get(spacy_label)
```

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added complete SQL database schema for entities, entity_sources, entity_mentions, and relationships
2. Added `entity_sources` junction table replacing the inline `source_ids: List[UUID]` field
3. Added Celery tasks for automatic extraction from memories, emails, and conversations
4. Added hooks to trigger extraction when new content is created
5. Added NER service configuration with spaCy model specification (`en_core_web_lg`)
6. Added spaCy label to EntityType mapping

**Cross-Sprint Dependencies:**
- Sprint 07: Memory creation triggers entity extraction
- Sprint 14/15: Email sync triggers entity extraction
- Sprint 09/10: Conversation messages can trigger extraction

**Model Requirements:**
- spaCy with `en_core_web_lg` model (~750MB)
- Install: `python -m spacy download en_core_web_lg`
