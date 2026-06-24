# Phase 1 (Week 1): Project skeleton + K8sJobOperator

**End-of-phase deliverable:** `K8sJobOperator` fully implemented with unit tests, project builds with uv, CI lint passes.

**Working directory:** `/work/run/projects/bio-24/my_projects/k8s-llm-runtime/`

---

## Task 1.1: Initialize uv project

**Files:**
- Create: `pyproject.toml`
- Create: `Makefile`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "k8s-llm-runtime"
version = "0.1.0"
description = "Kubernetes-based vLLM model serving router"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "bio-24" }]
dependencies = [
    "kubernetes>=29.0.0",
    "pydantic>=2.6.0",
    "structlog>=24.1.0",
    "prometheus-client>=0.20.0",
    "tenacity>=8.2.0",
    "httpx>=0.27.0",
    "pyyaml>=6.0",
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
    "pytest-cov>=4.1.0",
    "respx>=0.21.0",
    "ruff>=0.3.0",
    "mypy>=1.8.0",
    "openai>=1.30.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/k8s_llm_runtime"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "N", "ASYNC"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
files = ["src/k8s_llm_runtime"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests/unit", "tests/chart"]
addopts = "-v --tb=short"
```

- [ ] **Step 2: Create Makefile**

```makefile
.PHONY: help install lint format type-check test test-unit test-chart test-integration cluster-up cluster-down clean

CLUSTER ?= kind
KUBECONFIG ?= ./kubeconfig

help:
	@echo "Targets:"
	@echo "  install         - Install dev deps via uv"
	@echo "  lint            - Run ruff check"
	@echo "  format          - Run ruff format"
	@echo "  type-check      - Run mypy strict"
	@echo "  test            - Run unit + chart tests"
	@echo "  test-integration- Run kind e2e tests"
	@echo "  cluster-up      - Start \$$(CLUSTER) cluster"

install:
	uv sync --all-extras

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

type-check:
	uv run mypy src/k8s_llm_runtime

test: test-unit test-chart

test-unit:
	uv run pytest tests/unit -v

test-chart:
	uv run pytest tests/chart -v

test-integration:
	uv run pytest tests/integration -v

cluster-up:
	@./scripts/cluster/$(CLUSTER)-up.sh

cluster-down:
	@./scripts/cluster/$(CLUSTER)-down.sh

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache htmlcov *.egg-info dist
	find . -type d -name __pycache__ -exec rm -rf {} +
```

- [ ] **Step 3: Sync and verify**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime && uv sync --all-extras
```

- [ ] **Step 4: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add pyproject.toml Makefile uv.lock
git commit -m "feat: initialize uv project with pyproject + Makefile"
```

---

## Task 1.2: Create errors module

**Files:**
- Create: `src/k8s_llm_runtime/__init__.py`
- Create: `src/k8s_llm_runtime/errors.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/test_errors.py`

- [ ] **Step 1: Create package __init__**

Write to `src/k8s_llm_runtime/__init__.py`:

```python
"""k8s-llm-runtime: Kubernetes-based vLLM model serving router."""

__version__ = "0.1.0"
```

- [ ] **Step 2: Write failing test**

Write to `tests/unit/__init__.py`: empty file.

Write to `tests/unit/test_errors.py`:

```python
"""Tests for the typed exception hierarchy."""
import pytest

from k8s_llm_runtime.errors import (
    K8sLLMRuntimeError,
    JobCreationError,
    JobTimeoutError,
    JobLogRetrievalError,
    LockAcquireTimeoutError,
    ModelAliasError,
    ModelNotFoundError,
    VLLMDeployError,
    VLLMDeployTimeoutError,
    VLLMUndeployError,
)


def test_k8s_llm_runtime_error_is_base():
    for cls in [
        JobCreationError, JobTimeoutError, JobLogRetrievalError,
        VLLMDeployError, VLLMDeployTimeoutError, VLLMUndeployError,
        ModelNotFoundError, ModelAliasError, LockAcquireTimeoutError,
    ]:
        assert issubclass(cls, K8sLLMRuntimeError)


def test_vllm_deploy_timeout_inherits_deploy_error():
    assert issubclass(VLLMDeployTimeoutError, VLLMDeployError)


def test_job_creation_error_message():
    err = JobCreationError("test job")
    assert "test job" in str(err)
    assert isinstance(err, K8sLLMRuntimeError)


def test_model_not_found_error_carries_alias():
    err = ModelNotFoundError("qwen-99b")
    assert "qwen-99b" in str(err)


def test_lock_acquire_timeout_raises_in_caller():
    with pytest.raises(K8sLLMRuntimeError):
        raise LockAcquireTimeoutError("key=deploy-qwen")
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_errors.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'k8s_llm_runtime.errors'`

- [ ] **Step 4: Implement errors module**

Write to `src/k8s_llm_runtime/errors.py`:

```python
"""Typed exception hierarchy for k8s-llm-runtime.

All exceptions inherit from K8sLLMRuntimeError so callers can catch
the entire library's errors with a single except clause.
"""


class K8sLLMRuntimeError(Exception):
    """Base class for all errors raised by this library."""


# --- K8s Job layer ---


class JobCreationError(K8sLLMRuntimeError):
    """Failed to create a Kubernetes Job."""


class JobTimeoutError(K8sLLMRuntimeError):
    """Job did not complete within the timeout."""


class JobLogRetrievalError(K8sLLMRuntimeError):
    """Failed to fetch pod logs for a Job."""


# --- vLLM layer ---


class VLLMDeployError(K8sLLMRuntimeError):
    """Base error for vLLM Helm operations."""


class VLLMDeployTimeoutError(VLLMDeployError):
    """vLLM Helm install did not become ready within the timeout."""


class VLLMUndeployError(K8sLLMRuntimeError):
    """Failed to uninstall a vLLM Helm release."""


# --- Model routing layer ---


class ModelNotFoundError(K8sLLMRuntimeError):
    """Requested model alias is not configured."""


class ModelAliasError(K8sLLMRuntimeError):
    """Model alias configuration is invalid."""


# --- Locking ---


class LockAcquireTimeoutError(K8sLLMRuntimeError):
    """Failed to acquire a distributed lease within the timeout."""
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_errors.py -v
```

Expected: 5 tests pass.

- [ ] **Step 6: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add src/k8s_llm_runtime/__init__.py src/k8s_llm_runtime/errors.py tests/unit/
git commit -m "feat(errors): typed exception hierarchy"
```

---

## Task 1.3: Create types module (Pydantic models)

**Files:**
- Create: `src/k8s_llm_runtime/types.py`
- Create: `tests/unit/test_types.py`

- [ ] **Step 1: Write failing test**

Write to `tests/unit/test_types.py`:

```python
"""Tests for Pydantic data models."""
import pytest
from pydantic import ValidationError

from k8s_llm_runtime.types import (
    ContainerSpec,
    GPUResource,
    GPUVendor,
    JobSpec,
    JobStatus,
    ResourceSpec,
)


def test_gpu_vendor_enum_values():
    assert GPUVendor.NONE == "none"
    assert GPUVendor.NVIDIA == "nvidia"
    assert GPUVendor.AMD == "amd"


def test_gpu_resource_defaults():
    g = GPUResource()
    assert g.vendor == GPUVendor.NONE
    assert g.limit == 1


def test_resource_spec_defaults():
    r = ResourceSpec()
    assert r.cpu_request == "1"
    assert r.gpu.limit == 1
    assert r.gpu.vendor == GPUVendor.NONE


def test_container_spec_requires_image():
    with pytest.raises(ValidationError):
        ContainerSpec()


def test_container_spec_minimal():
    c = ContainerSpec(image="nginx:latest")
    assert c.image == "nginx:latest"
    assert c.command is None
    assert c.env == {}


def test_job_spec_defaults():
    spec = JobSpec(name="test-job", container=ContainerSpec(image="alpine"))
    assert spec.namespace == "default"
    assert spec.ttl_seconds_after_finished == 3600
    assert spec.backoff_limit == 3
    assert spec.restart_policy == "Never"


def test_job_spec_validates_restart_policy():
    with pytest.raises(ValidationError):
        JobSpec(
            name="x",
            container=ContainerSpec(image="alpine"),
            restart_policy="Always",
        )


def test_job_status_phase_enum():
    s = JobStatus(name="x", phase="running")
    assert s.active == 0
    assert s.phase == "running"


def test_job_status_rejects_invalid_phase():
    with pytest.raises(ValidationError):
        JobStatus(name="x", phase="unknown")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_types.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement types module**

Write to `src/k8s_llm_runtime/types.py`:

```python
"""Pydantic models shared across the library."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class GPUVendor(str, Enum):
    """GPU vendor selector for resource and node affinity configuration."""

    NONE = "none"
    NVIDIA = "nvidia"
    AMD = "amd"


class GPUResource(BaseModel):
    """GPU resource request."""

    vendor: GPUVendor = GPUVendor.NONE
    limit: int = Field(default=1, ge=1, le=8)


class ResourceSpec(BaseModel):
    """CPU, memory, and GPU resource requests/limits."""

    cpu_request: str = "1"
    cpu_limit: str = "2"
    memory_request: str = "1Gi"
    memory_limit: str = "2Gi"
    gpu: GPUResource = GPUResource()


class ContainerSpec(BaseModel):
    """Single container definition for a Job."""

    image: str
    command: Optional[list[str]] = None
    args: Optional[list[str]] = None
    env: dict[str, str] = Field(default_factory=dict)
    resources: ResourceSpec = ResourceSpec()
    ports: list[int] = Field(default_factory=list)


class JobSpec(BaseModel):
    """Kubernetes Job specification."""

    name: str
    namespace: str = "default"
    container: ContainerSpec
    service_account: Optional[str] = None
    ttl_seconds_after_finished: int = Field(default=3600, ge=0)
    backoff_limit: int = Field(default=3, ge=0)
    restart_policy: Literal["Never", "OnFailure"] = "Never"


class JobStatus(BaseModel):
    """Observed status of a Kubernetes Job."""

    name: str
    phase: Literal["pending", "running", "succeeded", "failed"]
    active: int = 0
    succeeded: int = 0
    failed: int = 0
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_types.py -v
```

Expected: 9 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add src/k8s_llm_runtime/types.py tests/unit/test_types.py
git commit -m "feat(types): Pydantic models for K8s Job and GPU resources"
```

---

## Task 1.4: Create _client module (kubernetes-client singleton)

**Files:**
- Create: `src/k8s_llm_runtime/_client.py`
- Create: `tests/unit/test_client.py`

- [ ] **Step 1: Write failing test**

Write to `tests/unit/test_client.py`:

```python
"""Tests for kubernetes-client singleton."""
from unittest.mock import patch

from kubernetes.config import ConfigException

from k8s_llm_runtime import _client


@pytest.fixture(autouse=True)
def reset_singletons():
    _client._batch_api = None
    _client._core_api = None
    _client._config_loaded = False
    yield
    _client._batch_api = None
    _client._core_api = None
    _client._config_loaded = False


def test_load_kube_config_uses_explicit_path(tmp_path):
    cfg_file = tmp_path / "kubeconfig"
    cfg_file.write_text("apiVersion: v1\nclusters: []\n")
    with patch("kubernetes.config.load_kube_config") as mock_load:
        _client.load_config(str(cfg_file))
        mock_load.assert_called_once()
        args, kwargs = mock_load.call_args
        assert args[0] == str(cfg_file)
        assert _client._config_loaded is True


def test_load_kube_config_falls_back_to_incluster():
    with patch("kubernetes.config.load_kube_config",
               side_effect=ConfigException("no kubeconfig")), \
         patch("kubernetes.config.load_incluster_config") as mock_incluster:
        _client.load_config(None)
        mock_incluster.assert_called_once()
        assert _client._config_loaded is True


def test_batch_api_lazy_loads():
    with patch.object(_client, "load_config") as mock_load:
        api = _client.batch_api()
        mock_load.assert_called_once()
        _client.batch_api()  # second call
        mock_load.assert_called_once()


def test_core_api_lazy_loads():
    with patch.object(_client, "load_config") as mock_load:
        _client.core_api()
        mock_load.assert_called_once()


def test_get_batch_api_returns_client_instance():
    with patch.object(_client, "load_config"):
        api = _client.batch_api()
        assert api is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_client.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement _client module**

Write to `src/k8s_llm_runtime/_client.py`:

```python
"""Singleton wrapper around the official kubernetes Python client.

Lazy-loads config and clients on first use. Honors `KUBECONFIG` env var
if `kubeconfig_path` is None.
"""
from __future__ import annotations

import os
from typing import Optional

from kubernetes import client, config
from kubernetes.config import ConfigException


_batch_api: Optional[client.BatchV1Api] = None
_core_api: Optional[client.CoreV1Api] = None
_config_loaded: bool = False


def load_config(kubeconfig_path: Optional[str] = None) -> None:
    """Load kubernetes config from explicit path or env or in-cluster."""
    global _config_loaded
    if _config_loaded:
        return

    path = kubeconfig_path or os.environ.get("KUBECONFIG")

    try:
        if path:
            config.load_kube_config(config_file=path)
        else:
            config.load_kube_config()  # default ~/.kube/config
    except ConfigException:
        config.load_incluster_config()

    _config_loaded = True


def batch_api() -> client.BatchV1Api:
    """Lazy-initialize and return the BatchV1Api client."""
    global _batch_api
    if _batch_api is None:
        load_config()
        _batch_api = client.BatchV1Api()
    return _batch_api


def core_api() -> client.CoreV1Api:
    """Lazy-initialize and return the CoreV1Api client."""
    global _core_api
    if _core_api is None:
        load_config()
        _core_api = client.CoreV1Api()
    return _core_api
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_client.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add src/k8s_llm_runtime/_client.py tests/unit/test_client.py
git commit -m "feat(client): lazy kubernetes-client singleton with config fallback"
```

---

## Task 1.5: Create _retry module (tenacity wrapper)

**Files:**
- Create: `src/k8s_llm_runtime/_retry.py`
- Create: `tests/unit/test_retry.py`

- [ ] **Step 1: Write failing test**

Write to `tests/unit/test_retry.py`:

```python
"""Tests for retry decorator."""
from kubernetes.client.rest import ApiException

from k8s_llm_runtime._retry import _is_transient, k8s_retry


def test_is_transient_returns_true_for_5xx():
    for status in (500, 502, 503, 504):
        exc = ApiException(status=status, reason="x")
        assert _is_transient(exc) is True


def test_is_transient_returns_true_for_429():
    exc = ApiException(status=429, reason="x")
    assert _is_transient(exc) is True


def test_is_transient_returns_false_for_4xx_other_than_429():
    for status in (400, 401, 403, 404, 409):
        exc = ApiException(status=status, reason="x")
        assert _is_transient(exc) is False


def test_is_transient_returns_false_for_non_api_exception():
    assert _is_transient(ValueError("x")) is False


def test_k8s_retry_succeeds_on_first_try():
    calls = []

    @k8s_retry
    def f(x):
        calls.append(x)
        return "ok"

    assert f(42) == "ok"
    assert calls == [42]


def test_k8s_retry_returns_function_result():
    @k8s_retry
    def double(x):
        return x * 2

    assert double(21) == 42
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_retry.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement _retry module**

Write to `src/k8s_llm_runtime/_retry.py`:

```python
"""Retry decorator for transient kubernetes API errors."""
from __future__ import annotations

import logging

from kubernetes.client.rest import ApiException
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


def _is_transient(exc: BaseException) -> bool:
    """Return True if the ApiException is retryable (5xx or 429)."""
    if isinstance(exc, ApiException):
        return exc.status in (429, 500, 502, 503, 504)
    return isinstance(exc, (TimeoutError, ConnectionError))


def k8s_retry(fn):
    """Decorator: retry transient K8s API errors with exponential backoff."""
    return Retrying(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception(_is_transient),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )(fn)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_retry.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add src/k8s_llm_runtime/_retry.py tests/unit/test_retry.py
git commit -m "feat(retry): tenacity wrapper with transient-error detection"
```

---

## Task 1.6: Implement K8sJobOperator

**Files:**
- Create: `src/k8s_llm_runtime/job.py`
- Modify: `src/k8s_llm_runtime/__init__.py`
- Create: `tests/unit/test_job.py`

- [ ] **Step 1: Write failing test**

Write to `tests/unit/test_job.py`:

```python
"""Tests for K8sJobOperator."""
from unittest.mock import MagicMock, patch

from kubernetes.client import V1Job

from k8s_llm_runtime.job import K8sJobOperator
from k8s_llm_runtime.types import (
    ContainerSpec,
    GPUResource,
    GPUVendor,
    JobSpec,
    ResourceSpec,
)


@pytest.fixture
def op():
    return K8sJobOperator(namespace="test-ns", kubeconfig="/tmp/fake")


def _mock_job_status(active=0, succeeded=0, failed=0):
    status = MagicMock()
    status.active = active
    status.succeeded = succeeded
    status.failed = failed
    status.start_time = None
    status.completion_time = None
    return status


def test_create_builds_and_submits_job(op):
    fake_batch = MagicMock()
    fake_batch.create_namespaced_job.return_value = V1Job()
    with patch("k8s_llm_runtime.job.batch_api", return_value=fake_batch):
        spec = JobSpec(name="hello", container=ContainerSpec(image="alpine:3.19"))
        returned = op.create(spec)
    assert returned == "hello"
    fake_batch.create_namespaced_job.assert_called_once()
    call = fake_batch.create_namespaced_job.call_args
    assert call.kwargs["namespace"] == "test-ns"
    body = call.kwargs["body"]
    assert body.metadata.name == "hello"
    assert body.metadata.namespace == "test-ns"


def test_create_sets_amd_gpu_resource():
    op = K8sJobOperator(namespace="ns")
    fake_batch = MagicMock()
    fake_batch.create_namespaced_job.return_value = V1Job()
    with patch("k8s_llm_runtime.job.batch_api", return_value=fake_batch):
        spec = JobSpec(
            name="gpu",
            container=ContainerSpec(
                image="rocm/pytorch",
                resources=ResourceSpec(gpu=GPUResource(vendor=GPUVendor.AMD, limit=2)),
            ),
        )
        op.create(spec)
    body = fake_batch.create_namespaced_job.call_args.kwargs["body"]
    container = body.spec.template.spec.containers[0]
    assert "amd.com/gpu" in container.resources.limits
    assert container.resources.limits["amd.com/gpu"] == "2"


def test_create_sets_nvidia_gpu_resource():
    op = K8sJobOperator(namespace="ns")
    fake_batch = MagicMock()
    fake_batch.create_namespaced_job.return_value = V1Job()
    with patch("k8s_llm_runtime.job.batch_api", return_value=fake_batch):
        spec = JobSpec(
            name="gpu",
            container=ContainerSpec(
                image="nvidia/cuda",
                resources=ResourceSpec(gpu=GPUResource(vendor=GPUVendor.NVIDIA, limit=1)),
            ),
        )
        op.create(spec)
    body = fake_batch.create_namespaced_job.call_args.kwargs["body"]
    container = body.spec.template.spec.containers[0]
    assert "nvidia.com/gpu" in container.resources.limits
    assert container.resources.limits["nvidia.com/gpu"] == "1"


def test_create_omits_gpu_resources_when_vendor_none():
    op = K8sJobOperator(namespace="ns")
    fake_batch = MagicMock()
    fake_batch.create_namespaced_job.return_value = V1Job()
    with patch("k8s_llm_runtime.job.batch_api", return_value=fake_batch):
        spec = JobSpec(name="cpu", container=ContainerSpec(image="alpine"))
        op.create(spec)
    body = fake_batch.create_namespaced_job.call_args.kwargs["body"]
    container = body.spec.template.spec.containers[0]
    assert "amd.com/gpu" not in container.resources.limits
    assert "nvidia.com/gpu" not in container.resources.limits


def test_get_status_parses_response(op):
    fake_job = MagicMock()
    fake_job.status = _mock_job_status(active=1)
    fake_batch = MagicMock()
    fake_batch.read_namespaced_job.return_value = fake_job
    with patch("k8s_llm_runtime.job.batch_api", return_value=fake_batch):
        status = op.get_status("hello")
    assert status.name == "hello"
    assert status.phase == "running"
    assert status.active == 1


def test_get_status_succeeded_phase(op):
    fake_job = MagicMock()
    fake_job.status = _mock_job_status(succeeded=1)
    fake_batch = MagicMock()
    fake_batch.read_namespaced_job.return_value = fake_job
    with patch("k8s_llm_runtime.job.batch_api", return_value=fake_batch):
        status = op.get_status("hello")
    assert status.phase == "succeeded"


def test_get_status_failed_phase(op):
    fake_job = MagicMock()
    fake_job.status = _mock_job_status(failed=1)
    fake_batch = MagicMock()
    fake_batch.read_namespaced_job.return_value = fake_job
    with patch("k8s_llm_runtime.job.batch_api", return_value=fake_batch):
        status = op.get_status("hello")
    assert status.phase == "failed"


def test_delete_submits_delete_request(op):
    fake_batch = MagicMock()
    with patch("k8s_llm_runtime.job.batch_api", return_value=fake_batch):
        op.delete("hello")
    fake_batch.delete_namespaced_job.assert_called_once()
    call = fake_batch.delete_namespaced_job.call_args
    assert call.kwargs["name"] == "hello"
    assert call.kwargs["namespace"] == "test-ns"


def test_get_logs_fetches_first_pod_logs(op):
    fake_pod = MagicMock()
    fake_pod.metadata.name = "hello-abc"
    fake_core = MagicMock()
    fake_core.list_namespaced_pod.return_value.items = [fake_pod]
    fake_core.read_namespaced_pod_log.return_value = "line1\nline2\n"
    with patch("k8s_llm_runtime.job.core_api", return_value=fake_core):
        logs = op.get_logs("hello")
    assert logs == "line1\nline2\n"
    assert fake_core.list_namespaced_pod.call_args.kwargs["label_selector"] == "job-name=hello"


def test_wait_for_completion_returns_status(op):
    fake_job = MagicMock()
    fake_job.status = _mock_job_status(succeeded=1)
    fake_batch = MagicMock()
    fake_batch.read_namespaced_job.return_value = fake_job
    with patch("k8s_llm_runtime.job.batch_api", return_value=fake_batch), \
         patch("k8s_llm_runtime.job.time.sleep"):
        status = op.wait_for_completion("hello", timeout=10, poll_interval=1)
    assert status.phase == "succeeded"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_job.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement K8sJobOperator**

Write to `src/k8s_llm_runtime/job.py`:

```python
"""Low-level K8s Job lifecycle management."""
from __future__ import annotations

import time
from typing import Optional

from kubernetes.client import (
    V1Container,
    V1EnvVar,
    V1Job,
    V1JobSpec,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1ResourceRequirements,
)

from k8s_llm_runtime import _client
from k8s_llm_runtime._retry import k8s_retry
from k8s_llm_runtime.errors import (
    JobCreationError,
    JobLogRetrievalError,
    JobTimeoutError,
)
from k8s_llm_runtime.types import ContainerSpec, GPUVendor, JobSpec, JobStatus


class K8sJobOperator:
    """Manages Kubernetes Jobs: create, query, wait, delete."""

    def __init__(self, namespace: str = "default", kubeconfig: Optional[str] = None):
        self.namespace = namespace
        self.kubeconfig = kubeconfig
        if kubeconfig is not None:
            _client.load_config(kubeconfig)

    @k8s_retry
    def create(self, spec: JobSpec) -> str:
        try:
            job = self._build_job(spec)
            _client.batch_api().create_namespaced_job(
                namespace=self.namespace, body=job,
            )
            return spec.name
        except Exception as exc:
            raise JobCreationError(f"Failed to create job {spec.name}: {exc}") from exc

    @k8s_retry
    def get_status(self, job_name: str) -> JobStatus:
        job = _client.batch_api().read_namespaced_job(
            name=job_name, namespace=self.namespace,
        )
        s = job.status
        phase = self._infer_phase(
            active=s.active or 0,
            succeeded=s.succeeded or 0,
            failed=s.failed or 0,
        )
        return JobStatus(
            name=job_name,
            phase=phase,
            active=s.active or 0,
            succeeded=s.succeeded or 0,
            failed=s.failed or 0,
            start_time=s.start_time,
            completion_time=s.completion_time,
        )

    @k8s_retry
    def get_logs(self, job_name: str, tail_lines: int = 200) -> str:
        try:
            pods = _client.core_api().list_namespaced_pod(
                namespace=self.namespace,
                label_selector=f"job-name={job_name}",
            )
            if not pods.items:
                return ""
            pod_name = pods.items[0].metadata.name
            return _client.core_api().read_namespaced_pod_log(
                name=pod_name,
                namespace=self.namespace,
                tail_lines=tail_lines,
            )
        except Exception as exc:
            raise JobLogRetrievalError(f"Failed to get logs for {job_name}: {exc}") from exc

    @k8s_retry
    def delete(self, job_name: str) -> None:
        _client.batch_api().delete_namespaced_job(
            name=job_name, namespace=self.namespace,
        )

    def wait_for_completion(
        self,
        job_name: str,
        timeout: int = 3600,
        poll_interval: int = 10,
    ) -> JobStatus:
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_status(job_name)
            if status.phase in ("succeeded", "failed"):
                return status
            time.sleep(poll_interval)
        raise JobTimeoutError(f"Job {job_name} did not complete within {timeout}s")

    def _build_job(self, spec: JobSpec) -> V1Job:
        container = self._build_container(spec.container)
        pod_spec = V1PodSpec(
            containers=[container],
            restart_policy=spec.restart_policy,
            service_account_name=spec.service_account,
        )
        template = V1PodTemplateSpec(
            metadata=V1ObjectMeta(labels={"app": spec.name}),
            spec=pod_spec,
        )
        job_spec = V1JobSpec(
            template=template,
            ttl_seconds_after_finished=spec.ttl_seconds_after_finished,
            backoff_limit=spec.backoff_limit,
        )
        return V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=V1ObjectMeta(name=spec.name, namespace=spec.namespace),
            spec=job_spec,
        )

    def _build_container(self, cs: ContainerSpec) -> V1Container:
        resources = V1ResourceRequirements(
            requests={
                "cpu": cs.resources.cpu_request,
                "memory": cs.resources.memory_request,
            },
            limits={
                "cpu": cs.resources.cpu_limit,
                "memory": cs.resources.memory_limit,
            },
        )
        if cs.resources.gpu.vendor == GPUVendor.AMD:
            resources.limits["amd.com/gpu"] = str(cs.resources.gpu.limit)
        elif cs.resources.gpu.vendor == GPUVendor.NVIDIA:
            resources.limits["nvidia.com/gpu"] = str(cs.resources.gpu.limit)

        return V1Container(
            name="main",
            image=cs.image,
            command=cs.command,
            args=cs.args,
            env=[V1EnvVar(name=k, value=v) for k, v in cs.env.items()],
            resources=resources,
            ports=[{"containerPort": p} for p in cs.ports],
        )

    @staticmethod
    def _infer_phase(active: int, succeeded: int, failed: int) -> str:
        if succeeded > 0:
            return "succeeded"
        if failed > 0:
            return "failed"
        if active > 0:
            return "running"
        return "pending"
```

- [ ] **Step 4: Update package __init__**

Replace `src/k8s_llm_runtime/__init__.py`:

```python
"""k8s-llm-runtime: Kubernetes-based vLLM model serving router."""

from k8s_llm_runtime.errors import K8sLLMRuntimeError
from k8s_llm_runtime.job import K8sJobOperator
from k8s_llm_runtime.types import (
    ContainerSpec,
    GPUResource,
    GPUVendor,
    JobSpec,
    JobStatus,
    ResourceSpec,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "ContainerSpec",
    "GPUResource",
    "GPUVendor",
    "JobSpec",
    "JobStatus",
    "K8sJobOperator",
    "K8sLLMRuntimeError",
    "ResourceSpec",
]
```

- [ ] **Step 5: Run full unit suite**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit -v
```

Expected: all unit tests pass (errors + types + client + retry + job).

- [ ] **Step 6: Lint + type-check**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make lint
make type-check
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add src/k8s_llm_runtime/job.py src/k8s_llm_runtime/__init__.py tests/unit/test_job.py
git commit -m "feat(job): K8sJobOperator with AMD/NVIDIA GPU support"
```

---

## Task 1.7: Add CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create CI workflow**

Write to `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-and-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install uv
        run: pip install uv
      - name: Sync dependencies
        run: uv sync --all-extras
      - name: Ruff check
        run: uv run ruff check src tests
      - name: Ruff format check
        run: uv run ruff format --check src tests
      - name: Mypy
        run: uv run mypy src/k8s_llm_runtime
      - name: Unit tests
        run: uv run pytest tests/unit --cov=k8s_llm_runtime --cov-report=xml
      - name: Upload coverage
        if: github.event_name == 'push'
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

- [ ] **Step 2: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add .github/workflows/ci.yml
git commit -m "chore(ci): GitHub Actions for lint + unit tests"
```

---

## Phase 1 Verification

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make test            # all unit tests pass
make lint            # ruff check passes
make type-check      # mypy strict passes
```

End-of-phase state:
- `src/k8s_llm_runtime/` has 6 modules: `__init__`, `errors`, `types`, `_client`, `_retry`, `job`
- `tests/unit/` has 6 test files, ~30 tests total, all passing
- Project builds with `uv sync --all-extras`
- CI workflow defined

Proceed to **Phase 2** (`2026-06-24-k8s-llm-runtime-phase2.md`).
