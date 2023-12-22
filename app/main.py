#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The backend website. Powered by FastAPI + Pydantic + SQLModel."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import access, routers


ORIGINS = [
    "http://localhost",
    "http://localhost:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI, /):
    # Startup
    await access.users.startup()
    print("Startup completed!")
    # ---
    yield
    # Teardown
    await access.users.teardown()


app = FastAPI(lifespan=lifespan)
app.include_router(access.auth.router)
app.include_router(routers.users.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"result": "Hello, World!"}
