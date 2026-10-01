from fastapi import FastAPI

from app.routers import reports, auth, moderator

app = FastAPI(
    title="WhistleDrop API",
    description="Confidential, anonymous reporting backend. See /docs for interactive Swagger UI.",
    version="1.0.0",
)

app.include_router(reports.router)
app.include_router(auth.router)
app.include_router(moderator.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
