#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pyright: reportMissingModuleSource=false
"""OAuth Authentication."""
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from jose import JWTError, jwt
from .users import User


# TODO: Find a way to remove the plain SECRET_KEY from the source code
# $ openssl rand -hex 32
SECRET_KEY = "7e8ef11c69e68b881b1db5533fb8eab61aac8b77b46939babc051f5598c27ac8"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

ERR_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str


def create_access_token(user: User, /, *, expires_delta: timedelta = timedelta(minutes=TOKEN_EXPIRE_MINUTES)) -> Token:
    data = {"sub": user.username, "exp": datetime.utcnow() + expires_delta}
    return Token(
        access_token=jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM),
        token_type="bearer",
    )


def verify_password(plain: str, hashed: str, /) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


async def me(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise ERR_UNAUTHORIZED
        token_data = TokenData(username=username)
    except JWTError:
        raise ERR_UNAUTHORIZED
    user = User.named(token_data.username)
    if user is None:
        raise ERR_UNAUTHORIZED
    return user

MeMaybeNotVerified = Annotated[User, Depends(me)]

def me_verified(me: MeMaybeNotVerified) -> User:
    if not me:
        raise ERR_UNAUTHORIZED
    return me

Me = Annotated[MeMaybeNotVerified, Depends(me_verified)]

def me_admin(me: Me) -> User:
    if not me.admin:
        raise ERR_UNAUTHORIZED
    return me

MeAdmin = Annotated[Me, Depends(me_admin)]

def authenticate_user(username: str, password: str, /) -> User | None:
    user = User.named(username)
    if user is None:
        return
    if not verify_password(password, user.hashed_password):
        return
    return user

def login(form: OAuth2PasswordRequestForm, /) -> Token:
    user = authenticate_user(form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_access_token(user)


__all__ = ["hash_password", "me", "login"]
