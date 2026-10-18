"""Text & Communication Analysis Pipeline Evaluator for Phase 1 Baseline.

Evaluates:
- MessageAnalyzer heuristics, entity extraction, claims, and solicitation flags
- SEBIGuidelineDetector regulatory violation matching
- 320 items balanced across:
  * 100 Genuine disclosures
  * 80 Classic investment fraud
  * 60 Multilingual fraud (Hindi, Hinglish, Tamil, Telugu, Marathi, Bengali)
  * 50 Adversarial evasions (leetspeak, zero-width characters, homoglyphs, emoji)
  * 30 Edge cases (microcaps, options disclosures, distress recovery)
- Statistical metrics with 95% bootstrap confidence intervals (seed 42, 1000 resamples)
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, UTC
from typing import Any

from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.verification import VerificationResult, VerificationState
from apps.api.src.engines.message_analyzer import MessageAnalyzer
from apps.api.src.knowledge.guideline_matcher import SEBIGuidelineDetector
from eval.metrics import (
    calculate_confusion_matrix,
    calculate_classification_metrics,
    calculate_auroc,
    calculate_fpr_at_fixed_recall,
    calculate_calibration_ece,
    bootstrap_confidence_intervals,
)

CORPUS_PATH = "eval/data/text_eval_corpus_300.json"
OUTPUT_PATH = "eval/results/text_baseline.json"


async def evaluate_text_pipeline() -> dict[str, Any]:
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)
        
    samples = corpus.get("samples", [])
    msg_analyzer = MessageAnalyzer()
    guideline_detector = SEBIGuidelineDetector()
    
    y_true = []
    y_pred = []
    y_scores = []
    
    # Category and language trackers
    category_data: dict[str, dict[str, list]] = {}
    language_data: dict[str, dict[str, list]] = {}
    
    sample_records = []
    start_time = time.perf_counter()
    
    for idx, sample in enumerate(samples):
        sample_id = sample["id"]
        content = sample["content"]
        is_fraud = sample["is_fraud"]
        category = sample["category"]
        language = sample.get("language", "en")
        
        evidence = CanonicalEvidenceItem(
            id=f"ev_eval_txt_{sample_id}",
            investigation_id="eval_phase1_text",
            media_type=EvidenceMediaType.TEXT,
            sha256="0" * 64,
            title=f"Text sample {sample_id}",
            source_origin="text_eval_corpus",
            content_payload=content,
            verification=VerificationResult(
                state=VerificationState.NOT_VERIFIED,
                source="eval.text.corpus",
                confidence=1.0,
                details="Evaluation sample verification harness.",
            ),
            created_at=datetime.now(UTC),
        )
        
        # 1. Message Analyzer Execution
        record = await msg_analyzer.execute(evidence)
        findings = record.findings
        total_indicators = findings.get("total_indicators_detected", 0)
        is_suspicious_msg = findings.get("is_suspicious", False)
        
        # 2. SEBI Guideline Matching Execution
        guideline_res = await guideline_detector.match_guideline(content)
        is_violation_sebi = guideline_res.is_violation
        sebi_conf = guideline_res.confidence if is_violation_sebi else 0.0
        
        # Baseline fusion rule: Flagged if either heuristic detected signals or SEBI matched violation
        is_flagged = is_suspicious_msg or is_violation_sebi
        
        # Score calculation: heuristic indicator density + SEBI confidence
        raw_score = min(1.0, (total_indicators * 0.25) + (sebi_conf * 0.5))
        score = round(raw_score, 4)
        
        y_true.append(is_fraud)
        y_pred.append(is_flagged)
        y_scores.append(score)
        
        # Track by Category
        if category not in category_data:
            category_data[category] = {"y_true": [], "y_pred": [], "y_scores": []}
        category_data[category]["y_true"].append(is_fraud)
        category_data[category]["y_pred"].append(is_flagged)
        category_data[category]["y_scores"].append(score)
        
        # Track by Language
        if language not in language_data:
            language_data[language] = {"y_true": [], "y_pred": [], "y_scores": []}
        language_data[language]["y_true"].append(is_fraud)
        language_data[language]["y_pred"].append(is_flagged)
        language_data[language]["y_scores"].append(score)
        
        sample_records.append({
            "id": sample_id,
            "category": category,
            "language": language,
            "is_fraud_true": is_fraud,
            "is_flagged_pred": is_flagged,
            "score": score,
            "indicators": total_indicators,
            "sebi_violation": is_violation_sebi,
            "content_preview": content[:75] + ("..." if len(content) > 75 else ""),
        })

    duration_total = time.perf_counter() - start_time
    
    # Overall Metrics
    cm = calculate_confusion_matrix(y_true, y_pred)
    metrics = calculate_classification_metrics(cm)
    auroc = calculate_auroc(y_true, y_scores)
    fpr_95 = calculate_fpr_at_fixed_recall(y_true, y_scores, target_recall=0.95)
    ece, rel_bins = calculate_calibration_ece(y_true, y_scores, n_bins=10)
    
    ci = bootstrap_confidence_intervals(
        y_true, y_scores,
        threshold=0.25,
        n_resamples=1000,
        seed=42,
    )
    
    # Per-category metrics
    category_metrics = {}
    for cat, data in category_data.items():
        cat_cm = calculate_confusion_matrix(data["y_true"], data["y_pred"])
        cat_m = calculate_classification_metrics(cat_cm)
        cat_auroc = calculate_auroc(data["y_true"], data["y_scores"])
        category_metrics[cat] = {
            "samples": len(data["y_true"]),
            "confusion_matrix": cat_cm,
            "metrics": cat_m,
            "auroc": cat_auroc,
        }
        
    # Per-language metrics
    language_metrics = {}
    for lang, data in language_data.items():
        lang_cm = calculate_confusion_matrix(data["y_true"], data["y_pred"])
        lang_m = calculate_classification_metrics(lang_cm)
        language_metrics[lang] = {
            "samples": len(data["y_true"]),
            "confusion_matrix": lang_cm,
            "recall": lang_m["recall"],
            "precision": lang_m["precision"],
            "f1": lang_m["f1"],
        }
        
    summary = {
        "evaluation_name": "Phase 1 Text & Communication Baseline Evaluation",
        "dataset": CORPUS_PATH,
        "sample_count": len(samples),
        "random_seed": 42,
        "execution_duration_sec": round(duration_total, 3),
        "metrics": {
            "confusion_matrix": cm,
            "classification": metrics,
            "auroc": auroc,
            "fpr_at_95_recall": fpr_95,
            "expected_calibration_error": ece,
            "confidence_intervals_95": ci,
            "reliability_diagram_bins": rel_bins,
        },
        "breakdown_by_category": category_metrics,
        "breakdown_by_language": language_metrics,
        "samples": sample_records,
    }
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"Text evaluation complete on {len(samples)} samples.")
    print(f"Overall Metrics: Precision={metrics['precision']}, Recall={metrics['recall']}, F1={metrics['f1']}, AUROC={auroc}, ECE={ece}, FPR@95={fpr_95}")
    for cat, m in category_metrics.items():
        print(f"  Category '{cat}': Recall={m['metrics']['recall']}, Precision={m['metrics']['precision']}, F1={m['metrics']['f1']}")
    print(f"Saved results to {OUTPUT_PATH}")
    return summary


if __name__ == "__main__":
    asyncio.run(evaluate_text_pipeline())
