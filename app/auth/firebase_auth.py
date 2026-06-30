from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
import os

# Initialize HTTPBearer security scheme
security = HTTPBearer()

def initialize_firebase():
    """
    Ensures the Firebase Admin SDK is initialized exactly once.
    Checks for service-account.json locally first.
    """
    try:
        firebase_admin.get_app()
    except ValueError:
        # App is not initialized yet.
        cred_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "service-account.json"
        )
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Fallback to default application credentials (GCP environment)
            firebase_admin.initialize_app()

# Initialize Firebase Admin on import
initialize_firebase()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency that parses the Bearer token from the Authorization header,
    verifies it against Firebase Auth, and returns the decoded token claims.
    Raises 401 Unauthorized if the token is invalid or expired.
    """
    token = credentials.credentials
    try:
        # verify_id_token validates signature, expiration, and target project match
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
