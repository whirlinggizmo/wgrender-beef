#!/usr/bin/env bash
# Serve a web build (default build/web; build/web-debug for Debug) at
# http://localhost:${1:-8000}/ with wgrender's dev server, which mounts wgrender's
# examples/assets at /assets.
set -euo pipefail
cd "$(dirname "$0")"
LIBWGR_ROOT="${LIBWGR_ROOT:-$HOME/projects/github/whirlinggizmo/wgrender-c}"
exec python3 "$LIBWGR_ROOT/tools/serve.py" "${1:-8000}" "${2:-build/web}"
