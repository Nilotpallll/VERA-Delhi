import sys
import os

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

# Try importing dependencies
deps = [
    "torch",
    "cv2",
    "numpy",
    "pydantic",
    "fastapi",
    "xgboost",
    "sentence_transformers",
    "faster_whisper",
    "langchain",
    "langgraph",
    "PIL",
    "httpx",
]

for dep in deps:
    try:
        mod = __import__(dep)
        ver = getattr(mod, "__version__", "installed")
        print(f"  [+] {dep}: {ver}")
    except ImportError as e:
        print(f"  [-] {dep}: NOT INSTALLED ({e})")
