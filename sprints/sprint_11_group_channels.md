# Sprint 11: Group Channels

**Phase:** 3 - Communication
**Focus:** Multi-user group conversations with role-based permissions
**Dependencies:** Sprint 01 (Database Schema), Sprint 09 (Direct Messaging + WebSocket)

---

## Testable Deliverable

**Human Test:**
1. Create a new group channel "Marketing Team"
2. Invite 2+ other users with different roles (admin, moderator, member)
3. All members can see and send messages
4. Admin can add a new member to existing group
5. Moderator can pin/delete messages
6. Owner can remove a member or change roles
7. Member can leave group
8. Verify WebSocket broadcasts to all group members

**Test Flow:**
```
Owner creates "Project Alpha"
    |
    +-- Invites: Sarah (admin), John (mod), Mike (member)
    |
All members receive WebSocket notification
    |
All members can send/receive messages in real-time
    |
Sarah (admin) adds: Lisa as member
    |
John (mod) pins important message
    |
John leaves group
    |
Owner removes: Mike
    |
Owner promotes Lisa to moderator
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_026 | Team and project group channels | 17 |
| REQ_093 | Collaborative features | 18 |

### Implementation Requirements

- REQ_026.2.1: Create group channels
- REQ_026.2.2: Manage group membership
- REQ_026.2.3: Group message broadcasting
- REQ_026.2.4: Group roles and permissions

---

## Schema Reference

> **Note:** The core database schema is defined in **Sprint 01: Database & Schema Foundation**.
> This sprint extends and utilizes the existing tables.

### Tables from Sprint 01

```sql
-- conversations table includes:
--   id, organization_id, type, name, description, avatar_url, is_private,
--   created_by, created_at, updated_at, last_message_at, deleted_at

-- conversation_participants table includes:
--   conversation_id, user_id, role, joined_at, last_read_at, is_muted
--   PRIMARY KEY (conversation_id, user_id)
```

### Sprint 11 Extensions

```python
# Extended channel roles (beyond Sprint 01's owner/admin/member)
class ChannelRole(Enum):
    OWNER = "owner"      # Can delete channel, transfer ownership
    ADMIN = "admin"      # Can manage members, change settings
    MODERATOR = "mod"    # Can pin/delete messages, mute members
    MEMBER = "member"    # Can read/write messages

# Channel settings model
class ChannelSettings(BaseModel):
    name: str
    description: str | None
    avatar_url: str | None
    is_private: bool = True
    organization_id: UUID | None  # For org-level channels
    allow_member_invite: bool = False
    slow_mode_seconds: int = 0  # Rate limiting for messages
```

---

## Channel Roles & Permissions

### Role Hierarchy

```python
class ChannelRole(Enum):
    OWNER = "owner"      # Highest - full control
    ADMIN = "admin"      # Can manage members and settings
    MODERATOR = "mod"    # Can moderate content
    MEMBER = "member"    # Basic read/write access
```

### Permission Matrix

| Action | Owner | Admin | Moderator | Member |
|--------|-------|-------|-----------|--------|
| Send messages | Y | Y | Y | Y |
| View messages | Y | Y | Y | Y |
| Edit own messages | Y | Y | Y | Y |
| Delete own messages | Y | Y | Y | Y |
| Pin messages | Y | Y | Y | - |
| Delete any message | Y | Y | Y | - |
| Mute members | Y | Y | Y | - |
| Edit channel info | Y | Y | - | - |
| Add members | Y | Y | - | - |
| Remove members | Y | Y | - | - |
| Change member roles | Y | - | - | - |
| Promote to admin | Y | - | - | - |
| Delete channel | Y | - | - | - |
| Transfer ownership | Y | - | - | - |
| Leave channel | Y* | Y | Y | Y |

*Owner must transfer ownership before leaving

### Permission Checking

```python
# Backend permission checking
class ChannelPermissions:
    @staticmethod
    def can_manage_members(role: ChannelRole) -> bool:
        return role in [ChannelRole.OWNER, ChannelRole.ADMIN]

    @staticmethod
    def can_moderate(role: ChannelRole) -> bool:
        return role in [ChannelRole.OWNER, ChannelRole.ADMIN, ChannelRole.MODERATOR]

    @staticmethod
    def can_change_roles(role: ChannelRole) -> bool:
        return role == ChannelRole.OWNER

    @staticmethod
    def can_delete_channel(role: ChannelRole) -> bool:
        return role == ChannelRole.OWNER
```

---

## WebSocket Integration

> **Note:** WebSocket infrastructure is established in **Sprint 09**.
> This sprint leverages that infrastructure for group-specific features.

### Room Management

```python
# WebSocket room naming convention
def get_channel_room(channel_id: UUID) -> str:
    return f"channel:{channel_id}"

# Room management operations
class ChannelRoomManager:
    async def join_channel_room(self, ws: WebSocket, channel_id: UUID, user_id: UUID):
        """Add user to channel's WebSocket room"""
        room = get_channel_room(channel_id)
        await self.connection_manager.add_to_room(ws, room)

    async def leave_channel_room(self, ws: WebSocket, channel_id: UUID):
        """Remove user from channel's WebSocket room"""
        room = get_channel_room(channel_id)
        await self.connection_manager.remove_from_room(ws, room)

    async def broadcast_to_channel(self, channel_id: UUID, event: dict):
        """Broadcast event to all channel members"""
        room = get_channel_room(channel_id)
        await self.connection_manager.broadcast_to_room(room, event)
```

### Channel Events

```python
# WebSocket events for channels
class ChannelEvent(Enum):
    MESSAGE_NEW = "channel.message.new"
    MESSAGE_EDIT = "channel.message.edit"
    MESSAGE_DELETE = "channel.message.delete"
    MESSAGE_PIN = "channel.message.pin"
    MEMBER_JOIN = "channel.member.join"
    MEMBER_LEAVE = "channel.member.leave"
    MEMBER_REMOVE = "channel.member.remove"
    MEMBER_ROLE_CHANGE = "channel.member.role_change"
    CHANNEL_UPDATE = "channel.update"
    CHANNEL_DELETE = "channel.delete"
    TYPING_START = "channel.typing.start"
    TYPING_STOP = "channel.typing.stop"

# Event payload examples
{
    "type": "channel.message.new",
    "channel_id": "uuid",
    "data": {
        "message": {...},
        "sender": {...}
    }
}

{
    "type": "channel.member.join",
    "channel_id": "uuid",
    "data": {
        "user": {...},
        "role": "member",
        "invited_by": {...}
    }
}
```

---

## Channel Discovery

### Public vs Private Channels

```python
class ChannelVisibility:
    """
    Private channels (is_private=True):
    - Only visible to members
    - Require invitation to join
    - Not listed in organization channel directory

    Public channels (is_private=False):
    - Visible in organization channel directory
    - Any org member can join without invitation
    - Listed in search results
    """

class ChannelDiscovery(BaseModel):
    id: UUID
    name: str
    description: str | None
    avatar_url: str | None
    member_count: int
    is_private: bool
    organization_id: UUID | None
```

### Discovery Endpoints

```yaml
# List discoverable channels in organization
GET /api/v1/organizations/{org_id}/channels
  Query: ?search=marketing&page=1
  Response: ChannelDiscovery[]

# Join public channel
POST /api/v1/channels/{id}/join
  Response: { role: "member", joined_at: timestamp }

# Request to join private channel (future enhancement)
POST /api/v1/channels/{id}/request-join
  Request:
    message: string (optional)
  Response: { request_id: uuid, status: "pending" }
```

---

## API Endpoints

### Channel Management

```yaml
# Create Group Channel
POST /api/v1/channels
  Request:
    name: string (required)
    description: string (optional)
    avatar_url: string (optional)
    participant_ids: uuid[] (initial members)
    is_private: bool (default: true)
    organization_id: uuid (optional, for org-level channels)
  Response: Channel

# Get Channel Details
GET /api/v1/channels/{id}
  Response: Channel with member_count

# Update Channel Settings
PATCH /api/v1/channels/{id}
  Request:
    name: string
    description: string
    avatar_url: string
    is_private: bool
  Response: Channel

# Delete Channel (owner only)
DELETE /api/v1/channels/{id}
  Response: 204
```

### Member Management

```yaml
# List Channel Members
GET /api/v1/channels/{id}/members
  Query: ?role=admin&page=1
  Response: [
    {
      user: User,
      role: string,
      joined_at: timestamp
    }
  ]

# Add Members (admin+)
POST /api/v1/channels/{id}/members
  Request:
    user_ids: uuid[]
    role: string (default: "member")
  Response: { added: int, members: Member[] }

# Remove Member (admin+)
DELETE /api/v1/channels/{id}/members/{user_id}
  Response: 204

# Update Member Role (owner only)
PATCH /api/v1/channels/{id}/members/{user_id}/role
  Request:
    role: string (admin | mod | member)
  Response: { role: string, updated_at: timestamp }

# Leave Channel
POST /api/v1/channels/{id}/leave
  Response: 204

# Transfer Ownership (owner only)
POST /api/v1/channels/{id}/transfer-ownership
  Request:
    new_owner_id: uuid
  Response: 204
```

### Message Moderation

```yaml
# Pin Message (moderator+)
POST /api/v1/channels/{id}/messages/{message_id}/pin
  Response: { pinned: true, pinned_at: timestamp, pinned_by: uuid }

# Unpin Message (moderator+)
DELETE /api/v1/channels/{id}/messages/{message_id}/pin
  Response: 204

# Get Pinned Messages
GET /api/v1/channels/{id}/pinned
  Response: Message[]

# Delete Message (moderator+ for any, member for own)
DELETE /api/v1/channels/{id}/messages/{message_id}
  Response: 204
```

---

## Tasks

### Backend - Channel Management
- [ ] Create channel service extending conversation service
- [ ] Implement create channel endpoint with initial members
- [ ] Implement update channel settings endpoint
- [ ] Implement delete channel (with ownership check)
- [ ] Add organization_id support for org-level channels

### Backend - Membership
- [ ] Implement add members endpoint (bulk invite)
- [ ] Implement remove member endpoint
- [ ] Implement leave channel (with ownership transfer check)
- [ ] Implement role management endpoints
- [ ] Implement ownership transfer logic

### Backend - Permissions
- [ ] Create ChannelPermissions service
- [ ] Add role-based middleware/decorators
- [ ] Check permissions on all member operations
- [ ] Check permissions on channel modifications
- [ ] Prevent owner from leaving without transfer

### Backend - WebSocket Integration
- [ ] Integrate with Sprint 09 WebSocket infrastructure
- [ ] Implement channel room management
- [ ] Broadcast member join/leave events
- [ ] Broadcast role change events
- [ ] Broadcast channel update/delete events
- [ ] Implement typing indicators for groups

### Backend - Channel Discovery
- [ ] Implement organization channel listing
- [ ] Add public channel join endpoint
- [ ] Add channel search functionality
- [ ] Filter private channels from discovery

### Backend - Message Moderation
- [ ] Implement pin/unpin message endpoints
- [ ] Add pinned messages query
- [ ] Implement message deletion with role check

### Frontend - Channel UI
- [ ] Create channel button/modal
- [ ] Channel settings page
- [ ] Member list with roles and badges
- [ ] Add/remove member interface
- [ ] Role management dropdown

### Frontend - Chat Enhancements
- [ ] Show channel name and avatar in header
- [ ] Show member count with member list sidebar
- [ ] Display role badges on messages
- [ ] Show pinned messages bar
- [ ] Channel info/settings sidebar

### Frontend - WebSocket Integration
- [ ] Subscribe to channel room on open
- [ ] Handle member join/leave events
- [ ] Update member list in real-time
- [ ] Show typing indicators for multiple users

### Frontend - Channel Discovery
- [ ] Organization channel browser
- [ ] Public channel search
- [ ] Join channel button for public channels

---

## Acceptance Criteria

1. Can create channel with name and initial members
2. Can update channel name/description/avatar
3. All members receive messages via WebSocket in real-time
4. Admin can add/remove members
5. Moderator can pin/delete messages
6. Owner can change member roles
7. Members can leave channel
8. Owner can transfer ownership
9. Channel appears in conversation list
10. Shows member count in UI
11. Role badges display correctly
12. Public channels discoverable in organization
13. WebSocket events broadcast to all channel members

---

## UI Components

### Create Channel Modal
```typescript
<CreateChannelModal>
  <Input label="Channel Name" required />
  <Textarea label="Description" />
  <ImageUpload label="Channel Avatar" />
  <UserMultiSelect
    label="Add Members"
    selected={selectedUsers}
    onChange={setSelectedUsers}
  />
  <Select
    label="Organization"
    options={userOrganizations}
    optional
  />
  <Checkbox label="Private Channel" defaultChecked />
  <Button>Create Channel</Button>
</CreateChannelModal>
```

### Channel Header
```typescript
<ChannelHeader channel={channel}>
  <ChannelAvatar src={channel.avatar_url} />
  <ChannelName>{channel.name}</ChannelName>
  <MemberCount onClick={openMemberList}>
    {members.length} members
  </MemberCount>
  <PinnedMessagesButton count={pinnedCount} />
  <SettingsButton onClick={openSettings} />
</ChannelHeader>
```

### Member Management
```typescript
<MemberList>
  {members.map(member => (
    <MemberItem
      user={member.user}
      role={member.role}
      isCurrentUser={member.user.id === currentUser.id}
      canManage={currentUserRole in ['owner', 'admin']}
      canChangeRole={currentUserRole === 'owner'}
      onRoleChange={handleRoleChange}
      onRemove={handleRemove}
    >
      <RoleBadge role={member.role} />
      {canChangeRole && (
        <RoleDropdown
          currentRole={member.role}
          onChange={(role) => handleRoleChange(member.user.id, role)}
        />
      )}
    </MemberItem>
  ))}
  {canAddMembers && <AddMemberButton onClick={openAddModal} />}
</MemberList>
```

### Role Badge Component
```typescript
const RoleBadge = ({ role }: { role: ChannelRole }) => {
  const colors = {
    owner: 'gold',
    admin: 'purple',
    mod: 'blue',
    member: 'gray'
  };

  const labels = {
    owner: 'Owner',
    admin: 'Admin',
    mod: 'Mod',
    member: null  // Don't show badge for regular members
  };

  if (!labels[role]) return null;

  return <Badge color={colors[role]}>{labels[role]}</Badge>;
};
```

---

## Files to Create

```
# Backend additions
src/
  channels/
    __init__.py
    models.py           # Channel-specific models
    schemas.py          # Request/response schemas
    service.py          # Channel business logic
    router.py           # API endpoints
    permissions.py      # Permission checking utilities
    membership.py       # Membership operations
    discovery.py        # Channel discovery service
    websocket.py        # WebSocket room management

# Frontend additions
frontend/src/
  components/
    channels/
      CreateChannelModal.tsx
      ChannelHeader.tsx
      ChannelSettings.tsx
      MemberList.tsx
      MemberItem.tsx
      AddMemberModal.tsx
      RoleBadge.tsx
      RoleDropdown.tsx
      ChannelDiscovery.tsx
      PinnedMessages.tsx

  hooks/
    useChannelWebSocket.ts
    useChannelMembers.ts
    useChannelPermissions.ts

  app/dashboard/
    channels/
      page.tsx              # Channel list/discovery
      [channelId]/
        page.tsx            # Channel chat view
        settings/
          page.tsx          # Channel settings
```

---

## Related Sprints

- **Sprint 01:** Database schema (conversations, conversation_participants)
- **Sprint 09:** Direct messaging foundation, WebSocket infrastructure
- **Sprint 12:** (If applicable) Additional real-time enhancements

---

## Related Requirement Groups

- Group 026: Team permissions
- Group 093: Collaboration features
- Authentication domain (for permissions)
- Organization domain (for org-level channels)
