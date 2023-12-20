#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Users"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class User(BaseModel):
    username: str
    hashed_password: str
    admin: bool = False


fake_db = {
    "rberga06":    User(username="rberga06", hashed_password="fakehashed@password", admin=True),
    "madda":       User(username="madda", hashed_password="fakehashed@password", admin=True),
    "TommyErBono": User(username="TommyErBono", hashed_password="fakehashed@password"),
}


@router.get("/users/@{username}")
async def get_user(username: str) -> User | None:
    if username in fake_db:
        return fake_db[username]
