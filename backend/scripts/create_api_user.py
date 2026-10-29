"""Gera uma chave de API pessoal e a entrada correspondente para API_USERS.

Uso (somente biblioteca padrao):
    python backend/scripts/create_api_user.py <user_id> <ANALISTA|AUDITOR|ADMIN>

A chave tem o formato "<user_id>:<segredo>" e e gravada em <user_id>.key no diretorio atual,
com permissao apenas para o dono (o arquivo nunca e sobrescrito). Entregue-a ao usuario por
canal seguro e apague o arquivo. O servidor guarda apenas o hash PBKDF2-HMAC-SHA256 do segredo, com
sal proprio (campo key_hash em API_USERS no .env). O formato do hash e o mesmo de
app.core.security.hash_api_key; um teste garante que a chave gerada aqui autentica no servidor.
"""

import hashlib
import json
import os
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


def write_key_file(path: str, key: str) -> None:
    """Grava a chave em arquivo novo, legivel apenas pelo dono; nunca sobrescreve."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(key + "\n")


def main(argv: list) -> int:
    if len(argv) != 3 or argv[2] not in ROLES or not USER_ID_PATTERN.match(argv[1]):
        print(__doc__, file=sys.stderr)
        return 2

    user_id = argv[1]
    path = os.path.abspath(f"{user_id}.key")
    key, entry = build_api_user(user_id, argv[2])
    try:
        write_key_file(path, key)
    except FileExistsError:
        print(f"Arquivo {path} ja existe; nada foi gerado.", file=sys.stderr)
        return 1

    # A chave nao e exibida no terminal: fica so no arquivo, fora do historico e de logs.
    print(f"Chave pessoal gravada em {path} (somente o dono pode ler).")
    print("Entregue-a ao usuario por canal seguro e apague o arquivo em seguida.")
    print("Entrada para a lista JSON de API_USERS no .env:")
    print(f"  {json.dumps(entry)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
