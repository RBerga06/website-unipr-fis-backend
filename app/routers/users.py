#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`APIRouter`s for account management."""
from fastapi import APIRouter
from ..access.auth import Me, MeAdmin
from ..access.users import User, del_user, get_all_users, get_user_unsafe, set_user


router = APIRouter(prefix="/users")


@router.get("/all")
async def get_all() -> list[User]:
    return await get_all_users()


@router.get("/me")
async def me_get(me: Me) -> User:
    return me

@router.post("/me/del")
async def me_del(me: Me) -> None:
    await del_user(me.username)


@router.get("/@{username}")
async def user_get(username: str) -> User:
    return await get_user_unsafe(username)

@router.post("/@{username}/del")
async def user_del(username: str, me: MeAdmin) -> None:
    await del_user(username)

@router.post("/@{username}/set")
async def user_set(username: str, admin: bool) -> User:
    await set_user(username, admin)
    return await get_user_unsafe(username)


__all__ = ["router"]
