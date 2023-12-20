#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The backend website. Powered by FastAPI + Pydantic + SQLModel."""
from fastapi import FastAPI
from . import access

app = FastAPI()
app.include_router(access.auth.router)
app.include_router(access.users.router)

@app.get("/")
def root():
    return {"result": "Hello, World!"}
