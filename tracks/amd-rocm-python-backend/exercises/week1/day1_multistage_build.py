# Day 1 实操：单阶段 vs 多阶段 Dockerfile
#
# 用法：
#   1. 创建 app 目录：mkdir -p app/src
#   2. 把这个脚本放到项目根，运行后会自动生成两个 Dockerfile
#   3. 构建并对比镜像大小
#
# 知识点：对比镜像层数、体积、安全性

from pathlib import Path
import subprocess
import sys


SINGLE_STAGE_DOCKERFILE = """\
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

MULTISTAGE_DOCKERFILE = """\
# ---- 阶段 1：构建 wheel ----
FROM python:3.11-slim AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
        build-essential \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- 阶段 2：运行时 ----
FROM python:3.11-slim AS runtime

RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \\
    && rm -rf /wheels

COPY --chown=app:app src/ ./src/

USER app
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

DOCKERIGNORE = """\
.git
.gitignore
.venv
venv
__pycache__
*.pyc
.pytest_cache
.mypy_cache
*.md
tests
"""

REQUIREMENTS = """\
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
"""

APP_MAIN = """\
from fastapi import FastAPI

app = FastAPI(title="Docker Demo")

@app.get("/")
def root():
    return {"message": "Hello from Docker"}

@app.get("/health")
def health():
    return {"status": "ok"}
"""


def setup_project(root: Path) -> None:
    """生成对比用的目录结构"""
    # 阶段 1：单阶段
    single_dir = root / "stage1_single"
    (single_dir / "src").mkdir(parents=True, exist_ok=True)
    (single_dir / "Dockerfile").write_text(SINGLE_STAGE_DOCKERFILE)
    (single_dir / "requirements.txt").write_text(REQUIREMENTS)
    (single_dir / "src" / "main.py").write_text(APP_MAIN)
    (single_dir / ".dockerignore").write_text(DOCKERIGNORE)

    # 阶段 2：多阶段
    multi_dir = root / "stage2_multistage"
    (multi_dir / "src").mkdir(parents=True, exist_ok=True)
    (multi_dir / "Dockerfile").write_text(MULTISTAGE_DOCKERFILE)
    (multi_dir / "requirements.txt").write_text(REQUIREMENTS)
    (multi_dir / "src" / "main.py").write_text(APP_MAIN)
    (multi_dir / ".dockerignore").write_text(DOCKERIGNORE)

    print(f"✓ 已生成项目结构：")
    print(f"  {single_dir}/")
    print(f"  {multi_dir}/")


def build_and_compare(stage_dir: Path, tag: str) -> tuple[str, str]:
    """构建镜像并返回 (镜像ID, 镜像大小)"""
    print(f"\n>>> 构建 {tag} ...")
    result = subprocess.run(
        ["docker", "build", "-t", tag, str(stage_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ 构建失败：\n{result.stderr}")
        sys.exit(1)

    # 获取镜像信息
    inspect = subprocess.run(
        ["docker", "images", tag, "--format", "{{.ID}}|{{.Size}}"],
        capture_output=True,
        text=True,
    )
    image_id, size = inspect.stdout.strip().split("|")
    print(f"✓ {tag}: ID={image_id[:12]}, SIZE={size}")
    return image_id, size


def main() -> None:
    root = Path(__file__).parent
    setup_project(root)

    if "--no-build" in sys.argv:
        print("\n跳过构建（--no-build）")
        return

    single_id, single_size = build_and_compare(
        root / "stage1_single", "demo:single"
    )
    multi_id, multi_size = build_and_compare(
        root / "stage2_multistage", "demo:multi"
    )

    # 简单的体积对比
    def to_mb(size_str: str) -> float:
        size_str = size_str.strip()
        if size_str.endswith("GB"):
            return float(size_str[:-2]) * 1024
        if size_str.endswith("MB"):
            return float(size_str[:-2])
        if size_str.endswith("kB"):
            return float(size_str[:-2]) / 1024
        return float(size_str) / (1024 * 1024)

    single_mb = to_mb(single_size)
    multi_mb = to_mb(multi_size)
    saved = single_mb - multi_mb
    pct = saved / single_mb * 100 if single_mb > 0 else 0

    print(f"\n=== 对比结果 ===")
    print(f"单阶段: {single_mb:.1f} MB")
    print(f"多阶段: {multi_mb:.1f} MB")
    print(f"节省:   {saved:.1f} MB ({pct:.1f}%)")

    # 安全检查
    print(f"\n=== 安全检查 ===")
    user_check = subprocess.run(
        ["docker", "run", "--rm", "demo:multi", "whoami"],
        capture_output=True,
        text=True,
    )
    print(f"运行时用户: {user_check.stdout.strip()} (期望: app)")

    if user_check.stdout.strip() != "app":
        print("⚠️  警告：未以非 root 用户运行")


if __name__ == "__main__":
    main()