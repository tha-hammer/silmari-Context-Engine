# Sprint 22: Audit & Compliance

**Phase:** 6 - Enterprise & Compliance
**Focus:** Audit logging and compliance features
**Dependencies:** Sprint 21 (RBAC)

---

## Testable Deliverable

**Human Test:**
1. Perform various actions (login, create, delete)
2. View audit log showing all actions
3. Filter by user, action type, date
4. Export audit log to CSV
5. View security events dashboard
6. Data retention settings work

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_011 | ISO 27001-2022 compliance | 17 |
| REQ_012 | SOC 2 Type II compliance | 17 |
| REQ_286 | ISO/SOC compliance achievement | 22 |

### Implementation Requirements
- REQ_011.3.1: Audit logging
- REQ_012.2.1: SOC 2 controls
- REQ_286.2.1: Compliance monitoring

---

## Data Model

```python
class AuditLog(BaseModel):
    id: UUID
    timestamp: datetime
    user_id: UUID | None       # None for system events
    organization_id: UUID

    # Action details
    action: str                # create, read, update, delete, login, etc.
    resource_type: str         # memory, conversation, user, etc.
    resource_id: str | None

    # Context
    ip_address: str | None
    user_agent: str | None
    session_id: str | None

    # Changes (for updates)
    old_value: Dict | None
    new_value: Dict | None

    # Status
    status: str                # success, failure
    error_message: str | None

    # Metadata
    metadata: Dict

class AuditAction(Enum):
    # Auth
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    PASSWORD_CHANGE = "auth.password_change"

    # CRUD
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # Admin
    ROLE_ASSIGN = "admin.role_assign"
    PERMISSION_CHANGE = "admin.permission_change"
    SETTINGS_CHANGE = "admin.settings_change"

    # Integration
    INTEGRATION_CONNECT = "integration.connect"
    INTEGRATION_DISCONNECT = "integration.disconnect"
    INTEGRATION_SYNC = "integration.sync"

    # Data
    EXPORT = "data.export"
    IMPORT = "data.import"
```

---

## API Endpoints

```yaml
# Audit Logs
GET /api/v1/audit/logs
  Query:
    user_id: uuid
    action: string
    resource_type: string
    start_date: datetime
    end_date: datetime
    page: int
    per_page: int
  Response:
    logs: AuditLog[]
    meta: { total, page, per_page }

# Export Audit Logs
POST /api/v1/audit/export
  Request:
    format: "csv" | "json"
    filters: { ... }
  Response:
    download_url: string

# Audit Summary
GET /api/v1/audit/summary
  Query: ?period=7d
  Response:
    total_events: int
    by_action: { login: 100, create: 50, ... }
    by_user: { user_id: count }
    failed_logins: int

# Compliance Dashboard
GET /api/v1/compliance/status
  Response:
    overall_status: "compliant" | "warning" | "critical"
    checks: [
      { name: "Audit Logging", status: "pass" },
      { name: "Encryption at Rest", status: "pass" },
      ...
    ]

# Data Retention
GET /api/v1/compliance/retention
PATCH /api/v1/compliance/retention
  Request:
    audit_log_days: int
    deleted_data_days: int
```

---

## Tasks

### Backend - Audit Logging
- [ ] Create AuditLog model
- [ ] Implement audit middleware
- [ ] Log all CRUD operations
- [ ] Log authentication events

### Backend - Log Management
- [ ] Query/filter audit logs
- [ ] Export to CSV/JSON
- [ ] Log rotation/archival
- [ ] Data retention enforcement

### Backend - Compliance Checks
- [ ] Define compliance rules
- [ ] Automated compliance checking
- [ ] Alert on violations
- [ ] Compliance report generation

### Frontend - Audit Viewer
- [ ] Audit log table with filters
- [ ] Log detail modal
- [ ] Export functionality
- [ ] Timeline visualization

### Frontend - Compliance Dashboard
- [ ] Compliance status overview
- [ ] Check results list
- [ ] Recommendations
- [ ] Remediation links

---

## Acceptance Criteria

1. All actions logged to audit
2. Login attempts tracked
3. Filter logs by criteria
4. Export works
5. Compliance checks run
6. Retention policy enforced
7. Security events highlighted

---

## Audit Middleware

```python
from fastapi import Request
from contextvars import ContextVar

current_request: ContextVar[Request] = ContextVar('current_request')

class AuditMiddleware:
    async def __call__(self, request: Request, call_next):
        # Store request context
        current_request.set(request)

        response = await call_next(request)

        return response

class AuditService:
    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str = None,
        old_value: Dict = None,
        new_value: Dict = None,
        status: str = "success",
        error: str = None,
        user_id: UUID = None,
        metadata: Dict = None
    ):
        """Create an audit log entry."""
        request = current_request.get(None)

        log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            old_value=old_value,
            new_value=new_value,
            status=status,
            error_message=error,
            metadata=metadata or {}
        )

        await self.repository.create(log)

        # Alert on security events
        if action.startswith("auth.") and status == "failure":
            await self.security_alert(log)

# Usage decorator
def audit_action(action: str, resource_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            audit = AuditService()
            try:
                result = await func(*args, **kwargs)
                await audit.log(
                    action=action,
                    resource_type=resource_type,
                    resource_id=str(result.id) if hasattr(result, 'id') else None,
                    status="success"
                )
                return result
            except Exception as e:
                await audit.log(
                    action=action,
                    resource_type=resource_type,
                    status="failure",
                    error=str(e)
                )
                raise
        return wrapper
    return decorator

# Usage
@audit_action("delete", "memory")
async def delete_memory(id: UUID):
    ...
```

---

## Compliance Checks

```python
COMPLIANCE_CHECKS = [
    {
        "id": "audit_logging",
        "name": "Audit Logging Enabled",
        "description": "All user actions are logged",
        "check": lambda: audit_service.is_enabled(),
        "remediation": "Enable audit logging in settings"
    },
    {
        "id": "encryption_at_rest",
        "name": "Encryption at Rest",
        "description": "Sensitive data is encrypted in database",
        "check": lambda: db_service.check_encryption(),
        "remediation": "Enable TDE or application-level encryption"
    },
    {
        "id": "mfa_enforced",
        "name": "MFA Enforcement",
        "description": "Multi-factor authentication is required",
        "check": lambda: auth_service.is_mfa_enforced(),
        "remediation": "Enable MFA requirement in security settings"
    },
    {
        "id": "password_policy",
        "name": "Strong Password Policy",
        "description": "Passwords meet minimum complexity",
        "check": lambda: auth_service.check_password_policy(),
        "remediation": "Update password policy to require 8+ chars, mixed case, numbers"
    },
    {
        "id": "session_timeout",
        "name": "Session Timeout",
        "description": "Inactive sessions expire",
        "check": lambda: auth_service.check_session_timeout(),
        "remediation": "Configure session timeout in settings"
    }
]

async def run_compliance_checks():
    results = []
    for check in COMPLIANCE_CHECKS:
        try:
            passed = await check["check"]()
            results.append({
                "id": check["id"],
                "name": check["name"],
                "status": "pass" if passed else "fail",
                "remediation": None if passed else check["remediation"]
            })
        except Exception as e:
            results.append({
                "id": check["id"],
                "name": check["name"],
                "status": "error",
                "error": str(e)
            })
    return results
```

---

## Files to Create

```
src/
  audit/
    __init__.py
    models.py
    schemas.py
    service.py
    router.py
    middleware.py
    decorators.py
    exporter.py

  compliance/
    __init__.py
    checks.py
    service.py
    router.py

frontend/src/
  app/dashboard/
    admin/
      audit/
        page.tsx
      compliance/
        page.tsx
  components/
    audit/
      AuditLogTable.tsx
      AuditLogDetail.tsx
      AuditFilters.tsx
      AuditExport.tsx
    compliance/
      ComplianceDashboard.tsx
      ComplianceCheck.tsx
```

---

## Related Requirement Groups

- REQ_011: ISO 27001
- REQ_012: SOC 2 Type II
- REQ_286: Compliance achievement

---

## Database Schema

```sql
-- Audit logs table with partitioning for performance
CREATE TABLE audit_logs (
    id UUID DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id UUID,                    -- NULL for system events
    organization_id UUID NOT NULL,

    -- Action details
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),

    -- Context
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),

    -- Changes
    old_value JSONB,
    new_value JSONB,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    error_message TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    PRIMARY KEY (timestamp, id)
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE audit_logs_2025_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- ... create more partitions as needed

-- Indexes on partitioned table
CREATE INDEX idx_audit_user ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_org ON audit_logs(organization_id, timestamp DESC);
CREATE INDEX idx_audit_action ON audit_logs(action, timestamp DESC);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);

-- Security events table for faster alerting queries
CREATE TABLE security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_log_timestamp TIMESTAMP NOT NULL,
    audit_log_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- failed_login, permission_denied, etc.
    user_id UUID,
    ip_address INET,
    severity VARCHAR(20) NOT NULL,    -- low, medium, high, critical
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolved_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_security_events_unresolved ON security_events(severity, created_at)
    WHERE resolved = false;

-- Data retention settings
CREATE TABLE compliance_settings (
    organization_id UUID PRIMARY KEY REFERENCES organizations(id),
    audit_log_retention_days INT DEFAULT 365,
    deleted_data_retention_days INT DEFAULT 30,
    mfa_required BOOLEAN DEFAULT false,
    session_timeout_minutes INT DEFAULT 60,
    password_min_length INT DEFAULT 8,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Guaranteed Audit Delivery

```python
from contextlib import asynccontextmanager

class TransactionalAuditService:
    """Ensure audit logs are written atomically with the action."""

    @asynccontextmanager
    async def audited_operation(
        self,
        action: str,
        resource_type: str,
        user_id: UUID,
        organization_id: UUID
    ):
        """Context manager for audited database operations."""
        async with db.transaction() as txn:
            # Capture start state
            context = {
                "action": action,
                "resource_type": resource_type,
                "user_id": user_id,
                "organization_id": organization_id,
                "old_value": None,
                "new_value": None,
            }

            try:
                yield context  # Let the operation run

                # Log success in same transaction
                await self._write_audit_log(
                    **context,
                    status="success"
                )

            except Exception as e:
                # Log failure in same transaction (will rollback together)
                await self._write_audit_log(
                    **context,
                    status="failure",
                    error_message=str(e)
                )
                raise

    async def _write_audit_log(self, **kwargs):
        """Write audit log entry."""
        request = current_request.get(None)

        log = AuditLog(
            timestamp=datetime.utcnow(),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            **kwargs
        )

        await db.execute(
            "INSERT INTO audit_logs (...) VALUES (...)",
            log.dict()
        )


# Usage example
async def delete_memory_with_audit(memory_id: UUID, user: User):
    audit = TransactionalAuditService()

    async with audit.audited_operation(
        action="delete",
        resource_type="memory",
        user_id=user.id,
        organization_id=user.organization_id
    ) as ctx:
        # Capture old value before delete
        memory = await get_memory(memory_id)
        ctx["old_value"] = memory.dict()
        ctx["resource_id"] = str(memory_id)

        # Perform the delete
        await db.execute("DELETE FROM memories WHERE id = :id", {"id": memory_id})

        # If we get here, both delete and audit log succeed or fail together
```

---

## Security Alert System

```python
from enum import Enum

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityAlertService:
    """Monitor and alert on security events."""

    # Define alert rules
    ALERT_RULES = {
        "auth.login_failed": {
            "threshold": 5,          # 5 failures
            "window_minutes": 15,    # in 15 minutes
            "severity": AlertSeverity.MEDIUM,
        },
        "admin.permission_change": {
            "threshold": 1,
            "window_minutes": 1,
            "severity": AlertSeverity.HIGH,
        },
        "auth.password_change": {
            "threshold": 1,
            "window_minutes": 1,
            "severity": AlertSeverity.LOW,
        },
    }

    async def check_and_alert(self, audit_log: AuditLog):
        """Check if audit log triggers any alerts."""
        rule = self.ALERT_RULES.get(audit_log.action)
        if not rule:
            return

        # Check threshold
        recent_count = await self._count_recent_events(
            audit_log.action,
            audit_log.user_id,
            rule["window_minutes"]
        )

        if recent_count >= rule["threshold"]:
            await self._create_alert(audit_log, rule["severity"])

    async def _create_alert(self, log: AuditLog, severity: AlertSeverity):
        """Create security event and send notifications."""
        # Store in security_events table
        event = SecurityEvent(
            audit_log_timestamp=log.timestamp,
            audit_log_id=log.id,
            event_type=log.action,
            user_id=log.user_id,
            ip_address=log.ip_address,
            severity=severity.value,
        )
        await db.execute("INSERT INTO security_events ...", event.dict())

        # Send notifications based on severity
        if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            # Email admins
            await send_admin_alert_email(event)

            # Slack webhook
            await send_slack_alert(event)

            # WebSocket to admin dashboard
            await websocket_manager.send_to_role(
                role="org_admin",
                organization_id=log.organization_id,
                message={
                    "type": "security_alert",
                    "payload": event.dict()
                }
            )
```

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added partitioned audit_logs table for performance at scale
2. Added `security_events` table for fast security alerting queries
3. Added `compliance_settings` table for per-organization settings
4. Added `TransactionalAuditService` for guaranteed audit delivery (same transaction)
5. Added `SecurityAlertService` with configurable alert rules and thresholds
6. Added multi-channel alert notifications (email, Slack, WebSocket)

**Cross-Sprint Dependencies:**
- Sprint 21: Organization and role context for audit logs
- Sprint 09: WebSocket for real-time security alerts to admin dashboard

**Important Notes:**
- Audit log partitions should be created in advance (monthly recommended)
- Old partitions can be archived/dropped based on retention policy
- Security events with HIGH/CRITICAL severity trigger immediate notifications
- MFA implementation referenced in compliance checks should be added to Sprint 02 or a future sprint
