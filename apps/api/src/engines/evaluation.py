"""ML Model Benchmark Evaluation and Forensic Metrics Reporter for VERA.

Architecture Rule 12: Every model/analyzer exposes version metadata.
Architecture Rule 13: Every investigation is reproducible.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from pydantic import BaseModel, Field


class ConfusionMatrix(BaseModel):
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0

    @property
    def matrix(self) -> list[list[int]]:
        """Standard 2x2 confusion matrix: [[TN, FP], [FN, TP]]."""
        return [
            [self.true_negatives, self.false_positives],
            [self.false_negatives, self.true_positives],
        ]


class ModelEvaluationReport(BaseModel):
    model_name: str
    model_version: str
    total_eval_samples: int
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1_score: float = Field(ge=0.0, le=1.0)
    confusion_matrix: list[list[int]]
    false_negative_rate: float = Field(ge=0.0, le=1.0, description="FNR = FN / (FN + TP)")
    avg_latency_ms: float
    p95_latency_ms: float
    inference_failure_rate: float = Field(ge=0.0, le=1.0)


class ModelEvaluator:
    """Benchmark runner for VERA ML models (URL, APK, Deepfake MesoNet).

    Computes:
    - Precision
    - Recall
    - F1 Score
    - 2x2 Confusion Matrix
    - False Negative Rate (critical for fraud: missing a scam has severe real-world harm)
    - Mean and P95 latency (ms)
    - Inference failure rate
    """

    def evaluate_model(
        self,
        model_name: str,
        model_version: str,
        dataset: list[dict[str, Any]],
        predict_fn: Callable[[Any], bool | float],
        threshold: float = 0.50,
    ) -> ModelEvaluationReport:
        """Run benchmark evaluation over labeled ground truth dataset.

        dataset items must contain:
        - "input": payload to evaluate
        - "ground_truth": bool (True = malicious/fraud/deepfake, False = benign)
        """
        cm = ConfusionMatrix()
        latencies_ms: list[float] = []
        failure_count = 0

        for item in dataset:
            inp = item["input"]
            actual = bool(item["ground_truth"])

            start = time.perf_counter()
            try:
                raw_pred = predict_fn(inp)
                duration = (time.perf_counter() - start) * 1000.0
                latencies_ms.append(duration)

                if isinstance(raw_pred, bool):
                    predicted = raw_pred
                else:
                    predicted = float(raw_pred) >= threshold

                if predicted and actual:
                    cm.true_positives += 1
                elif predicted and not actual:
                    cm.false_positives += 1
                elif not predicted and not actual:
                    cm.true_negatives += 1
                else:
                    cm.false_negatives += 1

            except Exception:
                duration = (time.perf_counter() - start) * 1000.0
                latencies_ms.append(duration)
                failure_count += 1
                # Fail-safe: failure counts as false negative against ground truth
                if actual:
                    cm.false_negatives += 1
                else:
                    cm.true_negatives += 1

        total_samples = max(1, len(dataset))
        tp = cm.true_positives
        fp = cm.false_positives
        fn = cm.false_negatives
        tn = cm.true_negatives

        # Precision = TP / (TP + FP)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0

        # Recall = TP / (TP + FN)
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

        # F1 = 2 * (P * R) / (P + R)
        f1 = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # False Negative Rate = FN / (FN + TP)
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        # Latency statistics
        sorted_latencies = sorted(latencies_ms) if latencies_ms else [0.0]
        avg_latency = sum(sorted_latencies) / len(sorted_latencies)
        p95_idx = int(0.95 * len(sorted_latencies))
        p95_latency = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)]

        failure_rate = failure_count / total_samples

        return ModelEvaluationReport(
            model_name=model_name,
            model_version=model_version,
            total_eval_samples=total_samples,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            confusion_matrix=cm.matrix,
            false_negative_rate=round(fnr, 4),
            avg_latency_ms=round(avg_latency, 2),
            p95_latency_ms=round(p95_latency, 2),
            inference_failure_rate=round(failure_rate, 4),
        )


# Global evaluator singleton
model_evaluator = ModelEvaluator()
