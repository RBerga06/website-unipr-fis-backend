#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The backend website. Powered by FastAPI + Pydantic + SQLModel."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from . import access


@asynccontextmanager
async def lifespan(app: FastAPI, /):
    # Startup
    await access.users.startup()
    print("Startup completed!")
    # ---
    yield
    # Teardown
    pass


app = FastAPI(lifespan=lifespan)
app.include_router(access.auth.router)
app.include_router(access.users.router)
app.include_router(access.admin.router)


@app.get("/")
def root():
    return {"result": "Hello, World!"}
