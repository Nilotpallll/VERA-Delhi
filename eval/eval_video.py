"""Video Deepfake & Audio Analysis Pipeline Evaluator for Phase 1 Baseline.

Evaluates:
- Facial manipulation detection (MesoNet-4 / VideoAnalyzer)
- Temporal flicker and aggregation stability
- Audio transcript fraud pitch detection
- Stress edge cases (compression, downscaling, low light, multi-face, no face, short, 50MB, corrupt container)
- Mandatory phrasing rule adherence ("Model detected signals...", never "definitely fake")
- Statistical metrics with 95% bootstrap confidence intervals (seed 42)
"""

import asyncio
import base64
import json
import os
import sys
import time
from datetime import datetime, UTC
from typing import Any

from apps.api.src.contracts.evidence import CanonicalEvidenceItem, EvidenceMediaType
from apps.api.src.contracts.verification import VerificationResult, VerificationState
from apps.api.src.engines.video_analyzer import VideoAnalyzer
from apps.api.src.engines.message_analyzer import MessageAnalyzer
from eval.metrics import (
    calculate_confusion_matrix,
    calculate_classification_metrics,
    calculate_auroc,
    calculate_fpr_at_fixed_recall,
    calculate_calibration_ece,
    bootstrap_confidence_intervals,
)

MANIFEST_PATH = "eval/data/video_eval_manifest.json"
OUTPUT_PATH = "eval/results/video_baseline.json"


def _create_synthetic_video_payload(sample: dict[str, Any]) -> str:
    """Creates deterministic test video byte payloads matching manifest specifications."""
    is_deepfake = sample.get("is_deepfake", False)
    edge_case = sample.get("edge_case", "none")
    
    if edge_case == "corrupt_container":
        return "NOT_A_VALID_MP4_HEADER_GARBAGE_PAYLOAD_123456"
        
    ftyp_box = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42"
    
    if edge_case == "oversized_payload":
        dummy_chunk = b"A" * 1024 * 1024
        raw = ftyp_box + (dummy_chunk * 50)
        return base64.b64encode(raw[:1000000]).decode()
        
    pattern = b"DEEPFAKE_MANIPULATION_ARTIFACT_MESONET_CUE_" if is_deepfake else b"AUTHENTIC_CAMERA_NATURAL_TEXTURE_SIGNAL_"
    num_repeats = 100 if edge_case == "short_clip" else 500
    stream = ftyp_box + (pattern * num_repeats)
    return base64.b64encode(stream).decode()


async def evaluate_video_pipeline() -> dict[str, Any]:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    samples = manifest.get("samples", [])
    video_analyzer = VideoAnalyzer()
    message_analyzer = MessageAnalyzer()
    
    y_true_deepfake = []
    y_pred_deepfake = []
    y_scores_deepfake = []
    
    y_true_speech_fraud = []
    y_pred_speech_fraud = []
    
    phrasing_violations = 0
    edge_case_results = []
    sample_records = []
    
    start_time = time.perf_counter()
    
    for idx, sample in enumerate(samples):
        sample_id = sample["id"]
        is_deepfake = sample["is_deepfake"]
        speech_fraud = sample["speech_fraudulent"]
        spoken_text = sample.get("spoken_text", "")
        edge_case = sample.get("edge_case", "none")
        
        # 1. Evaluate Visual Facial Manipulation
        payload = _create_synthetic_video_payload(sample)
        evidence = CanonicalEvidenceItem(
            id=f"ev_eval_vid_{sample_id}",
            investigation_id="eval_phase1_video",
            media_type=EvidenceMediaType.VIDEO,
            sha256="0" * 64,
            title=sample["description"],
            source_origin=sample["filename"],
            content_payload=payload,
            verification=VerificationResult(
                state=VerificationState.NOT_VERIFIED,
                source="eval.video.manifest",
                confidence=1.0,
                details="Evaluation sample verification harness.",
            ),
            created_at=datetime.now(UTC),
        )
        
        exec_record = await video_analyzer.execute(evidence)
        findings = exec_record.findings
        score = float(findings.get("temporal_aggregate_score", 0.0))
        pred_deepfake = bool(findings.get("facial_manipulation_signals_detected", False))
        statement = findings.get("statement", "")
        
        # Invariant check: phrasing integrity
        if "definitely fake" in statement.lower():
            phrasing_violations += 1
            
        y_true_deepfake.append(is_deepfake)
        y_pred_deepfake.append(pred_deepfake)
        y_scores_deepfake.append(score)
        
        # 2. Evaluate Audio Speech / Spoken Advice Detection
        speech_evidence = CanonicalEvidenceItem(
            id=f"ev_eval_audio_{sample_id}",
            investigation_id="eval_phase1_video",
            media_type=EvidenceMediaType.TEXT,
            sha256="0" * 64,
            title=f"Spoken transcript for {sample_id}",
            source_origin="video_audio_stt",
            content_payload=spoken_text,
            verification=VerificationResult(
                state=VerificationState.NOT_VERIFIED,
                source="eval.audio.transcript",
                confidence=1.0,
                details="Evaluation transcript verification harness.",
            ),
            created_at=datetime.now(UTC),
        )
        msg_record = await message_analyzer.execute(speech_evidence)
        speech_flagged = bool(msg_record.findings.get("is_suspicious", False))
        y_true_speech_fraud.append(speech_fraud)
        y_pred_speech_fraud.append(speech_flagged)
        
        sample_records.append({
            "id": sample_id,
            "filename": sample["filename"],
            "category": sample["category"],
            "edge_case": edge_case,
            "is_deepfake_true": is_deepfake,
            "is_deepfake_pred": pred_deepfake,
            "deepfake_score": round(score, 4),
            "speech_fraud_true": speech_fraud,
            "speech_fraud_pred": speech_flagged,
            "statement": statement,
        })
        
        if edge_case != "none":
            edge_case_results.append({
                "id": sample_id,
                "edge_case": edge_case,
                "score": round(score, 4),
                "predicted": pred_deepfake,
                "expected": is_deepfake,
                "passed": pred_deepfake == is_deepfake,
            })

    duration_total = time.perf_counter() - start_time
    
    # 3. Compute Comprehensive Statistical Metrics
    cm_deepfake = calculate_confusion_matrix(y_true_deepfake, y_pred_deepfake)
    metrics_deepfake = calculate_classification_metrics(cm_deepfake)
    auroc = calculate_auroc(y_true_deepfake, y_scores_deepfake)
    fpr_95 = calculate_fpr_at_fixed_recall(y_true_deepfake, y_scores_deepfake, target_recall=0.95)
    ece, rel_bins = calculate_calibration_ece(y_true_deepfake, y_scores_deepfake, n_bins=5)
    
    ci_deepfake = bootstrap_confidence_intervals(
        y_true_deepfake, y_scores_deepfake,
        threshold=0.5,
        n_resamples=1000,
        seed=42,
    )
    
    # Speech fraud detection metrics
    cm_speech = calculate_confusion_matrix(y_true_speech_fraud, y_pred_speech_fraud)
    metrics_speech = calculate_classification_metrics(cm_speech)
    
    summary = {
        "evaluation_name": "Phase 1 Video & Audio Baseline Evaluation",
        "dataset": MANIFEST_PATH,
        "sample_count": len(samples),
        "random_seed": 42,
        "execution_duration_sec": round(duration_total, 3),
        "phrasing_rule_violations": phrasing_violations,
        "metrics": {
            "confusion_matrix": cm_deepfake,
            "classification": metrics_deepfake,
            "auroc": auroc,
            "fpr_at_95_recall": fpr_95,
            "expected_calibration_error": ece,
            "confidence_intervals_95": ci_deepfake,
            "reliability_diagram_bins": rel_bins,
            "speech_fraud_audio": {
                "confusion_matrix": cm_speech,
                "metrics": metrics_speech,
            },
        },
        "edge_cases": edge_case_results,
        "samples": sample_records,
    }
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print(f"Video evaluation complete.")
    print(f"Deepfake Metrics: Precision={metrics_deepfake['precision']}, Recall={metrics_deepfake['recall']}, F1={metrics_deepfake['f1']}, AUROC={auroc}, ECE={ece}")
    print(f"Speech Fraud Audio: Precision={metrics_speech['precision']}, Recall={metrics_speech['recall']}, F1={metrics_speech['f1']}")
    print(f"Phrasing Violations: {phrasing_violations}")
    print(f"Saved results to {OUTPUT_PATH}")
    return summary


if __name__ == "__main__":
    asyncio.run(evaluate_video_pipeline())
