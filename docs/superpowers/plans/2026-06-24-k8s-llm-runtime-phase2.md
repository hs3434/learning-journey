# Phase 2 (Week 2): VLLMInferenceOperator + llm-inference chart

**End-of-phase deliverable:** `VLLMInferenceOperator` implemented + `charts/llm-inference/` complete + chart tests passing.

**Working directory:** `/work/run/projects/bio-24/my_projects/k8s-llm-runtime/`

---

## Task 2.1: Create llm-inference chart skeleton

**Files:**
- Create: `charts/llm-inference/Chart.yaml`
- Create: `charts/llm-inference/values.yaml`
- Create: `charts/llm-inference/templates/_helpers.tpl`

- [ ] **Step 1: Chart.yaml**

```yaml
apiVersion: v2
name: llm-inference
description: vLLM OpenAI-compatible inference server
type: application
version: 0.1.0
appVersion: "0.5.0"
```

- [ ] **Step 2: values.yaml**

```yaml
replicaCount: 1

image:
  repository: vllm/vllm-openai
  tag: latest
  pullPolicy: IfNotPresent

model:
  name: Qwen/Qwen2.5-0.5B-Instruct
  hfTokenSecret: ""

gpu:
  vendor: none
  limit: 1

resources:
  requests:
    cpu: "2"
    memory: "8Gi"
  limits:
    cpu: "8"
    memory: "16Gi"

vllm:
  args: []
  port: 8000

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: false
  className: nginx
  host: llm.local
  path: /

autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 3
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

serviceMonitor:
  enabled: false
  interval: 30s

nodeSelector: {}
tolerations: []
affinity: {}
```

- [ ] **Step 3: _helpers.tpl**

```
{{- define "llm-inference.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "llm-inference.fullname" -}}
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

{{- define "llm-inference.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{ include "llm-inference.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "llm-inference.selectorLabels" -}}
app.kubernetes.io/name: {{ include "llm-inference.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

- [ ] **Step 4: Verify helm lint**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
helm lint charts/llm-inference
```

Expected: `1 chart(s) linted, 0 failed(s)`.

- [ ] **Step 5: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add charts/llm-inference/
git commit -m "feat(chart): llm-inference skeleton with values + helpers"
```

---

## Task 2.2: Add templates (deployment, service, ingress, hpa, sa, monitor)

**Files:**
- Create: `charts/llm-inference/templates/deployment.yaml`
- Create: `charts/llm-inference/templates/service.yaml`
- Create: `charts/llm-inference/templates/ingress.yaml`
- Create: `charts/llm-inference/templates/hpa.yaml`
- Create: `charts/llm-inference/templates/serviceaccount.yaml`
- Create: `charts/llm-inference/templates/servicemonitor.yaml`

- [ ] **Step 1: deployment.yaml** (critical: GPU vendor switching)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "llm-inference.fullname" . }}
  labels:
    {{- include "llm-inference.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "llm-inference.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "llm-inference.selectorLabels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "llm-inference.fullname" . }}
      containers:
        - name: vllm
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          args:
            - --model
            - {{ .Values.model.name | quote }}
            - --port
            - {{ .Values.vllm.port | quote }}
            {{- with .Values.vllm.args }}
            {{- toYaml . | nindent 12 }}
            {{- end }}
          ports:
            - name: http
              containerPort: {{ .Values.vllm.port }}
              protocol: TCP
          env:
            {{- if .Values.model.hfTokenSecret }}
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.model.hfTokenSecret }}
                  key: token
            {{- end }}
          resources:
            requests:
              cpu: {{ .Values.resources.requests.cpu | quote }}
              memory: {{ .Values.resources.requests.memory | quote }}
            limits:
              cpu: {{ .Values.resources.limits.cpu | quote }}
              memory: {{ .Values.resources.limits.memory | quote }}
              {{- if eq .Values.gpu.vendor "amd" }}
              amd.com/gpu: {{ .Values.gpu.limit | quote }}
              {{- end }}
              {{- if eq .Values.gpu.vendor "nvidia" }}
              nvidia.com/gpu: {{ .Values.gpu.limit | quote }}
              {{- end }}
          {{- with .Values.nodeSelector }}
          nodeSelector:
            {{- toYaml . | nindent 12 }}
          {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

- [ ] **Step 2: service.yaml**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "llm-inference.fullname" . }}
  labels:
    {{- include "llm-inference.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "llm-inference.selectorLabels" . | nindent 4 }}
```

- [ ] **Step 3: ingress.yaml**

```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "llm-inference.fullname" . }}
  labels:
    {{- include "llm-inference.labels" . | nindent 4 }}
spec:
  ingressClassName: {{ .Values.ingress.className }}
  rules:
    - host: {{ .Values.ingress.host | quote }}
      http:
        paths:
          - path: {{ .Values.ingress.path }}
            pathType: Prefix
            backend:
              service:
                name: {{ include "llm-inference.fullname" . }}
                port:
                  number: {{ .Values.service.port }}
{{- end }}
```

- [ ] **Step 4: hpa.yaml**

```yaml
{{- if .Values.autoscaling.enabled -}}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "llm-inference.fullname" . }}
  labels:
    {{- include "llm-inference.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "llm-inference.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- end }}
    {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
    {{- end }}
{{- end }}
```

- [ ] **Step 5: serviceaccount.yaml**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "llm-inference.fullname" . }}
  labels:
    {{- include "llm-inference.labels" . | nindent 4 }}
```

- [ ] **Step 6: servicemonitor.yaml**

```yaml
{{- if .Values.serviceMonitor.enabled -}}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "llm-inference.fullname" . }}
  labels:
    {{- include "llm-inference.labels" . | nindent 4 }}
spec:
  endpoints:
    - port: http
      interval: {{ .Values.serviceMonitor.interval }}
  selector:
    matchLabels:
      {{- include "llm-inference.selectorLabels" . | nindent 6 }}
{{- end }}
```

- [ ] **Step 7: Verify lint + render**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
helm lint charts/llm-inference
helm template test-release charts/llm-inference --set gpu.vendor=amd | head -50
```

Expected: lint clean; template renders Deployment, Service, ServiceAccount.

- [ ] **Step 8: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add charts/llm-inference/templates/
git commit -m "feat(chart): llm-inference deployment + service + ingress + hpa + sa + monitor"
```

---

## Task 2.3: Chart tests (helm template rendering)

**Files:**
- Create: `tests/chart/__init__.py`
- Create: `tests/chart/conftest.py`
- Create: `tests/chart/test_llm_inference.py`

- [ ] **Step 1: Verify helm available**

```bash
helm version --short
```

Expected: `v3.x.x`. Install from https://helm.sh if missing.

- [ ] **Step 2: conftest.py**

Write to `tests/chart/__init__.py`: empty file.

Write to `tests/chart/conftest.py`:

```python
"""Shared fixtures for chart rendering tests."""
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def chart_path():
    return REPO_ROOT / "charts" / "llm-inference"


@pytest.fixture
def helm_template(chart_path):
    """Return a function that renders the chart with given --set values."""

    def _render(set_values: list[str] | None = None) -> str:
        cmd = [
            "helm", "template", "test-release", str(chart_path),
            "--namespace", "test-ns",
        ]
        for v in set_values or []:
            cmd.extend(["--set", v])
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    return _render
```

- [ ] **Step 3: test_llm_inference.py**

```python
"""Tests for llm-inference chart rendering."""


def test_default_values_render(helm_template):
    manifest = helm_template()
    assert "kind: Deployment" in manifest
    assert "kind: Service" in manifest
    assert "kind: ServiceAccount" in manifest


def test_ingress_disabled_by_default(helm_template):
    assert "kind: Ingress" not in helm_template()


def test_hpa_disabled_by_default(helm_template):
    assert "kind: HorizontalPodAutoscaler" not in helm_template()


def test_servicemonitor_disabled_by_default(helm_template):
    assert "kind: ServiceMonitor" not in helm_template()


def test_amd_gpu_resource_in_limits(helm_template):
    manifest = helm_template(["gpu.vendor=amd", "gpu.limit=2"])
    assert 'amd.com/gpu: "2"' in manifest
    assert "nvidia.com/gpu" not in manifest


def test_nvidia_gpu_resource_in_limits(helm_template):
    manifest = helm_template(["gpu.vendor=nvidia", "gpu.limit=1"])
    assert 'nvidia.com/gpu: "1"' in manifest
    assert "amd.com/gpu" not in manifest


def test_cpu_mode_has_no_gpu_resources(helm_template):
    manifest = helm_template(["gpu.vendor=none"])
    assert "amd.com/gpu" not in manifest
    assert "nvidia.com/gpu" not in manifest


def test_ingress_enabled_when_set(helm_template):
    manifest = helm_template(["ingress.enabled=true", "ingress.host=llm.example.com"])
    assert "kind: Ingress" in manifest
    assert "llm.example.com" in manifest


def test_hpa_enabled_when_set(helm_template):
    manifest = helm_template(["autoscaling.enabled=true", "autoscaling.maxReplicas=5"])
    assert "kind: HorizontalPodAutoscaler" in manifest


def test_image_repository_and_tag(helm_template):
    manifest = helm_template(["image.repository=my/vllm", "image.tag=v0.5"])
    assert "my/vllm:v0.5" in manifest


def test_model_name_passed_as_arg(helm_template):
    manifest = helm_template(["model.name=Qwen/Qwen2.5-7B-Instruct"])
    assert "Qwen/Qwen2.5-7B-Instruct" in manifest


def test_hf_token_secret_injected(helm_template):
    manifest = helm_template(["model.hfTokenSecret=hf-secret"])
    assert "secretKeyRef:" in manifest
    assert "name: hf-secret" in manifest
    assert "key: token" in manifest


def test_node_selector_propagates(helm_template):
    manifest = helm_template(['nodeSelector."amd\.com/gpu\.product"=MI300X'])
    assert "amd.com/gpu.product" in manifest
    assert "MI300X" in manifest
```

- [ ] **Step 4: Run chart tests**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/chart -v
```

Expected: 13 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add tests/chart/
git commit -m "test(chart): GPU vendor switching + optional resources"
```

---

## Task 2.4: VLLMInferenceOperator (helm CLI subprocess)

**Files:**
- Create: `src/k8s_llm_runtime/vllm.py`
- Modify: `src/k8s_llm_runtime/__init__.py`
- Create: `tests/unit/test_vllm.py`

- [ ] **Step 1: Write failing test**

Write to `tests/unit/test_vllm.py`:

```python
"""Tests for VLLMInferenceOperator."""
import json
from unittest.mock import MagicMock, patch

import pytest

from k8s_llm_runtime.types import GPUResource, GPUVendor
from k8s_llm_runtime.vllm import VLLMDeployment, VLLMInferenceOperator


@pytest.fixture
def op(tmp_path):
    chart = tmp_path / "fake-chart"
    chart.mkdir()
    (chart / "Chart.yaml").write_text("apiVersion: v2\nname: llm-inference\nversion: 0.1.0\n")
    return VLLMInferenceOperator(chart_path=str(chart), kubeconfig="/tmp/fake")


def _helm_ok(stdout: str = "") -> MagicMock:
    m = MagicMock()
    m.returncode = 0
    m.stdout = stdout
    m.stderr = ""
    return m


def _helm_fail(stderr: str = "release already exists") -> MagicMock:
    m = MagicMock()
    m.returncode = 1
    m.stdout = ""
    m.stderr = stderr
    return m


def test_deploy_renders_and_installs(op):
    with patch("subprocess.run") as mock_run, \
         patch.object(op, "_wait_for_ready", return_value=VLLMDeployment(
             release_name="qwen", namespace="llm-models",
             model_name="Qwen/...", endpoint="http://qwen.llm-models:8000",
             phase="ready", replicas_ready=1,
         )):
        mock_run.return_value = _helm_ok()
        result = op.deploy(
            "qwen", "Qwen/Qwen2.5-0.5B-Instruct", "llm-models",
            gpu=GPUResource(vendor=GPUVendor.AMD, limit=1),
        )
    assert result.release_name == "qwen"
    assert result.phase == "ready"
    cmd = mock_run.call_args_list[0].args[0]
    assert cmd[:4] == ["helm", "upgrade", "--install", "qwen"]


def test_deploy_passes_gpu_vendor_to_values(op):
    with patch("subprocess.run") as mock_run, \
         patch.object(op, "_wait_for_ready", return_value=VLLMDeployment(
             release_name="x", namespace="ns", model_name="m",
             endpoint="e", phase="ready", replicas_ready=1,
         )):
        mock_run.return_value = _helm_ok()
        op.deploy("x", "Qwen/0.5B", "ns", gpu=GPUResource(vendor=GPUVendor.AMD, limit=2))
    cmd = mock_run.call_args_list[0].args[0]
    assert any("gpu.vendor=amd" in a for a in cmd)
    assert any("gpu.limit=2" in a for a in cmd)


def test_deploy_propagates_helm_error(op):
    from k8s_llm_runtime.errors import VLLMDeployError
    with patch("subprocess.run", return_value=_helm_fail("bad chart")), \
         patch.object(op, "_wait_for_ready"):
        with pytest.raises(VLLMDeployError) as exc:
            op.deploy("x", "Qwen/0.5B", "ns")
    assert "bad chart" in str(exc.value)


def test_undeploy_calls_helm_uninstall(op):
    from k8s_llm_runtime.errors import VLLMDeployError
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _helm_ok()
        op.undeploy("qwen", "llm-models")
    cmd = mock_run.call_args.args[0]
    assert cmd[:3] == ["helm", "uninstall", "qwen"]
    assert "llm-models" in cmd


def test_undeploy_propagates_error(op):
    from k8s_llm_runtime.errors import VLLMUndeployError
    with patch("subprocess.run", return_value=_helm_fail("release not found")):
        with pytest.raises(VLLMUndeployError):
            op.undeploy("qwen", "llm-models")


def test_get_endpoint_builds_internal_url(op):
    assert op.get_endpoint("qwen-7b", "llm-models") == \
        "http://qwen-7b.llm-models.svc.cluster.local:8000"


def test_run_helm_sets_kubeconfig_env(op):
    with patch("subprocess.run", return_value=_helm_ok()) as mock_run:
        op._run_helm(["version"])
    assert mock_run.call_args.kwargs["env"].get("KUBECONFIG") == "/tmp/fake"


def test_run_helm_returns_stdout(op):
    with patch("subprocess.run", return_value=_helm_ok("release-list-output")):
        out = op._run_helm(["list"])
    assert out == "release-list-output"


def test_get_status_pending_when_no_release(op):
    with patch("subprocess.run", return_value=_helm_ok("[]")):
        status = op.get_status("missing", "llm-models")
    assert status.phase == "pending"
    assert status.replicas_ready == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit/test_vllm.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement VLLMInferenceOperator**

Write to `src/k8s_llm_runtime/vllm.py`:

```python
"""Mid-level vLLM deployment via Helm CLI."""
from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Literal, Optional

from kubernetes.client.rest import ApiException

from k8s_llm_runtime import _client
from k8s_llm_runtime.errors import (
    VLLMDeployError,
    VLLMDeployTimeoutError,
    VLLMUndeployError,
)
from k8s_llm_runtime.types import GPUResource


@dataclass
class VLLMDeployment:
    """Observed state of a vLLM Helm release."""

    release_name: str
    namespace: str
    model_name: str
    endpoint: str
    phase: Literal["pending", "deploying", "ready", "failed"]
    message: Optional[str] = None
    replicas_ready: int = 0


class VLLMInferenceOperator:
    """Deploy/undeploy/query vLLM via Helm chart."""

    DEFAULT_PORT = 8000

    def __init__(self, chart_path: str = "./charts/llm-inference",
                 kubeconfig: Optional[str] = None):
        self.chart_path = chart_path
        self.kubeconfig = kubeconfig

    def deploy(
        self,
        release_name: str,
        model_name: str,
        namespace: str = "default",
        gpu: GPUResource = GPUResource(),
        replicas: int = 1,
        timeout: int = 600,
    ) -> VLLMDeployment:
        """Helm install/upgrade vLLM with the given model. Idempotent."""
        args = [
            "helm", "upgrade", "--install", release_name, self.chart_path,
            "--namespace", namespace, "--create-namespace",
            "--wait", "--timeout", f"{timeout}s",
            "--set", f"model.name={model_name}",
            "--set", f"gpu.vendor={gpu.vendor.value}",
            "--set", f"gpu.limit={gpu.limit}",
            "--set", f"replicaCount={replicas}",
        ]
        self._run_helm(args)
        return self._wait_for_ready(release_name, namespace, model_name, timeout=timeout)

    def undeploy(self, release_name: str, namespace: str) -> None:
        """Helm uninstall a release."""
        try:
            self._run_helm(["helm", "uninstall", release_name, "--namespace", namespace])
        except VLLMDeployError as exc:
            raise VLLMUndeployError(str(exc)) from exc

    def get_status(self, release_name: str, namespace: str) -> VLLMDeployment:
        """Inspect helm release status and pod readiness."""
        out = self._run_helm([
            "helm", "list", "--namespace", namespace,
            "--filter", f"^{release_name}$",
            "--output", "json",
        ])
        try:
            releases = json.loads(out)
        except json.JSONDecodeError:
            return VLLMDeployment(
                release_name=release_name, namespace=namespace,
                model_name="", endpoint="", phase="pending",
            )
        if not releases:
            return VLLMDeployment(
                release_name=release_name, namespace=namespace,
                model_name="", endpoint="", phase="pending",
            )
        helm_status = releases[0].get("status", "unknown")
        phase: Literal["pending", "deploying", "ready", "failed"] = (
            "ready" if helm_status == "deployed" else "deploying"
        )

        # Check pod readiness
        replicas_ready = 0
        try:
            pods = _client.core_api().list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app.kubernetes.io/instance={release_name}",
            )
            for p in pods.items:
                if p.status and p.status.conditions:
                    if any(c.type == "Ready" and c.status == "True"
                           for c in p.status.conditions):
                        replicas_ready += 1
        except ApiException:
            pass

        if phase == "ready" and replicas_ready == 0:
            phase = "deploying"

        return VLLMDeployment(
            release_name=release_name, namespace=namespace,
            model_name="",
            endpoint=self.get_endpoint(release_name, namespace),
            phase=phase,
            replicas_ready=replicas_ready,
        )

    def get_endpoint(self, release_name: str, namespace: str) -> str:
        """Internal cluster DNS endpoint for the vLLM service."""
        return (
            f"http://{release_name}.{namespace}.svc.cluster.local:"
            f"{self.DEFAULT_PORT}"
        )

    # --- Internal helpers ---

    def _run_helm(self, args: list[str]) -> str:
        env = os.environ.copy()
        if self.kubeconfig:
            env["KUBECONFIG"] = self.kubeconfig
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=180, env=env,
        )
        if result.returncode != 0:
            raise VLLMDeployError(
                f"helm command failed (rc={result.returncode}): {result.stderr}"
            )
        return result.stdout

    def _wait_for_ready(
        self,
        release_name: str,
        namespace: str,
        model_name: str,
        timeout: int = 600,
        poll_interval: int = 5,
    ) -> VLLMDeployment:
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_status(release_name, namespace)
            if status.phase == "ready" and status.replicas_ready > 0:
                return VLLMDeployment(
                    release_name=release_name, namespace=namespace,
                    model_name=model_name,
                    endpoint=status.endpoint,
                    phase="ready",
                    replicas_ready=status.replicas_ready,
                )
            time.sleep(poll_interval)
        raise VLLMDeployTimeoutError(
            f"vLLM {release_name} did not become ready within {timeout}s"
        )
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
from k8s_llm_runtime.vllm import VLLMDeployment, VLLMInferenceOperator

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
    "VLLMDeployment",
    "VLLMInferenceOperator",
]
```

- [ ] **Step 5: Run tests**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
uv run pytest tests/unit tests/chart -v
```

Expected: all pass.

- [ ] **Step 6: Lint + type-check**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make lint
make type-check
```

- [ ] **Step 7: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add src/k8s_llm_runtime/vllm.py src/k8s_llm_runtime/__init__.py tests/unit/test_vllm.py
git commit -m "feat(vllm): VLLMInferenceOperator with helm CLI + GPU switching"
```

---

## Phase 2 Verification

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make test
helm lint charts/llm-inference
helm template demo charts/llm-inference --set gpu.vendor=amd --set model.name=Qwen/Qwen2.5-7B-Instruct | head -60
```

Expected: tests pass; helm template renders a Deployment with `amd.com/gpu: "1"` and `model: Qwen/Qwen2.5-7B-Instruct`.

Proceed to **Phase 3** (`2026-06-24-k8s-llm-runtime-phase3.md`).
