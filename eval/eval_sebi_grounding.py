"""SEBI Regulatory Grounding & Citation Veracity Evaluator for Phase 1 Baseline.

Evaluates:
- Citation Precision: Percentage of citations that match authoritative ground-truth circulars
- Citation Recall: Percentage of applicable regulatory circulars retrieved for target queries
- Regulatory Hallucination Rate: Rate of non-existent or fabricated circular citations
- Vector retrieval top-1 and top-3 accuracy against sebi_source_of_truth.json
"""

import asyncio
import json
import os
import sys
import time
from typing import Any

from apps.api.src.knowledge.guideline_matcher import SEBIGuidelineDetector
from apps.api.src.knowledge.store import RegulatoryVectorStore

GROUND_TRUTH_PATH = "eval/data/sebi_source_of_truth.json"
OUTPUT_PATH = "eval/results/sebi_grounding_baseline.json"

TEST_QUERIES = [
    {
        "query_id": "gt_q_01",
        "query": "Guaranteed 50% monthly profit Telegram VIP group with zero risk",
        "expected_circular_id": "CIR/2023/123",
        "category": "guaranteed_returns",
    },
    {
        "query_id": "gt_q_02",
        "query": "Join unregistered insider trading WhatsApp group with operator circuit calls",
        "expected_circular_id": "CIR/2024/45",
        "category": "unregistered_intermediary",
    },
    {
        "query_id": "gt_q_03",
        "query": "Pre-IPO special allotment of unlisted shares transfer money to personal account",
        "expected_circular_id": "CIR/2024/45",
        "category": "pre_ipo_fraud",
    },
    {
        "query_id": "gt_q_04",
        "query": "Trade binary options on unlicensed foreign forex app with UPI deposit",
        "expected_circular_id": "RBI/2023/ALERT-LIST",
        "category": "unauthorized_forex",
    },
    {
        "query_id": "gt_q_05",
        "query": "Social media operator channel pumping penny stocks for sudden upper circuit",
        "expected_circular_id": "NSE/2024/SOCIAL-ALERT",
        "category": "social_media_pump_and_dump",
    },
    {
        "query_id": "gt_q_06",
        "query": "SEBI certified cyber cell will recover your lost scam money for 10% advance fee",
        "expected_circular_id": "CIR/2024/45",
        "category": "recovery_scam",
    },
    {
        "query_id": "gt_q_07",
        "query": "Pay 15000 Demat unfreeze fee to UPI handle to avoid SEBI legal penalty",
        "expected_circular_id": "CIR/2024/45",
        "category": "impersonation_extortion",
    },
    {
        "query_id": "gt_q_08",
        "query": "100% loss-proof algorithmic options trading bot giving daily assured returns",
        "expected_circular_id": "CIR/2023/123",
        "category": "guaranteed_returns",
    },
    {
        "query_id": "gt_q_09",
        "query": "Dabba trading off-exchange terminal without PAN or KYC cash transactions",
        "expected_circular_id": "CIR/2024/45",
        "category": "unregistered_intermediary",
    },
    {
        "query_id": "gt_q_10",
        "query": "Offshore binary trading platform OlympTrade Quotex deposit INR",
        "expected_circular_id": "RBI/2023/ALERT-LIST",
        "category": "unauthorized_forex",
    },
    # Legitimate queries where no regulatory violation should be cited
    {
        "query_id": "gt_q_11",
        "query": "HDFC Securities quarterly research outlook on banking sector and loan book growth",
        "expected_circular_id": None,
        "category": "legitimate_research",
    },
    {
        "query_id": "gt_q_12",
        "query": "Mutual fund investments are subject to market risks read all scheme documents",
        "expected_circular_id": None,
        "category": "legitimate_disclosure",
    },
    {
        "query_id": "gt_q_13",
        "query": "NSE Samvat Muhurat trading session timings 18:15 to 19:15 official circular",
        "expected_circular_id": None,
        "category": "legitimate_notice",
    },
    {
        "query_id": "gt_q_14",
        "query": "AMFI monthly report on equity mutual fund inflows and SIP momentum",
        "expected_circular_id": None,
        "category": "legitimate_disclosure",
    },
    {
        "query_id": "gt_q_15",
        "query": "SEBI study discloses that 9 out of 10 retail traders incur net losses in F&O",
        "expected_circular_id": None,
        "category": "legitimate_disclosure",
    },
]


def resolve_citation_id(cit: Any, canonical_corpus: list[dict[str, Any]]) -> str | None:
    """Resolves citation URL or title against authoritative canonical corpus."""
    source_url = getattr(cit, "source_url", "")
    title = getattr(cit, "title", "").lower()
    
    for c in canonical_corpus:
        if c["official_url"] and c["official_url"].rstrip("/") == source_url.rstrip("/"):
            return c["circular_id"]
        if c["circular_id"].lower() in title:
            return c["circular_id"]
        # Partial title match
        if c["full_title"].lower() in title or title in c["full_title"].lower():
            return c["circular_id"]
    return None


async def evaluate_sebi_grounding() -> dict[str, Any]:
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        ground_truth_doc = json.load(f)
        
    canonical_corpus = ground_truth_doc.get("canonical_corpus", [])
    valid_circular_ids = {c["circular_id"] for c in canonical_corpus}
    
    detector = SEBIGuidelineDetector()
    vector_store = RegulatoryVectorStore()
    
    total_queries = len(TEST_QUERIES)
    fraud_queries = [q for q in TEST_QUERIES if q["expected_circular_id"] is not None]
    
    total_citations_emitted = 0
    valid_citations_count = 0
    hallucinated_citations_count = 0
    
    correct_retrievals = 0
    top3_retrievals = 0
    
    query_results = []
    start_time = time.perf_counter()
    
    for tq in TEST_QUERIES:
        query_text = tq["query"]
        expected_cid = tq["expected_circular_id"]
        
        # 1. Test Guideline Detector matching
        match_res = await detector.match_guideline(query_text)
        
        # 2. Test Vector Store direct search
        retrieval = await vector_store.search(query_text, top_k=3)
        retrieved_cids = []
        for cit in retrieval.citations:
            found_id = resolve_citation_id(cit, canonical_corpus)
            retrieved_cids.append(found_id or cit.title[:30])
            
        # Check citations emitted by detector
        emitted_cids = []
        for cit in match_res.citations:
            total_citations_emitted += 1
            cid = resolve_citation_id(cit, canonical_corpus)
            if cid and cid in valid_circular_ids:
                valid_citations_count += 1
                emitted_cids.append(cid)
            else:
                hallucinated_citations_count += 1
                emitted_cids.append(f"UNVERIFIED_{cit.title[:20]}")
                
        # Evaluate retrieval accuracy for fraud queries
        top1_match = False
        top3_match = False
        if expected_cid is not None:
            if retrieved_cids and retrieved_cids[0] == expected_cid:
                top1_match = True
                correct_retrievals += 1
            if expected_cid in retrieved_cids:
                top3_match = True
                top3_retrievals += 1
        else:
            top1_match = not match_res.is_violation
            top3_match = True
            
        query_results.append({
            "query_id": tq["query_id"],
            "query": query_text,
            "category": tq["category"],
            "expected_circular_id": expected_cid,
            "detector_violation": match_res.is_violation,
            "detector_confidence": match_res.confidence,
            "retrieved_cids": retrieved_cids,
            "emitted_cids": emitted_cids,
            "top1_match": top1_match,
            "top3_match": top3_match,
        })
        
    duration = time.perf_counter() - start_time
    
    citation_precision = (
        round(valid_citations_count / total_citations_emitted, 4)
        if total_citations_emitted > 0
        else 1.0
    )
    citation_recall = round(correct_retrievals / len(fraud_queries), 4)
    top3_recall = round(top3_retrievals / len(fraud_queries), 4)
    hallucination_rate = (
        round(hallucinated_citations_count / total_citations_emitted, 4)
        if total_citations_emitted > 0
        else 0.0
    )
    
    summary = {
        "evaluation_name": "Phase 1 SEBI Regulatory Grounding Baseline Evaluation",
        "ground_truth_dataset": GROUND_TRUTH_PATH,
        "total_test_queries": total_queries,
        "fraud_queries_evaluated": len(fraud_queries),
        "execution_duration_sec": round(duration, 3),
        "metrics": {
            "citation_precision": citation_precision,
            "citation_recall_top1": citation_recall,
            "citation_recall_top3": top3_recall,
            "hallucination_rate": hallucination_rate,
            "total_citations_emitted": total_citations_emitted,
            "valid_citations_count": valid_citations_count,
            "hallucinated_citations_count": hallucinated_citations_count,
        },
        "query_results": query_results,
    }
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"SEBI Grounding Evaluation Complete.")
    print(f"Citation Precision: {citation_precision}")
    print(f"Citation Recall (Top-1): {citation_recall}")
    print(f"Citation Recall (Top-3): {top3_recall}")
    print(f"Hallucination Rate: {hallucination_rate}")
    print(f"Saved results to {OUTPUT_PATH}")
    return summary


if __name__ == "__main__":
    asyncio.run(evaluate_sebi_grounding())
