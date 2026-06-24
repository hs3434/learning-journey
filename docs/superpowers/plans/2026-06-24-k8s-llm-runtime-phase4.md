# Phase 4 (Week 4): FastAPI server + llm-router chart + Docker

**End-of-phase deliverable:** Router image builds successfully; FastAPI server runs and serves `/healthz`, `/v1/models`, `/v1/chat/completions` (with mocked operator).

**Working directory:** `/work/run/projects/bio-24/my_projects/k8s-llm-runtime/`

---

## Task 4.1: FastAPI Router server.py

**Files:**
- Create: `examples/vllm-qwen/server.py`
- Create: `examples/__init__.py`
- Create: `examples/vllm-qwen/__init__.py`
- Create: `tests/unit/test_server.py`

- [ ] **Step 1: Create package markers**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
mkdir -p examples/vllm-qwen
touch examples/__init__.py examples/vllm-qwen/__init__.py
```

- [ ] **Step 2: Write failing test**

Write to `tests/unit/test_server.py`:

```python
"""Tests for the FastAPI Router server."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from k8s_llm_runtime.errors import ModelNotFoundError, VLLMDeployTimeoutError
from k8s_llm_runtime.model import ChatResponse


@pytest.fixture
def mock_op():
    op = MagicMock()
    op.chat = AsyncMock(return_value=ChatResponse(
        id="chatcmpl-1",
        object="chat.completion",
        created=1,
        model="qwen-0.5b",
        choices=[{"message": {"role": "assistant", "content": "hello"}}],
        usage={"total_tokens": 1},
    ))
    op.list_models = AsyncMock(return_value=["qwen-0.5b"])
    op.unload = AsyncMock()
    return op


@pytest.fixture
def client(mock_op):
    with patch("k8s_llm_runtime.model.ModelOperator") as mock_cls:
        mock_cls.return_value = mock_op
        import importlib
        import examples.vllm-qwen.server as srv
        importlib.reload(srv)
        srv.app.state.op = mock_op
        # Stub lifespan: skip startup
        with TestClient(srv.app) as c:
            yield c


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "LLM Router" in r.json()["message"]


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_chat_completions(client, mock_op):
    r = client.post("/v1/chat/completions", json={
        "model": "qwen-0.5b",
        "messages": [{"role": "user", "content": "hi"}],
    })
    assert r.status_code == 200
    assert r.json()["model"] == "qwen-0.5b"
    mock_op.chat.assert_called_once()


def test_chat_unknown_model_returns_404(client, mock_op):
    mock_op.chat.side_effect = ModelNotFoundError("foo")
    r = client.post("/v1/chat/completions", json={
        "model": "foo",
        "messages": [{"role": "user", "content": "hi"}],
    })
    assert r.status_code == 404
    assert "foo" in r.text


def test_chat_deploy_timeout_returns_503(client, mock_op):
    mock_op.chat.side_effect = VLLMDeployTimeoutError("timeout")
    r = client.post("/v1/chat/completions", json={
        "model": "qwen-0.5b",
        "messages": [{"role": "user", "content": "hi"}],
    })
    assert r.status_code == 503


def test_list_models(client):
    r = client.get("/v1/models")
    assert r.status_code == 200
    assert r.json()["data"][0]["id"] == "qwen-0.5b"


def test_unload_model(client, mock_op):
    r = client.delete("/v1/models/qwen-0.5b")
    assert r.status_code == 204
    mock_op.unload.assert_called_once_with("qwen-0.5b")


def test_request_id_header_echoed(client):
    r = client.post(
        "/v1/chat/completions",
        json={"model": "qwen-0.5b",
              "messages": [{"role": "user", "content": "hi"}]},
        headers={"X-Request-ID": "test-rid-123"},
    )
    assert r.headers.get("X-Request-ID") == "test-rid-123"


def test_request_id_generated_when_absent(client):
    r = client.post(
        "/v1/chat/completions",
        json={"model": "qwen-0.5b",
              "messages": [{"role": "user", "content": "hi"}]},
    )
    rid = r.headers.get("X-Request-ID")
    assert rid is not None
    assert len(rid) > 10
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_server.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Implement server.py**

Write to `examples/vllm-qwen/server.py`:

```python
"""FastAPI LLM Router.

OpenAI-compatible chat completion API. Auto-deploys vLLM models on demand
via the ModelOperator.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import structlog
import yaml
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from k8s_llm_runtime import (
    GPUResource,
    GPUVendor,
    ModelOperator,
    VLLMInferenceOperator,
)
from k8s_llm_runtime._log import configure_logging, get_logger
from k8s_llm_runtime.errors import (
    K8sLLMRuntimeError,
    LockAcquireTimeoutError,
    ModelAliasError,
    ModelNotFoundError,
    VLLMDeployError,
    VLLMDeployTimeoutError,
    VLLMUndeployError,
)
from k8s_llm_runtime.model import ChatRequest

configure_logging()
logger = get_logger(__name__)


# --- Configuration helpers ---


def load_model_aliases(path: Path) -> dict[str, str]:
    if not path.exists():
        logger.warning("model_aliases_file_not_found", path=str(path))
        return {}
    with path.open() as f:
        cfg = yaml.safe_load(f) or {}
    aliases = cfg.get("aliases", {})
    if not aliases:
        raise ModelAliasError(f"No aliases found in {path}")
    return aliases


# --- Lifespan ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg_path = Path(os.environ.get("MODEL_CONFIG_PATH", "/app/config/models.yaml"))
    aliases = load_model_aliases(cfg_path)

    chart_path = os.environ.get("CHART_PATH", "/app/charts/llm-inference")
    vllm_op = VLLMInferenceOperator(chart_path=chart_path)

    op = ModelOperator(
        model_aliases=aliases,
        vllm_op=vllm_op,
        namespace=os.environ.get("TARGET_NAMESPACE", "llm-models"),
        default_gpu=GPUResource(
            vendor=GPUVendor(os.environ.get("GPU_VENDOR", "amd")),
            limit=int(os.environ.get("GPU_LIMIT", "1")),
        ),
        idle_timeout_seconds=int(os.environ.get("IDLE_TIMEOUT", "600")),
    )
    await op.discover_existing()

    app.state.op = op
    logger.info("router_started", aliases=list(aliases.keys()))
    yield
    logger.info("router_stopping")


app = FastAPI(
    title="LLM Router",
    version="0.1.0",
    description="OpenAI-compatible vLLM model serving on Kubernetes",
    lifespan=lifespan,
)
app.mount("/metrics", make_asgi_app())


# --- Middleware ---


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("X-Request-ID", str(uuid4()))
    structlog.contextvars.bind_contextvars(request_id=rid)
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    structlog.contextvars.clear_contextvars()
    return response


# --- Exception mapping ---


ERROR_MAP: dict[type, tuple[int, str]] = {
    ModelNotFoundError: (404, "Unknown model alias"),
    ModelAliasError: (400, "Invalid alias config"),
    VLLMDeployError: (500, "vLLM deploy failed"),
    VLLMDeployTimeoutError: (503, "vLLM deploy timeout"),
    VLLMUndeployError: (500, "vLLM undeploy failed"),
    LockAcquireTimeoutError: (503, "Deploy lock timeout"),
}


@app.exception_handler(K8sLLMRuntimeError)
async def handle_lib_error(request: Request, exc: K8sLLMRuntimeError):
    status_code, msg = ERROR_MAP.get(type(exc), (500, "Internal error"))
    logger.error("lib_error", error_type=type(exc).__name__, message=str(exc))
    return JSONResponse(
        status_code=status_code,
        content={"error": {"type": type(exc).__name__, "message": f"{msg}: {exc}"}},
    )


# --- Endpoints ---


@app.get("/")
async def root():
    return {"message": "LLM Router", "version": "0.1.0"}


@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}


@app.get("/readyz")
async def readyz():
    """Check K8s API connectivity."""
    try:
        from k8s_llm_runtime import _client
        _client.core_api().list_namespace(limit=1)
    except Exception as exc:
        raise HTTPException(503, f"K8s API unreachable: {exc}")
    return {"status": "ready"}


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    return await app.state.op.chat(req)


@app.get("/v1/models")
async def list_models():
    aliases = await app.state.op.list_models()
    return {
        "object": "list",
        "data": [
            {"id": a, "object": "model", "owned_by": "k8s-llm-runtime"}
            for a in aliases
        ],
    }


@app.get("/v1/models/{alias}")
async def get_model(alias: str):
    aliases = await app.state.op.list_models()
    if alias not in aliases:
        raise HTTPException(404, f"Model {alias} not loaded")
    return {"id": alias, "object": "model", "owned_by": "k8s-llm-runtime"}


@app.delete("/v1/models/{alias}", status_code=status.HTTP_204_NO_CONTENT)
async def unload_model(alias: str):
    await app.state.op.unload(alias)
    return None
```

- [ ] **Step 5: Run tests**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_server.py -v
```

Expected: 9 tests pass.

- [ ] **Step 6: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add examples/ tests/unit/test_server.py
git commit -m "feat(server): FastAPI router with OpenAI-compatible endpoints"
```

---

## Task 4.2: Client and benchmark scripts

**Files:**
- Create: `examples/vllm-qwen/client.py`
- Create: `examples/vllm-qwen/benchmark.py`
- Create: `examples/vllm-qwen/test_request.json`

- [ ] **Step 1: client.py**

```python
"""Test client for the LLM Router. Supports HTTP and OpenAI SDK modes."""
from __future__ import annotations

import argparse
import json
import sys

import httpx


def chat_http(base_url: str, model: str, prompt: str) -> dict:
    resp = httpx.post(
        f"{base_url}/chat/completions",
        json={"model": model,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=300.0,
    )
    resp.raise_for_status()
    return resp.json()


def chat_openai_sdk(base_url: str, model: str, prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(base_url=base_url, api_key="not-needed")
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content or ""


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM Router test client")
    parser.add_argument("--base-url", default="http://localhost:8080/v1")
    parser.add_argument("--model", default="qwen-0.5b")
    parser.add_argument("--prompt", default="讲个关于 K8s 的冷笑话")
    parser.add_argument("--mode", choices=["http", "openai"], default="openai")
    args = parser.parse_args()

    try:
        if args.mode == "http":
            print(json.dumps(chat_http(args.base_url, args.model, args.prompt),
                             ensure_ascii=False, indent=2))
        else:
            print(chat_openai_sdk(args.base_url, args.model, args.prompt))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: benchmark.py**

```python
"""Concurrent load test for the LLM Router."""
from __future__ import annotations

import argparse
import asyncio
import statistics
import time

import httpx


async def one_request(client, base_url, model, prompt, idx):
    t0 = time.time()
    try:
        r = await client.post(
            f"{base_url}/chat/completions",
            json={"model": model,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=300.0,
        )
        elapsed = time.time() - t0
        body = r.json() if r.status_code == 200 else {}
        return {
            "idx": idx, "status": r.status_code, "latency_s": elapsed,
            "tokens": body.get("usage", {}).get("completion_tokens", 0),
        }
    except Exception as exc:
        return {"idx": idx, "status": -1,
                "latency_s": time.time() - t0, "error": str(exc)}


async def run(args):
    sem = asyncio.Semaphore(args.concurrency)
    async with httpx.AsyncClient() as client:
        async def task(i):
            async with sem:
                return await one_request(client, args.base_url,
                                         args.model, args.prompt, i)
        results = await asyncio.gather(*[task(i) for i in range(args.total)])

    successes = [r for r in results if 200 <= r["status"] < 300]
    failures = [r for r in results if r not in successes]
    latencies = sorted(r["latency_s"] for r in successes)

    print(f"\n=== Benchmark Summary ===")
    print(f"Total:    {len(results)}")
    print(f"OK:       {len(successes)}")
    print(f"Failed:   {len(failures)}")
    print(f"Concurr:  {args.concurrency}")
    if latencies:
        print(f"p50:      {statistics.median(latencies):.2f}s")
        p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
        print(f"p95:      {p95:.2f}s")
        total_tokens = sum(r["tokens"] for r in successes)
        if max(latencies) > 0:
            print(f"Throughput:{total_tokens / max(latencies):.1f} tok/s")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8080/v1")
    parser.add_argument("--model", default="qwen-0.5b")
    parser.add_argument("--prompt", default="写一句关于云计算的话")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--total", type=int, default=20)
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: test_request.json**

```json
{
  "model": "qwen-0.5b",
  "messages": [
    {"role": "system", "content": "你是一个简洁的助手，回答不超过 50 字。"},
    {"role": "user", "content": "用一句话介绍 Kubernetes"}
  ],
  "temperature": 0.7,
  "max_tokens": 100
}
```

- [ ] **Step 4: Smoke-test client**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run python examples/vllm-qwen/client.py --help
```

Expected: argparse help output, no error.

- [ ] **Step 5: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add examples/vllm-qwen/client.py examples/vllm-qwen/benchmark.py examples/vllm-qwen/test_request.json
git commit -m "feat(demo): client.py + benchmark.py + sample request"
```

---

## Task 4.3: llm-router Helm chart

**Files:**
- Create: `charts/llm-router/Chart.yaml`
- Create: `charts/llm-router/values.yaml`
- Create: `charts/llm-router/templates/_helpers.tpl`
- Create: `charts/llm-router/templates/serviceaccount.yaml`
- Create: `charts/llm-router/templates/role.yaml`
- Create: `charts/llm-router/templates/rolebinding.yaml`
- Create: `charts/llm-router/templates/configmap.yaml`
- Create: `charts/llm-router/templates/deployment.yaml`
- Create: `charts/llm-router/templates/service.yaml`
- Create: `charts/llm-router/templates/ingress.yaml`
- Create: `charts/llm-router/templates/hpa.yaml`
- Create: `charts/llm-router/templates/servicemonitor.yaml`
- Create: `tests/chart/test_llm_router.py`

- [ ] **Step 1: Chart.yaml**

```yaml
apiVersion: v2
name: llm-router
description: LLM Router service - OpenAI-compatible API gateway for vLLM
type: application
version: 0.1.0
appVersion: "0.1.0"
```

- [ ] **Step 2: values.yaml**

```yaml
replicaCount: 2

image:
  repository: k8s-llm-runtime/router
  tag: "0.1.0"
  pullPolicy: IfNotPresent

models:
  aliases:
    qwen-7b: Qwen/Qwen2.5-7B-Instruct
    qwen-0.5b: Qwen/Qwen2.5-0.5B-Instruct
  defaultGpu:
    vendor: amd
    limit: 1
  idleTimeoutSeconds: 600
  deployLockTtl: 600

targetNamespace: llm-models

service:
  type: ClusterIP
  port: 8080

ingress:
  enabled: false
  className: nginx
  host: router.local

resources:
  requests:
    cpu: 500m
    memory: 256Mi
  limits:
    cpu: "2"
    memory: 1Gi

autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70

serviceMonitor:
  enabled: false

podAnnotations: {}
```

- [ ] **Step 3: _helpers.tpl**

```
{{- define "llm-router.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "llm-router.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "llm-router.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{ include "llm-router.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "llm-router.selectorLabels" -}}
app.kubernetes.io/name: {{ include "llm-router.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

- [ ] **Step 4: serviceaccount.yaml**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "llm-router.fullname" . }}
  labels:
    {{- include "llm-router.labels" . | nindent 4 }}
```

- [ ] **Step 5: role.yaml**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ include "llm-router.fullname" . }}
  labels:
    {{- include "llm-router.labels" . | nindent 4 }}
rules:
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["services", "pods", "configmaps"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["coordination.k8s.io"]
    resources: ["leases"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

- [ ] **Step 6: rolebinding.yaml**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ include "llm-router.fullname" . }}
  labels:
    {{- include "llm-router.labels" . | nindent 4 }}
subjects:
  - kind: ServiceAccount
    name: {{ include "llm-router.fullname" . }}
    namespace: {{ .Release.Namespace }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{ include "llm-router.fullname" . }}
```

- [ ] **Step 7: configmap.yaml**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "llm-router.fullname" . }}-models
  labels:
    {{- include "llm-router.labels" . | nindent 4 }}
data:
  models.yaml: |
    aliases:
    {{- range $alias, $hf := .Values.models.aliases }}
      {{ $alias }}: {{ $hf | quote }}
    {{- end }}
    defaultGpu:
      vendor: {{ .Values.models.defaultGpu.vendor }}
      limit: {{ .Values.models.defaultGpu.limit }}
    idleTimeoutSeconds: {{ .Values.models.idleTimeoutSeconds }}
    deployLockTtl: {{ .Values.models.deployLockTtl }}
```

- [ ] **Step 8: deployment.yaml** (critical: in-cluster mode, mounted chart via init)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "llm-router.fullname" . }}
  labels:
    {{- include "llm-router.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "llm-router.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "llm-router.selectorLabels" . | nindent 8 }}
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
    spec:
      serviceAccountName: {{ include "llm-router.fullname" . }}
      containers:
        - name: router
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP
          env:
            - name: MODEL_CONFIG_PATH
              value: /app/config/models.yaml
            - name: CHART_PATH
              value: /app/charts/llm-inference
            - name: TARGET_NAMESPACE
              value: {{ .Values.targetNamespace }}
            - name: GPU_VENDOR
              value: {{ .Values.models.defaultGpu.vendor }}
            - name: GPU_LIMIT
              value: {{ .Values.models.defaultGpu.limit | quote }}
            - name: IDLE_TIMEOUT
              value: {{ .Values.models.idleTimeoutSeconds | quote }}
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          volumeMounts:
            - name: model-config
              mountPath: /app/config
              readOnly: true
            - name: chart-bundle
              mountPath: /app/charts
              readOnly: true
          resources:
            requests:
              cpu: {{ .Values.resources.requests.cpu | quote }}
              memory: {{ .Values.resources.requests.memory | quote }}
            limits:
              cpu: {{ .Values.resources.limits.cpu | quote }}
              memory: {{ .Values.resources.limits.memory | quote }}
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /readyz
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
      initContainers:
        - name: load-chart
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          command:
            - sh
            - -c
            - |
              mkdir -p /app/charts/llm-inference && \
              cp -r /chart-source/. /app/charts/llm-inference/ && \
              ls /app/charts/llm-inference/
          volumeMounts:
            - name: chart-source
              mountPath: /chart-source
              readOnly: true
            - name: chart-bundle
              mountPath: /app/charts
      volumes:
        - name: model-config
          configMap:
            name: {{ include "llm-router.fullname" . }}-models
        - name: chart-source
          configMap:
            name: {{ include "llm-router.fullname" . }}-chart-source
        - name: chart-bundle
          emptyDir: {}
```

(Note: the `chart-source` ConfigMap is created in Phase 5 by a `helm install` helper that packs `charts/llm-inference/` into a ConfigMap. For now, the chart references it as expected dependency.)

- [ ] **Step 9: service.yaml**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "llm-router.fullname" . }}
  labels:
    {{- include "llm-router.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "llm-router.selectorLabels" . | nindent 4 }}
```

- [ ] **Step 10: ingress.yaml**

```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "llm-router.fullname" . }}
  labels:
    {{- include "llm-router.labels" . | nindent 4 }}
spec:
  ingressClassName: {{ .Values.ingress.className }}
  rules:
    - host: {{ .Values.ingress.host | quote }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "llm-router.fullname" . }}
                port:
                  number: {{ .Values.service.port }}
{{- end }}
```

- [ ] **Step 11: hpa.yaml**

```yaml
{{- if .Values.autoscaling.enabled -}}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "llm-router.fullname" . }}
  labels:
    {{- include "llm-router.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "llm-router.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
{{- end }}
```

- [ ] **Step 12: servicemonitor.yaml**

```yaml
{{- if .Values.serviceMonitor.enabled -}}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "llm-router.fullname" . }}
  labels:
    {{- include "llm-router.labels" . | nindent 4 }}
spec:
  endpoints:
    - port: http
      path: /metrics
  selector:
    matchLabels:
      {{- include "llm-router.selectorLabels" . | nindent 6 }}
{{- end }}
```

- [ ] **Step 13: Verify helm lint**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
helm lint charts/llm-router
```

Expected: clean lint (warning about missing chart-source ConfigMap is OK; it's created externally).

- [ ] **Step 14: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add charts/llm-router/
git commit -m "feat(chart): llm-router with RBAC, ConfigMap, init chart loader"
```

---

## Task 4.4: Chart tests for llm-router

**Files:**
- Create: `tests/chart/test_llm_router.py`
- Modify: `tests/chart/conftest.py` (add chart_path for router)

- [ ] **Step 1: Update conftest.py**

Replace `tests/chart/conftest.py`:

```python
"""Shared fixtures for chart rendering tests."""
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def chart_paths():
    return {
        "inference": REPO_ROOT / "charts" / "llm-inference",
        "router": REPO_ROOT / "charts" / "llm-router",
    }


@pytest.fixture
def helm_template(chart_paths):
    """Render chart with given --set values."""

    def _render(chart: str = "inference", set_values: list[str] | None = None) -> str:
        cmd = [
            "helm", "template", "test-release", str(chart_paths[chart]),
            "--namespace", "test-ns",
        ]
        for v in set_values or []:
            cmd.extend(["--set", v])
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    return _render
```

- [ ] **Step 2: test_llm_router.py**

```python
"""Tests for llm-router chart rendering."""


def test_default_values_render(helm_template):
    manifest = helm_template(chart="router")
    assert "kind: Deployment" in manifest
    assert "kind: Service" in manifest
    assert "kind: ServiceAccount" in manifest
    assert "kind: Role" in manifest
    assert "kind: RoleBinding" in manifest
    assert "kind: ConfigMap" in manifest


def test_router_has_metrics_endpoint(helm_template):
    manifest = helm_template(chart="router")
    assert "/healthz" in manifest
    assert "/readyz" in manifest


def test_router_uses_in_cluster_service_account(helm_template):
    manifest = helm_template(chart="router")
    assert "serviceAccountName:" in manifest
    assert "POD_NAME" in manifest


def test_router_rbac_includes_leases(helm_template):
    manifest = helm_template(chart="router")
    assert "coordination.k8s.io" in manifest
    assert "leases" in manifest


def test_router_configmap_contains_aliases(helm_template):
    manifest = helm_template(chart="router")
    assert "aliases:" in manifest
    assert "qwen-7b" in manifest
    assert "Qwen/Qwen2.5-7B-Instruct" in manifest


def test_hpa_enabled_when_set(helm_template):
    manifest = helm_template(
        chart="router",
        set_values=["autoscaling.enabled=true", "autoscaling.maxReplicas=10"],
    )
    assert "kind: HorizontalPodAutoscaler" in manifest


def test_ingress_disabled_by_default(helm_template):
    manifest = helm_template(chart="router")
    assert "kind: Ingress" not in manifest


def test_replicas_configurable(helm_template):
    manifest = helm_template(chart="router", set_values=["replicaCount=5"])
    assert "replicas: 5" in manifest
```

- [ ] **Step 3: Run chart tests**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/chart -v
```

Expected: all chart tests pass (old + new).

- [ ] **Step 4: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add tests/chart/
git commit -m "test(chart): llm-router rendering + RBAC + ConfigMap"
```

---

## Task 4.5: Dockerfile.router (multi-stage)

**Files:**
- Create: `docker/Dockerfile.router`

- [ ] **Step 1: Dockerfile**

Write to `docker/Dockerfile.router`:

```dockerfile
# syntax=docker/dockerfile:1.7

# --- Stage 1: build Python deps ---
FROM python:3.11-slim AS builder
WORKDIR /build
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
RUN if [ -f uv.lock ]; then \
      uv export --frozen --no-dev -o requirements.txt; \
    else \
      uv pip compile pyproject.toml -o requirements.txt; \
    fi
RUN uv pip install --system --no-cache -r requirements.txt

# --- Stage 2: runtime ---
FROM python:3.11-slim AS runtime

# Helm CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates bash && \
    curl -fsSL https://get.helm.sh/helm-v3.14.0-linux-amd64.tar.gz \
        | tar -xz -C /tmp && \
    mv /tmp/linux-amd64/helm /usr/local/bin/helm && \
    rm -rf /tmp/linux-amd64 /var/lib/apt/lists/* && \
    helm version --short

# App code
WORKDIR /app
COPY charts/ /chart-source/
COPY src/k8s_llm_runtime/ /app/src/k8s_llm_runtime/
COPY examples/vllm-qwen/server.py /app/server.py

# Python deps from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_CONFIG_PATH=/app/config/models.yaml \
    CHART_PATH=/app/charts/llm-inference

EXPOSE 8080

USER 1000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
```

- [ ] **Step 2: Build image**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
docker build -f docker/Dockerfile.router -t router:dev .
```

Expected: build succeeds, image ~250MB.

- [ ] **Step 3: Smoke-test image**

```bash
docker run --rm router:dev --help
docker run --rm -p 8080:8080 router:dev &
sleep 5
curl -sf http://localhost:8080/healthz
```

Expected: `{"status":"healthy"}`.

- [ ] **Step 4: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add docker/
git commit -m "feat(docker): multi-stage Dockerfile for Router"
```

---

## Phase 4 Verification

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make test                       # all unit + chart tests pass
make lint
make type-check
helm lint charts/llm-router
docker build -f docker/Dockerfile.router -t router:dev .  # builds clean
```

End-of-phase state:
- `examples/vllm-qwen/server.py` serves FastAPI with 7 endpoints
- `charts/llm-router/` complete with RBAC + ConfigMap
- Docker image builds and starts

Proceed to **Phase 5** (`2026-06-24-k8s-llm-runtime-phase5.md`).
