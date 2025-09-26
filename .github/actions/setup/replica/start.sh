#!/bin/bash
set -euxo pipefail
echo 'Waiting for primary to be ready...'
while ! pg_isready -h postgres -p 5432 -U replica; do sleep 1; done;
echo 'Primary is ready, starting replica...'
rm -rf /var/lib/postgresql/data/* 2>/dev/null || true
PGPASSWORD=${POSTGRES_PASSWORD} pg_basebackup -h postgres -U replica -D /var/lib/postgresql/data -Fp -Xs -R -P
echo 'Replication setup complete, starting PostgreSQL...'
docker-entrypoint.sh postgres
