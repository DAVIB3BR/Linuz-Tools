#!/bin/sh
export PYTHONPATH="/app/lib${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m lunuz "$@"
