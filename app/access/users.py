#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pyright: reportUnknownVariableType=false
"""Users"""
from pathlib import Path
from typing import Annotated
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import Engine, create_engine
from sqlmodel import Field, SQLModel, Session, select


async def startup():
    global db
    db = create_engine(f"sqlite:///{(Path(__file__).parent/"users.sqlite").as_posix()}")
    SQLUser.metadata.create_all(db)
    # Ensure a specific admin's account exists.
    if (await get_user("rberga06")) is None:
        from .auth import hash_password
        await add_user(User(
            username="rberga06",
            hashed_password=hash_password("admin"),
            is_admin=True,
        ))


db: Engine


class User(BaseModel):
    """A user."""
    username: str
    hashed_password: str
    is_admin: bool = False


class SQLUser(SQLModel, table=True):
    """A user in the SQL database."""
    id: Annotated[int | None, Field(primary_key=True)] = None
    username: str
    hashed_password: str
    is_admin: bool = False


def _get_sql_user(session: Session, username: str, /) -> SQLUser | None:
    return session.exec(select(SQLUser).where(SQLUser.username == username)).first()


async def get_user(username: str, /) -> User | None:
    with Session(db) as session:
        sql = _get_sql_user(session, username)
        if sql is not None:
            return User.model_validate(sql, from_attributes=True)


async def get_user_unsafe(username: str) -> User:
    user = await get_user(username)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return user


async def get_all_users() -> list[User]:
    with Session(db) as session:
        return [
            User.model_validate(sql, from_attributes=True)
            for sql in session.exec(select(SQLUser))
        ]


async def rename_user(old_username: str, new_username: str, /) -> None:
    with Session(db) as session:
        sql_user = _get_sql_user(session, old_username)
        if sql_user is None:
            return
        sql_user.username = new_username
        session.add(sql_user)
        session.commit()


async def add_user(user: User, /) -> None:
    with Session(db) as session:
        sql_user = _get_sql_user(session, user.username)
        if sql_user is None:
            # create a new user
            session.add(SQLUser.model_validate(user, from_attributes=True))
        else:
            # update this user
            session.add(SQLUser.model_validate(user, from_attributes=True))
        session.commit()


async def set_user(username: str, is_admin: bool, /) -> None:
    with Session(db) as session:
        sql_user = _get_sql_user(session, username)
        sql_user.is_admin = is_admin
        session.commit()


async def del_user(username: str, /) -> None:
    with Session(db) as session:
        sql_user = _get_sql_user(session, username)
        if sql_user is None:
            return
        session.delete(sql_user)
        session.commit()


__all__ = ["User", "get_user", "get_all_users", "add_user", "set_user", "del_user"]
