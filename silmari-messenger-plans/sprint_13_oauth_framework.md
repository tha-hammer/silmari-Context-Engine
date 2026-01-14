# Sprint 13: OAuth Integration Framework

**Phase:** 4 - Business Tools
**Focus:** OAuth 2.0 framework for third-party integrations
**Dependencies:** Sprint 02 (Auth)

---

## Testable Deliverable

**Human Test:**
1. Navigate to Integrations settings page
2. Click "Connect Google Account"
3. Redirected to Google consent screen
4. Authorize and return to app
5. See "Google Connected" status
6. Can disconnect the integration

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_005 | Seamless integration with business tools | 17 |
| REQ_059 | Bidirectional data sync | 19 |

### Implementation Requirements
- REQ_005.2.4: Implement authentication flow for all integrations
- REQ_005.3.1-3.3: OAuth for Slack, Gmail, Notion

---

## Architecture

```
[User] --> [/integrations/connect/google]
                |
                v
        [Generate State Token]
                |
                v
        [Redirect to Google OAuth]
                |
                v
        [User Authorizes]
                |
                v
        [Callback with Code]
                |
                v
        [Exchange Code for Tokens]
                |
                v
        [Store Encrypted Tokens]
                |
                v
        [Integration Active]
```

---

## Data Model

```python
class Integration(BaseModel):
    id: UUID
    user_id: UUID
    provider: str           # google, microsoft, slack, notion
    status: IntegrationStatus
    access_token: str       # Encrypted
    refresh_token: str      # Encrypted
    token_expires_at: datetime
    scopes: List[str]
    metadata: Dict          # Provider-specific data
    connected_at: datetime
    last_sync_at: datetime | None

class IntegrationStatus(Enum):
    PENDING = "pending"     # OAuth started
    ACTIVE = "active"       # Connected and working
    EXPIRED = "expired"     # Token expired, needs refresh
    ERROR = "error"         # Connection error
    DISCONNECTED = "disconnected"

# Metadata schema - stores connected account info for UI display
class IntegrationMetadata(TypedDict, total=False):
    external_email: str       # The connected account email (user@gmail.com)
    external_name: str        # Account holder name
    external_id: str          # Provider's user ID
    profile_picture: str      # Avatar URL
    organization: str         # For work accounts
```

---

## API Endpoints

```yaml
# List Available Integrations
GET /api/v1/integrations/available
  Response:
    integrations: [
      { provider: "google", name: "Google Workspace", connected: bool }
    ]

# Start OAuth Flow
GET /api/v1/integrations/connect/{provider}
  Response: Redirect to provider OAuth URL

# OAuth Callback
GET /api/v1/integrations/callback/{provider}
  Query: code, state
  Response: Redirect to /settings/integrations?status=success

# List User's Integrations
GET /api/v1/integrations
  Response: Integration[]

# Get Integration Status
GET /api/v1/integrations/{provider}
  Response: Integration with status

# Disconnect Integration
DELETE /api/v1/integrations/{provider}
  Response: 204

# Refresh Token (internal/admin)
POST /api/v1/integrations/{provider}/refresh
  Response: { status: "refreshed" }
```

---

## Tasks

### Backend - OAuth Framework
- [ ] Create Integration model
- [ ] Implement OAuth state management
- [ ] Build generic OAuth flow handler
- [ ] Token encryption/decryption

### Backend - Provider Config
- [ ] Google OAuth configuration
- [ ] Microsoft OAuth configuration
- [ ] Slack OAuth configuration
- [ ] Notion OAuth configuration

### Backend - Token Management
- [ ] Secure token storage (encrypted at rest)
- [ ] Automatic token refresh
- [ ] Token expiration handling
- [ ] Revocation handling

### Frontend - Integration UI
- [ ] Integrations settings page
- [ ] Connect buttons per provider
- [ ] Connection status indicators
- [ ] Disconnect confirmation

---

## Acceptance Criteria

1. Can initiate OAuth flow for Google
2. Callback properly exchanges code for tokens
3. Tokens stored encrypted in database
4. Integration status visible in UI
5. Can disconnect integration
6. Token refresh works automatically
7. Proper error handling for OAuth failures

---

## Provider Configuration

```python
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

OAUTH_PROVIDERS = {
    "google": {
        "name": "Google Workspace",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "redirect_uri": f"{BASE_URL}/api/v1/integrations/callback/google",
        "scopes": [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    },
    "microsoft": {
        "name": "Microsoft 365",
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "redirect_uri": f"{BASE_URL}/api/v1/integrations/callback/microsoft",
        "scopes": [
            "Mail.Read",
            "Calendars.Read",
            "Files.Read",
            "User.Read",
        ],
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
    },
}
```

---

## Files to Create

```
src/
  integrations/
    __init__.py
    models.py
    schemas.py
    service.py
    router.py
    oauth/
      __init__.py
      base.py          # Generic OAuth handler
      google.py
      microsoft.py
      slack.py
      notion.py
    encryption.py      # Token encryption

frontend/src/
  app/dashboard/settings/
    integrations/
      page.tsx
  components/
    integrations/
      IntegrationCard.tsx
      ConnectButton.tsx
      StatusBadge.tsx
```

---

## Security Considerations

```python
# Token encryption
from cryptography.fernet import Fernet

class TokenEncryption:
    def __init__(self):
        self.key = os.getenv("TOKEN_ENCRYPTION_KEY")
        self.fernet = Fernet(self.key)

    def encrypt(self, token: str) -> str:
        return self.fernet.encrypt(token.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        return self.fernet.decrypt(encrypted.encode()).decode()

# State token (CSRF protection)
def generate_oauth_state(user_id: UUID, provider: str) -> str:
    payload = {
        "user_id": str(user_id),
        "provider": provider,
        "exp": datetime.utcnow() + timedelta(minutes=10)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

---

## Database Schema

```sql
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMP,
    scopes TEXT[],
    metadata JSONB DEFAULT '{}',
    connected_at TIMESTAMP,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, provider)
);

CREATE INDEX idx_integrations_user ON integrations(user_id);
CREATE INDEX idx_integrations_provider ON integrations(provider);
```

---

## Related Requirement Groups

- Integration domain (138 requirements)
- Group 005: Semantic: Authentication (OAuth flows)

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added `redirect_uri` to all provider configurations
2. Added `userinfo_url` for fetching connected account details
3. Added `IntegrationMetadata` schema for storing external account info (email, name, profile picture)
4. Added missing Microsoft client credentials environment variables
5. Added User.Read scope for Microsoft to fetch profile info

**Frontend Note:** After OAuth callback completes, the frontend should:
1. Poll `/api/v1/integrations/{provider}` for status changes, OR
2. Use WebSocket notification (from Sprint 09) to receive completion event
