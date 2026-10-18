"""Evaluation Metrics and Statistical Analysis Engine for VERA.

Calculates:
- Confusion Matrix (TP, FP, TN, FN)
- Precision, Recall, F1 Score
- AUROC (Area Under the Receiver Operating Characteristic)
- False Positive Rate at fixed Recall thresholds (90%, 95%)
- False Negative Rate on High-Severity Scams
- Expected Calibration Error (ECE) with reliability diagram data
- 95% Empirical Confidence Intervals via non-parametric bootstrap (1000 resamples)
"""

import math
import random
from typing import Any

RANDOM_SEED = 42

def calculate_confusion_matrix(y_true: list[bool], y_pred: list[bool]) -> dict[str, int]:
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt and yp)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and yp)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and not yp)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt and not yp)
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}

def calculate_classification_metrics(cm: dict[str, int]) -> dict[str, float]:
    tp, fp, tn, fn = cm["tp"], cm["fp"], cm["tn"], cm["fn"]
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0.0
    
    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
        "false_positive_rate": round(fpr, 4),
        "f1": round(f1, 4),
    }

def calculate_auroc(y_true: list[bool], y_scores: list[float]) -> float:
    """Calculates AUROC using the rank-sum / Mann-Whitney U formulation."""
    pos = [s for yt, s in zip(y_true, y_scores) if yt]
    neg = [s for yt, s in zip(y_true, y_scores) if not yt]
    
    if not pos or not neg:
        return 0.5
    
    # Sort combined pairs
    combined = sorted([(s, 1) for s in pos] + [(s, 0) for s in neg], key=lambda x: x[0])
    
    n_pos = len(pos)
    n_neg = len(neg)
    
    # Calculate rank sum for positive items
    rank_sum = 0.0
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        # Average rank for tied values (1-based index)
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            if combined[k][1] == 1:
                rank_sum += avg_rank
        i = j
        
    u = rank_sum - (n_pos * (n_pos + 1)) / 2.0
    auroc = u / (n_pos * n_neg)
    return round(max(0.0, min(1.0, auroc)), 4)

def calculate_fpr_at_fixed_recall(y_true: list[bool], y_scores: list[float], target_recall: float = 0.95) -> float:
    """Finds the lowest FPR achieved when achieving at least target_recall."""
    pos_scores = sorted([s for yt, s in zip(y_true, y_scores) if yt])
    if not pos_scores:
        return 0.0
    
    # Index for threshold to capture target_recall
    idx = max(0, int(len(pos_scores) * (1.0 - target_recall)))
    threshold = pos_scores[idx]
    
    neg_scores = [s for yt, s in zip(y_true, y_scores) if not yt]
    if not neg_scores:
        return 0.0
    
    fp = sum(1 for s in neg_scores if s >= threshold)
    return round(fp / len(neg_scores), 4)

def calculate_calibration_ece(y_true: list[bool], y_probs: list[float], n_bins: int = 10) -> tuple[float, list[dict[str, Any]]]:
    """Calculates Expected Calibration Error (ECE) and reliability bin statistics."""
    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
    bins_data = []
    total_samples = len(y_true)
    if total_samples == 0:
        return 0.0, []
    
    ece = 0.0
    for i in range(n_bins):
        low, high = bin_boundaries[i], bin_boundaries[i + 1]
        bin_items = [
            (yt, p) for yt, p in zip(y_true, y_probs)
            if (low <= p < high) or (i == n_bins - 1 and low <= p <= high)
        ]
        
        count = len(bin_items)
        if count > 0:
            avg_prob = sum(p for _, p in bin_items) / count
            accuracy = sum(1 for yt, _ in bin_items if yt) / count
            bin_error = abs(accuracy - avg_prob)
            ece += (count / total_samples) * bin_error
            bins_data.append({
                "bin": f"[{low:.1f}, {high:.1f}]",
                "count": count,
                "confidence": round(avg_prob, 4),
                "accuracy": round(accuracy, 4),
                "gap": round(bin_error, 4),
            })
        else:
            bins_data.append({
                "bin": f"[{low:.1f}, {high:.1f}]",
                "count": 0,
                "confidence": round((low + high) / 2.0, 4),
                "accuracy": 0.0,
                "gap": 0.0,
            })
            
    return round(ece, 4), bins_data

def bootstrap_confidence_intervals(
    y_true: list[bool],
    y_scores: list[float],
    threshold: float = 0.5,
    n_resamples: int = 1000,
    seed: int = RANDOM_SEED
) -> dict[str, tuple[float, float]]:
    """Calculates 95% non-parametric empirical bootstrap confidence intervals."""
    rng = random.Random(seed)
    n = len(y_true)
    if n < 5:
        return {}
    
    paired = list(zip(y_true, y_scores))
    f1_list, prec_list, rec_list, auroc_list = [], [], [], []
    
    for _ in range(n_resamples):
        sample = [rng.choice(paired) for _ in range(n)]
        sy_true = [s[0] for s in sample]
        sy_scores = [s[1] for s in sample]
        sy_pred = [s >= threshold for s in sy_scores]
        
        cm = calculate_confusion_matrix(sy_true, sy_pred)
        m = calculate_classification_metrics(cm)
        au = calculate_auroc(sy_true, sy_scores)
        
        f1_list.append(m["f1"])
        prec_list.append(m["precision"])
        rec_list.append(m["recall"])
        auroc_list.append(au)
        
    def get_ci(arr: list[float]) -> tuple[float, float]:
        arr.sort()
        low = arr[int(0.025 * len(arr))]
        high = arr[int(0.975 * len(arr))]
        return (round(low, 4), round(high, 4))
        
    return {
        "f1_ci_95": get_ci(f1_list),
        "precision_ci_95": get_ci(prec_list),
        "recall_ci_95": get_ci(rec_list),
        "auroc_ci_95": get_ci(auroc_list),
    }
