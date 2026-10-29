"""Provider Python do promptfoo: executa o Maker-Checker real sobre um documento de teste.

O promptfoo chama call_api(prompt, options, context) para cada caso de
promptfooconfig.yaml. As variaveis do caso trazem o rule_id e o texto do documento.
Sem OPENAI_API_KEY o Maker-Checker degrada para MANUAL_REVIEW_REQUIRED (fail-closed);
os casos negativos continuam validos, mas os positivos so sao informativos com chave.
"""

import json
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
# Valores descartaveis: o provider nao usa banco, fila nem storage.
for _name in ("SECRET_KEY", "API_KEY", "POSTGRES_PASSWORD", "MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD"):
    os.environ.setdefault(_name, "promptfoo-only")

from app.ai.llm_client import MakerCheckerValidator  # noqa: E402
from app.services.rules_engine import RulesEngine  # noqa: E402

RULES = {rule["id"]: rule for rule in RulesEngine().rules}


def call_api(prompt, options, context):
    variables = context["vars"]
    rule = RULES[variables["rule_id"]]
    result = MakerCheckerValidator().evaluate_rule(rule, variables["document"])
    return {
        "output": json.dumps(
            {
                "status": result["status"],
                "is_verified": result["is_verified"],
                "evidence_grounded": result.get("evidence_grounded", False),
                "error": result.get("error"),
            }
        )
    }
