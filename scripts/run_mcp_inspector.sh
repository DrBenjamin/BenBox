#!/usr/bin/env sh
# Starting the dev server with conda
conda run -n benbox mcp dev src/server.py > /dev/null 2>&1 &
