#!/usr/bin/env bash
# Gera ou valida o .env a partir do .env.example, trocando cada CHANGE_ME por um valor aleatorio.
# Idempotente: nao sobrescreve um .env existente (use --sync para acrescentar chaves novas ou
# --force para regenerar do zero).
set -eu

cd "$(dirname "$0")/.."

MODE="${1:-}"
if [ -n "$MODE" ] && [ "$MODE" != "--force" ] && [ "$MODE" != "--sync" ]; then
  echo "Uso: bash scripts/setup-env.sh [--sync | --force]" >&2
  exit 2
fi

gen() { LC_ALL=C tr -dc 'a-f0-9' </dev/urandom | head -c 32; }

fill_secrets() {
  local line="$1"
  while [[ "$line" == *CHANGE_ME* ]]; do
    line="${line/CHANGE_ME/$(gen)}"
  done
  printf '%s\n' "$line"
}

has_key() {
  local key="$1"
  local file="$2"
  grep -Eq "^[[:space:]]*(export[[:space:]]+)?${key}[[:space:]]*=" "$file"
}

missing_keys() {
  local line key
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)= ]]; then
      key="${BASH_REMATCH[1]}"
      if ! has_key "$key" .env; then
        printf '%s\n' "$key"
      fi
    fi
  done < .env.example
}

if [ -f .env ] && [ "$MODE" != "--force" ]; then
  missing="$(missing_keys)"
  if [ -z "$missing" ]; then
    echo ".env ja existe e contem todas as variaveis de .env.example (use --force para regenerar)."
    exit 0
  fi

  missing_list="$(printf '%s\n' "$missing" | paste -sd ', ' - | sed 's/,/, /g')"
  if [ "$MODE" = "--sync" ]; then
    if [ -s .env ] && [ "$(tail -c 1 .env | wc -l)" -eq 0 ]; then
      printf '\n' >> .env
    fi
    while IFS= read -r line || [ -n "$line" ]; do
      line="${line%$'\r'}"
      if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)= ]]; then
        key="${BASH_REMATCH[1]}"
        if ! has_key "$key" .env; then
          fill_secrets "$line" >> .env
        fi
      fi
    done < .env.example
    chmod 600 .env
    echo ".env atualizado (segredos existentes preservados). Variaveis acrescentadas: ${missing_list}."
    exit 0
  fi

  {
    echo "ERRO: .env desatualizado. Variaveis ausentes em relacao ao .env.example: ${missing_list}"
    echo "Para acrescentar apenas as chaves novas sem apagar os segredos existentes, execute:"
    echo "  bash scripts/setup-env.sh --sync"
    echo "Para regenerar o .env completo do zero (substitui as senhas atuais), execute:"
    echo "  bash scripts/setup-env.sh --force"
  } >&2
  exit 1
fi

: > .env
while IFS= read -r line || [ -n "$line" ]; do
  line="${line%$'\r'}"
  fill_secrets "$line" >> .env
done < .env.example

chmod 600 .env
echo ".env gerado com segredos aleatorios. NAO commite este arquivo."
echo "Se os volumes do Postgres/MinIO ja existiam com outras senhas, rode 'make clean' antes de 'make up'."
