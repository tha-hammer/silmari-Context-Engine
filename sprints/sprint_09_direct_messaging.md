# Sprint 09: Direct Messaging with Real-Time WebSocket Infrastructure

**Phase:** 3 - Communication
**Focus:** User-to-user messaging with WebSocket-based real-time updates
**Dependencies:** Sprint 01 (Database Schema), Sprint 02 (Auth), Sprint 03 (API/Redis), Sprint 04 (UI)

---

## Testable Deliverable

**Human Test:**
1. User A logs in and starts a conversation with User B
2. User A sends a message
3. User B sees the message appear **instantly** (no refresh needed)
4. User B starts typing - User A sees "typing..." indicator
5. User B replies
6. Both users see the conversation history with delivery receipts
7. User A goes offline - User B sees presence update
8. Messages persist after logout/login

**Test Flow:**
```
User A                          User B
  |                               |
  |-- WebSocket connect --------->|<-- WebSocket connect
  |                               |
  |-- Start conversation -------->|
  |-- Send "Hello!" ------------->|
  |                               |-- [Real-time] See message instantly
  |                               |-- See "delivered" status
  |                               |-- Start typing...
  |<-- [Real-time] See "typing..."|
  |                               |-- Send "Hi back!"
  |<-- [Real-time] See reply -----|
  |-- Mark as read -------------->|
  |                               |-- See "read" status
  |                               |
  |-- [Disconnect] ---------------|
  |                               |-- See "offline" status
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_029 | Text message communication | 18 |
| REQ_026 | Team and project group channels | 17 |
| REQ_010 | End-to-end encryption | 17 |

### Implementation Requirements

- REQ_029.2.1: Send text messages between users
- REQ_029.2.2: Display message history
- REQ_029.2.3: Message delivery status
- REQ_010.2.2: Generate encryption key per chat
- REQ_010.2.4: Encrypt messages
- REQ_010.2.5: Decrypt messages

---

## Database Schema

> **Reference:** All messaging tables are defined in **Sprint 01 (Database Schema)**:
> - `conversations` - Conversation metadata (type, created_by, last_message_at)
> - `conversation_participants` - User membership with last_read_at tracking
> - `messages` - Message content with status (sent/delivered/read)

### Additional Tables for Real-Time Features

```sql
-- User presence tracking (ephemeral, Redis-backed, with DB fallback)
CREATE TABLE user_presence (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'offline',  -- online, away, offline
    last_seen_at TIMESTAMP DEFAULT NOW(),
    current_conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL
);

CREATE INDEX idx_presence_status ON user_presence(status) WHERE status = 'online';

-- Typing indicators stored temporarily for reconnection scenarios
-- Primary storage is Redis with 5-second TTL
```

---

## WebSocket Infrastructure

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        WebSocket Flow                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Browser A          FastAPI Server           Browser B          │
│     │                    │                      │               │
│     │──WS Connect───────>│<─────WS Connect──────│               │
│     │   (JWT Auth)       │     (JWT Auth)       │               │
│     │                    │                      │               │
│     │                ┌───┴───┐                  │               │
│     │                │ Redis │                  │               │
│     │                │Pub/Sub│                  │               │
│     │                └───┬───┘                  │               │
│     │                    │                      │               │
│     │──Send Message─────>│                      │               │
│     │                    │──Publish to Room────>│               │
│     │                    │                      │──Receive──────│
│     │                    │                      │               │
└─────────────────────────────────────────────────────────────────┘
```

### WebSocket Server Setup (FastAPI)

```python
# websocket/manager.py
from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from typing import Dict, List, Set
from dataclasses import dataclass
from datetime import datetime
import json
import asyncio

@dataclass
class WebSocketConnection:
    websocket: WebSocket
    user_id: str
    connected_at: datetime

class ConnectionManager:
    """
    Manages WebSocket connections with Redis pub/sub for horizontal scaling.
    Each conversation is a "room" that users subscribe to.
    """

    def __init__(self):
        # Local connections per server instance
        self.active_connections: Dict[str, List[WebSocketConnection]] = {}
        # Track which conversations each user is in
        self.user_conversations: Dict[str, Set[str]] = {}
        # Redis for cross-server communication
        self.redis: Redis = None
        self.pubsub = None

    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis connection for pub/sub."""
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        # Start background task to listen for Redis messages
        asyncio.create_task(self._listen_redis())

    async def connect(
        self,
        websocket: WebSocket,
        conversation_id: str,
        user_id: str
    ) -> None:
        """
        Accept WebSocket connection and subscribe to conversation room.
        """
        await websocket.accept()

        connection = WebSocketConnection(
            websocket=websocket,
            user_id=user_id,
            connected_at=datetime.utcnow()
        )

        # Add to local connections
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
            # Subscribe to Redis channel for this conversation
            await self.pubsub.subscribe(f"chat:{conversation_id}")

        self.active_connections[conversation_id].append(connection)

        # Track user's conversations
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = set()
        self.user_conversations[user_id].add(conversation_id)

        # Update presence
        await self._set_presence(user_id, "online", conversation_id)

        # Notify others in the conversation
        await self.broadcast(conversation_id, {
            "type": "presence",
            "user_id": user_id,
            "status": "online"
        }, exclude_user=user_id)

    def disconnect(self, websocket: WebSocket, conversation_id: str, user_id: str) -> None:
        """Remove connection and update presence."""
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id] = [
                conn for conn in self.active_connections[conversation_id]
                if conn.websocket != websocket
            ]

            # Cleanup empty rooms
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

        # Update user conversations tracking
        if user_id in self.user_conversations:
            self.user_conversations[user_id].discard(conversation_id)

        # Schedule presence update (delayed to handle reconnects)
        asyncio.create_task(self._delayed_offline_check(user_id))

    async def _delayed_offline_check(self, user_id: str, delay: float = 5.0):
        """Check if user is still offline after delay (handles reconnects)."""
        await asyncio.sleep(delay)

        # If user has no active conversations, mark offline
        if not self.user_conversations.get(user_id):
            await self._set_presence(user_id, "offline", None)
            # Notify all conversations user was in
            for conv_id in list(self.user_conversations.get(user_id, [])):
                await self.broadcast(conv_id, {
                    "type": "presence",
                    "user_id": user_id,
                    "status": "offline"
                })

    async def broadcast(
        self,
        conversation_id: str,
        message: dict,
        exclude_user: str = None
    ) -> None:
        """
        Broadcast message to all users in a conversation.
        Uses Redis pub/sub for cross-server broadcasting.
        """
        payload = {
            "conversation_id": conversation_id,
            "message": message,
            "exclude_user": exclude_user
        }

        # Publish to Redis for all server instances
        await self.redis.publish(
            f"chat:{conversation_id}",
            json.dumps(payload)
        )

    async def _listen_redis(self):
        """Background task to receive Redis pub/sub messages."""
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await self._deliver_locally(
                        data["conversation_id"],
                        data["message"],
                        data.get("exclude_user")
                    )
                except (json.JSONDecodeError, KeyError):
                    continue

    async def _deliver_locally(
        self,
        conversation_id: str,
        message: dict,
        exclude_user: str = None
    ):
        """Deliver message to local WebSocket connections."""
        connections = self.active_connections.get(conversation_id, [])

        for connection in connections:
            if exclude_user and connection.user_id == exclude_user:
                continue
            try:
                await connection.websocket.send_json(message)
            except Exception:
                # Connection likely closed, will be cleaned up
                pass

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to a specific user across all their conversations."""
        conversation_ids = self.user_conversations.get(user_id, set())

        for conv_id in conversation_ids:
            connections = self.active_connections.get(conv_id, [])
            for conn in connections:
                if conn.user_id == user_id:
                    try:
                        await conn.websocket.send_json(message)
                    except Exception:
                        pass

    async def _set_presence(
        self,
        user_id: str,
        status: str,
        conversation_id: str = None
    ):
        """Update user presence in Redis with 60-second TTL."""
        presence_key = f"presence:{user_id}"
        presence_data = {
            "status": status,
            "last_seen": datetime.utcnow().isoformat(),
            "current_conversation": conversation_id
        }
        await self.redis.setex(presence_key, 60, json.dumps(presence_data))

    async def get_presence(self, user_id: str) -> dict:
        """Get user's current presence status."""
        presence_key = f"presence:{user_id}"
        data = await self.redis.get(presence_key)
        if data:
            return json.loads(data)
        return {"status": "offline", "last_seen": None}


# Global connection manager instance
manager = ConnectionManager()
```

### WebSocket Endpoint

```python
# api/v1/endpoints/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState
from websocket.manager import manager
from api.dependencies import get_current_user_ws
from services.message_service import MessageService
from services.conversation_service import ConversationService

router = APIRouter()

@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: str,
    token: str = Query(...),  # JWT token passed as query param
):
    """
    WebSocket endpoint for real-time chat.

    Message Types (client -> server):
    - message: Send a new message
    - typing: Indicate typing status
    - read: Mark messages as read
    - ping: Keep connection alive

    Message Types (server -> client):
    - message: New message received
    - typing: User typing indicator
    - read_receipt: Message read confirmation
    - presence: User online/offline status
    - delivered: Message delivery confirmation
    - error: Error notification
    """
    # Authenticate user from token
    try:
        user = await get_current_user_ws(token)
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Verify user is participant in conversation
    conversation_service = ConversationService()
    if not await conversation_service.is_participant(conversation_id, user.id):
        await websocket.close(code=4003, reason="Not a participant")
        return

    # Connect to the conversation room
    await manager.connect(websocket, conversation_id, str(user.id))

    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(websocket, conversation_id, user.id, data)

    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id, str(user.id))
    except Exception as e:
        manager.disconnect(websocket, conversation_id, str(user.id))
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=4000, reason=str(e))


async def handle_message(
    websocket: WebSocket,
    conversation_id: str,
    user_id: str,
    data: dict
):
    """Route incoming WebSocket messages to appropriate handlers."""
    message_type = data.get("type")

    if message_type == "message":
        await handle_new_message(websocket, conversation_id, user_id, data)

    elif message_type == "typing":
        await handle_typing(conversation_id, user_id, data)

    elif message_type == "read":
        await handle_read_receipt(conversation_id, user_id, data)

    elif message_type == "ping":
        await websocket.send_json({"type": "pong"})

    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        })


async def handle_new_message(
    websocket: WebSocket,
    conversation_id: str,
    user_id: str,
    data: dict
):
    """Handle new message from user."""
    message_service = MessageService()

    # Create message in database
    message = await message_service.create_message(
        conversation_id=conversation_id,
        sender_id=user_id,
        content=data.get("content", ""),
        content_type=data.get("content_type", "text")
    )

    # Send confirmation to sender
    await websocket.send_json({
        "type": "message_sent",
        "message_id": str(message.id),
        "temp_id": data.get("temp_id"),  # Client-side temp ID for optimistic updates
        "created_at": message.created_at.isoformat()
    })

    # Broadcast to other participants
    await manager.broadcast(conversation_id, {
        "type": "message",
        "message": {
            "id": str(message.id),
            "conversation_id": conversation_id,
            "sender_id": user_id,
            "content": message.content,
            "content_type": message.content_type,
            "created_at": message.created_at.isoformat(),
            "status": "delivered"
        }
    }, exclude_user=user_id)

    # Update message status to delivered for online recipients
    await message_service.update_status(message.id, "delivered")


async def handle_typing(conversation_id: str, user_id: str, data: dict):
    """Handle typing indicator."""
    is_typing = data.get("is_typing", False)

    # Store in Redis with 5-second TTL
    redis = manager.redis
    typing_key = f"typing:{conversation_id}:{user_id}"

    if is_typing:
        await redis.setex(typing_key, 5, "1")
    else:
        await redis.delete(typing_key)

    # Broadcast to other participants
    await manager.broadcast(conversation_id, {
        "type": "typing",
        "user_id": user_id,
        "is_typing": is_typing
    }, exclude_user=user_id)


async def handle_read_receipt(conversation_id: str, user_id: str, data: dict):
    """Handle read receipt from user."""
    message_id = data.get("message_id")

    if not message_id:
        return

    message_service = MessageService()
    conversation_service = ConversationService()

    # Update last_read_at for participant
    await conversation_service.update_last_read(conversation_id, user_id, message_id)

    # Get message to notify sender
    message = await message_service.get_message(message_id)
    if message and message.sender_id != user_id:
        # Update message status
        await message_service.update_status(message_id, "read")

        # Notify sender
        await manager.broadcast(conversation_id, {
            "type": "read_receipt",
            "message_id": message_id,
            "read_by": user_id,
            "read_at": datetime.utcnow().isoformat()
        })
```

---

## Presence System

### Backend Presence Service

```python
# services/presence_service.py
from redis.asyncio import Redis
from datetime import datetime
from typing import List, Dict
import json

class PresenceService:
    """
    Manages user online/offline status with Redis.
    Uses heartbeat mechanism for accurate presence detection.
    """

    def __init__(self, redis: Redis):
        self.redis = redis
        self.presence_ttl = 60  # Seconds before considered offline
        self.heartbeat_interval = 30  # Seconds between heartbeats

    async def set_online(self, user_id: str, conversation_id: str = None):
        """Mark user as online."""
        presence_data = {
            "status": "online",
            "last_heartbeat": datetime.utcnow().isoformat(),
            "current_conversation": conversation_id
        }
        await self.redis.setex(
            f"presence:{user_id}",
            self.presence_ttl,
            json.dumps(presence_data)
        )

        # Add to online users set
        await self.redis.sadd("online_users", user_id)

    async def set_offline(self, user_id: str):
        """Mark user as offline."""
        await self.redis.delete(f"presence:{user_id}")
        await self.redis.srem("online_users", user_id)

    async def heartbeat(self, user_id: str):
        """Refresh user's presence TTL."""
        presence_data = await self.get_presence(user_id)
        if presence_data:
            presence_data["last_heartbeat"] = datetime.utcnow().isoformat()
            await self.redis.setex(
                f"presence:{user_id}",
                self.presence_ttl,
                json.dumps(presence_data)
            )

    async def get_presence(self, user_id: str) -> dict | None:
        """Get user's current presence status."""
        data = await self.redis.get(f"presence:{user_id}")
        if data:
            return json.loads(data)
        return None

    async def get_bulk_presence(self, user_ids: List[str]) -> Dict[str, dict]:
        """Get presence for multiple users efficiently."""
        if not user_ids:
            return {}

        pipeline = self.redis.pipeline()
        for user_id in user_ids:
            pipeline.get(f"presence:{user_id}")

        results = await pipeline.execute()

        presence_map = {}
        for user_id, data in zip(user_ids, results):
            if data:
                presence_map[user_id] = json.loads(data)
            else:
                presence_map[user_id] = {"status": "offline", "last_heartbeat": None}

        return presence_map

    async def get_online_users_in_conversation(
        self,
        conversation_id: str,
        participant_ids: List[str]
    ) -> List[str]:
        """Get list of online users in a conversation."""
        presence_map = await self.get_bulk_presence(participant_ids)
        return [
            user_id for user_id, presence in presence_map.items()
            if presence.get("status") == "online"
        ]
```

### Presence API Endpoint

```python
# api/v1/endpoints/presence.py
from fastapi import APIRouter, Depends
from services.presence_service import PresenceService
from api.dependencies import get_current_user, get_presence_service

router = APIRouter()

@router.get("/conversations/{conversation_id}/presence")
async def get_conversation_presence(
    conversation_id: str,
    current_user = Depends(get_current_user),
    presence_service: PresenceService = Depends(get_presence_service),
    conversation_service = Depends(get_conversation_service)
):
    """Get online status of all participants in a conversation."""
    # Verify user is participant
    if not await conversation_service.is_participant(conversation_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not a participant")

    # Get participants
    participants = await conversation_service.get_participants(conversation_id)
    participant_ids = [str(p.user_id) for p in participants]

    # Get presence for all participants
    presence_map = await presence_service.get_bulk_presence(participant_ids)

    return {
        "conversation_id": conversation_id,
        "participants": [
            {
                "user_id": user_id,
                "status": presence.get("status", "offline"),
                "last_seen": presence.get("last_heartbeat")
            }
            for user_id, presence in presence_map.items()
        ]
    }
```

---

## Typing Indicators

### Typing Indicator Service

```python
# services/typing_service.py
from redis.asyncio import Redis
from typing import List

class TypingService:
    """Manages typing indicators with Redis."""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.typing_ttl = 5  # Typing indicator expires after 5 seconds

    async def set_typing(self, conversation_id: str, user_id: str, is_typing: bool):
        """Set/clear typing indicator for a user."""
        key = f"typing:{conversation_id}:{user_id}"

        if is_typing:
            await self.redis.setex(key, self.typing_ttl, "1")
        else:
            await self.redis.delete(key)

    async def get_typing_users(self, conversation_id: str) -> List[str]:
        """Get list of users currently typing in a conversation."""
        pattern = f"typing:{conversation_id}:*"
        keys = await self.redis.keys(pattern)

        typing_users = []
        for key in keys:
            # Extract user_id from key
            user_id = key.split(":")[-1]
            typing_users.append(user_id)

        return typing_users
```

---

## Message Delivery Receipts

### Message Status Flow

```
1. User A sends message
   └── Status: "sent" (stored in DB)

2. Message broadcasted via WebSocket
   └── If User B online and receives:
       └── Status: "delivered" (updated in DB, notification sent)

3. User B views conversation
   └── Client sends "read" acknowledgment
   └── Status: "read" (updated in DB, notification sent)
```

### Message Service with Receipts

```python
# services/message_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import UUID

class MessageService:
    """Handles message CRUD and delivery status."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
        self,
        conversation_id: str,
        sender_id: str,
        content: str,
        content_type: str = "text"
    ) -> Message:
        """Create a new message with 'sent' status."""
        message = Message(
            conversation_id=UUID(conversation_id),
            sender_id=UUID(sender_id),
            content=content,
            content_type=content_type,
            status="sent",
            created_at=datetime.utcnow()
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        # Update conversation's last_message_at
        await self._update_conversation_timestamp(conversation_id)

        return message

    async def update_status(self, message_id: str, status: str):
        """Update message delivery status."""
        await self.db.execute(
            update(Message)
            .where(Message.id == UUID(message_id))
            .values(status=status)
        )
        await self.db.commit()

    async def mark_conversation_read(
        self,
        conversation_id: str,
        user_id: str,
        up_to_message_id: str = None
    ) -> List[str]:
        """
        Mark messages as read for a user.
        Returns list of message IDs that were marked as read.
        """
        # Get unread messages sent by others
        query = (
            select(Message)
            .where(
                Message.conversation_id == UUID(conversation_id),
                Message.sender_id != UUID(user_id),
                Message.status != "read"
            )
        )

        if up_to_message_id:
            # Get the timestamp of the specified message
            ref_message = await self.get_message(up_to_message_id)
            if ref_message:
                query = query.where(Message.created_at <= ref_message.created_at)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        marked_ids = []
        for message in messages:
            message.status = "read"
            marked_ids.append(str(message.id))

        if marked_ids:
            await self.db.commit()

        return marked_ids

    async def get_messages(
        self,
        conversation_id: str,
        before_id: str = None,
        limit: int = 50
    ) -> List[Message]:
        """Get messages with cursor-based pagination."""
        query = (
            select(Message)
            .where(Message.conversation_id == UUID(conversation_id))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        if before_id:
            before_message = await self.get_message(before_id)
            if before_message:
                query = query.where(Message.created_at < before_message.created_at)

        result = await self.db.execute(query)
        return result.scalars().all()
```

---

## REST API Endpoints

> **Note:** WebSocket handles real-time operations. REST API handles:
> - Initial data loading
> - Message history with pagination
> - Conversation management
> - Offline message sending fallback

```yaml
# Conversations
POST /api/v1/conversations
  Request:
    type: "direct"
    participant_ids: uuid[] (for direct: exactly 1 other user)
  Response: Conversation with participants

GET /api/v1/conversations
  Query: ?type=direct&page=1
  Response: Conversation[] with last_message preview and unread_count

GET /api/v1/conversations/{id}
  Response: Conversation with participants, presence status

# Messages (REST fallback - prefer WebSocket)
POST /api/v1/conversations/{id}/messages
  Request:
    content: string
    content_type: "text" (default)
  Response: Message

GET /api/v1/conversations/{id}/messages
  Query: ?before=<message_id>&limit=50
  Response: Message[] (reverse chronological for pagination)

# Read Receipts (REST fallback)
POST /api/v1/conversations/{id}/read
  Request:
    last_read_message_id: uuid
  Response: { unread_count: 0 }

# Presence
GET /api/v1/conversations/{id}/presence
  Response: { participants: [{ user_id, status, last_seen }] }

# User Search (for starting conversations)
GET /api/v1/users/search
  Query: ?q=john&limit=10
  Response: User[] (id, email, name, avatar)
```

---

## Frontend WebSocket Integration

### WebSocket Hook

```typescript
// hooks/useChatSocket.ts
import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';

interface ChatMessage {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  content_type: string;
  created_at: string;
  status: 'sent' | 'delivered' | 'read';
}

interface TypingIndicator {
  user_id: string;
  is_typing: boolean;
}

interface PresenceUpdate {
  user_id: string;
  status: 'online' | 'offline';
}

interface UseChatSocketOptions {
  onMessage?: (message: ChatMessage) => void;
  onTyping?: (data: TypingIndicator) => void;
  onPresence?: (data: PresenceUpdate) => void;
  onReadReceipt?: (data: { message_id: string; read_by: string }) => void;
}

export function useChatSocket(
  conversationId: string,
  options: UseChatSocketOptions = {}
) {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const [isConnected, setIsConnected] = useState(false);
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());

  const connect = useCallback(() => {
    if (!token || !conversationId) return;

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/chat/${conversationId}?token=${token}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleSocketMessage(data);
    };

    socket.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setIsConnected(false);

      // Reconnect after 3 seconds (unless intentional close)
      if (event.code !== 1000) {
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [token, conversationId]);

  const handleSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'message':
        // Update React Query cache with new message
        queryClient.setQueryData(
          ['messages', conversationId],
          (old: ChatMessage[] | undefined) => {
            if (!old) return [data.message];
            return [...old, data.message];
          }
        );
        options.onMessage?.(data.message);
        break;

      case 'message_sent':
        // Handle optimistic update confirmation
        queryClient.invalidateQueries({ queryKey: ['messages', conversationId] });
        break;

      case 'typing':
        setTypingUsers((prev) => {
          const next = new Set(prev);
          if (data.is_typing) {
            next.add(data.user_id);
          } else {
            next.delete(data.user_id);
          }
          return next;
        });
        options.onTyping?.(data);

        // Auto-clear typing indicator after 5 seconds
        setTimeout(() => {
          setTypingUsers((prev) => {
            const next = new Set(prev);
            next.delete(data.user_id);
            return next;
          });
        }, 5000);
        break;

      case 'presence':
        options.onPresence?.(data);
        // Update presence in query cache
        queryClient.invalidateQueries({
          queryKey: ['presence', conversationId]
        });
        break;

      case 'read_receipt':
        options.onReadReceipt?.(data);
        // Update message status in cache
        queryClient.setQueryData(
          ['messages', conversationId],
          (old: ChatMessage[] | undefined) => {
            if (!old) return old;
            return old.map((msg) =>
              msg.id === data.message_id
                ? { ...msg, status: 'read' as const }
                : msg
            );
          }
        );
        break;

      case 'delivered':
        // Update message status to delivered
        queryClient.setQueryData(
          ['messages', conversationId],
          (old: ChatMessage[] | undefined) => {
            if (!old) return old;
            return old.map((msg) =>
              msg.id === data.message_id
                ? { ...msg, status: 'delivered' as const }
                : msg
            );
          }
        );
        break;

      case 'pong':
        // Heartbeat response
        break;

      case 'error':
        console.error('WebSocket error:', data.message);
        break;
    }
  }, [conversationId, queryClient, options]);

  // Send message
  const sendMessage = useCallback((content: string, contentType = 'text') => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    const tempId = `temp-${Date.now()}`;

    socketRef.current.send(JSON.stringify({
      type: 'message',
      content,
      content_type: contentType,
      temp_id: tempId
    }));

    return tempId;
  }, []);

  // Send typing indicator
  const sendTyping = useCallback((isTyping: boolean) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    socketRef.current.send(JSON.stringify({
      type: 'typing',
      is_typing: isTyping
    }));
  }, []);

  // Mark messages as read
  const markAsRead = useCallback((messageId: string) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    socketRef.current.send(JSON.stringify({
      type: 'read',
      message_id: messageId
    }));
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();

    // Heartbeat every 30 seconds
    const heartbeatInterval = setInterval(() => {
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(heartbeatInterval);
      clearTimeout(reconnectTimeoutRef.current);
      socketRef.current?.close(1000, 'Component unmounted');
    };
  }, [connect]);

  return {
    isConnected,
    typingUsers: Array.from(typingUsers),
    sendMessage,
    sendTyping,
    markAsRead
  };
}
```

### Chat View Component

```typescript
// components/messages/ChatView.tsx
'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useChatSocket } from '@/hooks/useChatSocket';
import { api } from '@/lib/api-client';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { ChatHeader } from './ChatHeader';
import { TypingIndicator } from './TypingIndicator';

interface ChatViewProps {
  conversationId: string;
}

export function ChatView({ conversationId }: ChatViewProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout>();

  // Fetch initial messages
  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages', conversationId],
    queryFn: () => api.get(`/api/v1/conversations/${conversationId}/messages`),
  });

  // Fetch conversation details with presence
  const { data: conversation } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => api.get(`/api/v1/conversations/${conversationId}`),
  });

  // WebSocket connection
  const {
    isConnected,
    typingUsers,
    sendMessage,
    sendTyping,
    markAsRead
  } = useChatSocket(conversationId, {
    onMessage: (message) => {
      // Auto-scroll to new message
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

      // Mark as read if viewing
      if (document.visibilityState === 'visible') {
        markAsRead(message.id);
      }
    }
  });

  // Handle typing indicator
  const handleInputChange = (value: string) => {
    setInputValue(value);

    // Send typing indicator
    sendTyping(true);

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Stop typing indicator after 2 seconds of no typing
    typingTimeoutRef.current = setTimeout(() => {
      sendTyping(false);
    }, 2000);
  };

  // Send message
  const handleSend = () => {
    if (!inputValue.trim()) return;

    sendMessage(inputValue.trim());
    setInputValue('');
    sendTyping(false);
  };

  // Mark messages as read when viewing
  useEffect(() => {
    if (messages?.length > 0) {
      const lastMessage = messages[messages.length - 1];
      markAsRead(lastMessage.id);
    }
  }, [messages, markAsRead]);

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (isLoading) {
    return <div className="flex-1 flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <ChatHeader
        conversation={conversation}
        isConnected={isConnected}
      />

      <div className="flex-1 overflow-y-auto p-4">
        <MessageList
          messages={messages || []}
          conversationId={conversationId}
        />
        <div ref={messagesEndRef} />
      </div>

      {typingUsers.length > 0 && (
        <TypingIndicator userIds={typingUsers} />
      )}

      <MessageInput
        value={inputValue}
        onChange={handleInputChange}
        onSend={handleSend}
        disabled={!isConnected}
        placeholder={isConnected ? "Type a message..." : "Connecting..."}
      />
    </div>
  );
}
```

### Typing Indicator Component

```typescript
// components/messages/TypingIndicator.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';

interface TypingIndicatorProps {
  userIds: string[];
}

export function TypingIndicator({ userIds }: TypingIndicatorProps) {
  // Fetch user names for typing users
  const { data: users } = useQuery({
    queryKey: ['users', userIds],
    queryFn: async () => {
      const results = await Promise.all(
        userIds.map(id => api.get(`/api/v1/users/${id}`))
      );
      return results;
    },
    enabled: userIds.length > 0
  });

  if (!users || users.length === 0) return null;

  const names = users.map(u => u.display_name || u.email.split('@')[0]);

  let text: string;
  if (names.length === 1) {
    text = `${names[0]} is typing...`;
  } else if (names.length === 2) {
    text = `${names[0]} and ${names[1]} are typing...`;
  } else {
    text = `${names.length} people are typing...`;
  }

  return (
    <div className="px-4 py-2 text-sm text-gray-500 italic flex items-center gap-2">
      <span className="flex gap-1">
        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </span>
      {text}
    </div>
  );
}
```

### Message Status Indicator

```typescript
// components/messages/MessageStatus.tsx
'use client';

import { Check, CheckCheck } from 'lucide-react';

interface MessageStatusProps {
  status: 'sent' | 'delivered' | 'read';
}

export function MessageStatus({ status }: MessageStatusProps) {
  switch (status) {
    case 'sent':
      return <Check className="w-4 h-4 text-gray-400" />;
    case 'delivered':
      return <CheckCheck className="w-4 h-4 text-gray-400" />;
    case 'read':
      return <CheckCheck className="w-4 h-4 text-blue-500" />;
    default:
      return null;
  }
}
```

---

## Tasks

### Backend - WebSocket Infrastructure (CRITICAL)
- [ ] Set up FastAPI WebSocket endpoint
- [ ] Implement ConnectionManager with Redis pub/sub
- [ ] Add JWT authentication for WebSocket connections
- [ ] Implement room-based messaging (one room per conversation)
- [ ] Handle connection/disconnection gracefully
- [ ] Add heartbeat mechanism for connection health

### Backend - Presence System
- [ ] Create PresenceService with Redis storage
- [ ] Implement online/offline detection
- [ ] Add heartbeat-based presence refresh
- [ ] Create presence REST endpoint
- [ ] Broadcast presence changes via WebSocket

### Backend - Typing Indicators
- [ ] Create TypingService with Redis TTL storage
- [ ] Handle typing start/stop events
- [ ] Broadcast typing status to room participants

### Backend - Message Delivery
- [ ] Implement message status tracking (sent -> delivered -> read)
- [ ] Update status when message reaches online recipients
- [ ] Implement read receipt handling
- [ ] Broadcast status updates via WebSocket

### Backend - Conversations (reference Sprint 01 schema)
- [ ] Implement create conversation endpoint
- [ ] Implement list conversations with unread counts
- [ ] Handle direct message deduplication (A->B == B->A)
- [ ] Add participant management

### Backend - Messages
- [ ] Implement send message (REST fallback)
- [ ] Implement message history with cursor pagination
- [ ] Implement bulk read receipt endpoint

### Frontend - WebSocket Integration
- [ ] Create useChatSocket hook
- [ ] Implement automatic reconnection
- [ ] Add heartbeat mechanism
- [ ] Integrate with React Query cache

### Frontend - Conversation List
- [ ] Create Conversations sidebar/page
- [ ] Show conversation previews with presence dots
- [ ] Display unread counts (real-time updates)
- [ ] Sort by last message time

### Frontend - Chat View
- [ ] Build real-time message list
- [ ] Implement message input with typing indicator
- [ ] Show message status indicators (sent/delivered/read)
- [ ] Auto-scroll to new messages
- [ ] Show connection status

### Frontend - Typing & Presence
- [ ] Display typing indicators
- [ ] Show online/offline status in headers
- [ ] Update presence in real-time

### Frontend - New Conversation
- [ ] User search component
- [ ] Start conversation modal
- [ ] Navigate to new conversation

---

## Acceptance Criteria

1. WebSocket connection establishes with JWT authentication
2. Messages appear instantly for all participants (no refresh)
3. Typing indicators show when users are typing
4. Presence (online/offline) updates in real-time
5. Message status shows sent -> delivered -> read progression
6. Reconnection works automatically on network issues
7. Message history loads with pagination
8. Unread counts update in real-time
9. Works across multiple browser tabs/devices
10. Graceful degradation to REST when WebSocket unavailable

---

## UI Components

### Conversation List
```typescript
<ConversationList>
  <ConversationItem
    avatar={user.avatar}
    name={user.name}
    lastMessage="Hey, about the project..."
    timestamp="2m ago"
    unreadCount={3}
    isOnline={true}  // Presence indicator
    onClick={() => selectConversation(id)}
  />
</ConversationList>
```

### Chat View
```typescript
<ChatView conversation={conversation}>
  <ChatHeader>
    <Avatar />
    <Name />
    <OnlineStatus status="online" />  // Real-time presence
    <ConnectionIndicator connected={true} />
  </ChatHeader>

  <MessageList messages={messages}>
    <Message
      content="Hello!"
      sender={user}
      timestamp="10:30 AM"
      status="read"  // Delivery receipt
      isMine={true}
    />
  </MessageList>

  <TypingIndicator users={typingUsers} />

  <MessageInput
    onSend={sendMessage}
    onTypingChange={sendTyping}
    placeholder="Type a message..."
  />
</ChatView>
```

---

## Files to Create

```
# Backend
src/
  websocket/
    __init__.py
    manager.py          # ConnectionManager with Redis pub/sub
    handlers.py         # Message type handlers

  services/
    presence_service.py
    typing_service.py
    message_service.py  # Enhanced with status tracking
    conversation_service.py

  api/v1/
    endpoints/
      websocket.py      # WebSocket endpoint
      presence.py       # Presence REST endpoints
      conversations.py  # Conversation CRUD
      messages.py       # Message CRUD

# Frontend
frontend/src/
  hooks/
    useChatSocket.ts    # WebSocket hook with React Query
    usePresence.ts      # Presence queries

  app/dashboard/
    messages/
      page.tsx
      [conversationId]/
        page.tsx

  components/
    messages/
      ConversationList.tsx
      ConversationItem.tsx
      ChatView.tsx
      ChatHeader.tsx
      MessageList.tsx
      Message.tsx
      MessageInput.tsx
      MessageStatus.tsx
      TypingIndicator.tsx
      OnlineStatus.tsx
      NewConversation.tsx
      UserSearch.tsx
```

---

## Environment Configuration

```env
# Backend (.env)
REDIS_URL=redis://localhost:6379
WS_HEARTBEAT_INTERVAL=30
WS_PRESENCE_TTL=60
WS_TYPING_TTL=5

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Related Requirement Groups

- Group 011: Semantic: Status Updates
- Group 019: Semantic: User Interface
- Messaging domain requirements
