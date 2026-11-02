// Teste de carga da API (k6). Cenarios e limites (thresholds) valem como contrato de desempenho:
// se um limite for violado, o k6 termina com codigo diferente de zero.
//
// Uso (com a stack no ar):
//   docker run --rm -i -e BASE_URL=http://host.docker.internal:8000 \
//     --add-host host.docker.internal:host-gateway grafana/k6 run - < tests/load/api.js
//
// Variaveis: BASE_URL, API_KEY (opcional, fora de development), VUS, DURATION e os limites
// P95_READ_MS, P95_HEALTH_MS e P95_UPLOAD_MS (no CI, mais folgados por causa do runner).
import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

const BASE = __ENV.BASE_URL || "http://localhost:8000";
const API = `${BASE}/api/v1`;
const HEADERS = __ENV.API_KEY ? { "X-API-Key": __ENV.API_KEY } : {};
const VUS = Number(__ENV.VUS || 20);
const DURATION = __ENV.DURATION || "30s";
const P95_READ = Number(__ENV.P95_READ_MS || 500);
const P95_HEALTH = Number(__ENV.P95_HEALTH_MS || 300);
const P95_UPLOAD = Number(__ENV.P95_UPLOAD_MS || 2000);

// PDF minimo valido (assinatura %PDF-) para o upload.
const PDF = "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n";

const uploadLatency = new Trend("upload_latency", true);

export const options = {
  scenarios: {
    leitura: { executor: "constant-vus", exec: "leitura", vus: VUS, duration: DURATION },
    upload: { executor: "constant-arrival-rate", exec: "upload", rate: 5, timeUnit: "1s", duration: DURATION, preAllocatedVUs: 10, maxVUs: 30 },
  },
  thresholds: {
    // Limites escolhidos com folga sobre o medido numa maquina de desenvolvimento.
    "http_req_failed": ["rate<0.01"],
    "http_req_duration{kind:read}": [`p(95)<${P95_READ}`],
    "http_req_duration{kind:health}": [`p(95)<${P95_HEALTH}`],
    "upload_latency": [`p(95)<${P95_UPLOAD}`],
    "checks": ["rate>0.99"],
  },
};

export function leitura() {
  const health = http.get(`${API}/health`, { tags: { kind: "health" } });
  check(health, { "health 200": (r) => r.status === 200 });

  const list = http.get(`${API}/documents?limit=50`, { headers: HEADERS, tags: { kind: "read" } });
  check(list, { "listagem 200": (r) => r.status === 200 });

  const rules = http.get(`${API}/compliance/rules`, { headers: HEADERS, tags: { kind: "read" } });
  check(rules, { "regras 200": (r) => r.status === 200 });

  const trail = http.get(`${API}/compliance/audit-trail?limit=50`, { headers: HEADERS, tags: { kind: "read" } });
  check(trail, { "auditoria 200": (r) => r.status === 200 });
  sleep(0.2);
}

export function upload() {
  const res = http.post(
    `${API}/documents/upload`,
    { file: http.file(PDF, "carga.pdf", "application/pdf") },
    { headers: HEADERS, tags: { kind: "upload" } },
  );
  uploadLatency.add(res.timings.duration);
  check(res, { "upload 201": (r) => r.status === 201 });
}
