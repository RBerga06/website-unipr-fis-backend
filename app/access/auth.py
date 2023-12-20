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
from .users import User, get_user


# TODO: Find a way to remove the plain SECRET_KEY from the source code
# $ openssl rand -hex 32
SECRET_KEY = "7e8ef11c69e68b881b1db5533fb8eab61aac8b77b46939babc051f5598c27ac8"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

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


def hash_password(password: str, /) -> str:
    return pwd_context.hash(password)


@router.get("/users/me")
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], /) -> User:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise error
        token_data = TokenData(username=username)
    except JWTError:
        raise error
    user = await get_user(token_data.username)
    if user is None:
        raise error
    return user


async def authenticate_user(username: str, password: str, /) -> User | None:
    user = await get_user(username)
    if not user:
        return
    if not verify_password(password, user.hashed_password):
        return
    return user


@router.post("/token")
async def login_for_access_token(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
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


__all__ = ["router", "get_current_user"]
