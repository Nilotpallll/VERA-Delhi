"""URL, UPI, and SEBI Intermediary Verification Evaluator for Phase 1 Baseline.

Evaluates:
- 50 URLs (punycode, typosquatting, raw IP, high-risk TLDs, legit portals)
- 30 UPI IDs (impersonation handles, merchant escrows)
- 20 Companies / Intermediaries (SEBI registered vs debarred / fictitious)
- Computes statistical metrics, AUROC, ECE, and 95% bootstrap CI (seed 42)
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
from apps.api.src.engines.url_analyzer import URLAnalyzer
from apps.api.src.investigator.tools import InvestigatorToolRegistry
from eval.metrics import (
    calculate_confusion_matrix,
    calculate_classification_metrics,
    calculate_auroc,
    calculate_fpr_at_fixed_recall,
    calculate_calibration_ece,
    bootstrap_confidence_intervals,
)

EVAL_PATH = "eval/data/url_upi_company_eval.json"
OUTPUT_PATH = "eval/results/url_upi_baseline.json"


async def evaluate_url_upi_pipeline() -> dict[str, Any]:
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    samples = data.get("samples", [])
    url_analyzer = URLAnalyzer()
    
    y_true_all = []
    y_pred_all = []
    y_scores_all = []
    
    modality_data: dict[str, dict[str, list]] = {
        "url": {"y_true": [], "y_pred": [], "y_scores": []},
        "upi": {"y_true": [], "y_pred": [], "y_scores": []},
        "company": {"y_true": [], "y_pred": [], "y_scores": []},
    }
    
    sample_records = []
    start_time = time.perf_counter()
    
    for idx, sample in enumerate(samples):
        sample_id = sample["id"]
        modality = sample["modality"]
        content = sample["content"]
        is_fraud = sample["is_fraud"]
        
        is_flagged = False
        score = 0.0
        details = ""
        
        # 1. URL Modality Evaluation
        if modality == "url":
            evidence = CanonicalEvidenceItem(
                id=f"ev_eval_url_{sample_id}",
                investigation_id="eval_phase1_url",
                media_type=EvidenceMediaType.URL,
                sha256="0" * 64,
                title=f"URL {content}",
                source_origin=content,
                content_payload=content,
                verification=VerificationResult(
                    state=VerificationState.NOT_VERIFIED,
                    source="eval.url.dataset",
                    confidence=1.0,
                    details="Evaluation sample verification harness.",
                ),
                created_at=datetime.now(UTC),
            )
            exec_record = await url_analyzer.execute(evidence)
            findings = exec_record.findings
            det_signals = findings.get("deterministic_signals", {})
            ml_pred = findings.get("ml_prediction", {})
            
            is_flagged = bool(findings.get("is_suspicious", False))
            risk_prob = float(ml_pred.get("risk_probability", 0.0))
            indicator_cnt = int(det_signals.get("risk_indicator_count", 0))
            
            score = round(max(risk_prob, 0.85 if indicator_cnt > 0 else 0.10), 4)
            details = f"is_suspicious={is_flagged}, indicators={indicator_cnt}, ml_risk={risk_prob}"
            
        # 2. UPI Modality Evaluation
        elif modality == "upi":
            res = await InvestigatorToolRegistry.verify_payment(upi_id=content)
            findings = res.findings
            is_mismatch = bool(findings.get("is_mismatch", False))
            reasons = findings.get("reasons", [])
            is_flagged = is_mismatch
            score = 0.90 if is_mismatch else 0.10
            details = f"is_mismatch={is_mismatch}, reasons={reasons}"
            
        # 3. Company / Intermediary Evaluation
        elif modality == "company":
            name = content.split("(")[0].strip()
            reg_no = None
            if "Reg:" in content:
                reg_no = content.split("Reg:")[1].split(")")[0].strip()
            elif "Status:" in content:
                reg_no = content.split("Status:")[1].split(")")[0].strip()
                
            res = await InvestigatorToolRegistry.verify_sebi_entity(entity_name=name, registration_number=reg_no)
            verif_state = res.findings.get("state")
            is_flagged = (verif_state == VerificationState.NOT_VERIFIED.value)
            score = 0.95 if is_flagged else 0.05
            details = res.findings.get("details", "")
            
        y_true_all.append(is_fraud)
        y_pred_all.append(is_flagged)
        y_scores_all.append(score)
        
        modality_data[modality]["y_true"].append(is_fraud)
        modality_data[modality]["y_pred"].append(is_flagged)
        modality_data[modality]["y_scores"].append(score)
        
        sample_records.append({
            "id": sample_id,
            "modality": modality,
            "content": content,
            "is_fraud_true": is_fraud,
            "is_flagged_pred": is_flagged,
            "score": score,
            "details": details,
        })
        
    duration_total = time.perf_counter() - start_time
    
    # Overall Metrics
    cm_all = calculate_confusion_matrix(y_true_all, y_pred_all)
    metrics_all = calculate_classification_metrics(cm_all)
    auroc_all = calculate_auroc(y_true_all, y_scores_all)
    fpr_95_all = calculate_fpr_at_fixed_recall(y_true_all, y_scores_all, target_recall=0.95)
    ece_all, rel_bins_all = calculate_calibration_ece(y_true_all, y_scores_all, n_bins=5)
    
    ci_all = bootstrap_confidence_intervals(
        y_true_all, y_scores_all,
        threshold=0.5,
        n_resamples=1000,
        seed=42,
    )
    
    # Per-modality metrics
    modality_metrics = {}
    for mod, data_dict in modality_data.items():
        cm_mod = calculate_confusion_matrix(data_dict["y_true"], data_dict["y_pred"])
        m_mod = calculate_classification_metrics(cm_mod)
        auroc_mod = calculate_auroc(data_dict["y_true"], data_dict["y_scores"])
        modality_metrics[mod] = {
            "samples": len(data_dict["y_true"]),
            "confusion_matrix": cm_mod,
            "metrics": m_mod,
            "auroc": auroc_mod,
        }
        
    summary = {
        "evaluation_name": "Phase 1 URL, UPI, and Entity Verification Baseline Evaluation",
        "dataset": EVAL_PATH,
        "sample_count": len(samples),
        "random_seed": 42,
        "execution_duration_sec": round(duration_total, 3),
        "metrics": {
            "confusion_matrix": cm_all,
            "classification": metrics_all,
            "auroc": auroc_all,
            "fpr_at_95_recall": fpr_95_all,
            "expected_calibration_error": ece_all,
            "confidence_intervals_95": ci_all,
            "reliability_diagram_bins": rel_bins_all,
        },
        "breakdown_by_modality": modality_metrics,
        "samples": sample_records,
    }
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"URL/UPI/Entity evaluation complete on {len(samples)} samples.")
    print(f"Overall Metrics: Precision={metrics_all['precision']}, Recall={metrics_all['recall']}, F1={metrics_all['f1']}, AUROC={auroc_all}, ECE={ece_all}")
    for mod, m in modality_metrics.items():
        print(f"  Modality '{mod}': Precision={m['metrics']['precision']}, Recall={m['metrics']['recall']}, F1={m['metrics']['f1']}, AUROC={m['auroc']}")
    print(f"Saved results to {OUTPUT_PATH}")
    return summary


if __name__ == "__main__":
    asyncio.run(evaluate_url_upi_pipeline())
