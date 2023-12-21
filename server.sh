#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
exec pdm run uvicorn app.main:app
