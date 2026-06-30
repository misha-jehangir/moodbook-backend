import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")

    @property
    def is_valid(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.FIREBASE_PROJECT_ID)

settings = Settings()
