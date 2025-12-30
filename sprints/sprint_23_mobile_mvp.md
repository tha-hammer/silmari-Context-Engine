# Sprint 23: Mobile App MVP

**Phase:** 7 - Mobile & Scale
**Focus:** iOS and Android mobile applications
**Dependencies:** All API sprints complete

---

## Testable Deliverable

**Human Test:**
1. Install app on iOS/Android device
2. Login with existing account
3. View conversations and messages
4. Send a message
5. View memories
6. Receive push notifications
7. Basic offline support

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_009 | iOS and Android mobile apps | 20 |
| REQ_291 | Phase 7 mobile development | 21 |

### Implementation Requirements
- REQ_009.2.1: iOS app development
- REQ_009.2.2: Android app development
- REQ_009.4.1-4.4: Mobile auth integration
- REQ_291.2.1-2.3: Mobile features

---

## Tech Stack

```
Framework: React Native (or Flutter)
Navigation: React Navigation
State: Zustand / Redux Toolkit
API: Shared API client (axios/fetch)
Push: Firebase Cloud Messaging
Storage: AsyncStorage + SQLite for offline
```

---

## MVP Features

### Must Have (This Sprint)
- [x] Login/logout
- [x] View conversation list
- [x] View messages in conversation
- [x] Send text message
- [x] View memory list
- [x] Push notifications
- [x] Pull-to-refresh

### Nice to Have (Future)
- [ ] AI chat
- [ ] Create memories
- [ ] Search
- [ ] File attachments
- [ ] Biometric auth

---

## Screens

```
├── Auth
│   ├── Login
│   └── Register
├── Main (Tab Navigator)
│   ├── Conversations
│   │   ├── List
│   │   └── Chat
│   ├── Memories
│   │   ├── List
│   │   └── Detail
│   └── Settings
│       ├── Profile
│       ├── Notifications
│       └── Logout
```

---

## API Integration

```typescript
// Shared API client
class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor() {
    this.baseUrl = Config.API_URL;
  }

  setToken(token: string) {
    this.token = token;
    AsyncStorage.setItem('auth_token', token);
  }

  async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new ApiError(response.status, await response.json());
    }

    return response.json();
  }

  // Convenience methods
  get = <T>(endpoint: string) => this.request<T>(endpoint);
  post = <T>(endpoint: string, data: any) =>
    this.request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) });
}
```

---

## Tasks

### Setup
- [ ] Initialize React Native project
- [ ] Configure iOS and Android projects
- [ ] Set up development environment
- [ ] Configure CI/CD for mobile

### Authentication
- [ ] Login screen
- [ ] Register screen
- [ ] Token storage (secure)
- [ ] Auto-login on app launch
- [ ] Logout functionality

### Conversations
- [ ] Conversation list screen
- [ ] Chat screen with messages
- [ ] Send message functionality
- [ ] Real-time updates (polling)
- [ ] Typing indicators

### Memories
- [ ] Memory list screen
- [ ] Memory detail view
- [ ] Pull-to-refresh
- [ ] Infinite scroll

### Push Notifications
- [ ] Firebase setup
- [ ] Device token registration
- [ ] Handle incoming notifications
- [ ] Deep linking from notification

### Offline Support
- [ ] Cache conversations locally
- [ ] Cache memories locally
- [ ] Queue offline actions
- [ ] Sync when online

---

## Acceptance Criteria

1. App installs on iOS and Android
2. Can login with credentials
3. Conversations load and display
4. Can send messages
5. Memories viewable
6. Push notifications work
7. Offline viewing works

---

## Screen Components

```typescript
// ConversationListScreen
function ConversationListScreen() {
  const { conversations, isLoading, refresh } = useConversations();

  return (
    <FlatList
      data={conversations}
      renderItem={({ item }) => (
        <ConversationItem
          conversation={item}
          onPress={() => navigation.navigate('Chat', { id: item.id })}
        />
      )}
      refreshControl={
        <RefreshControl refreshing={isLoading} onRefresh={refresh} />
      }
      ListEmptyComponent={<EmptyState message="No conversations yet" />}
    />
  );
}

// ChatScreen
function ChatScreen({ route }) {
  const { id } = route.params;
  const { messages, sendMessage, isLoading } = useChat(id);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container}>
      <FlatList
        data={messages}
        renderItem={({ item }) => <MessageBubble message={item} />}
        inverted
      />
      <View style={styles.inputContainer}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="Type a message..."
          style={styles.input}
        />
        <TouchableOpacity onPress={handleSend}>
          <SendIcon />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}
```

---

## Push Notifications

```typescript
// Firebase setup
import messaging from '@react-native-firebase/messaging';

async function setupPushNotifications() {
  // Request permission
  const authStatus = await messaging().requestPermission();
  const enabled = authStatus === messaging.AuthorizationStatus.AUTHORIZED;

  if (enabled) {
    // Get token
    const token = await messaging().getToken();

    // Register with backend
    await api.post('/api/v1/devices', {
      token,
      platform: Platform.OS,
    });

    // Handle incoming messages
    messaging().onMessage(async remoteMessage => {
      // Show in-app notification
      showNotification(remoteMessage);
    });

    // Handle background messages
    messaging().setBackgroundMessageHandler(async remoteMessage => {
      console.log('Background message:', remoteMessage);
    });

    // Handle notification tap
    messaging().onNotificationOpenedApp(remoteMessage => {
      navigateToContent(remoteMessage.data);
    });
  }
}
```

---

## File Structure

```
mobile/
├── src/
│   ├── api/
│   │   ├── client.ts
│   │   ├── auth.ts
│   │   ├── conversations.ts
│   │   └── memories.ts
│   ├── components/
│   │   ├── ConversationItem.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── MemoryCard.tsx
│   │   └── common/
│   ├── screens/
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   └── RegisterScreen.tsx
│   │   ├── conversations/
│   │   │   ├── ListScreen.tsx
│   │   │   └── ChatScreen.tsx
│   │   ├── memories/
│   │   │   ├── ListScreen.tsx
│   │   │   └── DetailScreen.tsx
│   │   └── settings/
│   ├── navigation/
│   │   └── index.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useConversations.ts
│   │   └── useMemories.ts
│   ├── stores/
│   │   └── index.ts
│   └── utils/
│       ├── storage.ts
│       └── notifications.ts
├── ios/
├── android/
└── package.json
```

---

## Related Requirement Groups

- REQ_009: Mobile apps
- REQ_291: Phase 7 mobile
- UI components domain

---

## Backend: Device Registration API

```yaml
# Add to backend API (not in mobile folder)
POST /api/v1/devices
  Request:
    token: string         # FCM device token
    platform: string      # ios, android
    app_version: string
  Response:
    id: uuid
    registered: true

DELETE /api/v1/devices/{token}
  Response: 204

GET /api/v1/devices
  Response: UserDevice[]
```

---

## Backend Database Schema

```sql
-- User devices for push notifications
CREATE TABLE user_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_token TEXT NOT NULL UNIQUE,
    platform VARCHAR(10) NOT NULL,    -- ios, android
    app_version VARCHAR(20),
    last_active_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_devices_user ON user_devices(user_id);
CREATE INDEX idx_devices_token ON user_devices(device_token);
```

---

## Backend: Push Notification Service

```python
import firebase_admin
from firebase_admin import messaging, credentials

class PushNotificationService:
    """Send push notifications to mobile devices."""

    def __init__(self):
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
        firebase_admin.initialize_app(cred)

    async def send_to_user(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: Dict = None
    ):
        """Send push notification to all user's devices."""
        devices = await get_user_devices(user_id)

        for device in devices:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    data=data or {},
                    token=device.device_token,
                )
                messaging.send(message)

            except messaging.UnregisteredError:
                # Device token is invalid, remove it
                await delete_device(device.id)

    async def send_to_device(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Dict = None
    ):
        """Send to specific device."""
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=device_token,
        )
        return messaging.send(message)


# Usage in other services
async def notify_new_message(conversation_id: UUID, message: Message):
    """Notify participants of new message."""
    participants = await get_conversation_participants(conversation_id)

    push_service = PushNotificationService()
    for user_id in participants:
        if user_id != message.sender_id:
            await push_service.send_to_user(
                user_id=user_id,
                title=f"New message from {message.sender_name}",
                body=message.content[:100],
                data={
                    "type": "new_message",
                    "conversation_id": str(conversation_id),
                    "message_id": str(message.id),
                }
            )
```

---

## Secure Token Storage (Mobile)

```typescript
// IMPORTANT: Use secure storage, NOT AsyncStorage
import * as Keychain from 'react-native-keychain';

class SecureStorage {
  static async setToken(token: string): Promise<void> {
    await Keychain.setGenericPassword('auth', token, {
      service: 'com.tanka.app',
      accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED,
    });
  }

  static async getToken(): Promise<string | null> {
    try {
      const credentials = await Keychain.getGenericPassword({
        service: 'com.tanka.app',
      });
      if (credentials) {
        return credentials.password;
      }
      return null;
    } catch (error) {
      console.error('Error getting token from keychain:', error);
      return null;
    }
  }

  static async clearToken(): Promise<void> {
    await Keychain.resetGenericPassword({
      service: 'com.tanka.app',
    });
  }
}

// Update API client to use secure storage
class ApiClient {
  private token: string | null = null;

  async initialize() {
    this.token = await SecureStorage.getToken();
  }

  async setToken(token: string) {
    this.token = token;
    await SecureStorage.setToken(token);
  }

  async clearToken() {
    this.token = null;
    await SecureStorage.clearToken();
  }

  // ... rest of API client
}
```

---

## WebSocket for Real-time (Alternative to Polling)

```typescript
// Use WebSocket for real-time chat instead of polling
import { io, Socket } from 'socket.io-client';

class ChatWebSocket {
  private socket: Socket | null = null;

  connect(token: string) {
    this.socket = io(Config.WS_URL, {
      auth: { token },
      transports: ['websocket'],
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('new_message', (message) => {
      // Update local state
      messageStore.addMessage(message);
    });

    this.socket.on('typing', ({ conversationId, userId }) => {
      typingStore.setTyping(conversationId, userId);
    });
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }

  joinConversation(conversationId: string) {
    this.socket?.emit('join_conversation', { conversationId });
  }

  sendMessage(conversationId: string, content: string) {
    this.socket?.emit('send_message', { conversationId, content });
  }

  sendTyping(conversationId: string) {
    this.socket?.emit('typing', { conversationId });
  }
}
```

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added backend device registration API (`POST /api/v1/devices`)
2. Added `user_devices` database table for push token storage
3. Added `PushNotificationService` using Firebase Admin SDK
4. Fixed insecure token storage: replaced AsyncStorage with react-native-keychain
5. Added WebSocket option for real-time chat (alternative to polling)
6. Added push notification integration for new messages

**Cross-Sprint Dependencies:**
- Sprint 09: WebSocket infrastructure for real-time messaging
- Sprint 18: Task reminders use push notifications

**Required Dependencies:**
- `react-native-keychain` for secure token storage
- `socket.io-client` for WebSocket (optional, can use native WebSocket)
- Firebase Admin SDK on backend
- Firebase Cloud Messaging setup in iOS/Android projects

**Security Note:**
- NEVER use AsyncStorage for auth tokens - it's not encrypted
- Always use Keychain (iOS) / EncryptedSharedPreferences (Android)
