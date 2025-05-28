from fastapi import HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from app.core.config import settings
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


async def get_current_user(token: str = Security(oauth2_scheme)) -> dict:
    """
    Authenticates the current user by verifying the Supabase JWT.
    Returns the Supabase user object if authentication is successful.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print('token',token)
        response = supabase.auth.get_user(token)

        if response is None or response.user is None:
            raise credentials_exception

        logging.info(f"User authenticated: {response.user.email}")
        return response.user.model_dump()
    except Exception as e:
        logging.error(f"Supabase JWT verification error: {e}")
        raise credentials_exception
