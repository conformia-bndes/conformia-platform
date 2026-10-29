"""Gera uma chave de API pessoal e a entrada correspondente para API_USERS.

Uso (somente biblioteca padrao):
    python backend/scripts/create_api_user.py <user_id> <ANALISTA|AUDITOR|ADMIN>

A chave tem o formato "<user_id>:<segredo>", e exibida uma unica vez e deve ser entregue ao
usuario por canal seguro. O servidor guarda apenas o hash PBKDF2-HMAC-SHA256 do segredo, com
sal proprio (campo key_hash em API_USERS no .env). O formato do hash e o mesmo de
app.core.security.hash_api_key; um teste garante que a chave gerada aqui autentica no servidor.
"""

import hashlib
import json
import re
import secrets
import sys

ROLES = ("ANALISTA", "AUDITOR", "ADMIN")
USER_ID_PATTERN = re.compile(r"^[a-z0-9._-]{3,64}$")
ITERATIONS = 200_000


def build_api_user(user_id: str, role: str) -> tuple:
    """Retorna (chave para o usuario, entrada para API_USERS)."""
    secret = secrets.token_urlsafe(32)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, ITERATIONS)
    entry = {
        "user_id": user_id,
        "role": role,
        "key_hash": f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}",
    }
    return f"{user_id}:{secret}", entry


def main(argv: list) -> int:
    if len(argv) != 3 or argv[2] not in ROLES or not USER_ID_PATTERN.match(argv[1]):
        print(__doc__, file=sys.stderr)
        return 2

    key, entry = build_api_user(argv[1], argv[2])
    print("Chave pessoal (exibida uma unica vez, entregue ao usuario):")
    print(f"  {key}")
    print("Entrada para a lista JSON de API_USERS no .env:")
    print(f"  {json.dumps(entry)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
