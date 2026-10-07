# VERA Machine Learning Engine Architecture

This directory governs ML models, feature pipelines, and model registry contracts for the VERA investment-fraud platform.

## Architecture Rules Enforced

1. **Rule 4: Detection engines are independent modules**  
   Every ML model is encapsulated within an isolated analyzer adapter. Models never invoke each other directly; they consume canonical evidence and emit structured findings.

2. **Rule 6 & 7: Risk scoring is deterministic; LLMs/ML models cannot directly assign final risk scores**  
   Models output normalized feature vectors, confidence intervals, and anomaly probabilities. The deterministic risk engine evaluates these features through rule matrices to calculate the final 0–100 score.

3. **Rule 12: Every model/analyzer must expose version metadata**  
   Weights digests, training dataset hashes, and semver codes are registered in [`registry.json`](./registry.json) and embedded into the immutable `InvestigationManifest`.

4. **Rule 15: Zero paid dependencies**  
   All models run locally via PyTorch, ONNX, or Hugging Face open weights.

---

## Model Inventory

| Engine / Model | Framework | Purpose | Failsafe Behavior |
| :--- | :--- | :--- | :--- |
| **MesoNet-4** | PyTorch / ONNX | Frame-level deepfake video detection | Returns `uncertainty=1.0` if video codec is unsupported |
| **XGBoost Classifier** | XGBoost | Structured investment claim pattern classification | Falls back to rule heuristic if tabular features are sparse |
| **BGE-M3** | sentence-transformers | 1024-d dense multilingual text embeddings | Used for RAG registry search against pgvector |

---

## Directory Layout

```
ml/
├── registry.json             # Canonical machine-readable model catalog
└── README.md                 # ML governance & operational documentation
```
