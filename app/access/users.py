#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Users"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class User(BaseModel):
    """A user."""
    username: str
    hashed_password: str
    admin: bool = False


fake_db: dict[str, User] = {}


async def get_user(username: str, /) -> User | None:
    if username in fake_db:
        return fake_db[username]


@router.get("/users/@{username}")
async def get_user_unsafe(username: str) -> User:
    user = await get_user(username)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return user


@router.get("/users/init")
async def init_db():
    from .auth import hash_password
    for user in [
        User(username="rberga06", hashed_password=hash_password("password"), admin=True),
        User(username="madda", hashed_password=hash_password("password"), admin=True),
        User(username="TommyErBono", hashed_password=hash_password("password")),
    ]:
        fake_db[user.username] = user
    return {"result": "Everything ok!"}
