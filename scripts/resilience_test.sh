#!/usr/bin/env bash
# Teste de resiliencia: derruba MinIO, Redis e PostgreSQL com a stack no ar e confere que a API
#   - responde 503 no upload dentro do prazo total quando MinIO ou Redis estao parados;
#   - responde 503 na listagem quando o PostgreSQL esta parado;
#   - mantem o healthcheck respondendo rapido (200 degradado, sem travar);
#   - se recupera sozinha quando a dependencia volta.
#
# Uso: scripts/resilience_test.sh            (stack ja no ar, API em http://127.0.0.1:8000)
# Variaveis: API_KEY (obrigatoria), API_URL, COMPOSE, UPLOAD_TOTAL_TIMEOUT_SECONDS
set -u

API_URL="${API_URL:-http://127.0.0.1:8000}"
COMPOSE="${COMPOSE:-docker compose --env-file .env -f infra/docker-compose.yml}"
UPLOAD_TOTAL_TIMEOUT_SECONDS="${UPLOAD_TOTAL_TIMEOUT_SECONDS:-8}"
: "${API_KEY:?Defina API_KEY (chave de servico) no ambiente antes de rodar.}"

if ! awk -v timeout="$UPLOAD_TOTAL_TIMEOUT_SECONDS" \
  'BEGIN { exit !(timeout ~ /^[0-9]+([.][0-9]+)?$/ && timeout > 0) }'; then
  echo "UPLOAD_TOTAL_TIMEOUT_SECONDS deve ser um numero positivo."
  exit 2
fi

# Arquivo no diretorio atual (caminho relativo): funciona com curl nativo e no Windows.
PDF="$(mktemp ./resilience-XXXXXX.pdf)"
printf '%%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%%%EOF\n' > "$PDF"
failures=0
MINIO_WAS_RUNNING=0
REDIS_WAS_RUNNING=0
MINIO_STOPPED_BY_TEST=0
REDIS_STOPPED_BY_TEST=0
POSTGRES_WAS_RUNNING=0
POSTGRES_STOPPED_BY_TEST=0

fail() { echo "  FALHA: $*"; failures=$((failures + 1)); }
code() { curl -s -o /dev/null -w '%{http_code}' --max-time "$1" "${@:2}"; }

health_status() {
  curl -s --max-time 10 "$API_URL/api/v1/health" | grep -o '"status":"[a-z]*"' | head -1 | cut -d'"' -f4
}

wait_healthy() {
  for _ in $(seq 1 30); do
    [ "$(health_status)" = "healthy" ] && return 0
    sleep 1
  done
  return 1
}

check_health_fast() {
  local started code_health elapsed
  started=$(date +%s)
  code_health=$(code 12 "$API_URL/api/v1/health")
  elapsed=$(( $(date +%s) - started ))
  [ "$code_health" = "200" ] || fail "health respondeu $code_health (esperado 200 degradado)"
  [ "$elapsed" -le 8 ] || fail "health levou ${elapsed}s (limite 8s): o healthcheck nao pode travar"
}

service_running() {
  [ -n "$($COMPOSE ps --status running -q "$1" 2>/dev/null)" ]
}

restore_service() {
  local service="$1" was_running="$2" stopped_var="$3"
  local stopped
  eval "stopped=\$$stopped_var"
  if [ "$was_running" -eq 1 ] && [ "$stopped" -eq 1 ]; then
    echo "[$service restauracao]"
    $COMPOSE start "$service" > /dev/null 2>&1 || echo "  FALHA: nao foi possivel iniciar $service"
    eval "$stopped_var=0"
  fi
}

cleanup() {
  restore_service minio "$MINIO_WAS_RUNNING" MINIO_STOPPED_BY_TEST
  restore_service redis "$REDIS_WAS_RUNNING" REDIS_STOPPED_BY_TEST
  restore_service postgres "$POSTGRES_WAS_RUNNING" POSTGRES_STOPPED_BY_TEST
  rm -f -- "$PDF"
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

stop_service() {
  local service="$1"
  echo "[$service parado]"
  case "$service" in
    minio) MINIO_STOPPED_BY_TEST=1 ;;
    redis) REDIS_STOPPED_BY_TEST=1 ;;
    postgres) POSTGRES_STOPPED_BY_TEST=1 ;;
  esac
  $COMPOSE stop "$service" > /dev/null 2>&1 || fail "nao foi possivel parar $service"
}

start_service() {
  local service="$1"
  echo "[$service de volta]"
  if $COMPOSE start "$service" > /dev/null 2>&1; then
    case "$service" in
      minio) MINIO_STOPPED_BY_TEST=0 ;;
      redis) REDIS_STOPPED_BY_TEST=0 ;;
      postgres) POSTGRES_STOPPED_BY_TEST=0 ;;
    esac
  else
    fail "nao foi possivel iniciar $service"
  fi
  wait_healthy || fail "API nao voltou a ficar healthy apos religar $service"
}

scenario() {
  local service="$1" result curl_rc status elapsed curl_max
  stop_service "$service"
  check_health_fast
  curl_max=$(awk -v timeout="$UPLOAD_TOTAL_TIMEOUT_SECONDS" 'BEGIN { printf "%.3f", timeout + 3 }')
  result=$(curl -s -o /dev/null -w '%{http_code} %{time_total}' \
    --max-time "$curl_max" -H "X-API-Key: $API_KEY" \
    -F "file=@$PDF;type=application/pdf" "$API_URL/api/v1/documents/upload")
  curl_rc=$?
  status="${result%% *}"
  elapsed="${result#* }"
  [ "$curl_rc" -eq 0 ] || fail "$service upload curl saiu com codigo $curl_rc"
  echo "  HTTP $status; tempo ${elapsed}s (limite ${UPLOAD_TOTAL_TIMEOUT_SECONDS}s + 1s)"
  [ "$status" = "503" ] || fail "upload sem $service respondeu $status (esperado 503)"
  if ! awk -v elapsed="$elapsed" -v timeout="$UPLOAD_TOTAL_TIMEOUT_SECONDS" \
    'BEGIN { exit !(elapsed ~ /^[0-9]+([.][0-9]+)?$/ && elapsed <= timeout + 1) }'; then
    fail "upload sem $service levou ${elapsed}s (limite ${UPLOAD_TOTAL_TIMEOUT_SECONDS}s + 1s)"
  fi
  start_service "$service"
}

[ "$(health_status)" = "healthy" ] || { echo "Stack nao esta healthy; abortando."; exit 2; }
MINIO_WAS_RUNNING=0
REDIS_WAS_RUNNING=0
service_running minio && MINIO_WAS_RUNNING=1
service_running redis && REDIS_WAS_RUNNING=1
[ "$MINIO_WAS_RUNNING" -eq 1 ] || { echo "MinIO nao estava ativo inicialmente; abortando."; exit 2; }
[ "$REDIS_WAS_RUNNING" -eq 1 ] || { echo "Redis nao estava ativo inicialmente; abortando."; exit 2; }

postgres_scenario() {
  local got
  stop_service postgres
  check_health_fast
  got=$(code 20 -H "X-API-Key: $API_KEY" "$API_URL/api/v1/documents")
  [ "$got" = "503" ] || fail "listagem sem Postgres respondeu $got (esperado 503)"
  start_service postgres
}

for service in minio redis; do
  scenario "$service"
done
service_running postgres && POSTGRES_WAS_RUNNING=1
[ "$POSTGRES_WAS_RUNNING" -eq 1 ] || { echo "PostgreSQL nao estava ativo; abortando."; exit 2; }
postgres_scenario

if [ "$failures" -gt 0 ]; then
  echo "Resiliencia: $failures falha(s)."
  exit 1
fi
echo "Resiliencia OK: degradacao controlada e recuperacao automatica em todos os cenarios."
