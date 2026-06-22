# Code Review — Task Management API
**Reviewer:** Lead Engineer (20+ YOE)
**Stack:** FastAPI · SQLAlchemy · PostgreSQL · PyJWT · Alembic
**Scope:** Full codebase — security, architecture, database, API design, code quality, structure

---

> [!CAUTION]
> **One vulnerability alone (hardcoded JWT secret) can allow any attacker to forge authentication tokens and gain full admin access. Fix this before anything else.**

---

## Table of Contents

1. [🔴 Critical Security Vulnerabilities](#1-critical-security-vulnerabilities)
2. [🟠 Architectural Flaws](#2-architectural-flaws)
3. [🟡 Database Design Problems](#3-database-design-problems)
4. [🔵 API Design Violations](#4-api-design-violations)
5. [🟢 Code Quality Issues](#5-code-quality-issues)
6. [⚪ Project Structure Gaps](#6-project-structure-gaps)
7. [✅ FastAPI Best Practices Reference](#7-fastapi-best-practices-reference)
8. [📊 Final Scorecard](#8-final-scorecard)

---

## 1. 🔴 Critical Security Vulnerabilities

---

### 1.1 Hardcoded JWT Secret Key
**File:** [`app/auth/jwt_handler.py`](file:///c:/Coding/PYTHON/Task%20Management/app/auth/jwt_handler.py) — Line 11

**Problem:** The JWT secret key is a raw string literal baked into source code. Anyone with repository access can use this key to forge valid tokens for any user, including admin. This is a **critical authentication bypass** vulnerability.

```python
# ❌ WRONG — SECRET_KEY exposed in source code
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
```

**Fix:** Move ALL JWT configuration into `Settings` via `pydantic-settings`, loaded exclusively from environment variables.

```python
# ✅ CORRECT — in app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Task Management API"
    debug: bool = False
    database_url: str

    # JWT — all in settings, loaded from env
    jwt_secret_key: str           # Must be set in .env, no default
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

# ✅ CORRECT — in app/auth/jwt_handler.py
from app.core.config import get_settings

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = utc_now() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
```

```bash
# .env — generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=<generated-256-bit-random-hex>
```

---

### 1.2 Any User Can Self-Assign Admin Role at Registration
**File:** [`app/schemas/user.py`](file:///c:/Coding/PYTHON/Task%20Management/app/schemas/user.py) — Line 9

**Problem:** `UserBase` exposes `role_id` as a writable field. `UserCreate` inherits it. This means a user can POST `{"username": "hacker", "password": "x", "role_id": "<admin-role-uuid>"}` to `/users/auth/register` and grant themselves admin rights.

```python
# ❌ WRONG — role_id is client-controlled
class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    role_id: UUID | None = None   # ← attacker can set this to admin UUID

class UserCreate(UserBase):
    password: str
```

**Fix:** Remove `role_id` from all client-facing schemas. Role assignment must be server-side only.

```python
# ✅ CORRECT
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)  # enforce min password length

class UserRead(BaseModel):
    id: UUID
    username: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# In the service layer, role_id is assigned by server logic, never from client input
```

---

### 1.3 Admin Password Entered in Plaintext Terminal
**File:** [`app/scripts/create_admin.py`](file:///c:/Coding/PYTHON/Task%20Management/app/scripts/create_admin.py) — Line 9

**Problem:** `input("Password: ")` echoes the password to the terminal in plaintext. It can be captured by terminal logs, screen recordings, or shoulder-surfing.

```python
# ❌ WRONG
password = input("Password: ")
```

**Fix:** Use `getpass` from the standard library.

```python
# ✅ CORRECT
import getpass
password = getpass.getpass("Password: ")  # input is hidden
```

---

### 1.4 No Refresh Token — Forced Re-authentication Attack Surface
**File:** [`app/routers/users.py`](file:///c:/Coding/PYTHON/Task%20Management/app/routers/users.py) — Line 54

**Problem:** Only short-lived access tokens are issued. There is no refresh token mechanism. This forces clients to re-submit credentials frequently, which is insecure UX and doesn't support token revocation.

**Fix:** Issue both an access token (15 min) and a refresh token (7 days). Store refresh token hash in DB. Provide a `POST /auth/refresh` endpoint.

---

### 1.5 No `WWW-Authenticate` Header on Project/Task 403 Responses
**File:** [`app/authorization/permissions.py`](file:///c:/Coding/PYTHON/Task%20Management/app/authorization/permissions.py) — Lines 72, 78, 102, 108

**Problem:** `raise HTTPException(403)` with no `detail` and no `headers`. RFC 7235 mandates a `WWW-Authenticate` header on auth-related errors. The bare `403` with no detail is also an unusable API error for clients.

```python
# ❌ WRONG
raise HTTPException(403)

# ✅ CORRECT
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You do not have permission to perform this action."
)
```

---

## 2. 🟠 Architectural Flaws

---

### 2.1 `get_current_user` Misplaced in the Service Layer
**File:** [`app/services/user.py`](file:///c:/Coding/PYTHON/Task%20Management/app/services/user.py) — Line 63

**Problem:** The code even has a comment admitting this: `# place this function in a more appropriate file`. `get_current_user` is an **HTTP infrastructure concern** — it depends on `OAuth2PasswordBearer` and `Depends`. Service layers must be interface-agnostic (they should work from CLI, tests, or Celery tasks equally). Placing this here creates an illegal coupling between the service layer and the HTTP layer.

```
❌ Current (wrong dependency direction):
services/user.py  ←── imports ──  dependencies.py (HTTP infrastructure)

✅ Correct:
dependencies.py  ←── imports ──  services/user.py (pure business logic)
```

**Fix:** Move `get_current_user` to `app/dependencies.py` or a new `app/auth/dependencies.py`.

```python
# ✅ CORRECT — in app/dependencies.py
from app.auth.jwt_handler import decode_jwt_token

def get_current_user(
    token: Annotated[str, Depends(oauth_scheme)],
    db: Session = Depends(get_db)
) -> UserModel:
    payload = decode_jwt_token(token)
    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload.")
    user = user_repository.get_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user
```

---

### 2.2 `utc_now()` Does NOT Return UTC
**File:** [`app/core/config.py`](file:///c:/Coding/PYTHON/Task%20Management/app/core/config.py) — Lines 9–14

**Problem:** The function is named `utc_now()` but returns **Nepal local time (UTC+5:45)**. This is a critical naming lie and a logic error. Every timestamp stored in the database (`created_at`, `updated_at`) will be in Nepal time, not UTC. If the app ever moves to a different server timezone, all comparisons and JWT `exp` checks will be wrong.

```python
# ❌ WRONG — named utc_now but returns Nepal time
timezone_nepal = timezone(timedelta(hours=5, minutes=45), name="Asia/Kathmandu")

def utc_now() -> datetime:
    return datetime.now(timezone_nepal)  # this is NOT UTC
```

**Fix:** Always store UTC in the database. If you need to display Nepal time, convert at the presentation layer.

```python
# ✅ CORRECT
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)   # true UTC, timezone-aware
```

---

### 2.3 `dataclass` Used Instead of `pydantic-settings`
**File:** [`app/core/config.py`](file:///c:/Coding/PYTHON/Task%20Management/app/core/config.py)

**Problem:** Using `@dataclass(frozen=True)` with `os.getenv()` is a manual, fragile reimplementation of what `pydantic-settings` does natively — with type validation, `.env` file loading, and proper error messages when a required variable is missing. Also, JWT settings are missing from config entirely.

```python
# ❌ WRONG — manual, no validation, missing JWT config
@dataclass(frozen=True)
class Settings:
    app_name: str
    debug: bool
    database_url: str
```

```python
# ✅ CORRECT
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Task Management API"
    debug: bool = False
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
```

---

### 2.4 `MemberRemovalError` Has No Exception Handler
**File:** [`app/main.py`](file:///c:/Coding/PYTHON/Task%20Management/app/main.py)

**Problem:** `MemberRemovalError` is raised in `services/project.py` but has no registered exception handler in `main.py`. It will bubble up as an unhandled `500 Internal Server Error` to the client with a raw Python traceback, leaking internal details.

```python
# ❌ WRONG — missing handler for MemberRemovalError
# main.py only registers MemberAdditionError, but MemberRemovalError is also raised
```

**Fix:** Register the missing handler, or better — use a generic `AppBaseException` handler:

```python
# ✅ CORRECT — single handler covers all custom exceptions
from app.core.exceptions import AppBaseException

@api.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    status_map = {
        UserAlreadyExistsException: status.HTTP_409_CONFLICT,
        UserNotFoundException: status.HTTP_404_NOT_FOUND,
        TaskNotFoundException: status.HTTP_404_NOT_FOUND,
        ProjectNotFoundException: status.HTTP_404_NOT_FOUND,
        MemberAdditionError: status.HTTP_409_CONFLICT,
        MemberRemovalError: status.HTTP_400_BAD_REQUEST,
    }
    status_code = status_map.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})
```

---

### 2.5 Two Conflicting, Unintegrated Permission Systems
**Files:** [`app/models/authorization.py`](file:///c:/Coding/PYTHON/Task%20Management/app/models/authorization.py) · [`app/authorization/permissions.py`](file:///c:/Coding/PYTHON/Task%20Management/app/authorization/permissions.py)

**Problem:** The system has **two separate, disconnected authorization mechanisms**:
- A **database-backed RBAC** (Role → Permission → RolePermission tables) used for global checks.
- A **hardcoded dictionary** `PROJECT_ROLE_PERMISSIONS` for project-level checks.

These are never integrated. The DB RBAC is seeded but the project-level permission check completely bypasses it. This makes the authorization system impossible to manage or audit consistently.

**Fix (Design):** Decide on one system. For project-level roles, either:
- **Option A:** Extend the DB model with a `ProjectRole` concept linked to `ProjectMember`.
- **Option B (simpler):** Keep the hardcoded dict but document explicitly that it governs project-scope actions only. Either way — consolidate, document, and be consistent.

---

### 2.6 `asynccontextmanager` Imported but Never Used
**File:** [`app/main.py`](file:///c:/Coding/PYTHON/Task%20Management/app/main.py) — Line 1

**Problem:** `from contextlib import asynccontextmanager` is imported but never used. This suggests the `lifespan` startup pattern was intended but never implemented.

**Fix:** Implement the lifespan for startup validation (DB connectivity check, RBAC seeding on first run, etc.):

```python
# ✅ CORRECT
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: validate DB connection, warm caches
    logger.info("Application startup: validating database connection...")
    yield
    # shutdown: clean up resources
    logger.info("Application shutdown.")

api = FastAPI(title=settings.app_name, lifespan=lifespan)
```

---

## 3. 🟡 Database Design Problems

---

### 3.1 No Connection Pool Configuration
**File:** [`app/db/database.py`](file:///c:/Coding/PYTHON/Task%20Management/app/db/database.py) — Line 8

**Problem:** `create_engine(settings.database_url, echo=False)` uses SQLAlchemy's defaults (pool_size=5, max_overflow=10). Under any real traffic this will exhaust connections. Also missing `pool_pre_ping=True` which is essential for handling stale connections.

```python
# ❌ WRONG — no pool configuration
engine = create_engine(settings.database_url, echo=False)
```

```python
# ✅ CORRECT
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,  # recycle connections every 30 min
    pool_pre_ping=True, # test connections before use (prevents stale conn errors)
)
```

---

### 3.2 `Task.project_id` Has Wrong Python Type Annotation
**File:** [`app/models/task.py`](file:///c:/Coding/PYTHON/Task%20Management/app/models/task.py) — Line 20

**Problem:** `Mapped[UUID]` uses `UUID` which is the **SQLAlchemy column type** (imported from `sqlalchemy`), not the Python `uuid.UUID`. The `Mapped[]` annotation should contain the **Python type**, not the SQLAlchemy type.

```python
# ❌ WRONG — UUID here is sqlalchemy.UUID (a column type), not uuid.UUID (Python type)
from sqlalchemy import ..., UUID
project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ...)
```

```python
# ✅ CORRECT — Mapped[] takes the Python type; mapped_column() takes the SA column type
import uuid
project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ...)
```

---

### 3.3 `User.role_id` Non-Optional Type but Nullable Column
**File:** [`app/models/user.py`](file:///c:/Coding/PYTHON/Task%20Management/app/models/user.py) — Line 31

**Problem:** The column is `nullable=True` with `ondelete="SET NULL"`, meaning the DB can set it to NULL. But the Python type annotation is `Mapped[uuid.UUID]` (non-optional), which is a lie to the type checker. SQLAlchemy ORM will return `None` here but mypy/pyright will not flag it.

```python
# ❌ WRONG — annotation says non-nullable, column says nullable
role_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
)
```

```python
# ✅ CORRECT
role_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
)
```

---

### 3.4 Inconsistent ORM Query Styles (Legacy vs Modern)
**Files:** Multiple service files

**Problem:** The codebase mixes the **legacy `db.query()` API** (SQLAlchemy 1.x style) with the modern **`select()` Core API** (SQLAlchemy 2.x style). This inconsistency creates cognitive load and makes future migration harder.

```python
# ❌ WRONG — legacy 1.x style
role = db.query(Role).filter(Role.name == "user").first()
users = db.query(UserModel).filter(UserModel.username == username).first()

# ✅ CORRECT — modern 2.x style (consistent with select() usage elsewhere)
from sqlalchemy import select
role = db.scalar(select(Role).where(Role.name == "user"))
user = db.scalar(select(UserModel).where(UserModel.username == username))
```

**Rule:** Pick one style for the entire project. Use the modern `select()` style everywhere.

---

### 3.5 N+1 Query in Permission Check (Lazy Loading)
**File:** [`app/authorization/permissions.py`](file:///c:/Coding/PYTHON/Task%20Management/app/authorization/permissions.py) — Lines 37–41

**Problem:** `require_permission` accesses `current_user.role.permissions`. With default lazy loading:
1. Query 1: Load `current_user` (already done by `get_current_user`)
2. Query 2: Lazy-load `current_user.role`
3. Query 3: Lazy-load `role.permissions`

This is **3 queries per request** for every protected endpoint.

**Fix:** Use `selectinload` when fetching the current user:

```python
# ✅ CORRECT — in get_current_user, eager-load relationships needed downstream
from sqlalchemy.orm import selectinload

stmt = (
    select(UserModel)
    .where(UserModel.username == username)
    .options(selectinload(UserModel.role).selectinload(Role.permissions))
)
user = db.scalar(stmt)
```

---

### 3.6 Double DB Query: Task Count Computed Separately
**File:** [`app/routers/projects.py`](file:///c:/Coding/PYTHON/Task%20Management/app/routers/projects.py) — Lines 74–77

**Problem:** Two separate database round-trips to get the same data.

```python
# ❌ WRONG — 2 queries: one for tasks, one for count
db_tasks = list_tasks_from_db(project_id, db)
count = get_task_count_from_db(project_id, db)   # hits DB again, also re-checks project existence
```

```python
# ✅ CORRECT — count is already known from the first query
db_tasks = list_tasks_from_db(project_id, db)
return TaskListResponse(tasks=[TaskRead.model_validate(t) for t in db_tasks], count=len(db_tasks))
```

---

### 3.7 No DB Indexes on Foreign Keys in `ProjectMember`
**File:** [`app/models/project.py`](file:///c:/Coding/PYTHON/Task%20Management/app/models/project.py) — Lines 46–49

**Problem:** `project_id` and `user_id` in `ProjectMember` are part of the composite primary key, so they're indexed. But the `role` column and `joined_at` column — which are frequently filtered/ordered — have no indexes.

More critically, **`Task.assigned_to` has `index=True`** but `ProjectMember` composite key columns are only indexed together (as PK). Queries filtering only on `user_id` (e.g., "all projects a user is a member of") cannot use the PK index efficiently.

**Fix:** Add an explicit index on `ProjectMember.user_id`:

```python
# ✅ in ProjectMember
user_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("users.id", ondelete="CASCADE"),
    primary_key=True,
    index=True,   # ← explicit index for user-centric queries
)
```

---

## 4. 🔵 API Design Violations

---

### 4.1 Critical Route Ordering Bug — `/me` Never Reachable
**File:** [`app/routers/users.py`](file:///c:/Coding/PYTHON/Task%20Management/app/routers/users.py) — Lines 33–61

**Problem:** `protected_router` registers routes in this order:
1. `GET /list`
2. `GET /{user_id}` ← **path parameter, matches anything**
3. `GET /me`

FastAPI matches routes in registration order. When a client requests `GET /users/me`, FastAPI matches it to `GET /{user_id}` first, tries to parse `"me"` as a `uuid.UUID`, and returns a `422 Unprocessable Entity`. The `/me` endpoint is **completely unreachable**.

```python
# ❌ WRONG — /{user_id} will consume /me before it is ever checked
@protected_router.get("/list", ...)
@protected_router.get("/{user_id}", ...)   # ← swallows /me
@protected_router.get("/me", ...)          # ← dead route
```

```python
# ✅ CORRECT — specific routes must come BEFORE parameterized routes
@protected_router.get("/me", response_model=UserRead)
async def read_users_me(current_user: CurrentUser):
    return current_user

@protected_router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, ...):
    ...
```

---

### 4.2 `GET /users/list` Violates REST Conventions
**File:** [`app/routers/users.py`](file:///c:/Coding/PYTHON/Task%20Management/app/routers/users.py) — Line 33

**Problem:** The list endpoint is `GET /users/list`. REST convention is `GET /users` (the collection itself). Using a `/list` suffix is an RPC-style pattern, not RESTful.

```
❌ WRONG:   GET /users/list
✅ CORRECT: GET /users
```

---

### 4.3 No Pagination on Any List Endpoint
**Files:** All three routers

**Problem:** `list_users`, `list_projects`, and `list_tasks` all return unbounded lists. As data grows, this will cause:
- Enormous response payloads
- Full table scans on every request
- Out-of-memory crashes

```python
# ✅ CORRECT — add pagination parameters to all list endpoints
from fastapi import Query

@project_router.get("", response_model=PaginatedResponse[ProjectRead])
def list_projects(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    projects, total = list_projects_from_db(db, current_user, offset=offset, limit=page_size)
    return PaginatedResponse(items=projects, total=total, page=page, page_size=page_size)
```

---

### 4.4 No API Versioning
**File:** [`app/main.py`](file:///c:/Coding/PYTHON/Task%20Management/app/main.py) — Line 22

**Problem:** All routes are at root level (`/users`, `/projects`, `/tasks`). No version prefix. Any breaking API change will immediately break all clients with no migration path.

```python
# ❌ WRONG
api.include_router(user_router)    # /users/...

# ✅ CORRECT — URI versioning
api.include_router(user_router, prefix="/api/v1")     # /api/v1/users/...
api.include_router(project_router, prefix="/api/v1")  # /api/v1/projects/...
api.include_router(task_router, prefix="/api/v1")     # /api/v1/tasks/...
```

---

### 4.5 DELETE Request with a Request Body
**File:** [`app/routers/projects.py`](file:///c:/Coding/PYTHON/Task%20Management/app/routers/projects.py) — Lines 93–97

**Problem:** `DELETE /projects/{project_id}/members` accepts `member_in: ProjectMemberAdd` as a **request body**. The HTTP spec discourages bodies on DELETE requests, and many proxies/load balancers strip them. Use a path or query parameter instead.

```
❌ WRONG:   DELETE /projects/{project_id}/members   + body: {"user_id": "..."}
✅ CORRECT: DELETE /projects/{project_id}/members/{user_id}
```

---

### 4.6 Wrong HTTP Semantics on Member Addition Conflict
**File:** [`app/services/project.py`](file:///c:/Coding/PYTHON/Task%20Management/app/services/project.py) — Lines 96–98

**Problem:** When a user is already a project member, the service silently returns the existing membership and the router returns `201 Created`. This is incorrect — `201` means a new resource was created. A no-op on an already-existing member should return `200 OK` or raise `409 Conflict`.

```python
# ❌ WRONG — silent no-op masquerading as a creation
existing_membership = db.get(ProjectMemberModel, (project.id, user.id))
if existing_membership:
    return existing_membership  # router will still return 201 Created
```

```python
# ✅ CORRECT
if existing_membership:
    raise MemberAdditionError(
        f"User '{member_in.user_id}' is already a member of this project."
    )
```

---

### 4.7 Wrong Exception Type for Authorization Failure
**File:** [`app/services/project.py`](file:///c:/Coding/PYTHON/Task%20Management/app/services/project.py) — Lines 79–80

**Problem:** When a non-owner tries to delete a project, the service raises `ProjectNotFoundException` (which maps to 404). The correct response is 403 Forbidden. Returning 404 for authorization failures leaks information (the resource exists but you can't see it) and is semantically incorrect when the permission layer has already confirmed the project exists.

```python
# ❌ WRONG — authorization failure reported as not-found
if project.owner_id != current_user.id:
    raise ProjectNotFoundException(...)  # wrong! this is a 403, not 404
```

```python
# ✅ CORRECT — use a dedicated exception or let the permission layer handle this
class PermissionDeniedException(AppBaseException):
    """Raised when a user lacks permission for an action."""
    pass

if project.owner_id != current_user.id:
    raise PermissionDeniedException("Only the project owner can delete this project.")
```

---

### 4.8 `assign_task_to_user` Catches ALL Exceptions Blindly
**File:** [`app/routers/tasks.py`](file:///c:/Coding/PYTHON/Task%20Management/app/routers/tasks.py) — Lines 71–74

**Problem:** `except Exception as e` swallows all exceptions — including database errors, internal bugs, and unexpected failures — and reports them all as `404 Not Found`. This hides bugs, makes debugging impossible, and reports wrong status codes.

```python
# ❌ WRONG — swallows everything as 404
try:
    return assign_task_to_user_in_db(task_id, user_id, db)
except Exception as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

```python
# ✅ CORRECT — let the global exception handlers work; only catch what you intend
# The AppBaseException handler in main.py will handle TaskNotFoundException etc.
return assign_task_to_user_in_db(task_id, user_id, db)
```

---

## 5. 🟢 Code Quality Issues

---

### 5.1 `print()` Used Instead of `logging`
**Files:** [`app/main.py`](file:///c:/Coding/PYTHON/Task%20Management/app/main.py) L33 · [`app/services/task.py`](file:///c:/Coding/PYTHON/Task%20Management/app/services/task.py) L23

**Problem:** `print()` is not structured, not filterable by log level, and disappears in production environments. `print(task_db)` in a service function is a debug statement that should never be in committed code.

```python
# ❌ WRONG
print(f"Database connection error: {exc}")
print(task_db)

# ✅ CORRECT — configure logging once, use everywhere
import logging
logger = logging.getLogger(__name__)

logger.error("Database connection error", exc_info=exc)
logger.debug("Task created: %s", task_db.id)
```

---

### 5.2 `import jwt` in `security.py` Is Unused
**File:** [`app/auth/security.py`](file:///c:/Coding/PYTHON/Task%20Management/app/auth/security.py) — Line 1

**Problem:** `import jwt` is at the top of `security.py` but `jwt` is never used in this file. Dead imports increase cognitive load and confuse future readers.

```python
# ❌ WRONG
import jwt                  # ← unused import
from pwdlib import PasswordHash
```

---

### 5.3 Expensive Hash Computed at Module Import Time
**File:** [`app/auth/security.py`](file:///c:/Coding/PYTHON/Task%20Management/app/auth/security.py) — Line 7

**Problem:** `DUMMY_HASH = password_hash.hash("dummypassword")` runs a full Argon2/bcrypt computation every time the module is imported. This adds significant startup latency (hundreds of milliseconds) for no benefit, since `DUMMY_HASH` is never actually used in the current codebase.

```python
# ❌ WRONG — expensive computation at import time
DUMMY_HASH = password_hash.hash("dummypassword")
```

Remove this line entirely unless you implement constant-time dummy verification for timing attack prevention, in which case it should be computed lazily.

---

### 5.4 `get_task_from_db` Inconsistently Does Not Raise on Missing Task
**File:** [`app/services/task.py`](file:///c:/Coding/PYTHON/Task%20Management/app/services/task.py) — Lines 49–51

**Problem:** Every other `get_X_from_db` function (`get_user_from_db`, `get_project_from_db`) raises a `NotFoundException` when the entity is not found. But `get_task_from_db` returns `None`, forcing every caller to do its own null-check and manually raise HTTP exceptions — **breaking the service-layer contract**.

```python
# ❌ WRONG — inconsistent: returns None instead of raising
def get_task_from_db(task_id: uuid.UUID, db: Session) -> Task | None:
    return db.get(Task, task_id)

# Every caller must then do:
task = get_task_from_db(task_id, db)
if not task:
    raise HTTPException(404, "Task not found")  # HTTP exception in router — acceptable
```

```python
# ✅ CORRECT — consistent with other service functions
def get_task_from_db(task_id: uuid.UUID, db: Session) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise TaskNotFoundException(f"Task with ID '{task_id}' not found.")
    return task
```

---

### 5.5 `assign_task_to_user_in_db` Raises Wrong Exception for Membership Failure
**File:** [`app/services/task.py`](file:///c:/Coding/PYTHON/Task%20Management/app/services/task.py) — Lines 82–83

**Problem:** When a user is not a member of the project, the function raises `UserNotFoundException`. The user clearly exists — the issue is **authorization/membership**, not a missing user. This maps to a misleading error message and the wrong HTTP status code.

```python
# ❌ WRONG — user exists, but wrong exception raised
if not _check_project_membership(db, project_id, user_id):
    raise UserNotFoundException(f"User ... is not a member of the project.")
```

```python
# ✅ CORRECT — use a semantically correct exception
raise PermissionDeniedException(
    f"User '{user_id}' is not a member of project '{project_id}'."
)
```

---

### 5.6 `_check_project_membership` Naming Convention Violated
**File:** [`app/services/project.py`](file:///c:/Coding/PYTHON/Task%20Management/app/services/project.py) — Line 139

**Problem:** A leading underscore `_` in Python signals a private/internal function. But `_check_project_membership` is imported and used in `services/task.py`, making it effectively public. The naming is misleading.

```python
# ❌ WRONG — private convention but used externally
from app.services.project import _check_project_membership
```

```python
# ✅ CORRECT — rename to public and move to a shared utility if cross-module
def check_project_membership(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    return db.get(ProjectMemberModel, (project_id, user_id)) is not None
```

---

### 5.7 Inconsistent `db` Parameter Position
**Files:** `services/task.py` vs all other service files

**Problem:** All user and project service functions follow `(db: Session, ...)` convention. But task service functions use `(task_id, db)` — `db` last. This inconsistency creates confusion when calling functions and means you can't apply the same calling patterns uniformly.

```python
# ❌ WRONG — db is last in task services
def list_tasks_from_db(project_id: uuid.UUID, db: Session) -> list[Task]:
def get_task_from_db(task_id: uuid.UUID, db: Session) -> Task | None:

# ✅ CORRECT — db always first, consistent with user/project services
def list_tasks_from_db(db: Session, project_id: uuid.UUID) -> list[Task]:
def get_task_from_db(db: Session, task_id: uuid.UUID) -> Task:
```

---

### 5.8 No Password Strength Validation
**File:** [`app/schemas/user.py`](file:///c:/Coding/PYTHON/Task%20Management/app/schemas/user.py) — Line 12

**Problem:** `password: str` has zero validation. Users can register with `password=""` or `password="a"`.

```python
# ✅ CORRECT — enforce minimum security requirements
from pydantic import field_validator

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v
```

---

### 5.9 `ProjectMember` Schema in Wrong File
**File:** [`app/schemas/user.py`](file:///c:/Coding/PYTHON/Task%20Management/app/schemas/user.py) — Lines 23–24

**Problem:** `class ProjectMember(BaseModel): members: list[UserRead]` is defined inside `schemas/user.py`. This is a project-domain schema and belongs in `schemas/project.py`. It also shadows the ORM model `ProjectMember` from `models/project.py`, which can cause confusion on imports.

---

### 5.10 `create_user_in_db` Has Unhandled `role_id` Bug
**File:** [`app/services/user.py`](file:///c:/Coding/PYTHON/Task%20Management/app/services/user.py) — Lines 22–33

**Problem:** If `user_in.role_id` is `None` AND there is no "user" role in the DB (e.g., RBAC hasn't been seeded yet), `role_id` is never assigned and the function proceeds to create a `UserModel(role_id=role_id)` where `role_id` is an **unbound local variable**. This raises `UnboundLocalError`.

```python
# ❌ WRONG — role_id may be unbound
if user_in.role_id:
    role_id = user_in.role_id
else:
    role = db.query(Role).filter(Role.name == "user").first()
    if role:
        role_id = role.id   # only set if role exists!
# If neither branch sets role_id, the next line crashes:
user_db = UserModel(..., role_id=role_id)  # UnboundLocalError
```

```python
# ✅ CORRECT
role = db.scalar(select(Role).where(Role.name == "user"))
role_id: uuid.UUID | None = role.id if role else None

user_db = UserModel(
    username=user_in.username,
    hashed_password=get_password_hash(user_in.password),
    role_id=role_id,
)
```

---

## 6. ⚪ Project Structure Gaps

---

### 6.1 `pyproject.toml` Is Empty
**File:** [`pyproject.toml`](file:///c:/Coding/PYTHON/Task%20Management/pyproject.toml)

**Problem:** The file has only 2 bytes — it contains no project metadata, no tool configuration. This means `ruff`, `mypy`, `pytest`, and `black` all have no project-specific configuration.

```toml
# ✅ CORRECT — minimal pyproject.toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["app"]
omit = ["app/scripts/*"]
```

---

### 6.2 No Tests
**Problem:** Zero test files exist. This is the most significant long-term risk. No test coverage means every refactor is a potential silent regression.

**Minimum required test structure:**
```
tests/
  conftest.py          ← shared fixtures (test DB, test client, mock user)
  test_auth.py         ← register, login, JWT validation
  test_users.py        ← CRUD + permission checks
  test_projects.py     ← CRUD + membership + permission checks
  test_tasks.py        ← CRUD + assignment + permission checks
  test_permissions.py  ← role permission enforcement
```

---

### 6.3 Missing `__init__.py` in Several Packages
**Directories:** `app/auth/`, `app/authorization/`, `app/core/`, `app/services/`

**Problem:** These directories lack `__init__.py`, making them implicit namespace packages. This is inconsistent with `app/models/`, `app/routers/`, and `app/schemas/` which all have `__init__.py`. The inconsistency is confusing and can cause subtle import resolution issues.

---

### 6.4 No `.env.example` File
**Problem:** The `.env` file contains real credentials (DB password visible). There is no `.env.example` to guide new developers on required variables. New contributors either guess required vars or inadvertently commit real credentials.

```bash
# ✅ .env.example — commit this, not .env
APP_NAME=Task Management API
DEBUG=false
DATABASE_URL=postgresql://user:password@localhost:5432/task_management
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

### 6.5 `.env` Should Be in `.gitignore`
**File:** [`.gitignore`](file:///c:/Coding/PYTHON/Task%20Management/.gitignore)

**Problem:** Verify that `.env` is in `.gitignore`. The `.env` file currently contains the database password (`suman123`). If this were committed to a public repository, the credentials would be permanently exposed in Git history even after deletion.

---

## 7. ✅ FastAPI Best Practices Reference

A consolidated checklist of industry-standard practices for production FastAPI services:

### Security
| Practice | Status |
|---|---|
| JWT secret loaded from env var only | ❌ Fix required |
| Refresh token mechanism | ❌ Missing |
| `role_id` not client-assignable at registration | ❌ Fix required |
| Password minimum length + complexity | ❌ Fix required |
| `HTTPS_ONLY` enforced in production | ❌ Not configured |
| Rate limiting on auth endpoints | ❌ Missing |
| Admin password via `getpass` | ❌ Fix required |

### Architecture
| Practice | Status |
|---|---|
| Service layer is HTTP-agnostic | ❌ `get_current_user` in services |
| Settings via `pydantic-settings` `BaseSettings` | ❌ Custom dataclass used |
| All exceptions handled (no silent 500s) | ❌ `MemberRemovalError` unhandled |
| Lifespan used for startup/shutdown hooks | ❌ Import unused |
| Single, consistent permission system | ❌ Two conflicting systems |

### Database
| Practice | Status |
|---|---|
| Connection pool configured | ❌ Defaults only |
| `pool_pre_ping=True` | ❌ Missing |
| Consistent modern `select()` style | ❌ Mixed legacy/modern |
| Eager loading for permission checks | ❌ N+1 on every request |
| Correct nullable type annotations | ❌ `User.role_id` wrong |
| Indexes on frequently queried FKs | ⚠️ Partially done |

### API Design
| Practice | Status |
|---|---|
| URI versioning (`/api/v1/`) | ❌ Missing |
| Pagination on all list endpoints | ❌ Missing |
| `GET /users` not `GET /users/list` | ❌ Wrong convention |
| `/me` route before `/{user_id}` | ❌ Route ordering bug |
| No request body on DELETE | ❌ Members endpoint |
| Correct HTTP status codes | ⚠️ Several wrong |

### Code Quality
| Practice | Status |
|---|---|
| `logging` module (no `print()`) | ❌ `print()` in production code |
| No dead imports | ❌ `import jwt` unused |
| Consistent `db` param position | ❌ Inconsistent in tasks |
| All service functions raise on not-found | ❌ `get_task_from_db` returns None |
| No `except Exception` that swallows bugs | ❌ `assign_task` does this |
| Correct exception types for each scenario | ❌ Several semantic mismatches |

### Project Structure
| Practice | Status |
|---|---|
| `pyproject.toml` with tool config | ❌ Empty |
| Test suite with `pytest-anyio` | ❌ Zero tests |
| `.env.example` committed | ❌ Missing |
| `.env` in `.gitignore` | ⚠️ Verify |
| Consistent `__init__.py` across packages | ❌ Missing in several |

---

## 8. 📊 Final Scorecard

| Category | Score | Critical Issues |
|---|---|---|
| 🔴 Security | **2/10** | Hardcoded JWT secret, role elevation at register, plaintext password input |
| 🟠 Architecture | **4/10** | Service/HTTP boundary violated, UTC naming lie, missing exception handler |
| 🟡 Database | **5/10** | No pool config, type annotation bugs, N+1 queries, inconsistent query style |
| 🔵 API Design | **4/10** | Dead `/me` route, no versioning, no pagination, wrong status codes |
| 🟢 Code Quality | **5/10** | `print()` debugging, unbound variable bug, inconsistent conventions |
| ⚪ Structure | **3/10** | No tests, empty pyproject.toml, no `.env.example` |
| **Overall** | **3.8/10** | Not production-ready |

---

> [!IMPORTANT]
> **Prioritized Fix Order:**
> 1. 🔴 Move `JWT_SECRET_KEY` to environment variable immediately
> 2. 🔴 Remove `role_id` from `UserCreate` schema
> 3. 🔴 Register `MemberRemovalError` handler (or use generic `AppBaseException` handler)
> 4. 🔴 Fix the `/me` route ordering bug — it's completely broken right now
> 5. 🟠 Fix `utc_now()` to return actual UTC
> 6. 🟠 Move `get_current_user` to `dependencies.py`
> 7. 🟠 Switch `Settings` to `pydantic-settings BaseSettings`
> 8. 🟡 Fix `User.role_id` and `Task.project_id` type annotations
> 9. 🟡 Fix the `UnboundLocalError` bug in `create_user_in_db`
> 10. 🟢 Write tests

---

*Review completed by: Antigravity Lead Engineer Review System*
*Date: 2026-06-22*
*Codebase: Task Management API — FastAPI + SQLAlchemy + PostgreSQL*
