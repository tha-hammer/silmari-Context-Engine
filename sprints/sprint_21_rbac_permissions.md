# Sprint 21: RBAC & Permissions

**Phase:** 6 - Enterprise & Compliance
**Focus:** Role-based access control
**Dependencies:** Sprint 02 (Auth), Sprint 11 (Groups)

---

## Testable Deliverable

**Human Test:**
1. Admin creates new role "Manager"
2. Admin assigns permissions to role
3. Admin assigns role to user
4. User can only access permitted features
5. Attempting unauthorized action shows error
6. Permission changes take effect immediately

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_250 | Role-based access control enforcement | 18 |
| REQ_011 | ISO 27001-2022 compliance | 17 |
| REQ_128 | Enterprise admin custom integrations | 18 |

### Implementation Requirements
- REQ_011.2.3: Access controls (least privilege)
- REQ_128.2.1: Enterprise admin permissions
- REQ_250.2.1: Role definition
- REQ_250.2.2: Permission assignment

---

## Data Model

```python
class Role(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    is_system: bool           # Built-in vs custom
    permissions: List[str]    # Permission codes
    created_at: datetime
    updated_at: datetime

class Permission(BaseModel):
    code: str                 # e.g., "memories:write"
    name: str
    description: str
    category: str             # UI grouping
    resource: str             # memories, conversations, etc.
    action: str               # read, write, delete, admin

class UserRole(BaseModel):
    user_id: UUID
    role_id: UUID
    organization_id: UUID
    granted_by: UUID
    granted_at: datetime
    expires_at: datetime | None

# System Roles
SYSTEM_ROLES = {
    "super_admin": ["*"],  # All permissions
    "org_admin": [
        "users:*", "roles:*", "integrations:*",
        "audit:read", "settings:*"
    ],
    "member": [
        "memories:read", "memories:write",
        "conversations:*", "tasks:*"
    ],
    "viewer": [
        "memories:read", "conversations:read"
    ]
}
```

---

## Permission Structure

```python
PERMISSIONS = {
    # Memories
    "memories:read": "View memories",
    "memories:write": "Create and edit memories",
    "memories:delete": "Delete memories",
    "memories:admin": "Manage all user memories",

    # Conversations
    "conversations:read": "View conversations",
    "conversations:write": "Send messages",
    "conversations:create": "Create conversations",
    "conversations:admin": "Manage all conversations",

    # Tasks
    "tasks:read": "View tasks",
    "tasks:write": "Create and edit tasks",
    "tasks:delete": "Delete tasks",

    # Users
    "users:read": "View user list",
    "users:invite": "Invite users",
    "users:manage": "Edit user roles",
    "users:delete": "Remove users",

    # Integrations
    "integrations:read": "View integrations",
    "integrations:connect": "Connect integrations",
    "integrations:admin": "Manage org integrations",

    # Admin
    "roles:read": "View roles",
    "roles:manage": "Create and edit roles",
    "audit:read": "View audit logs",
    "settings:read": "View settings",
    "settings:write": "Change settings",
}
```

---

## API Endpoints

```yaml
# Roles
GET /api/v1/roles
POST /api/v1/roles
GET /api/v1/roles/{id}
PATCH /api/v1/roles/{id}
DELETE /api/v1/roles/{id}

# Role Permissions
GET /api/v1/roles/{id}/permissions
PUT /api/v1/roles/{id}/permissions
  Request: { permissions: string[] }

# User Roles
GET /api/v1/users/{id}/roles
POST /api/v1/users/{id}/roles
  Request: { role_id: uuid }
DELETE /api/v1/users/{id}/roles/{role_id}

# Permission Check
POST /api/v1/permissions/check
  Request: { permission: string, resource_id?: uuid }
  Response: { allowed: bool }

# Available Permissions
GET /api/v1/permissions
  Response: Permission[]
```

---

## Tasks

### Backend - Role System
- [ ] Create Role model
- [ ] Implement CRUD operations
- [ ] System role seeding
- [ ] Permission validation

### Backend - User Roles
- [ ] User-role assignment
- [ ] Multiple roles per user
- [ ] Role inheritance (optional)
- [ ] Permission aggregation

### Backend - Permission Checking
- [ ] Permission check middleware
- [ ] Resource-level permissions
- [ ] Permission caching
- [ ] Permission decorators

### Frontend - Admin UI
- [ ] Role management page
- [ ] Permission editor
- [ ] User role assignment
- [ ] Permission matrix view

### Security
- [ ] Audit role changes
- [ ] Prevent privilege escalation
- [ ] Admin lockout protection

---

## Acceptance Criteria

1. Admin can create custom roles
2. Roles have assigned permissions
3. Users can have multiple roles
4. Permissions aggregate correctly
5. Unauthorized actions blocked
6. Permission changes immediate
7. Audit log tracks changes

---

## Permission Middleware

```python
from functools import wraps
from fastapi import Depends, HTTPException

class PermissionChecker:
    def __init__(self):
        self.cache = {}  # User permission cache

    async def get_user_permissions(self, user_id: UUID) -> Set[str]:
        """Get aggregated permissions for user."""
        if user_id in self.cache:
            return self.cache[user_id]

        roles = await get_user_roles(user_id)
        permissions = set()

        for role in roles:
            for perm in role.permissions:
                if perm == "*":
                    permissions.add("*")
                else:
                    permissions.add(perm)

        self.cache[user_id] = permissions
        return permissions

    async def has_permission(
        self,
        user_id: UUID,
        permission: str
    ) -> bool:
        """Check if user has specific permission."""
        perms = await self.get_user_permissions(user_id)

        if "*" in perms:
            return True

        # Check exact match
        if permission in perms:
            return True

        # Check wildcard (e.g., memories:* matches memories:read)
        resource = permission.split(":")[0]
        if f"{resource}:*" in perms:
            return True

        return False

def require_permission(permission: str):
    """Decorator for permission-protected endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            checker = PermissionChecker()
            if not await checker.has_permission(current_user.id, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@router.delete("/memories/{id}")
@require_permission("memories:delete")
async def delete_memory(id: UUID, current_user: User):
    ...
```

---

## UI Components

```typescript
// Permission Matrix
<PermissionMatrix role={role}>
  {Object.entries(groupedPermissions).map(([category, perms]) => (
    <PermissionGroup key={category} name={category}>
      {perms.map(perm => (
        <PermissionToggle
          key={perm.code}
          permission={perm}
          enabled={role.permissions.includes(perm.code)}
          onChange={(enabled) => togglePermission(perm.code, enabled)}
        />
      ))}
    </PermissionGroup>
  ))}
</PermissionMatrix>

// Role Assignment
<UserRoleAssignment user={user}>
  <RoleMultiSelect
    available={roles}
    selected={user.roles}
    onChange={updateUserRoles}
  />
</UserRoleAssignment>
```

---

## Files to Create

```
src/
  rbac/
    __init__.py
    models.py
    schemas.py
    service.py
    router.py
    middleware.py
    permissions.py
    decorators.py

frontend/src/
  app/dashboard/
    admin/
      roles/
        page.tsx
        [id]/
          page.tsx
      users/
        [id]/
          roles/
            page.tsx
  components/
    rbac/
      RoleList.tsx
      RoleEditor.tsx
      PermissionMatrix.tsx
      UserRoleAssignment.tsx
```

---

## Related Requirement Groups

- REQ_250: RBAC enforcement
- REQ_011: ISO 27001
- Authentication domain

---

## Database Schema

```sql
-- Organizations table (multi-tenancy foundation)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    owner_id UUID NOT NULL REFERENCES users(id),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_orgs_slug ON organizations(slug);
CREATE INDEX idx_orgs_owner ON organizations(owner_id);

-- Organization memberships
CREATE TABLE organization_members (
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (organization_id, user_id)
);

CREATE INDEX idx_org_members_user ON organization_members(user_id);

-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT false,
    permissions TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(organization_id, name)
);

CREATE INDEX idx_roles_org ON roles(organization_id);

-- User roles assignment
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    PRIMARY KEY (user_id, role_id, organization_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_org ON user_roles(organization_id);

-- System roles seed data
INSERT INTO roles (id, organization_id, name, is_system, permissions) VALUES
    -- These will be copied per organization
    ('00000000-0000-0000-0000-000000000001', NULL, 'super_admin', true, ARRAY['*']),
    ('00000000-0000-0000-0000-000000000002', NULL, 'org_admin', true, ARRAY['users:*', 'roles:*', 'integrations:*', 'audit:read', 'settings:*']),
    ('00000000-0000-0000-0000-000000000003', NULL, 'member', true, ARRAY['memories:read', 'memories:write', 'conversations:*', 'tasks:*']),
    ('00000000-0000-0000-0000-000000000004', NULL, 'viewer', true, ARRAY['memories:read', 'conversations:read']);
```

---

## Cache Invalidation with Redis

```python
import redis
from typing import Set

redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

class PermissionChecker:
    CACHE_TTL = 300  # 5 minutes

    async def get_user_permissions(self, user_id: UUID) -> Set[str]:
        """Get aggregated permissions for user with Redis caching."""
        cache_key = f"user_perms:{user_id}"

        # Check cache first
        cached = redis_client.get(cache_key)
        if cached:
            return set(json.loads(cached))

        # Compute permissions
        roles = await get_user_roles(user_id)
        permissions = set()

        for role in roles:
            for perm in role.permissions:
                if perm == "*":
                    permissions.add("*")
                else:
                    permissions.add(perm)

        # Cache the result
        redis_client.setex(
            cache_key,
            self.CACHE_TTL,
            json.dumps(list(permissions))
        )

        return permissions

    @staticmethod
    async def invalidate_user_permissions(user_id: UUID):
        """Invalidate cache when permissions change."""
        cache_key = f"user_perms:{user_id}"
        redis_client.delete(cache_key)

    @staticmethod
    async def invalidate_role_permissions(role_id: UUID):
        """Invalidate cache for all users with this role."""
        # Get all users with this role
        user_ids = await get_users_with_role(role_id)
        for user_id in user_ids:
            cache_key = f"user_perms:{user_id}"
            redis_client.delete(cache_key)


# Hook into role/permission changes
async def on_role_updated(role_id: UUID):
    """Called when a role's permissions are modified."""
    await PermissionChecker.invalidate_role_permissions(role_id)

async def on_user_role_changed(user_id: UUID):
    """Called when a user's role assignment changes."""
    await PermissionChecker.invalidate_user_permissions(user_id)
```

---

## Resource-Level Permission Check

```python
async def has_permission_for_resource(
    user_id: UUID,
    permission: str,
    resource_type: str,
    resource_id: UUID
) -> bool:
    """Check if user has permission for a specific resource."""
    checker = PermissionChecker()

    # First check if user has the base permission
    if not await checker.has_permission(user_id, permission):
        return False

    # Then check resource ownership/access
    if resource_type == "memory":
        memory = await get_memory(resource_id)
        # User owns the memory
        if memory.user_id == user_id:
            return True
        # Or user has admin permission
        if await checker.has_permission(user_id, "memories:admin"):
            return True
        return False

    elif resource_type == "conversation":
        # User is participant in conversation
        if await is_conversation_participant(resource_id, user_id):
            return True
        if await checker.has_permission(user_id, "conversations:admin"):
            return True
        return False

    # Default to base permission check
    return True


# Usage in endpoint
@router.delete("/memories/{id}")
@require_permission("memories:delete")
async def delete_memory(id: UUID, current_user: User):
    # Additional resource-level check
    if not await has_permission_for_resource(
        current_user.id, "memories:delete", "memory", id
    ):
        raise HTTPException(403, "Cannot delete this memory")

    await memory_service.delete(id)
```

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added `organizations` table for multi-tenancy foundation
2. Added `organization_members` table for user-organization relationships
3. Added complete SQL database schema for roles and user_roles
4. Added Redis-based cache with proper invalidation on role/permission changes
5. Added `has_permission_for_resource()` for resource-level permission checks
6. Added system roles seed data

**Cross-Sprint Dependencies:**
- Sprint 02: User authentication base
- Sprint 22: Audit logging for role changes

**Important Notes:**
- All data queries should include `organization_id` filter for tenant isolation
- Cache invalidation must be called whenever roles or permissions change
- System roles are templates that get copied when new organizations are created
