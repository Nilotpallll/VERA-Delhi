"""Dependency Gap Analysis & Source Scan Script for VERA Maintenance."""

import ast
import importlib.metadata
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"c:\Users\shara\OneDrive\Desktop\VERA_Delhi\VERA-Delhi\VERA-Delhi")

# 1. Read declared Python requirements
def parse_requirements(req_path: Path) -> dict[str, str]:
    pkgs = {}
    if not req_path.is_file():
        return pkgs
    for line in req_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Strip environment markers (e.g. ; sys_platform == ...)
        spec = line.split(";")[0].strip()
        # Parse package name and version constraint
        m = re.match(r"^([a-zA-Z0-9_\-\[\]]+)(.*)$", spec)
        if m:
            raw_name = m.group(1).split("[")[0].lower().replace("_", "-")
            constraint = m.group(2).strip()
            pkgs[raw_name] = constraint
    return pkgs

api_reqs = parse_requirements(ROOT / "apps" / "api" / "requirements.txt")
ml_reqs = parse_requirements(ROOT / "apps" / "ml_worker" / "requirements.txt")
all_declared = {**api_reqs, **ml_reqs}

print("=== 1. DECLARED REQUIREMENTS STATUS ===")
status_table = []
installed_dists = {d.metadata["Name"].lower().replace("_", "-"): d.version for d in importlib.metadata.distributions()}

for pkg, constraint in sorted(all_declared.items()):
    installed_ver = installed_dists.get(pkg)
    if installed_ver:
        status = "INSTALLED"
    else:
        # Check alias (e.g., python-multipart -> multipart, pyjwt -> jwt)
        alias_map = {
            "python-multipart": "multipart",
            "pyjwt": "jwt",
            "psycopg2-binary": "psycopg2",
            "python-magic-bin": "python-magic",
        }
        alias = alias_map.get(pkg)
        if alias and alias in installed_dists:
            installed_ver = installed_dists[alias]
            status = "INSTALLED (alias)"
        else:
            status = "MISSING"
    status_table.append((pkg, constraint, installed_ver or "NONE", status))
    print(f"{pkg:30} declared: {constraint:15} installed: {str(installed_ver):15} status: {status}")

# 2. Source scan for Python imports
print("\n=== 2. PYTHON SOURCE IMPORT SCAN ===")
py_files = list((ROOT / "apps" / "api").rglob("*.py")) + \
           list((ROOT / "apps" / "ml_worker").rglob("*.py")) + \
           list((ROOT / "eval").rglob("*.py")) + \
           list((ROOT / "tests").rglob("*.py"))

all_imports = set()
for f in py_files:
    try:
        tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    all_imports.add(name.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    all_imports.add(node.module.split(".")[0])
    except Exception as e:
        pass

# Distinguish stdlib vs third-party vs internal
stdlib = sys.stdlib_module_names
internal = {"apps", "packages", "eval", "tests", "scripts"}
external_imports = all_imports - stdlib - internal

# Module to package name mapping
mod_to_pkg = {
    "cv2": "opencv-python",
    "PIL": "pillow",
    "numpy": "numpy",
    "torch": "torch",
    "torchvision": "torchvision",
    "xgboost": "xgboost",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    "pydantic_settings": "pydantic-settings",
    "sqlalchemy": "sqlalchemy",
    "alembic": "alembic",
    "asyncpg": "asyncpg",
    "psycopg2": "psycopg2-binary",
    "httpx": "httpx",
    "jwt": "pyjwt",
    "jose": "python-jose",
    "passlib": "passlib",
    "redis": "redis",
    "sentry_sdk": "sentry-sdk",
    "slowapi": "slowapi",
    "magic": "python-magic-bin",
    "anyio": "anyio",
    "pytest": "pytest",
    "pytest_asyncio": "pytest-asyncio",
    "pytest_mock": "pytest-mock",
    "locust": "locust",
    "langgraph": "langgraph",
    "langchain_core": "langchain-core",
    "sentence_transformers": "sentence-transformers",
    "faster_whisper": "faster-whisper",
    "androguard": "androguard",
    "dotenv": "python-dotenv",
    "multipart": "python-multipart",
}

print(f"External modules imported in source: {sorted(external_imports)}")
missing_declarations = []
for mod in sorted(external_imports):
    pkg_name = mod_to_pkg.get(mod, mod.lower().replace("_", "-"))
    is_declared = (pkg_name in all_declared) or (mod.lower() in all_declared)
    is_installed = (pkg_name in installed_dists) or (mod.lower() in installed_dists) or (mod in sys.modules)
    try:
        __import__(mod)
        can_import = True
    except Exception as e:
        can_import = False
    print(f"Module: {mod:25} mapped_pkg: {pkg_name:25} declared: {str(is_declared):6} installed: {str(is_installed):6} importable: {str(can_import):6}")
    if not is_declared:
        missing_declarations.append((mod, pkg_name, can_import))

# 3. Model weights and data files check
print("\n=== 3. MODEL WEIGHTS AND DATA FILES CHECK ===")
# Search for files matching weights patterns or directories
model_paths = [
    ROOT / "models",
    ROOT / "weights",
    ROOT / "apps" / "ml_worker" / "weights",
    ROOT / "apps" / "ml_worker" / "models",
    Path(os.environ.get("USERPROFILE", "")) / ".cache" / "huggingface",
    Path(os.environ.get("USERPROFILE", "")) / ".cache" / "torch",
]
for p in model_paths:
    print(f"Path {str(p):60} exists: {p.exists()}")

# Search codebase for model path references or URLs
weight_refs = []
for f in py_files:
    content = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r'["\']([^"\']+\.(?:bin|onnx|pt|pth|h5|tflite|joblib|pkl))["\']', content):
        weight_refs.append((f.name, m.group(1)))
print("Referenced weight files in code:")
for fn, ref in sorted(set(weight_refs)):
    p = ROOT / ref
    print(f"  {fn:30} -> {ref:40} exists locally: {p.exists()}")
