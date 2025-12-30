# Sprint 02: Authentication Core

**Phase:** 1 - Foundation
**Focus:** User authentication system with JWT and refresh tokens
**Dependencies:** Sprint 01 (Database)

---

## Testable Deliverable

**Human Test:**
1. Register a new account with email/password
2. Receive confirmation (or auto-confirm for MVP)
3. Login with credentials
4. Receive access token AND refresh token
5. Access protected endpoint with access token
6. Refresh access token when expired
7. Logout and verify tokens are invalidated

**Test Flow:**
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
# Returns: {"access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 3600}

# Access protected route
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"

# Refresh token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'

# Logout
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_010 | End-to-end encryption for private chats | 17 |
| REQ_011 | ISO 27001-2022 compliance | 17 |
| REQ_017 | User Authentication | 2 |

### Implementation Requirements

**Group 005 - Authentication (8 requirements)**
- REQ_007.2.2: Implement user authentication and authorization
- REQ_009.2.2: Implement user authentication flow (sign-up, login, password reset)
- REQ_011.2.3: Implement access controls based on least privilege
- REQ_011.3.1: Enforce strong password policy
- REQ_011.3.4: Securely hash passwords using bcrypt

**Group 017 - User Authentication (2 requirements)**
- REQ_002.4.5: Verify user identity and manage session
- REQ_005.2.4: Implement authentication flow for all integrations

---

## Authentication Features

### Core Auth (This Sprint)
- [x] Email/password registration
- [x] Password hashing with bcrypt
- [x] JWT access token generation (short-lived)
- [x] Refresh token generation (long-lived)
- [x] Token validation middleware
- [x] Session management in database
- [x] Logout/token revocation
- [x] Token refresh endpoint

### Future Sprints
- [ ] OAuth2 providers (Sprint 13)
- [ ] MFA/TOTP (Sprint 21)
- [ ] Password reset flow
- [ ] Email verification

---

## API Endpoints

```yaml
POST /api/auth/register
  Request:
    email: string (required)
    password: string (required, min 8 chars)
    first_name: string (optional)
    last_name: string (optional)
  Response:
    user_id: uuid
    email: string
    created_at: timestamp

POST /api/auth/login
  Request:
    email: string
    password: string
  Response:
    access_token: string
    refresh_token: string
    token_type: "bearer"
    expires_in: integer (seconds, default 3600)
    user: { id, email, display_name, avatar_url }

POST /api/auth/refresh
  Request:
    refresh_token: string
  Response:
    access_token: string
    refresh_token: string (rotated)
    token_type: "bearer"
    expires_in: integer

POST /api/auth/logout
  Headers:
    Authorization: Bearer <token>
  Response:
    message: "Logged out successfully"

POST /api/auth/logout-all
  Headers:
    Authorization: Bearer <token>
  Response:
    message: "All sessions logged out"
    sessions_revoked: integer

GET /api/auth/me
  Headers:
    Authorization: Bearer <token>
  Response:
    id: uuid
    email: string
    display_name: string
    first_name: string
    last_name: string
    avatar_url: string
    created_at: timestamp

GET /api/auth/sessions
  Headers:
    Authorization: Bearer <token>
  Response:
    sessions: [
      { id, ip_address, user_agent, created_at, is_current }
    ]

DELETE /api/auth/sessions/{session_id}
  Headers:
    Authorization: Bearer <token>
  Response:
    message: "Session revoked"
```

---

## Token Architecture

```
Access Token (JWT)
├── Short-lived: 1 hour
├── Contains: user_id, email, session_id
├── Stored: Client-side only (not in DB)
└── Used for: API authentication

Refresh Token
├── Long-lived: 7 days
├── Contains: random token hash
├── Stored: Database (sessions table)
├── Rotated: On each refresh
└── Used for: Getting new access tokens
```

### JWT Payload
```json
{
  "sub": "user_uuid",
  "email": "user@example.com",
  "session_id": "session_uuid",
  "iat": 1234567890,
  "exp": 1234571490,
  "type": "access"
}
```

---

## Tasks

### User Registration
- [ ] Create registration endpoint
- [ ] Validate email format and uniqueness
- [ ] Implement password strength requirements
- [ ] Hash password with bcrypt (cost factor 12)
- [ ] Create user record in database
- [ ] Create user_preferences record with defaults

### Login System
- [ ] Create login endpoint
- [ ] Verify credentials against database
- [ ] Create session record in database
- [ ] Generate JWT access token
- [ ] Generate refresh token (store hash in DB)
- [ ] Set token expiration (1 hour access, 7 day refresh)
- [ ] Return both tokens to client

### Token Refresh
- [ ] Create refresh endpoint
- [ ] Validate refresh token against database
- [ ] Rotate refresh token (invalidate old, create new)
- [ ] Generate new access token
- [ ] Handle expired refresh tokens

### Session Management
- [ ] Store session in database with metadata
- [ ] Track IP address and user agent
- [ ] Implement single session logout
- [ ] Implement logout from all devices
- [ ] List active sessions endpoint

### Security
- [ ] Rate limit auth endpoints (5 attempts per minute per IP)
- [ ] Log authentication events to audit_logs
- [ ] Implement account lockout after 5 failed attempts
- [ ] Sanitize all inputs
- [ ] Use secure cookies for web client (httpOnly, SameSite)

---

## Acceptance Criteria

1. User can register with valid email/password
2. Duplicate email registration is rejected
3. Weak passwords are rejected with helpful message
4. Login returns valid access token and refresh token
5. Protected endpoints reject invalid/missing tokens
6. Refresh endpoint returns new tokens
7. Logout invalidates the session
8. Logout-all invalidates all user sessions
9. Rate limiting prevents brute force attempts
10. All auth events logged to audit_logs

---

## Files to Create

```
src/
  auth/
    __init__.py
    router.py          # FastAPI routes
    service.py         # Business logic
    schemas.py         # Pydantic models
    security.py        # Password hashing, JWT utils
    middleware.py      # Auth middleware
    dependencies.py    # FastAPI dependencies (get_current_user)
```

---

## Implementation Details

### Password Hashing
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### JWT Token Generation
```python
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token() -> tuple[str, str]:
    """Returns (token, token_hash) - store hash in DB, return token to client."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash

def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.JWTError:
        raise InvalidTokenError("Invalid token")
```

### Auth Middleware
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        session_id = payload.get("session_id")

        # Verify session is still valid
        session = await db.get(Session, session_id)
        if not session or session.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Session expired")

        user = await db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Session Management
```python
async def create_session(
    user_id: UUID,
    ip_address: str,
    user_agent: str,
    db: AsyncSession
) -> tuple[str, str]:
    """Create session and return (access_token, refresh_token)."""

    # Generate refresh token
    refresh_token, refresh_token_hash = create_refresh_token()

    # Create session record
    session = Session(
        user_id=user_id,
        refresh_token_hash=refresh_token_hash,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(session)
    await db.commit()

    # Generate access token
    access_token = create_access_token({
        "sub": str(user_id),
        "session_id": str(session.id)
    })

    return access_token, refresh_token

async def refresh_session(
    refresh_token: str,
    db: AsyncSession
) -> tuple[str, str]:
    """Rotate refresh token and return new tokens."""

    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

    # Find session by refresh token hash
    session = await db.execute(
        select(Session).where(
            Session.refresh_token_hash == refresh_token_hash,
            Session.expires_at > datetime.utcnow()
        )
    )
    session = session.scalar_one_or_none()

    if not session:
        raise InvalidTokenError("Invalid refresh token")

    # Rotate refresh token
    new_refresh_token, new_refresh_token_hash = create_refresh_token()
    session.refresh_token_hash = new_refresh_token_hash
    session.expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    await db.commit()

    # Generate new access token
    access_token = create_access_token({
        "sub": str(session.user_id),
        "session_id": str(session.id)
    })

    return access_token, new_refresh_token
```

---

## Password Policy

```python
PASSWORD_REQUIREMENTS = {
    "min_length": 8,
    "max_length": 128,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": False,  # Optional for MVP
}

def validate_password(password: str) -> tuple[bool, list[str]]:
    errors = []

    if len(password) < PASSWORD_REQUIREMENTS["min_length"]:
        errors.append(f"Password must be at least {PASSWORD_REQUIREMENTS['min_length']} characters")

    if PASSWORD_REQUIREMENTS["require_uppercase"] and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if PASSWORD_REQUIREMENTS["require_lowercase"] and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if PASSWORD_REQUIREMENTS["require_digit"] and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")

    return len(errors) == 0, errors
```

---

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    ...

@router.post("/register")
@limiter.limit("3/minute")
async def register(request: Request, data: RegisterRequest):
    ...
```

---

## Audit Logging

```python
async def log_auth_event(
    action: str,
    user_id: UUID | None,
    status: str,
    ip_address: str,
    user_agent: str,
    error: str | None = None,
    db: AsyncSession
):
    audit_log = AuditLog(
        action=action,
        user_id=user_id,
        resource_type="auth",
        status=status,
        ip_address=ip_address,
        user_agent=user_agent,
        error_message=error
    )
    db.add(audit_log)
    await db.commit()

# Usage
await log_auth_event(
    action="auth.login",
    user_id=user.id,
    status="success",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    db=db
)
```

---

## Related Requirement Groups

- Group 005: Semantic: Authentication
- Group 017: Semantic: User Authentication
- Group 018: Semantic: Security Policy
