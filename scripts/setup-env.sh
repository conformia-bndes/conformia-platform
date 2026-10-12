#!/usr/bin/env bash
# Gera o .env a partir do .env.example, trocando cada CHANGE_ME por um valor aleatorio.
# Idempotente: nao sobrescreve um .env existente (use --force para regenerar).
set -eu

cd "$(dirname "$0")/.."

if [ -f .env ] && [ "${1:-}" != "--force" ]; then
  echo ".env ja existe; nada a fazer (use --force para regenerar)."
  exit 0
fi

gen() { LC_ALL=C tr -dc 'a-f0-9' </dev/urandom | head -c 32; }

: > .env
while IFS= read -r line || [ -n "$line" ]; do
  while [[ "$line" == *CHANGE_ME* ]]; do
    line="${line/CHANGE_ME/$(gen)}"
  done
  printf '%s\n' "$line" >> .env
done < .env.example

chmod 600 .env
echo ".env gerado com segredos aleatorios. NAO commite este arquivo."
echo "Se os volumes do Postgres/MinIO ja existiam com outras senhas, rode 'make clean' antes de 'make up'."
