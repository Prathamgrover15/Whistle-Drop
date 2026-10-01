import os
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
