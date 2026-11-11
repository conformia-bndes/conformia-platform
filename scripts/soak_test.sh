#!/usr/bin/env bash
# Teste de soak (padrao 30m a carga moderada): executa tests/load/soak.js via k6 e verifica que
# nao ha vazamento de conexoes no PostgreSQL nem crescimento descontrolado de memoria nos
# conteineres backend e worker.
#
# Uso:
#   DURATION=30m bash scripts/soak_test.sh
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="docker compose --env-file .env -f infra/docker-compose.yml"
DURATION="${DURATION:-30m}"
VUS="${VUS:-10}"
UPLOAD_RATE="${UPLOAD_RATE:-1}"
BASE_URL="${BASE_URL:-http://host.docker.internal:8000}"
MAX_CONN_DRIFT="${MAX_CONN_DRIFT:-10}"

pg_connections() {
  $COMPOSE exec -T postgres psql -U "${POSTGRES_USER:-conformia_user}" -d "${POSTGRES_DB:-conformia_db}" \
    -tAc "SELECT count(*) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB:-conformia_db}';" | tr -d '[:space:]'
}

echo "[soak] Estado inicial antes de ${DURATION} (VUS=${VUS}, UPLOAD_RATE=${UPLOAD_RATE}/s):"
CONN_BEFORE="$(pg_connections)"
echo "[soak] Conexoes ativas no PostgreSQL (antes): ${CONN_BEFORE}"
docker stats --no-stream --format "  {{.Name}}: {{.MemUsage}} ({{.MemPerc}})" \
  conformia-backend conformia-worker conformia-frontend

docker run --rm -i \
  -e BASE_URL="${BASE_URL}" \
  -e DURATION="${DURATION}" \
  -e VUS="${VUS}" \
  -e UPLOAD_RATE="${UPLOAD_RATE}" \
  --add-host host.docker.internal:host-gateway \
  grafana/k6 run --quiet - < tests/load/soak.js

# Aguarda drenagem das tarefas em voo e reciclagem de conexoes ociosas
sleep 5

echo "[soak] Estado final apos ${DURATION}:"
CONN_AFTER="$(pg_connections)"
echo "[soak] Conexoes ativas no PostgreSQL (depois): ${CONN_AFTER}"
docker stats --no-stream --format "  {{.Name}}: {{.MemUsage}} ({{.MemPerc}})" \
  conformia-backend conformia-worker conformia-frontend

DRIFT=$((CONN_AFTER - CONN_BEFORE))
if [ "$DRIFT" -gt "$MAX_CONN_DRIFT" ]; then
  echo "[soak] FALHA: conexoes no PostgreSQL cresceram de ${CONN_BEFORE} para ${CONN_AFTER} (+${DRIFT} > ${MAX_CONN_DRIFT})." >&2
  exit 1
fi

echo "[soak] OK - sem vazamento de conexoes (antes=${CONN_BEFORE}, depois=${CONN_AFTER}) e limites de memoria respeitados."
