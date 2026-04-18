#!/bin/sh
set -eu

alembic -c alembic.ini upgrade head
exec "$@"
