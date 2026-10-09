"""Evaluation Benchmark Dataset and Metrics Reporter for VERA Phase 3.

Evaluates:
  - genuine investment guidance
  - scam messages
  - guaranteed-return claims
  - impersonation claims
  - registration claims
  - ambiguous claims
  - adversarially worded claims

Metrics:
  - Precision
  - Recall
  - F1 Score
  - Citation Accuracy
  - False-Positive Rate (FPR)
  - False-Negative Rate (FNR)
"""

from typing import Any

from pydantic import BaseModel, Field

from .guideline_matcher import SEBIGuidelineDetector


class EvaluationSample(BaseModel):
    id: str
    category: str
    text: str
    is_scam: bool
    expected_violation: bool
    must_have_citation: bool
    notes: str = ""


# Labelled Evaluation Dataset
LABELED_EVALUATION_DATASET: list[EvaluationSample] = [
    # 1. Guaranteed-return claims (True Positives)
    EvaluationSample(
        id="eval_001",
        category="guaranteed_return",
        text="Join our VIP trading pool today and get 40% monthly returns guaranteed with zero drawdown risk.",
        is_scam=True,
        expected_violation=True,
        must_have_citation=True,
        notes="Classic guaranteed return promise prohibited by SEBI.",
    ),
    EvaluationSample(
        id="eval_002",
        category="guaranteed_return",
        text="Invest 50,000 INR now and get double your money in 15 days fixed return without any loss.",
        is_scam=True,
        expected_violation=True,
        must_have_citation=True,
        notes="Doubling money scheme.",
    ),
    # 2. Impersonation / Unregistered institutional accounts (True Positives)
    EvaluationSample(
        id="eval_003",
        category="impersonation",
        text="We are institutional FII partners offering special pre-IPO quota allocations via custom APK download.",
        is_scam=True,
        expected_violation=True,
        must_have_citation=True,
        notes="FII institutional quota scam using APKs.",
    ),
    EvaluationSample(
        id="eval_004",
        category="scam_message",
        text="Secret WhatsApp VIP group with insider operator tips. Buy XYZ penny stock tomorrow morning for 10x target.",
        is_scam=True,
        expected_violation=True,
        must_have_citation=True,
        notes="Social media pump-and-dump tipster.",
    ),
    # 3. Genuine investment guidance (True Negatives / Compliant)
    EvaluationSample(
        id="eval_005",
        category="genuine_guidance",
        text="Equity investments are subject to market risks. Please read all scheme-related documents carefully before investing.",
        is_scam=False,
        expected_violation=False,
        must_have_citation=False,
        notes="Standard statutory risk disclaimer.",
    ),
    EvaluationSample(
        id="eval_006",
        category="genuine_guidance",
        text="Diversifying your portfolio across index funds and sovereign gold bonds can help manage long-term volatility.",
        is_scam=False,
        expected_violation=False,
        must_have_citation=False,
        notes="Prudent financial planning advice.",
    ),
    # 4. Registration claims
    EvaluationSample(
        id="eval_007",
        category="registration_claim",
        text="We are registered with SEBI under registration number INA000012345.",
        is_scam=False,
        expected_violation=False,
        must_have_citation=False,
        notes="Legitimate registration statement claiming valid format.",
    ),
    EvaluationSample(
        id="eval_008",
        category="registration_claim",
        text="Our company is 100% government approved with fake certificate number SEBI-XYZ-9999.",
        is_scam=True,
        expected_violation=True,
        must_have_citation=True,
        notes="Fabricated registration format.",
    ),
    # 5. Ambiguous claims
    EvaluationSample(
        id="eval_009",
        category="ambiguous",
        text="Historically, equity mutual funds have generated an inflation-beating annualized CAGR of 12% to 14% over 10-year horizons.",
        is_scam=False,
        expected_violation=False,
        must_have_citation=False,
        notes="Historical statistical observation without guarantees.",
    ),
    # 6. Adversarially worded claims (Testing evasion)
    EvaluationSample(
        id="eval_010",
        category="adversarial",
        text="Not an investment advisory, but our proprietary algorithm has delivered 100% profit continuously and guarantees safety.",
        is_scam=True,
        expected_violation=True,
        must_have_citation=True,
        notes="Adversarially disguised guarantee with fake disclaimer.",
    ),
]


class EvaluationReport(BaseModel):
    total_samples: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    citation_accuracy: float
    false_positive_rate: float
    false_negative_rate: float
    breakdown_by_category: dict[str, dict[str, Any]] = Field(default_factory=dict)


class BenchmarkEvaluator:
    """Runs evaluation benchmark and computes metrics."""

    def __init__(self, detector: SEBIGuidelineDetector | None = None):
        self.detector = detector or SEBIGuidelineDetector()

    async def run_evaluation(self, samples: list[EvaluationSample] | None = None) -> EvaluationReport:
        dataset = samples or LABELED_EVALUATION_DATASET
        tp = fp = tn = fn = 0
        valid_citations = 0
        total_citations_required = 0
        category_stats: dict[str, dict[str, int]] = {}

        for sample in dataset:
            cat = sample.category
            if cat not in category_stats:
                category_stats[cat] = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "count": 0}
            category_stats[cat]["count"] += 1

            result = await self.detector.match_guideline(sample.text)
            predicted_violation = result.is_violation

            # Check citation accuracy
            if sample.must_have_citation:
                total_citations_required += 1
                if result.citations and all(c.source_url.startswith("http") for c in result.citations):
                    valid_citations += 1

            if predicted_violation and sample.expected_violation:
                tp += 1
                category_stats[cat]["tp"] += 1
            elif predicted_violation and not sample.expected_violation:
                fp += 1
                category_stats[cat]["fp"] += 1
            elif not predicted_violation and not sample.expected_violation:
                tn += 1
                category_stats[cat]["tn"] += 1
            else:
                fn += 1
                category_stats[cat]["fn"] += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        citation_acc = valid_citations / total_citations_required if total_citations_required > 0 else 1.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        return EvaluationReport(
            total_samples=len(dataset),
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            citation_accuracy=round(citation_acc, 4),
            false_positive_rate=round(fpr, 4),
            false_negative_rate=round(fnr, 4),
            breakdown_by_category=category_stats,
        )
