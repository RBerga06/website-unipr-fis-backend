#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The backend website. Powered by FastAPI + Pydantic + SQLModel."""
from fastapi import FastAPI
from .access import auth, users

app = FastAPI()
app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"result": "Hello, World!"}
