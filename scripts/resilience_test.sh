#!/usr/bin/env bash
# Teste de resiliencia: derruba cada dependencia com a stack no ar e confere que a API
#   - nunca responde 500 por causa da dependencia (503 com mensagem clara, ou 200 degradado);
#   - mantem o healthcheck respondendo rapido (nao pode travar);
#   - se recupera sozinha quando a dependencia volta.
#
# Uso: scripts/resilience_test.sh            (stack ja no ar, API em http://127.0.0.1:8000)
# Variaveis: API_URL, COMPOSE (comando do compose, ex.: "docker compose --env-file .env -f infra/docker-compose.yml")
set -u

API_URL="${API_URL:-http://127.0.0.1:8000}"
COMPOSE="${COMPOSE:-docker compose --env-file .env -f infra/docker-compose.yml}"
# Arquivo no diretorio atual (caminho relativo): funciona com curl nativo e no Windows.
PDF="$(mktemp ./resilience-XXXXXX.pdf)"
trap 'rm -f "$PDF"' EXIT
printf '%%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%%%EOF\n' > "$PDF"
failures=0

fail() { echo "  FALHA: $*"; failures=$((failures + 1)); }
code() { curl -s -o /dev/null -w '%{http_code}' --max-time "$1" "${@:2}"; }

health_status() {
  # O primeiro campo "status" do JSON e o estado geral (sem depender de python ou jq).
  curl -s --max-time 10 "$API_URL/api/v1/health" | grep -o '"status":"[a-z]*"' | head -1 | cut -d'"' -f4
}

wait_healthy() {
  for _ in $(seq 1 30); do
    [ "$(health_status)" = "healthy" ] && return 0
    sleep 3
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

scenario() {
  local service="$1"
  echo "[$service parado]"
  $COMPOSE stop "$service" > /dev/null 2>&1
  check_health_fast
  case "$service" in
    redis)
      got=$(code 40 -F "file=@$PDF;type=application/pdf" "$API_URL/api/v1/documents/upload")
      [ "$got" = "503" ] || fail "upload sem Redis respondeu $got (esperado 503)"
      ;;
    postgres)
      got=$(code 20 "$API_URL/api/v1/documents")
      [ "$got" = "503" ] || fail "listagem sem Postgres respondeu $got (esperado 503)"
      ;;
  esac
  echo "[$service de volta]"
  $COMPOSE start "$service" > /dev/null 2>&1
  wait_healthy || fail "API nao voltou a ficar healthy apos religar $service"
}

[ "$(health_status)" = "healthy" ] || { echo "Stack nao esta healthy; abortando."; exit 2; }
for service in redis minio postgres; do
  scenario "$service"
done

if [ "$failures" -gt 0 ]; then
  echo "Resiliencia: $failures falha(s)."
  exit 1
fi
echo "Resiliencia OK: degradacao controlada e recuperacao automatica em todos os cenarios."
