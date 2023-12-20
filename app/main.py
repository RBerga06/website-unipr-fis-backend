#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The backend website. Powered by FastAPI + Pydantic + SQLModel."""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"result": "Hello, World!"}
