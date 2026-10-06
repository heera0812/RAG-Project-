"""Evaluation harness for the 105 Master Test Cases from Shantikunj Gayatri Mahavigyan literature.

Evaluates:
1. Normalization & Query Processing
2. Hybrid Retrieval Performance & Confidence
3. Safe Abstention vs Grounded Generation
4. Citation Integrity (0% hallucinated citations)
5. Section-wise evaluation across all 10 literature domains
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.config import settings
from app.retrieval.hybrid_search import hybrid_search_engine
from app.retrieval.query_normalizer import query_normalizer
from app.generation.citation_validator import citation_validator
from app.generation.abstention import get_abstention_text
from app.api.chat import chat_endpoint
from app.db.models import ChatRequest


def run_master_testcase_evaluation(
    dataset_path: str = "app/evaluation/master_testcases.json",
    sample_chat_size: int = 15,
) -> Dict[str, Any]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases: List[Dict[str, Any]] = json.load(f)

    total_cases = len(test_cases)
    section_stats = defaultdict(lambda: {"total": 0, "high_conf": 0, "med_conf": 0, "low_conf": 0, "latencies": []})

    confidence_counts = {"high": 0, "medium": 0, "insufficient_evidence": 0}
    retrieval_latencies = []

    print(f"\n=======================================================")
    print(f"   SHANTIKUNJ AI — 105 MASTER TEST CASES EVALUATION    ")
    print(f"=======================================================\n")
    print(f"Evaluating {total_cases} test cases across 10 literature sections...\n")

    # 1. Retrieval & Confidence across all 105 test cases
    for tc in test_cases:
        qid = tc["id"]
        q_text = tc["question"]
        sec = tc["section"]

        norm_query = query_normalizer.normalize(q_text)

        t0 = time.perf_counter()
        results, confidence = hybrid_search_engine.search(
            query=norm_query,
            top_k=5,
            use_hybrid=True,
        )
        elapsed = time.perf_counter() - t0
        retrieval_latencies.append(elapsed)

        section_stats[sec]["total"] += 1
        section_stats[sec]["latencies"].append(elapsed)

        if confidence == "high":
            confidence_counts["high"] += 1
            section_stats[sec]["high_conf"] += 1
        elif confidence == "medium":
            confidence_counts["medium"] += 1
            section_stats[sec]["med_conf"] += 1
        else:
            confidence_counts["insufficient_evidence"] += 1
            section_stats[sec]["low_conf"] += 1

    # 2. End-to-end Chat and Citation Verification on Representative Sample
    # Sample from different sections to verify grounding & abstention integrity
    step = max(1, total_cases // sample_chat_size)
    chat_sample = [test_cases[i] for i in range(0, total_cases, step)][:sample_chat_size]

    chat_results = []
    hallucinated_citations_count = 0
    valid_citations_count = 0
    safe_abstentions_count = 0

    print(f"Running end-to-end Chat & Citation validation on {len(chat_sample)} representative test cases...")

    for tc in chat_sample:
        qid = tc["id"]
        q_text = tc["question"]

        req = ChatRequest(question=q_text, language="hi")
        resp = chat_endpoint(req)

        # Citation validation check: verify all returned citations are valid
        if resp.sources:
            for s in resp.sources:
                if not s.chunk_id or not s.book:
                    hallucinated_citations_count += 1
                else:
                    valid_citations_count += 1

        # Abstention check: if insufficient evidence, verify canonical response matches
        if resp.evidence_status == "insufficient_evidence":
            if resp.answer.strip() == get_abstention_text("hi").strip():
                safe_abstentions_count += 1

        chat_results.append({
            "id": qid,
            "question": q_text[:60] + "...",
            "section": tc["section"][:40] + "...",
            "evidence_status": resp.evidence_status,
            "confidence": resp.retrieval_confidence,
            "citations_count": len(resp.sources),
            "answer_preview": resp.answer[:90].replace("\n", " ") + "..."
        })

    avg_latency = sum(retrieval_latencies) / len(retrieval_latencies) if retrieval_latencies else 0.0

    summary = {
        "total_test_cases": total_cases,
        "average_retrieval_latency": round(avg_latency, 4),
        "confidence_distribution": confidence_counts,
        "section_breakdown": {k: {
            "total": v["total"],
            "high": v["high_conf"],
            "medium": v["med_conf"],
            "insufficient": v["low_conf"]
        } for k, v in section_stats.items()},
        "chat_evaluation": {
            "evaluated_count": len(chat_sample),
            "safe_abstentions": safe_abstentions_count,
            "valid_citations": valid_citations_count,
            "hallucinated_citations": hallucinated_citations_count,
            "sample_details": chat_results
        }
    }

    report_path = Path(__file__).resolve().parent / "master_testcase_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    try:
        print("\n--- SECTION-WISE RETRIEVAL BREAKDOWN ---")
        for idx, (sec_name, stats) in enumerate(section_stats.items(), start=1):
            sec_avg_lat = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0.0
            print(f"[{idx:02d}] Section: {sec_name[:40]} | Total: {stats['total']} | High: {stats['high_conf']} | Med: {stats['med_conf']} | Insuff: {stats['low_conf']} | Lat: {sec_avg_lat:.3f}s")

        print("\n--- END-TO-END CHAT & GROUNDING INTEGRITY ---")
        print(f"Evaluated Questions: {len(chat_sample)}")
        print(f"Safe Canonical Abstentions: {safe_abstentions_count}")
        print(f"Valid Citations: {valid_citations_count}")
        print(f"Hallucinated Citations: {hallucinated_citations_count} (0.00% target)")
        print(f"\nSaved evaluation summary report to {report_path}\n")
    except Exception as e:
        print(f"Report saved to {report_path}")
    return summary


if __name__ == "__main__":
    run_master_testcase_evaluation()
