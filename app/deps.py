from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import TokenData, decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    return decode_access_token(token)


def require_roles(*allowed_roles: str) -> Callable[[TokenData], TokenData]:
    normalized_roles = {role.strip().lower() for role in allowed_roles}

    def dependency(user: TokenData = Depends(get_current_user)) -> TokenData:
        user_roles = {role.strip().lower() for role in user.roles}
        if not user_roles.intersection(normalized_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action.",
            )
        return user

    return dependency
