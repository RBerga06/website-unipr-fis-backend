#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pyright: reportMissingModuleSource=false
"""OAuth Authentication."""
from datetime import datetime, timedelta
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status
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
router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str


def create_access_token(data: dict[str, Any], expires_delta: timedelta, /) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + expires_delta})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain: str, hashed: str, /) -> bool:
    return pwd_context.verify(plain, hashed)


@router.post("/hash-pwd")
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


@router.get("/users/me")
async def get_user_me(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
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


Me = Annotated[User, Depends(get_user_me)]

def me_admin(me: Me, /) -> User:
    if not me.is_admin:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return me

MeAdmin = Annotated[User, Depends(me_admin)]


async def authenticate_user(username: str, password: str, /) -> User | None:
    user = User.named(username)
    if not user:
        return
    if not verify_password(password, user.hashed_password):
        return
    return user


async def login(form: OAuth2PasswordRequestForm, /) -> Token:
    user = await authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(
        access_token=create_access_token(
            {"sub": user.username},
            timedelta(minutes=TOKEN_EXPIRE_MINUTES),
        ),
        token_type="bearer",
    )


__all__ = ["router", "get_user_me"]
