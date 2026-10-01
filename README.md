# WhistleDrop — Speak Without Being Seen

A confidential reporting backend built with **FastAPI** + **Supabase (Postgres)**.
Anyone can file a report with no account and no identifying information;
moderators review and resolve reports through an authenticated API.

## 1. How it's built

```
whistledrop/
├── app/
│   ├── main.py            # FastAPI app, mounts the three routers
│   ├── config.py          # env-based settings
│   ├── database.py        # async SQLAlchemy engine/session
│   ├── models.py          # Report, StatusUpdate, Moderator tables
│   ├── schemas.py         # Pydantic request/response models
│   ├── security.py        # case-code + password hashing, JWT
│   ├── deps.py             # get_current_moderator auth dependency
│   └── routers/
│       ├── reports.py     # PUBLIC: submit + track (no auth)
│       ├── auth.py        # moderator login / register
│       └── moderator.py   # moderator: list / view / update reports
├── scripts/seed_moderator.py
├── supabase_schema.sql    # run this in Supabase's SQL editor
├── tests/                 # pytest, no live DB needed
├── requirements.txt
└── .env.example
```

- **FastAPI** serves the HTTP API and auto-generates Swagger docs at `/docs`.
- **Supabase** provides a hosted Postgres database. The backend talks to it
  directly over a normal Postgres connection string using SQLAlchemy's async
  engine (`asyncpg` driver) — this is the most common, most transparent way
  to use Supabase from a Python backend, rather than going through Supabase's
  REST layer.
- **JWT** (via `python-jose`) protects moderator-only endpoints; passwords
  are hashed with **bcrypt** (via `passlib`).

## 2. Setup

### a) Create the Supabase project and schema
1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor → New query**, paste the contents of `supabase_schema.sql`, and run it. This creates the three tables, the two enum types, and enables Row Level Security with no policies (explained below).
3. Go to **Project Settings → Database → Connection string → URI** and copy it.

### b) Configure the app
```bash
cd whistledrop
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Edit `.env`:
- `DATABASE_URL` — paste the Supabase connection string, but change its scheme from `postgresql://` to `postgresql+asyncpg://`.
- `JWT_SECRET` — generate one with `python -c "import secrets; print(secrets.token_hex(32))"`.

### c) Create your first moderator
There's no public sign-up for moderators, so bootstrap one directly:
```bash
python -m scripts.seed_moderator alice "a-strong-password"
```

### d) Run it
```bash
uvicorn app.main:app --reload
```
Interactive docs: `http://127.0.0.1:8000/docs`

### e) Run the tests
```bash
pytest
```
These test the hashing, JWT, and status-transition logic directly and don't need a live database.

## 3. API endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/reports` | none | Submit a new anonymous report; returns a one-time case code |
| POST | `/reports/track` | none (case code) | Look up a report's status and update history |
| POST | `/moderator/login` | none | Exchange username/password for a JWT |
| POST | `/moderator/register` | moderator JWT | Create another moderator account |
| GET | `/moderator/reports` | moderator JWT | List reports, filterable by `category` / `status` |
| GET | `/moderator/reports/{id}` | moderator JWT | View one report in full |
| PATCH | `/moderator/reports/{id}` | moderator JWT | Change status and/or add a status message |
| GET | `/health` | none | Liveness check |

Status workflow enforced server-side: `SUBMITTED → UNDER_REVIEW → RESOLVED / DISMISSED`. `RESOLVED` and `DISMISSED` are terminal; any other transition is rejected with `409 Conflict`.

## 4. How anonymity is maintained

- **Nothing identifying is ever stored.** The `reports` and `status_updates` tables have no reporter ID, email, username, session token, or IP address column — there's simply nowhere in the schema for that data to go.
- **The case code itself isn't stored.** Only its SHA-256 hash is (`case_code_hash`), the same pattern used for passwords. Tracking a report means hashing the submitted code and matching it against that column — even a full database dump doesn't reveal usable case codes.
- **144 bits of randomness.** Case codes come from `secrets.token_urlsafe(18)`, so they can't be guessed or brute-forced.
- **Moderators can't identify reporters** because there is no reporter data in the reports they view — only category, description, and an optional evidence URL supplied by the reporter themselves.
- **Row Level Security is enabled with zero policies** on every table (see `supabase_schema.sql`). That means Supabase's public/anon API key can't touch these tables at all — the only path in is this backend's own direct database connection. It's a second lock behind the API's own auth checks, not a replacement for them.
- **Operational note:** whatever server you deploy this on will, by default, write the client IP to its access logs on every request. That's outside this application's code, but it's worth disabling access logging (or at least IP logging) on your reverse proxy/hosting platform if true anonymity matters end-to-end.

## 5. Example requests

**Submit a report**
```bash
curl -X POST http://127.0.0.1:8000/reports \
  -H "Content-Type: application/json" \
  -d '{"category": "CORRUPTION", "description": "Vendor payments are being approved without any second sign-off.", "evidence_url": "https://example.com/invoice.pdf"}'
```
```json
{
  "case_code": "WD-8pQZ3n...redacted...",
  "status": "SUBMITTED",
  "created_at": "2026-09-27T10:15:00Z",
  "note": "Save this case code now. It is shown only once and cannot be recovered if lost."
}
```

**Track a report**
```bash
curl -X POST http://127.0.0.1:8000/reports/track \
  -H "Content-Type: application/json" \
  -d '{"case_code": "WD-8pQZ3n...redacted..."}'
```
```json
{
  "category": "CORRUPTION",
  "description": "Vendor payments are being approved without any second sign-off.",
  "evidence_url": "https://example.com/invoice.pdf",
  "status": "UNDER_REVIEW",
  "created_at": "2026-09-27T10:15:00Z",
  "updates": [
    {"status": "SUBMITTED", "message": "Report submitted.", "created_at": "2026-09-27T10:15:00Z"},
    {"status": "UNDER_REVIEW", "message": "A finance auditor has been assigned.", "created_at": "2026-09-27T11:02:00Z"}
  ]
}
```
Note there's no moderator name anywhere in that response.

**Moderator login, then update a report**
```bash
curl -X POST http://127.0.0.1:8000/moderator/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "a-strong-password"}'
# -> {"access_token": "...", "token_type": "bearer"}

curl -X PATCH http://127.0.0.1:8000/moderator/reports/<report-id> \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "UNDER_REVIEW", "message": "A finance auditor has been assigned."}'
```

## 6. Assumptions & design decisions

- **Auth: custom JWT instead of Supabase Auth.** Supabase Auth would work too, but a self-contained `moderators` table + JWT keeps the whole flow visible in this codebase rather than split across two systems — easier to learn from and to swap out later.
- **No moderator self-registration.** The first account is created with a CLI script; afterwards, only an already-authenticated moderator can create another. This avoids an open door to creating moderator accounts.
- **Case code shown exactly once.** By design there's no "resend my code" feature — that would require storing something that maps back to a specific reporter to send it to, which defeats the purpose.
- **Terminal states.** Once `RESOLVED` or `DISMISSED`, a report can't be reopened through the API. If you need that, it's a small addition to `ALLOWED_TRANSITIONS` in `app/routers/moderator.py`.
- **Not yet included (natural next steps):** rate limiting on `POST /reports` (to deter spam/abuse), file upload for evidence (currently just a URL string), and audit logging of moderator actions beyond what's already in `status_updates`.
