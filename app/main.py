from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title="MoodBook AI Companion API",
    description="Backend API serving the AI wellness companion and deterministic stats tools.",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "moodbook-backend",
        "config_loaded": settings.is_valid
    }
