# Phase 3 (Week 3): ModelOperator + K8sLeaseLock

**End-of-phase deliverable:** `ModelOperator` with auto-deploy-on-demand working in unit tests; `K8sLeaseLock` ready for integration testing.

**Working directory:** `/work/run/projects/bio-24/my_projects/k8s-llm-runtime/`

---

## Task 3.1: K8sLeaseLock (distributed lock via Lease)

**Files:**
- Modify: `src/k8s_llm_runtime/_client.py` (add coordination_api)
- Create: `src/k8s_llm_runtime/lock.py`
- Create: `tests/unit/test_lock.py`

- [ ] **Step 1: Add coordination_api to _client.py**

Replace `src/k8s_llm_runtime/_client.py`:

```python
"""Singleton wrapper around the official kubernetes Python client."""
from __future__ import annotations

import os
from typing import Optional

from kubernetes import client, config
from kubernetes.config import ConfigException


_batch_api: Optional[client.BatchV1Api] = None
_core_api: Optional[client.CoreV1Api] = None
_coordination_api: Optional[client.CoordinationV1Api] = None
_config_loaded: bool = False


def load_config(kubeconfig_path: Optional[str] = None) -> None:
    global _config_loaded
    if _config_loaded:
        return

    path = kubeconfig_path or os.environ.get("KUBECONFIG")

    try:
        if path:
            config.load_kube_config(config_file=path)
        else:
            config.load_kube_config()
    except ConfigException:
        config.load_incluster_config()

    _config_loaded = True


def batch_api() -> client.BatchV1Api:
    global _batch_api
    if _batch_api is None:
        load_config()
        _batch_api = client.BatchV1Api()
    return _batch_api


def core_api() -> client.CoreV1Api:
    global _core_api
    if _core_api is None:
        load_config()
        _core_api = client.CoreV1Api()
    return _core_api


def coordination_api() -> client.CoordinationV1Api:
    global _coordination_api
    if _coordination_api is None:
        load_config()
        _coordination_api = client.CoordinationV1Api()
    return _coordination_api
```

- [ ] **Step 2: Write failing test for lock**

Write to `tests/unit/test_lock.py`:

```python
"""Tests for K8sLeaseLock."""
import asyncio
from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.rest import ApiException

from k8s_llm_runtime.errors import LockAcquireTimeoutError
from k8s_llm_runtime.lock import K8sLeaseLock


@pytest.fixture
def mock_coord_api():
    api = MagicMock()
    api.create_namespaced_lease = MagicMock()
    api.read_namespaced_lease = MagicMock()
    api.replace_namespaced_lease = MagicMock()
    api.delete_namespaced_lease = MagicMock()
    return api


def _make_spec(holder="other-pod", acquired_at=0):
    spec = MagicMock()
    spec.holder_identity = holder
    spec.acquire_time = MagicMock()
    spec.acquire_time.timestamp = MagicMock(return_value=acquired_at)
    spec.renew_time = MagicMock()
    return spec


def test_acquire_succeeds_when_lease_free(mock_coord_api):
    # read_namespaced_lease raises 404 → create succeeds
    mock_coord_api.read_namespaced_lease.side_effect = ApiException(status=404, reason="not found")
    mock_coord_api.create_namespaced_lease.return_value = None
    lock = K8sLeaseLock(key="deploy-qwen", namespace="ns", ttl=60)

    with patch("k8s_llm_runtime.lock._client.coordination_api",
               return_value=mock_coord_api):
        asyncio.run(lock.acquire())

    mock_coord_api.create_namespaced_lease.assert_called_once()


def test_acquire_replaces_expired_lease(mock_coord_api):
    # Lease exists but expired (acquired at 0, now=1000, ttl=60)
    mock_lease = MagicMock()
    mock_lease.spec = _make_spec(holder="other-pod", acquired_at=0)
    mock_coord_api.read_namespaced_lease.return_value = mock_lease
    mock_coord_api.replace_namespaced_lease.return_value = None
    lock = K8sLeaseLock(key="deploy-qwen", namespace="ns", ttl=60)

    with patch("k8s_llm_runtime.lock._client.coordination_api",
               return_value=mock_coord_api), \
         patch("k8s_llm_runtime.lock.time.time", return_value=1000):
        asyncio.run(lock.acquire())

    mock_coord_api.replace_namespaced_lease.assert_called_once()


def test_acquire_raises_when_held_by_other(mock_coord_api):
    # Lease exists and NOT expired (acquired recently)
    mock_lease = MagicMock()
    mock_lease.spec = _make_spec(holder="other-pod", acquired_at=0)
    mock_coord_api.read_namespaced_lease.return_value = mock_lease
    lock = K8sLeaseLock(
        key="deploy-qwen", namespace="ns", ttl=60,
        acquire_timeout=0.1, poll_interval=0.05,
    )

    with patch("k8s_llm_runtime.lock._client.coordination_api",
               return_value=mock_coord_api), \
         patch("k8s_llm_runtime.lock.time.time", return_value=10):
        with pytest.raises(LockAcquireTimeoutError):
            asyncio.run(lock.acquire())


def test_release_deletes_lease(mock_coord_api):
    lock = K8sLeaseLock(key="deploy-qwen", namespace="ns", ttl=60)
    lock._held = True

    with patch("k8s_llm_runtime.lock._client.coordination_api",
               return_value=mock_coord_api):
        asyncio.run(lock.release())

    mock_coord_api.delete_namespaced_lease.assert_called_once()


def test_release_silently_ignores_404(mock_coord_api):
    mock_coord_api.delete_namespaced_lease.side_effect = ApiException(status=404, reason="gone")
    lock = K8sLeaseLock(key="k", namespace="ns", ttl=60)
    lock._held = True

    with patch("k8s_llm_runtime.lock._client.coordination_api",
               return_value=mock_coord_api):
        # Should not raise
        asyncio.run(lock.release())


def test_release_noop_when_not_held(mock_coord_api):
    lock = K8sLeaseLock(key="k", namespace="ns", ttl=60)
    with patch("k8s_llm_runtime.lock._client.coordination_api",
               return_value=mock_coord_api):
        asyncio.run(lock.release())
    mock_coord_api.delete_namespaced_lease.assert_not_called()


@pytest.mark.asyncio
async def test_async_context_manager(mock_coord_api):
    mock_coord_api.read_namespaced_lease.side_effect = ApiException(status=404, reason="nf")
    mock_coord_api.create_namespaced_lease.return_value = None
    mock_coord_api.delete_namespaced_lease.return_value = None
    lock = K8sLeaseLock(key="k", namespace="ns", ttl=60)

    with patch("k8s_llm_runtime.lock._client.coordination_api",
               return_value=mock_coord_api):
        async with lock:
            mock_coord_api.create_namespaced_lease.assert_called_once()
        mock_coord_api.delete_namespaced_lease.assert_called_once()
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_lock.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Implement K8sLeaseLock**

Write to `src/k8s_llm_runtime/lock.py`:

```python
"""Distributed lock backed by Kubernetes Lease objects."""
from __future__ import annotations

import asyncio
import os
import socket
import time
import uuid
from datetime import datetime, timezone

from kubernetes import client
from kubernetes.client.rest import ApiException

from k8s_llm_runtime import _client
from k8s_llm_runtime.errors import LockAcquireTimeoutError


def _hostname() -> str:
    return os.environ.get("POD_NAME") or f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"


class K8sLeaseLock:
    """Async distributed lock via coordination.k8s.io/v1 Lease."""

    def __init__(
        self,
        key: str,
        namespace: str = "default",
        ttl: int = 60,
        acquire_timeout: float = 600,
        poll_interval: float = 2.0,
    ):
        self.key = key
        self.namespace = namespace
        self.ttl = ttl
        self.acquire_timeout = acquire_timeout
        self.poll_interval = poll_interval
        self._holder = _hostname()
        self._held = False

    async def __aenter__(self) -> "K8sLeaseLock":
        await self.acquire()
        return self

    async def __aexit__(self, *exc):
        await self.release()

    async def acquire(self) -> None:
        deadline = time.time() + self.acquire_timeout
        while True:
            if self._try_acquire_once():
                self._held = True
                return
            if time.time() >= deadline:
                raise LockAcquireTimeoutError(
                    f"Could not acquire lease {self.key} in {self.acquire_timeout}s"
                )
            await asyncio.sleep(self.poll_interval)

    async def release(self) -> None:
        if not self._held:
            return
        try:
            _client.coordination_api().delete_namespaced_lease(
                name=self.key, namespace=self.namespace,
            )
        except ApiException as exc:
            if exc.status != 404:
                raise
        finally:
            self._held = False

    def _try_acquire_once(self) -> bool:
        api = _client.coordination_api()
        try:
            existing = api.read_namespaced_lease(
                name=self.key, namespace=self.namespace,
            )
            holder = existing.spec.holder_identity
            acquired_at = existing.spec.acquire_time
            if holder and acquired_at and self._is_expired(acquired_at):
                api.replace_namespaced_lease(
                    name=self.key, namespace=self.namespace,
                    body=self._build_lease(),
                )
                return True
            return False
        except ApiException as exc:
            if exc.status == 404:
                api.create_namespaced_lease(
                    namespace=self.namespace,
                    body=self._build_lease(),
                )
                return True
            raise

    def _is_expired(self, acquired_at: datetime) -> bool:
        if acquired_at is None:
            return True
        elapsed = time.time() - acquired_at.timestamp()
        return elapsed > self.ttl

    def _build_lease(self) -> client.V1Lease:
        now = datetime.now(timezone.utc)
        return client.V1Lease(
            api_version="coordination.k8s.io/v1",
            kind="Lease",
            metadata=client.V1ObjectMeta(name=self.key, namespace=self.namespace),
            spec=client.V1LeaseSpec(
                holder_identity=self._holder,
                acquire_time=now,
                renew_time=now,
                lease_duration_seconds=self.ttl,
            ),
        )
```

- [ ] **Step 5: Run tests**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_lock.py -v
```

Expected: 7 tests pass.

- [ ] **Step 6: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add src/k8s_llm_runtime/_client.py src/k8s_llm_runtime/lock.py tests/unit/test_lock.py
git commit -m "feat(lock): K8sLeaseLock via coordination.k8s.io Lease"
```

---

## Task 3.2: _log.py (structlog config)

**Files:**
- Create: `src/k8s_llm_runtime/_log.py`

- [ ] **Step 1: Implement structlog config**

Write to `src/k8s_llm_runtime/_log.py`:

```python
"""structlog configuration for JSON-structured logging."""
from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog to emit JSON to stdout."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    return structlog.get_logger(name)
```

- [ ] **Step 2: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add src/k8s_llm_runtime/_log.py
git commit -m "feat(log): structlog JSON logging config"
```

---

## Task 3.3: _metrics.py (Prometheus definitions)

**Files:**
- Create: `src/k8s_llm_runtime/_metrics.py`

- [ ] **Step 1: Implement metric definitions**

Write to `src/k8s_llm_runtime/_metrics.py`:

```python
"""Prometheus metric definitions."""
from prometheus_client import Counter, Gauge, Histogram

# --- K8s operations ---
JOBS_CREATED = Counter(
    "k8s_jobs_created_total",
    "K8s Jobs created",
    labelnames=("vendor", "result"),
)

# --- vLLM deploy ---
VLLM_DEPLOY_DURATION = Histogram(
    "vllm_deploy_duration_seconds",
    "vLLM Helm deploy duration",
    labelnames=("model_alias",),
)

VLLM_DEPLOY_FAILURES = Counter(
    "vllm_deploy_failures_total",
    "vLLM deploy failures",
    labelnames=("model_alias", "reason"),
)

# --- Inference routing ---
INFERENCE_REQUESTS = Counter(
    "inference_requests_total",
    "Inference requests",
    labelnames=("model_alias", "status"),
)

INFERENCE_LATENCY = Histogram(
    "inference_latency_seconds",
    "Inference request latency",
    labelnames=("model_alias",),
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300),
)

MODELS_LOADED = Gauge(
    "models_loaded",
    "Currently loaded model count",
    labelnames=("model_alias",),
)
```

- [ ] **Step 2: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add src/k8s_llm_runtime/_metrics.py
git commit -m "feat(metrics): Prometheus metric definitions"
```

---

## Task 3.4: ModelOperator (high-level router)

**Files:**
- Create: `src/k8s_llm_runtime/model.py`
- Modify: `src/k8s_llm_runtime/__init__.py`
- Create: `tests/unit/test_model.py`

- [ ] **Step 1: Write failing test**

Write to `tests/unit/test_model.py`:

```python
"""Tests for ModelOperator."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from k8s_llm_runtime.errors import (
    ModelAliasError,
    ModelNotFoundError,
    VLLMDeployError,
    VLLMDeployTimeoutError,
)
from k8s_llm_runtime.model import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ModelOperator,
)
from k8s_llm_runtime.types import GPUResource, GPUVendor
from k8s_llm_runtime.vllm import VLLMDeployment


@pytest.fixture
def mock_vllm_op():
    op = MagicMock()
    op.get_endpoint.return_value = "http://qwen.llm-models.svc.cluster.local:8000"
    op.get_status.return_value = VLLMDeployment(
        release_name="qwen", namespace="llm-models", model_name="",
        endpoint="http://qwen.llm-models.svc.cluster.local:8000",
        phase="ready", replicas_ready=1,
    )
    op.deploy = MagicMock(return_value=VLLMDeployment(
        release_name="qwen", namespace="llm-models",
        model_name="Qwen/Qwen2.5-0.5B-Instruct",
        endpoint="http://qwen.llm-models.svc.cluster.local:8000",
        phase="ready", replicas_ready=1,
    ))
    return op


@pytest.fixture
def op(mock_vllm_op):
    return ModelOperator(
        model_aliases={"qwen-0.5b": "Qwen/Qwen2.5-0.5B-Instruct"},
        vllm_op=mock_vllm_op,
        namespace="llm-models",
        default_gpu=GPUResource(vendor=GPUVendor.AMD, limit=1),
    )


def _mock_response(payload, status_code=200):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp,
        )
    return resp


def test_alias_required():
    with pytest.raises(ModelAliasError):
        ModelOperator(model_aliases={}, vllm_op=MagicMock())


def test_chat_unknown_alias_raises(op):
    req = ChatRequest(model="unknown-llm",
                      messages=[ChatMessage(role="user", content="hi")])
    with pytest.raises(ModelNotFoundError):
        asyncio.run(op.chat(req))


def test_chat_routes_to_ready_deployment(op, mock_vllm_op):
    req = ChatRequest(model="qwen-0.5b",
                      messages=[ChatMessage(role="user", content="hi")])
    payload = {
        "id": "chatcmpl-1", "object": "chat.completion", "created": 1,
        "model": "qwen-0.5b",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "hello"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    with patch("k8s_llm_runtime.model.httpx.AsyncClient") as mock_client_cls:
        client_instance = AsyncMock()
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=None)
        client_instance.post = AsyncMock(return_value=_mock_response(payload))
        mock_client_cls.return_value = client_instance

        resp = asyncio.run(op.chat(req))

    mock_vllm_op.deploy.assert_not_called()
    assert resp.model == "qwen-0.5b"
    assert resp.choices[0]["message"]["content"] == "hello"


def test_chat_deploys_when_not_ready(op, mock_vllm_op):
    mock_vllm_op.get_status.return_value = VLLMDeployment(
        release_name="qwen", namespace="llm-models", model_name="",
        endpoint="http://qwen.llm-models.svc.cluster.local:8000",
        phase="pending", replicas_ready=0,
    )
    req = ChatRequest(model="qwen-0.5b",
                      messages=[ChatMessage(role="user", content="hi")])
    payload = {"id": "x", "object": "chat.completion", "created": 1,
               "model": "qwen-0.5b", "choices": [], "usage": {}}
    with patch("k8s_llm_runtime.model.httpx.AsyncClient") as mock_client_cls, \
         patch("k8s_llm_runtime.model.K8sLeaseLock") as mock_lock_cls:
        mock_lock = AsyncMock()
        mock_lock.__aenter__ = AsyncMock(return_value=mock_lock)
        mock_lock.__aexit__ = AsyncMock(return_value=None)
        mock_lock_cls.return_value = mock_lock
        client_instance = AsyncMock()
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=None)
        client_instance.post = AsyncMock(return_value=_mock_response(payload))
        mock_client_cls.return_value = client_instance

        asyncio.run(op.chat(req))

    mock_vllm_op.deploy.assert_called_once()
    assert "qwen-0.5b" in mock_lock_cls.call_args.kwargs["key"]


def test_chat_propagates_deploy_error(op, mock_vllm_op):
    mock_vllm_op.get_status.return_value = VLLMDeployment(
        release_name="qwen", namespace="llm-models", model_name="",
        endpoint="", phase="failed", replicas_ready=0,
    )
    mock_vllm_op.deploy.side_effect = VLLMDeployError("boom")
    req = ChatRequest(model="qwen-0.5b",
                      messages=[ChatMessage(role="user", content="hi")])
    with patch("k8s_llm_runtime.model.K8sLeaseLock") as mock_lock_cls:
        mock_lock = AsyncMock()
        mock_lock.__aenter__ = AsyncMock(return_value=mock_lock)
        mock_lock.__aexit__ = AsyncMock(return_value=None)
        mock_lock_cls.return_value = mock_lock
        with pytest.raises(VLLMDeployError):
            asyncio.run(op.chat(req))


def test_chat_raises_deploy_timeout(op, mock_vllm_op):
    mock_vllm_op.get_status.return_value = VLLMDeployment(
        release_name="qwen", namespace="llm-models", model_name="",
        endpoint="", phase="pending", replicas_ready=0,
    )
    mock_vllm_op.deploy.side_effect = VLLMDeployTimeoutError("timeout")
    req = ChatRequest(model="qwen-0.5b",
                      messages=[ChatMessage(role="user", content="hi")])
    with patch("k8s_llm_runtime.model.K8sLeaseLock") as mock_lock_cls:
        mock_lock = AsyncMock()
        mock_lock.__aenter__ = AsyncMock(return_value=mock_lock)
        mock_lock.__aexit__ = AsyncMock(return_value=None)
        mock_lock_cls.return_value = mock_lock
        with pytest.raises(VLLMDeployTimeoutError):
            asyncio.run(op.chat(req))


def test_list_models_returns_loaded(op):
    op._loaded.add("qwen-0.5b")
    assert asyncio.run(op.list_models()) == ["qwen-0.5b"]


def test_unload_calls_undeploy(op, mock_vllm_op):
    op._loaded.add("qwen-0.5b")
    asyncio.run(op.unload("qwen-0.5b"))
    mock_vllm_op.undeploy.assert_called_once_with("qwen-0.5b", "llm-models")
    assert "qwen-0.5b" not in op._loaded


def test_unload_silent_when_not_loaded(op, mock_vllm_op):
    asyncio.run(op.unload("not-loaded"))
    mock_vllm_op.undeploy.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_model.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement ModelOperator**

Write to `src/k8s_llm_runtime/model.py`:

```python
"""High-level model serving router."""
from __future__ import annotations

import json
import os
import subprocess
import time
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict

from k8s_llm_runtime import _metrics
from k8s_llm_runtime._log import get_logger
from k8s_llm_runtime.errors import (
    ModelAliasError,
    ModelNotFoundError,
    VLLMDeployError,
)
from k8s_llm_runtime.lock import K8sLeaseLock
from k8s_llm_runtime.types import GPUResource
from k8s_llm_runtime.vllm import VLLMDeployment, VLLMInferenceOperator

logger = get_logger(__name__)


# --- OpenAI-compatible Pydantic models ---


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str  # alias, e.g. "qwen-0.5b"
    messages: list[ChatMessage]
    temperature: float = 1.0
    max_tokens: int = 1024
    stream: bool = False  # reserved for v1.1


class ChatResponse(BaseModel):
    """OpenAI-compatible response; allows extra fields from vLLM."""

    model_config = ConfigDict(extra="allow")

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict]
    usage: dict


# --- Operator ---


class ModelOperator:
    """Routes user requests to deployed vLLM pods, auto-deploying on demand."""

    def __init__(
        self,
        model_aliases: dict[str, str],
        vllm_op: VLLMInferenceOperator,
        namespace: str = "llm-models",
        default_gpu: GPUResource = GPUResource(),
        default_replicas: int = 1,
        idle_timeout_seconds: int = 0,
        deploy_lock_ttl: int = 600,
        deploy_timeout: int = 600,
        request_timeout: float = 300.0,
    ):
        if not model_aliases:
            raise ModelAliasError("model_aliases cannot be empty")
        self.model_aliases = model_aliases
        self.vllm_op = vllm_op
        self.namespace = namespace
        self.default_gpu = default_gpu
        self.default_replicas = default_replicas
        self.idle_timeout_seconds = idle_timeout_seconds
        self.deploy_lock_ttl = deploy_lock_ttl
        self.deploy_timeout = deploy_timeout
        self.request_timeout = request_timeout
        self._loaded: set[str] = set()
        self._last_used: dict[str, float] = {}

    async def chat(self, req: ChatRequest) -> ChatResponse:
        """Route chat request. Auto-deploys model if not yet ready."""
        hf_model = self.model_aliases.get(req.model)
        if not hf_model:
            raise ModelNotFoundError(
                f"Unknown model alias: {req.model}. "
                f"Available: {list(self.model_aliases.keys())}"
            )

        start = time.time()
        lock = K8sLeaseLock(
            key=f"deploy-{req.model}",
            namespace=self.namespace,
            ttl=self.deploy_lock_ttl,
            acquire_timeout=self.deploy_timeout,
        )

        try:
            async with lock:
                status = self.vllm_op.get_status(req.model, self.namespace)
                if status.phase != "ready" or status.replicas_ready == 0:
                    logger.info("deploying_model", alias=req.model, hf_model=hf_model)
                    with _metrics.VLLM_DEPLOY_DURATION.labels(
                        model_alias=req.model
                    ).time():
                        try:
                            status = self.vllm_op.deploy(
                                release_name=req.model,
                                model_name=hf_model,
                                namespace=self.namespace,
                                gpu=self.default_gpu,
                                replicas=self.default_replicas,
                                timeout=self.deploy_timeout,
                            )
                        except VLLMDeployError:
                            _metrics.VLLM_DEPLOY_FAILURES.labels(
                                model_alias=req.model, reason="deploy_error",
                            ).inc()
                            raise
                self._loaded.add(req.model)

            # Forward request (outside lock)
            endpoint = status.endpoint or self.vllm_op.get_endpoint(
                req.model, self.namespace,
            )
            payload = req.model_dump(exclude_none=True)
            payload["model"] = hf_model  # forward HF model name to vLLM

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{endpoint}/v1/chat/completions",
                    json=payload,
                    timeout=self.request_timeout,
                )
                resp.raise_for_status()
                body = resp.json()

            self._last_used[req.model] = time.time()
            _metrics.INFERENCE_LATENCY.labels(model_alias=req.model).observe(
                time.time() - start
            )
            _metrics.INFERENCE_REQUESTS.labels(
                model_alias=req.model, status="ok",
            ).inc()
            _metrics.MODELS_LOADED.labels(model_alias=req.model).set(1)
            return ChatResponse.model_validate(body)

        except httpx.HTTPError:
            _metrics.INFERENCE_REQUESTS.labels(
                model_alias=req.model, status="error",
            ).inc()
            raise

    async def list_models(self) -> list[str]:
        return sorted(self._loaded)

    async def unload(self, alias: str) -> None:
        if alias not in self._loaded:
            return
        self.vllm_op.undeploy(alias, self.namespace)
        self._loaded.discard(alias)
        self._last_used.pop(alias, None)
        _metrics.MODELS_LOADED.labels(model_alias=alias).set(0)

    async def discover_existing(self) -> None:
        """Rebuild loaded-set from current helm releases in namespace."""
        env = os.environ.copy()
        kubeconfig = self.vllm_op.kubeconfig
        if kubeconfig:
            env["KUBECONFIG"] = kubeconfig
        result = subprocess.run(
            ["helm", "list", "--namespace", self.namespace, "-q", "--output", "json"],
            capture_output=True, text=True, env=env,
        )
        if result.returncode != 0:
            return
        try:
            releases = json.loads(result.stdout)
        except json.JSONDecodeError:
            return
        for release in releases:
            name = release.get("name")
            if name and name in self.model_aliases:
                self._loaded.add(name)
                _metrics.MODELS_LOADED.labels(model_alias=name).set(1)
```

- [ ] **Step 4: Update package __init__**

Replace `src/k8s_llm_runtime/__init__.py`:

```python
"""k8s-llm-runtime: Kubernetes-based vLLM model serving router."""

from k8s_llm_runtime.errors import K8sLLMRuntimeError
from k8s_llm_runtime.job import K8sJobOperator
from k8s_llm_runtime.lock import K8sLeaseLock
from k8s_llm_runtime.model import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ModelOperator,
)
from k8s_llm_runtime.types import (
    ContainerSpec,
    GPUResource,
    GPUVendor,
    JobSpec,
    JobStatus,
    ResourceSpec,
)
from k8s_llm_runtime.vllm import VLLMDeployment, VLLMInferenceOperator

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ContainerSpec",
    "GPUResource",
    "GPUVendor",
    "JobSpec",
    "JobStatus",
    "K8sJobOperator",
    "K8sLLMRuntimeError",
    "K8sLeaseLock",
    "ModelOperator",
    "ResourceSpec",
    "VLLMDeployment",
    "VLLMInferenceOperator",
]
```

- [ ] **Step 5: Run all unit tests + lint + type-check**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make test
make lint
make type-check
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add src/k8s_llm_runtime/model.py src/k8s_llm_runtime/_log.py src/k8s_llm_runtime/_metrics.py src/k8s_llm_runtime/lock.py src/k8s_llm_runtime/__init__.py tests/unit/test_model.py tests/unit/test_lock.py
git commit -m "feat(model): ModelOperator with auto-deploy, distributed lock, OpenAI-compat"
```

---

## Phase 3 Verification

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make test           # all unit + chart tests pass
make lint           # ruff passes
make type-check     # mypy strict passes
```

End-of-phase state:
- 10 source modules in `src/k8s_llm_runtime/`
- ~50 unit tests total
- All 4 metrics exported and exercised in ModelOperator
- Distributed lock ready (integration tested in Phase 5)

Proceed to **Phase 4** (`2026-06-24-k8s-llm-runtime-phase4.md`).
