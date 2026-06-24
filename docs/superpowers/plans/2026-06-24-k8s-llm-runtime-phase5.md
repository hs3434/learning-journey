# Phase 5 (Week 5): Cluster scripts + Integration tests + CI

**End-of-phase deliverable:** End-to-end demo works against a real kind cluster; CI runs unit + chart + integration tests.

**Working directory:** `/work/run/projects/bio-24/my_projects/k8s-llm-runtime/`

---

## Task 5.1: Cluster install scripts (kind + minikube)

**Files:**
- Create: `scripts/cluster/common.sh`
- Create: `scripts/cluster/kind-up.sh`
- Create: `scripts/cluster/kind-down.sh`
- Create: `scripts/cluster/kind-config.yaml`
- Create: `scripts/cluster/minikube-up.sh`
- Create: `scripts/cluster/minikube-down.sh`
- Create: `scripts/cluster/common/install-nginx.sh`
- Create: `scripts/cluster/common/install-metrics-server.sh`

- [ ] **Step 1: common.sh (shared shell library)**

```bash
#!/usr/bin/env bash
# scripts/cluster/common.sh — shared shell functions for cluster setup
set -euo pipefail

export KUBECONFIG="${KUBECONFIG:-./kubeconfig}"
export CLUSTER_NAME="${CLUSTER_NAME:-k8s-llm-demo}"

log() { echo "[$(date +%H:%M:%S)] $*"; }

wait_for_node_ready() {
    local timeout="${1:-120}"
    log "Waiting for node Ready (timeout=${timeout}s)"
    kubectl wait --for=condition=Ready node --all --timeout="${timeout}s"
}

install_ingress_nginx() {
    log "Installing ingress-nginx"
    kubectl apply -f \
        https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.0/deploy/static/provider/kind/deploy.yaml
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=120s
}

install_metrics_server() {
    log "Installing metrics-server (for HPA)"
    kubectl apply -f \
        https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    # Patch for kind: --kubelet-insecure-tls (insecure certs)
    kubectl patch deployment metrics-server -n kube-system --type=json \
        -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
}
```

- [ ] **Step 2: kind-up.sh**

```bash
#!/usr/bin/env bash
# scripts/cluster/kind-up.sh — start a kind cluster
set -euo pipefail
source "$(dirname "$0")/common.sh"

CLUSTER_NAME="${CLUSTER_NAME}-kind"

if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    log "kind cluster ${CLUSTER_NAME} already exists"
else
    log "Creating kind cluster: ${CLUSTER_NAME}"
    kind create cluster --name "${CLUSTER_NAME}" \
        --config "$(dirname "$0")/kind-config.yaml"
fi

kind export kubeconfig --name "${CLUSTER_NAME}" --kubeconfig "${KUBECONFIG}"
wait_for_node_ready 120
install_ingress_nginx
install_metrics_server

log "✓ kind cluster ready. KUBECONFIG=${KUBECONFIG}"
```

- [ ] **Step 3: kind-down.sh**

```bash
#!/usr/bin/env bash
# scripts/cluster/kind-down.sh
set -euo pipefail
source "$(dirname "$0")/common.sh"

CLUSTER_NAME="${CLUSTER_NAME}-kind"
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    kind delete cluster --name "${CLUSTER_NAME}"
fi
rm -f "${KUBECONFIG}"
log "✓ kind cluster deleted"
```

- [ ] **Step 4: kind-config.yaml (multi-node)**

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

- [ ] **Step 5: minikube-up.sh**

```bash
#!/usr/bin/env bash
# scripts/cluster/minikube-up.sh — start a minikube cluster
set -euo pipefail
source "$(dirname "$0")/common.sh"

CLUSTER_NAME="${CLUSTER_NAME}-minikube"

if minikube status -p "${CLUSTER_NAME}" >/dev/null 2>&1; then
    log "minikube profile ${CLUSTER_NAME} already exists"
else
    log "Creating minikube profile: ${CLUSTER_NAME}"
    minikube start -p "${CLUSTER_NAME}" \
        --driver=docker \
        --cpus=4 --memory=4g --disk-size=20g
    minikube addons enable ingress -p "${CLUSTER_NAME}"
    minikube addons enable metrics-server -p "${CLUSTER_NAME}"
fi

minikube update-context -p "${CLUSTER_NAME}" --kubeconfig "${KUBECONFIG}"
wait_for_node_ready 180

log "✓ minikube cluster ready. KUBECONFIG=${KUBECONFIG}"
```

- [ ] **Step 6: minikube-down.sh**

```bash
#!/usr/bin/env bash
# scripts/cluster/minikube-down.sh
set -euo pipefail
source "$(dirname "$0")/common.sh"

CLUSTER_NAME="${CLUSTER_NAME}-minikube"
if minikube status -p "${CLUSTER_NAME}" >/dev/null 2>&1; then
    minikube delete -p "${CLUSTER_NAME}"
fi
rm -f "${KUBECONFIG}"
log "✓ minikube cluster deleted"
```

- [ ] **Step 7: install-nginx.sh**

```bash
#!/usr/bin/env bash
# scripts/cluster/common/install-nginx.sh
set -euo pipefail
source "$(dirname "$0")/../common.sh"
install_ingress_nginx
```

- [ ] **Step 8: install-metrics-server.sh**

```bash
#!/usr/bin/env bash
# scripts/cluster/common/install-metrics-server.sh
set -euo pipefail
source "$(dirname "$0")/../common.sh"
install_metrics_server
```

- [ ] **Step 9: Make scripts executable**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
chmod +x scripts/cluster/*.sh scripts/cluster/common/*.sh
```

- [ ] **Step 10: Verify kind-up works**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make cluster-up CLUSTER=kind
kubectl get nodes
make cluster-down CLUSTER=kind
```

Expected: 3-node kind cluster, then cleanup.

- [ ] **Step 11: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add scripts/cluster/
git commit -m "feat(scripts): cluster-up/down for kind + minikube with shared helpers"
```

---

## Task 5.2: Integration test fixtures

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/conftest.py`
- Create: `tests/integration/test_e2e.py`

- [ ] **Step 1: conftest.py**

```python
"""Integration test fixtures (kind cluster)."""
import os
import subprocess
import time
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
KUBECONFIG = REPO_ROOT / "kubeconfig"


@pytest.fixture(scope="session")
def kubeconfig():
    return str(KUBECONFIG)


@pytest.fixture(scope="session", autouse=True)
def kind_cluster():
    """Bring up kind cluster for the whole test session."""
    if not KUBECONFIG.exists():
        subprocess.run(["make", "cluster-up", "CLUSTER=kind"],
                       cwd=REPO_ROOT, check=True, env={**os.environ})
    os.environ["KUBECONFIG"] = str(KUBECONFIG)
    yield
    # Don't teardown by default; CI does it separately.
    # To force teardown: subprocess.run(["make", "cluster-down", "CLUSTER=kind"])


@pytest.fixture(scope="session")
def router_port_forward():
    """Install llm-router chart + port-forward to localhost."""
    # Pre-create chart-source ConfigMap by packing llm-inference chart
    # (read by llm-router Deployment's initContainer)
    subprocess.run([
        "kubectl", "create", "configmap", "llm-router-chart-source",
        "--from-file=charts/llm-inference/",
        "--namespace", "llm-system",
        "--kubeconfig", str(KUBECONFIG),
    ], cwd=REPO_ROOT, check=True, env={**os.environ, "KUBECONFIG": str(KUBECONFIG)})

    # Install llm-router chart
    subprocess.run([
        "helm", "install", "llm-router",
        str(REPO_ROOT / "charts" / "llm-router"),
        "--namespace", "llm-system",
        "--create-namespace",
        "--kubeconfig", str(KUBECONFIG),
        "--wait", "--timeout", "180s",
    ], check=True)

    # Wait for ready
    subprocess.run([
        "kubectl", "wait", "--namespace", "llm-system",
        "--for=condition=ready", "pod",
        "--selector=app.kubernetes.io/name=llm-router",
        "--timeout", "120s",
        "--kubeconfig", str(KUBECONFIG),
    ], check=True)

    # Port-forward
    proc = subprocess.Popen([
        "kubectl", "--namespace", "llm-system",
        "port-forward", "svc/llm-router", "18080:8080",
        "--kubeconfig", str(KUBECONFIG),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        try:
            r = httpx.get("http://localhost:18080/healthz", timeout=2)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(1)
    yield "http://localhost:18080"
    proc.terminate()
    proc.wait(timeout=5)
    subprocess.run([
        "helm", "uninstall", "llm-router",
        "--namespace", "llm-system",
        "--kubeconfig", str(KUBECONFIG),
    ], check=False)
```

- [ ] **Step 2: test_e2e.py**

```python
"""End-to-end tests against kind cluster.

Skipped unless KUBECONFIG points to a live cluster.
"""
import os

import httpx
import pytest


@pytest.mark.skipif(
    not os.environ.get("KUBECONFIG") or not os.path.exists(os.environ["KUBECONFIG"]),
    reason="KUBECONFIG not set or cluster not running",
)
def test_healthz(router_port_forward):
    r = httpx.get(f"{router_port_forward}/healthz", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


@pytest.mark.skipif(
    not os.environ.get("KUBECONFIG") or not os.path.exists(os.environ["KUBECONFIG"]),
    reason="KUBECONFIG not set or cluster not running",
)
def test_readyz(router_port_forward):
    r = httpx.get(f"{router_port_forward}/readyz", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


@pytest.mark.skipif(
    not os.environ.get("KUBECONFIG") or not os.path.exists(os.environ["KUBECONFIG"]),
    reason="KUBECONFIG not set or cluster not running",
)
@pytest.mark.slow
def test_first_chat_auto_deploys_model(router_port_forward):
    """End-to-end: first request triggers vLLM deploy."""
    r = httpx.post(
        f"{router_port_forward}/v1/chat/completions",
        json={
            "model": "qwen-0.5b",
            "messages": [{"role": "user", "content": "hi"}],
        },
        timeout=300,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["model"] == "qwen-0.5b"
    assert len(body["choices"]) > 0
```

- [ ] **Step 3: Skip marker for non-CI**

The `pytest.mark.skipif` ensures unit-only runs skip these gracefully.

- [ ] **Step 4: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add tests/integration/
git commit -m "test(integration): kind cluster e2e fixtures + first chat auto-deploy"
```

---

## Task 5.3: Integration CI workflow

**Files:**
- Create: `.github/workflows/integration.yml`

- [ ] **Step 1: Create integration.yml**

```yaml
name: Integration

on:
  workflow_dispatch:
  schedule:
    - cron: "0 3 * * *"  # nightly 03:00 UTC

jobs:
  kind-e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install uv
        run: pip install uv
      - name: Sync dependencies
        run: uv sync --all-extras
      - name: Install helm
        uses: azure/setup-helm@v3
        with:
          version: v3.14.0
      - name: Install kind
        run: |
          curl -fsSL https://kind.sigs.k8s.io/dl/v0.23.0/kind-linux-amd64 \
              | install -m 0755 /dev/stdin /usr/local/bin/kind
      - name: Start cluster
        run: make cluster-up CLUSTER=kind
      - name: Run integration tests
        run: uv run pytest tests/integration -v
      - name: Teardown
        if: always()
        run: make cluster-down CLUSTER=kind
```

- [ ] **Step 2: Commit**

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
git add .github/workflows/integration.yml
git commit -m "ci(integration): nightly + manual kind e2e workflow"
```

---

## Phase 5 Verification

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make cluster-up CLUSTER=kind
make cluster-down CLUSTER=kind
```

End-of-phase state:
- `make cluster-up/down` works for both kind and minikube
- `tests/integration/` ready (runs against kind)
- CI integration workflow defined

Proceed to **Phase 6** (`2026-06-24-k8s-llm-runtime-phase6.md`).
