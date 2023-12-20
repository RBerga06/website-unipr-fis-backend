#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from .users import User, add_user, del_user, get_user_unsafe
from .auth import get_current_user

router = APIRouter()


def admin(me: Annotated[User, Depends(get_current_user)], /) -> User:
    if not me.is_admin:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return me


type Admin = Annotated[User, Depends(admin)]


@router.post("/users/new")
async def user_new(me: Admin, user: User):
    await add_user(user)


@router.post("/users/@{username}/edit")
async def user_edit(me: Admin, username: str, is_admin: bool | None = None):
    user = await get_user_unsafe(username)
    if is_admin is not None:
        user.is_admin = is_admin
    await add_user(user)


@router.post("/users/del")
async def user_del(me: Admin, user: User):
    await del_user(user)
