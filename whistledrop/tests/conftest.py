import os

# These tests only exercise pure functions (hashing, JWT, transition
# rules) -- they never touch a real database. Settings still requires
# these env vars to be present at import time, so set harmless
# placeholders if a real .env isn't loaded.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
