#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`APIRouter`s for account management."""
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from ..access.auth import Me, ERR_UNAUTHORIZED, Token, hash_password, login, me_admin
from ..access.users import User, get_all_users, get_passcode, set_passcode


router = APIRouter(prefix="/users")


@router.post("/me/verify")
async def verify(me: Me, form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> User:
    if (form.username != "passcode") and (form.password != get_passcode()):
        raise ERR_UNAUTHORIZED
    return me

MeVerified = Annotated[User, Depends(verify)]
MeAdmin = Annotated[MeVerified, Depends(me_admin)]


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
        if user.is_admin:
            continue
        user.verified = False
        user.save()


@router.get("/me")
async def me_get(me: Me) -> User:
    return me

# @router.get("/me/set")
# async def me_set(me: Me, user: User) -> User:
#     return await user_set(me.username, user, me)

@router.post("/me/del")
async def me_del(me: Me) -> None:
    me.delete()


@router.get("/@{username}")
async def user_get(username: str) -> User:
    return User.named(username, strict=True)

# @router.post("/@{username}/del")
# async def user_del(username: str, me: MeAdmin) -> None:
#     User.named(username, strict=True).delete()

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
    return await login(form)


@router.post("/create/token")
async def create_token(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = User(username=form.username, hashed_password=hash_password(form.password))
    user.save(new=True)
    return await login(form)


__all__ = ["router"]
