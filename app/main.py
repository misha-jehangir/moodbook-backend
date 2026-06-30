from fastapi import FastAPI, Depends
from app.config import settings
from app.auth.firebase_auth import get_current_user
from app.routers import chat

app = FastAPI(
    title="MoodBook AI Companion API",
    description="Backend API serving the AI wellness companion and deterministic stats tools.",
    version="1.0.0"
)

# Register routers
app.include_router(chat.router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "moodbook-backend",
        "config_loaded": settings.is_valid
    }

@app.get("/test-auth")
async def test_auth(user: dict = Depends(get_current_user)):
    return {
        "status": "authenticated",
        "uid": user.get("uid"),
        "email": user.get("email"),
        "name": user.get("name")
    }
