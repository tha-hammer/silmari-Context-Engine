# Sprint 19: Document Generation

**Phase:** 5 - AI Enhancement
**Focus:** AI-generated business documents
**Dependencies:** Sprint 10 (AI Chat), Sprint 17 (RAG)

---

## Testable Deliverable

**Human Test:**
1. Ask AI "Generate a project proposal for our Q2 launch"
2. AI generates formatted document
3. Document includes relevant context from memories
4. Can edit generated content
5. Export to PDF/DOCX
6. Save as template for reuse

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_069 | Generate comprehensive business plans | 19 |
| REQ_070 | Create and review pitch decks | 17 |
| REQ_076 | Create landing page content | 18 |

### Implementation Requirements
- REQ_069.2.1: Business plan generation
- REQ_070.2.1: Pitch deck creation
- REQ_071.2.1: Onboarding document generation

---

## Document Types

```python
class DocumentType(Enum):
    BUSINESS_PLAN = "business_plan"
    PROJECT_PROPOSAL = "project_proposal"
    PITCH_DECK = "pitch_deck"
    MEETING_NOTES = "meeting_notes"
    STATUS_REPORT = "status_report"
    ONBOARDING_DOC = "onboarding_doc"
    EMAIL_DRAFT = "email_draft"
    CUSTOM = "custom"

class GeneratedDocument(BaseModel):
    id: UUID
    user_id: UUID
    document_type: DocumentType
    title: str
    content: str              # Markdown content
    outline: List[str]        # Section headers
    context_used: List[UUID]  # Memory IDs used
    template_id: UUID | None
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

class DocumentStatus(Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    EXPORTED = "exported"

# Export job tracking
class DocumentExport(BaseModel):
    id: UUID
    document_id: UUID
    format: str                # pdf, docx, md
    status: str                # pending, processing, completed, failed
    file_path: str | None      # S3 key or local path
    download_url: str | None   # Presigned URL
    expires_at: datetime | None
    error_message: str | None
    created_at: datetime
```

---

## Database Schema

```sql
-- Generated documents table
CREATE TABLE generated_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,                    -- Markdown content
    outline JSONB DEFAULT '[]',      -- Section headers
    template_id UUID,                -- Optional template reference
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documents_user ON generated_documents(user_id);
CREATE INDEX idx_documents_type ON generated_documents(user_id, document_type);

-- Document templates table
CREATE TABLE document_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,                    -- NULL for system templates
    document_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    outline JSONB DEFAULT '[]',
    instructions TEXT,
    is_system BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_templates_type ON document_templates(document_type);
CREATE INDEX idx_templates_user ON document_templates(user_id) WHERE user_id IS NOT NULL;

-- Document context sources (many-to-many with memories)
CREATE TABLE document_context_sources (
    document_id UUID NOT NULL REFERENCES generated_documents(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    relevance_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (document_id, memory_id)
);

-- Document exports tracking
CREATE TABLE document_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES generated_documents(id) ON DELETE CASCADE,
    format VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    file_path TEXT,                  -- S3 key: documents/{user_id}/{document_id}/{filename}
    download_url TEXT,
    expires_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_exports_document ON document_exports(document_id);
```

---

## API Endpoints

```yaml
# Generate Document
POST /api/v1/documents/generate
  Request:
    type: DocumentType
    title: string
    instructions: string      # User's guidance
    context_query: string     # What to search for
    template_id: uuid (optional)
  Response:
    document_id: uuid
    status: "generating"

# Stream Generation
GET /api/v1/documents/{id}/stream
  Response: SSE stream of content

# Get Document
GET /api/v1/documents/{id}
  Response: GeneratedDocument

# Update Document
PATCH /api/v1/documents/{id}
  Request:
    title: string
    content: string
  Response: GeneratedDocument

# Export Document
POST /api/v1/documents/{id}/export
  Request:
    format: "pdf" | "docx" | "md"
  Response:
    download_url: string

# Templates
GET /api/v1/documents/templates
POST /api/v1/documents/templates
GET /api/v1/documents/templates/{id}
```

---

## Tasks

### Backend - Document Generation
- [ ] Create document generation service
- [ ] Implement streaming generation
- [ ] Context retrieval for generation
- [ ] Section-by-section generation

### Backend - Templates
- [ ] Create template model
- [ ] Default templates per type
- [ ] Custom template support
- [ ] Template variable substitution

### Backend - Export
- [ ] Markdown to PDF (WeasyPrint/Puppeteer)
- [ ] Markdown to DOCX (python-docx)
- [ ] Export job queue
- [ ] Download URL generation

### Frontend - Document Editor
- [ ] Generation wizard
- [ ] Live preview during generation
- [ ] Rich text editing
- [ ] Outline navigation

### Frontend - Export UI
- [ ] Format selection
- [ ] Export progress
- [ ] Download button
- [ ] Share options

---

## Acceptance Criteria

1. Can generate document from instructions
2. Generation uses relevant memories
3. Streaming shows progress
4. Can edit generated content
5. Export to PDF works
6. Export to DOCX works
7. Templates speed up generation

---

## Generation Service

```python
class DocumentGenerationService:
    def __init__(self, llm: LLMService, rag: RAGService):
        self.llm = llm
        self.rag = rag

    async def generate_document(
        self,
        doc_type: DocumentType,
        title: str,
        instructions: str,
        user_id: UUID,
        template_id: UUID = None
    ) -> AsyncGenerator[str, None]:
        """Generate document with streaming."""

        # 1. Get template
        template = await self.get_template(doc_type, template_id)

        # 2. Retrieve context
        context = await self.rag.retrieve_context(
            query=f"{title} {instructions}",
            user_id=user_id,
            config=RAGConfig(max_sources=10)
        )

        # 3. Build generation prompt
        prompt = self.build_prompt(template, instructions, context)

        # 4. Stream generation
        async for chunk in self.llm.stream_generate(prompt):
            yield chunk

    def build_prompt(
        self,
        template: DocumentTemplate,
        instructions: str,
        context: List[RetrievedSource]
    ) -> str:
        context_text = "\n".join([
            f"- {c.content[:300]}" for c in context
        ])

        return f"""Generate a {template.document_type} document.

Template structure:
{template.outline}

User instructions:
{instructions}

Relevant context from user's knowledge:
{context_text}

Generate the complete document in Markdown format.
Include appropriate headers, bullet points, and formatting.
Make it professional and comprehensive."""
```

---

## Document Templates

```python
TEMPLATES = {
    DocumentType.PROJECT_PROPOSAL: {
        "name": "Project Proposal",
        "outline": [
            "# Executive Summary",
            "# Problem Statement",
            "# Proposed Solution",
            "# Scope and Objectives",
            "# Timeline and Milestones",
            "# Resource Requirements",
            "# Risk Assessment",
            "# Budget",
            "# Conclusion"
        ],
        "instructions": "Create a comprehensive project proposal..."
    },
    DocumentType.MEETING_NOTES: {
        "name": "Meeting Notes",
        "outline": [
            "# Meeting Details",
            "## Date, Time, Attendees",
            "# Agenda Items",
            "# Discussion Points",
            "# Decisions Made",
            "# Action Items",
            "# Next Steps"
        ]
    },
    DocumentType.STATUS_REPORT: {
        "name": "Status Report",
        "outline": [
            "# Summary",
            "# Accomplishments This Period",
            "# In Progress",
            "# Upcoming Tasks",
            "# Blockers and Risks",
            "# Metrics"
        ]
    }
}
```

---

## Export Implementation

```python
import markdown
from weasyprint import HTML
from docx import Document
from docx.shared import Inches

class DocumentExporter:
    async def export_pdf(self, content: str, title: str) -> bytes:
        """Convert Markdown to PDF."""
        html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])

        styled_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; border-bottom: 2px solid #333; }}
                h2 {{ color: #555; }}
                table {{ border-collapse: collapse; width: 100%; }}
                td, th {{ border: 1px solid #ddd; padding: 8px; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            {html_content}
        </body>
        </html>
        """

        pdf = HTML(string=styled_html).write_pdf()
        return pdf

    async def export_docx(self, content: str, title: str) -> bytes:
        """Convert Markdown to DOCX."""
        doc = Document()
        doc.add_heading(title, 0)

        # Parse markdown and add to document
        for line in content.split('\n'):
            if line.startswith('# '):
                doc.add_heading(line[2:], 1)
            elif line.startswith('## '):
                doc.add_heading(line[3:], 2)
            elif line.startswith('- '):
                doc.add_paragraph(line[2:], style='List Bullet')
            elif line.strip():
                doc.add_paragraph(line)

        # Save to bytes
        buffer = BytesIO()
        doc.save(buffer)
        return buffer.getvalue()
```

---

## Files to Create

```
src/
  documents/
    __init__.py
    models.py
    schemas.py
    service.py
    router.py
    generator.py
    templates.py
    exporter.py

frontend/src/
  app/dashboard/
    documents/
      page.tsx
      [id]/
        page.tsx
  components/
    documents/
      DocumentWizard.tsx
      DocumentEditor.tsx
      GenerationProgress.tsx
      ExportMenu.tsx
      TemplateSelector.tsx
```

---

## Related Requirement Groups

- REQ_069: Business plans
- REQ_070: Pitch decks
- REQ_076: Landing page content

---

## File Storage Configuration

```python
import boto3
from botocore.config import Config

class DocumentStorageService:
    """Store and retrieve generated document exports."""

    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            config=Config(signature_version='s3v4')
        )
        self.bucket = os.getenv('DOCUMENT_BUCKET', 'tanka-documents')

    async def upload_export(
        self,
        content: bytes,
        user_id: UUID,
        document_id: UUID,
        filename: str
    ) -> str:
        """Upload exported document to S3."""
        key = f"documents/{user_id}/{document_id}/{filename}"

        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=self._get_content_type(filename)
        )

        return key

    async def generate_download_url(
        self,
        file_path: str,
        expires_in: int = 3600  # 1 hour
    ) -> str:
        """Generate presigned URL for download."""
        url = self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': file_path},
            ExpiresIn=expires_in
        )
        return url

    def _get_content_type(self, filename: str) -> str:
        if filename.endswith('.pdf'):
            return 'application/pdf'
        elif filename.endswith('.docx'):
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        return 'application/octet-stream'


# Export job with background processing
@celery.task
def process_document_export(export_id: UUID):
    """Background task to generate and upload document export."""
    export = get_export(export_id)
    document = get_document(export.document_id)

    try:
        export.status = 'processing'
        db.commit()

        # Generate the export
        exporter = DocumentExporter()
        if export.format == 'pdf':
            content = await exporter.export_pdf(document.content, document.title)
            filename = f"{document.title}.pdf"
        elif export.format == 'docx':
            content = await exporter.export_docx(document.content, document.title)
            filename = f"{document.title}.docx"

        # Upload to storage
        storage = DocumentStorageService()
        file_path = await storage.upload_export(
            content=content,
            user_id=document.user_id,
            document_id=document.id,
            filename=filename
        )

        # Generate download URL
        download_url = await storage.generate_download_url(file_path)

        # Update export record
        export.status = 'completed'
        export.file_path = file_path
        export.download_url = download_url
        export.expires_at = datetime.utcnow() + timedelta(hours=1)
        db.commit()

    except Exception as e:
        export.status = 'failed'
        export.error_message = str(e)
        db.commit()
        raise
```

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added complete SQL database schema for documents, templates, context sources, and exports
2. Added `DocumentExport` model for tracking export jobs
3. Added `document_context_sources` junction table for many-to-many with memories
4. Added S3 storage service with presigned URLs for secure downloads
5. Added Celery background task for export processing
6. Added proper content type handling for PDF and DOCX

**Cross-Sprint Dependencies:**
- Sprint 17: RAG service for context retrieval
- Sprint 03: Celery for background export processing
- Sprint 05: Memory table for context sources

**Infrastructure Requirements:**
- AWS S3 bucket for document storage (or compatible like MinIO)
- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `DOCUMENT_BUCKET`
- WeasyPrint or Puppeteer for PDF generation
- python-docx for DOCX generation
