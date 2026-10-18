#!/bin/sh

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)" || exit 1
exec "$SCRIPT_DIR/Run_Clicker" "$@"