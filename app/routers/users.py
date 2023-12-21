#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`APIRouter`s for account management."""
from fastapi import APIRouter
from ..access.auth import Me, MeAdmin, ERR_UNAUTHORIZED
from ..access.users import User, add_user, del_user, get_all_users, get_user_unsafe, set_user, get_passcode, set_passcode


router = APIRouter(prefix="/users")


@router.get("/all")
async def get_all() -> list[User]:
    return await get_all_users()


# TODO: Talk to frontend devs about the passcode parameter:
#   how are we going to interact with the API functions that accept a passcode?

@router.get("/passcode")
async def admin_get_passcode(me: MeAdmin) -> str:
    return get_passcode()

@router.post("/passcode/set")
async def admin_set_passcode(me: MeAdmin, passcode: str) -> None:
    set_passcode(passcode)
    for user in await get_all_users():
        if user.username == me.username:
            continue
        user.verified = False
        await add_user(user)


@router.get("/me")
async def me_get(me: Me) -> User:
    return me

@router.post("/me/del")
async def me_del(me: Me) -> None:
    await del_user(me.username)

@router.post("/me/verify")
async def me_verify(me: Me, passcode: str) -> None:
    if passcode != get_passcode():
        raise ERR_UNAUTHORIZED


@router.get("/@{username}")
async def user_get(username: str) -> User:
    return await get_user_unsafe(username)

@router.post("/@{username}/del")
async def user_del(username: str, me: MeAdmin) -> None:
    await del_user(username)

@router.post("/@{username}/set")
async def user_set(username: str, me: MeAdmin, admin: bool) -> User:
    await set_user(username, admin)
    return await get_user_unsafe(username)


__all__ = ["router"]
