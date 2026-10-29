"""Gera uma chave de API pessoal e a entrada correspondente para API_USERS.

Uso (somente biblioteca padrao):
    python backend/scripts/create_api_user.py <user_id> <ANALISTA|AUDITOR|ADMIN>

A chave e exibida uma unica vez e deve ser entregue ao usuario por canal seguro.
O servidor guarda apenas o hash SHA-256 (campo key_sha256 em API_USERS no .env).
"""

import hashlib
import json
import re
import secrets
import sys

ROLES = ("ANALISTA", "AUDITOR", "ADMIN")
USER_ID_PATTERN = re.compile(r"^[a-z0-9._-]{3,64}$")


def main(argv: list) -> int:
    if len(argv) != 3 or argv[2] not in ROLES or not USER_ID_PATTERN.match(argv[1]):
        print(__doc__, file=sys.stderr)
        return 2

    key = secrets.token_urlsafe(32)
    entry = {
        "user_id": argv[1],
        "role": argv[2],
        "key_sha256": hashlib.sha256(key.encode("utf-8")).hexdigest(),
    }
    print("Chave pessoal (exibida uma unica vez, entregue ao usuario):")
    print(f"  {key}")
    print("Entrada para a lista JSON de API_USERS no .env:")
    print(f"  {json.dumps(entry)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
