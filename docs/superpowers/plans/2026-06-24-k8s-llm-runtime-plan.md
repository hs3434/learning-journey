# k8s-llm-runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Python library + Helm chart toolkit that provides an OpenAI-compatible vLLM model serving router on Kubernetes, with auto-deploy-on-demand, distributed locking, and AMD ROCm GPU support.

**Architecture:** Three-layer Python library (low-level `K8sJobOperator` → mid-level `VLLMInferenceOperator` → high-level `ModelOperator`) wrapped by a FastAPI Router deployed via Helm into K8s. User sends `POST /v1/chat/completions`; Router auto-deploys the model Pod via Helm if not already loaded, then forwards the request. Two Helm charts: `llm-inference` (vLLM workload) and `llm-router` (FastAPI service).

**Tech Stack:** Python 3.11+, uv, kubernetes (official client), helm 3.14+, pydantic v2, fastapi, structlog, prometheus_client, tenacity, httpx, pyyaml, openai (optional), pytest, ruff, mypy.

**Reference Spec:** `learning-journey/docs/superpowers/specs/2026-06-24-k8s-llm-runtime-design.md`

**Execution Target:** New repository at `/work/run/projects/bio-24/my_projects/k8s-llm-runtime/` (already scaffolded with README + AGENTS + LICENSE + .gitignore).

---

## Plan Structure

This plan is split across multiple files for readability. **Read in order**:

| File | Phase | Days |
|---|---|---|
| `2026-06-24-k8s-llm-runtime-plan.md` | this file (header + file structure + execution handoff) | — |
| `2026-06-24-k8s-llm-runtime-phase1.md` | Phase 1: project skeleton + K8sJobOperator | Week 1 |
| `2026-06-24-k8s-llm-runtime-phase2.md` | Phase 2: VLLMInferenceOperator + llm-inference chart | Week 2 |
| `2026-06-24-k8s-llm-runtime-phase3.md` | Phase 3: ModelOperator + K8sLeaseLock | Week 3 |
| `2026-06-24-k8s-llm-runtime-phase4.md` | Phase 4: FastAPI server + llm-router chart + Docker | Week 4 |
| `2026-06-24-k8s-llm-runtime-phase5.md` | Phase 5: cluster scripts + integration tests + CI | Week 5 |
| `2026-06-24-k8s-llm-runtime-phase6.md` | Phase 6: docs + AMD demo rehearsal | Week 6 |

Each phase produces a **working, testable checkpoint**. Don't skip ahead.

---

## File Structure Overview

```
k8s-llm-runtime/
├── AGENTS.md, README.md, LICENSE, .gitignore    (scaffolded)
├── Makefile                                     (Phase 1)
├── pyproject.toml                               (Phase 1)
├── docker/Dockerfile.router                     (Phase 4)
├── src/k8s_llm_runtime/
│   ├── __init__.py                              (Phase 1)
│   ├── errors.py                                (Phase 1)
│   ├── types.py                                 (Phase 1)
│   ├── _client.py                               (Phase 1)
│   ├── _retry.py                                (Phase 1)
│   ├── _log.py                                  (Phase 3)
│   ├── _metrics.py                              (Phase 3)
│   ├── job.py                                   (Phase 1)
│   ├── vllm.py                                  (Phase 2)
│   ├── lock.py                                  (Phase 3)
│   └── model.py                                 (Phase 3)
├── charts/
│   ├── llm-inference/                           (Phase 2)
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   └── templates/{_helpers,deployment,service,ingress,hpa,serviceaccount,configmap,servicemonitor}.yaml
│   └── llm-router/                              (Phase 4)
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/{_helpers,deployment,service,ingress,serviceaccount,role,rolebinding,configmap,hpa,servicemonitor}.yaml
├── examples/vllm-qwen/                          (Phase 4)
│   ├── server.py
│   ├── client.py
│   ├── benchmark.py
│   └── test_request.json
├── scripts/cluster/                             (Phase 5)
│   ├── common.sh
│   ├── kind-up.sh, kind-down.sh
│   ├── kind-config.yaml
│   ├── minikube-up.sh, minikube-down.sh
│   └── common/{install-nginx.sh, install-metrics-server.sh}
├── tests/
│   ├── unit/                                    (Phases 1-4)
│   ├── chart/                                   (Phases 2, 4)
│   └── integration/                             (Phase 5)
├── docs/                                        (Phase 6)
│   ├── architecture.md
│   └── amd-interview-demo.md
└── .github/workflows/
    ├── ci.yml                                   (Phase 1)
    └── integration.yml                          (Phase 5)
```

---

## Working Agreements

- **TDD discipline**: every code step writes the failing test FIRST, then implementation
- **Frequent commits**: each task ends with `git commit`
- **One phase = one PR**: review between phases
- **Mock external boundaries**: kubernetes-client, helm subprocess, httpx — never call them in unit tests
- **Type hints everywhere**: `mypy --strict` on `src/k8s_llm_runtime/` must pass
- **No placeholders**: if you see "TODO" / "TBD" / "implement later" in a step, that's a bug — fix the plan before executing

---

## Verification Between Phases

After each phase, run from repo root:

```bash
cd /work/run/projects/bio-24/my_projects/k8s-llm-runtime
make test                # unit + chart tests
make lint                # ruff check
make format              # ruff format (auto-fix)
make type-check          # mypy --strict
```

End-of-phase demos:

| Phase | Manual demo command |
|---|---|
| 1 | `make test` passes; no manual demo |
| 2 | `helm install demo ./charts/llm-inference --set gpu.vendor=amd --dry-run` |
| 3 | `make test` passes; no manual demo |
| 4 | `docker build -f docker/Dockerfile.router -t router:dev .` |
| 5 | `make cluster-up && make demo && make test-integration` |
| 6 | Full end-to-end demo per `docs/amd-interview-demo.md` |

---

## Execution Handoff

After all 6 phase plans are complete and committed to `learning-journey/docs/superpowers/plans/`, choose execution mode:

**Option 1: Subagent-Driven (recommended for parallel work)**
- Dispatch a fresh subagent per task
- Review between tasks
- Best for: large batch execution, parallel phases

**Option 2: Inline Execution**
- Execute tasks in this session with checkpoints
- Best for: learning, debugging, careful review

---

## Spec Coverage Map

Quick reference: which phase implements which spec section.

| Spec Section | Phase / Task |
|---|---|
| § 1. Repo architecture | Phase 1 Task 1.1 |
| § 2.1 Python lib API / types | Phase 1 Task 1.3 |
| § 2.2 K8sJobOperator | Phase 1 Tasks 1.4–1.6 |
| § 2.3 VLLMInferenceOperator | Phase 2 Task 2.5 |
| § 2.4 ModelOperator | Phase 3 Task 3.2 |
| § 2.5 K8sLeaseLock | Phase 3 Task 3.1 |
| § 2.6 Errors | Phase 1 Task 1.2 |
| § 3.1 llm-inference chart | Phase 2 Tasks 2.1–2.4 |
| § 3.2 llm-router chart | Phase 4 Task 4.3 |
| § 4 server.py | Phase 4 Task 4.1 |
| § 4 client.py + benchmark.py | Phase 4 Task 4.2 |
| § 4 Dockerfile.router | Phase 4 Task 4.4 |
| § 5 4-layer testing | Phases 1-5 (each adds its layer) |
| § 6 errors + observability | Phase 3 (metrics) + Phase 4 (server exception mapping) |
| § 7 cluster scripts | Phase 5 |
| § 8 docs + demo | Phase 6 |
