#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`APIRouter`s for account management."""
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from ..access.auth import MeMaybeNotVerified, MeAdmin, ERR_UNAUTHORIZED, Token, hash_password, login
from ..access.users import User, get_all_users, get_passcode, set_passcode


router = APIRouter(prefix="/users")


@router.post("/verify")
async def verify(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> User:
    if form.password != get_passcode():
        raise ERR_UNAUTHORIZED
    user = User.named(form.username)
    if user is None:
        raise ERR_UNAUTHORIZED
    user.verified = True
    user.save(new=False)
    return user


@router.get("/all")
async def get_all() -> list[User]:
    return await get_all_users()


# TODO: Talk to frontend devs about the passcode parameter:
#   how are we going to interact with the API functions that accept a passcode?

@router.get("/passcode")
async def admin_get_passcode(me: MeAdmin) -> str:
    return get_passcode()

@router.post("/passcode/set")
async def admin_set_passcode(me: MeAdmin, form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> None:
    if (form.username != "passcode"):
        raise ERR_UNAUTHORIZED
    set_passcode(form.password)
    for user in await get_all_users():
        if user.admin:
            continue
        user.verified = False
        user.save()


@router.get("/me")
async def me_get(me: MeMaybeNotVerified) -> User:
    return me

@router.get("/me/edit")
async def me_set(me: MeMaybeNotVerified, online: bool | None = None) -> User:
    return await user_edit(me, me.username, online=online)

@router.post("/me/del")
async def me_del(me: MeMaybeNotVerified) -> None:
    me.delete()


@router.get("/@{username}")
async def user_get(username: str) -> User:
    return User.named(username, strict=True)

@router.get("/@{username}/edit")
async def user_edit(me: MeAdmin, username: str, banned: bool | None = None, online: bool | None = None) -> User:
    user = User.named(username, strict=True)
    if banned is not None:
        user.banned = banned
    if online is not None:
        user.online = online
    return user.save(new=False)

@router.post("/@{username}/del")
async def user_del(me: MeAdmin, username: str) -> None:
    User.named(username, strict=True).delete()

# @router.post("/@{username}/set")
# async def user_set(username: str, user: User, me: MeAdmin) -> User:
#     if user.username != username:
#         raise HTTPException(
#             status.HTTP_409_CONFLICT,
#             detail="Username does not match.",
#         )
#     return user.save(new=False)

@router.post("/@{username}/rename")
async def user_rename(username: str, new: str, me: MeAdmin) -> User:
    return User.named(username, strict=True).rename(new)


@router.post("/login/token")
async def login_token(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    return login(form)


@router.post("/create/token")
async def create_token(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = User(username=form.username, hashed_password=hash_password(form.password))
    user.save(new=True)
    print("before:", User.named(form.username))
    return login(form)


@router.post("/me/chpwd/token")
async def me_chpwd_token(me: MeMaybeNotVerified, form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    if form.username != me.username:
        raise ERR_UNAUTHORIZED
    me.hashed_password = hash_password(form.password)
    me.save(new=False)
    return login(form)


__all__ = ["router"]
