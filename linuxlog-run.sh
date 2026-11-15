#!/bin/bash
set -e

cd "/home/serhii/.local/share/linuxlog"
source .venv/bin/activate
exec python main.py "$@"
