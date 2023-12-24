#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pyright: reportUnknownVariableType=false
"""Users"""
from pathlib import Path
from typing import Annotated, Literal, Self, overload
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import Engine, create_engine
from sqlmodel import Field, SQLModel, Session, select


PASSCODE_FILE = (Path(__file__).parent/"passcode.txt").resolve()


async def startup():
    global db, server_passcode
    # Read global passcode
    if PASSCODE_FILE.exists():
        server_passcode = PASSCODE_FILE.read_text().strip().splitlines()[0]
    else:
        server_passcode = "La sgancia"
    # --- Open the database ---
    db = create_engine(
        f"sqlite:///{(Path(__file__).parent/"users.sqlite").as_posix()}",
        # echo=True, # Uncomment for debug
    )
    SQLUser.metadata.create_all(db)
    # --- Create gods if necessary ---
    for username, password in [
        [x for x in map(str.strip, line.split(" ")) if x][:2] for line in
        map(str.strip, (Path(__file__).parent/"gods.txt").read_text().splitlines())
        if line and not line.startswith("#")
    ]:
        god = User.named(username)
        if god is None:
            from .auth import hash_password
            god = User(username=username, hashed_password=hash_password(password))
        if not god.admin:
            god.admin = True
        if not god.verified:
            god.verified = True
        if god.banned:
            god.banned = False
        god.save()


async def teardown():
    # Save global passcode
    PASSCODE_FILE.write_text(f"{server_passcode}\n")


db: Engine
server_passcode: str


class User(BaseModel):
    """A user."""
    username: str
    hashed_password: str  # TODO: find a way to exclude this from responses
    admin:    bool = False
    banned:   bool = False
    verified: bool = False

    @overload
    @classmethod
    def named(cls, username: str, /, *, strict: Literal[True]) -> Self: ...
    @overload
    @classmethod
    def named(cls, username: str, /, *, strict: Literal[False] = ...) -> Self | None: ...
    @classmethod
    def named(cls, username: str, /, *, strict: bool = False) -> Self | None:
        """Return the user with the given username in the database (or None if it doesn't exist)."""
        with Session(db) as session:
            sql = _get_sql_user(session, username)
            if sql is not None:
                return cls.model_validate(sql.model_dump(mode="python"))
            elif strict:
                raise HTTPException(status.HTTP_404_NOT_FOUND)

    def rename(self, new_username: str, /) -> Self:
        """Save changes to this instance in the database and then rename this user."""
        with Session(db) as session:
            sql = _get_sql_user(session, self.username)
            self.username = new_username
            if sql is None:
                return self
            sql.username = new_username
            session.add(sql)
            session.commit()
        return self

    def save(self, /, *, new: bool | None = None) -> Self:
        """Save changes to this instance in the database."""
        with Session(db) as session:
            # Use the current object if the user already exists
            sql = _get_sql_user(session, self.username)
            if sql is None:
                if new is False:
                    raise HTTPException(status.HTTP_404_NOT_FOUND)
                sql = SQLUser.model_validate(self.model_dump())
            else:
                if new is True:
                    raise HTTPException(status.HTTP_409_CONFLICT)
                for field in self.model_fields:
                    if hasattr(sql, field):
                        setattr(sql, field, getattr(self, field))
            # Commit the user to the database
            session.add(sql)
            session.commit()
        return self

    def delete(self, /) -> None:
        """Delete this user from the database (if it's there)."""
        with Session(db) as session:
            sql_user = _get_sql_user(session, self.username)
            if sql_user is None:
                return
            session.delete(sql_user)
            session.commit()


class SQLUser(SQLModel, table=True):
    """A user in the SQL database."""
    id: Annotated[int | None, Field(primary_key=True)] = None
    username: Annotated[str, Field(index=True)]
    hashed_password: str
    is_admin: bool = False
    verified: bool = False


def _get_sql_user(session: Session, username: str, /):
    return session.exec(select(SQLUser).where(SQLUser.username == username)).first()


async def get_all_users() -> list[User]:
    with Session(db) as session:
        return [
            User.model_validate(sql, from_attributes=True)
            for sql in session.exec(select(SQLUser))
        ]


def get_passcode() -> str:
    return server_passcode

def set_passcode(passcode: str, /) -> None:
    global server_passcode
    server_passcode = passcode


__all__ = ["User", "get_all_users", "get_passcode", "set_passcode"]
