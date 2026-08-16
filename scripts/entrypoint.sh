#!/bin/sh
set -eu

# Schema migration is an explicit one-shot Compose responsibility. Keeping the
# long-running entrypoint side-effect free allows web and worker root filesystems
# to remain read-only in the production topology.
exec "$@"
