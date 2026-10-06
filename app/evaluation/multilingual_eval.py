import json
import time
from pathlib import Path
from typing import Dict, Any, List

from app.retrieval.hybrid_search import hybrid_search_engine
from app.retrieval.query_normalizer import query_normalizer


def evaluate_dataset(
    dataset_path: str,
    lang_name: str,
    top_k: int = 5,
    use_hybrid: bool = True,
) -> Dict[str, Any]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        items: List[Dict[str, Any]] = json.load(f)

    total = len(items)
    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    reciprocal_ranks = []
    latencies = []
    abstained_count = 0
    answered_count = 0

    results_detail = []

    for item in items:
        qid = item["id"]
        q_text = item["question"]
        is_answerable = item.get("answerable", True)

        t0 = time.perf_counter()
        results, confidence = hybrid_search_engine.search(
            query=q_text,
            top_k=top_k,
            use_hybrid=use_hybrid,
        )
        elapsed = time.perf_counter() - t0
        latencies.append(elapsed)

        if not is_answerable:
            if confidence == "insufficient_evidence" or len(results) == 0:
                abstained_count += 1
            results_detail.append({
                "id": qid,
                "question": q_text,
                "answerable": False,
                "confidence": confidence,
                "status": "correctly_abstained" if confidence == "insufficient_evidence" else "false_positive",
            })
            continue

        answered_count += 1
        expected_q = item["question"].strip().lower()
        expected_page = item.get("q_num") if lang_name == "Hinglish" else (100 + item.get("q_num", 0))

        found_rank = None
        for rank, res in enumerate(results, start=1):
            chunk_content = res.content.lower()
            p_start = res.metadata.get("page_start")
            
            # Match via page number, exact question inside chunk, or key concepts
            if (
                p_start == expected_page
                or expected_q in chunk_content
                or (item.get("bold_concepts") and any(c.lower() in chunk_content for c in item["bold_concepts"] if len(c) > 3))
            ):
                found_rank = rank
                break

        if found_rank == 1:
            hits_at_1 += 1
        if found_rank and found_rank <= 3:
            hits_at_3 += 1
        if found_rank and found_rank <= 5:
            hits_at_5 += 1

        reciprocal_ranks.append(1.0 / found_rank if found_rank else 0.0)

        results_detail.append({
            "id": qid,
            "question": q_text,
            "answerable": True,
            "found_rank": found_rank,
            "confidence": confidence,
            "top_chunk_id": results[0].chunk_id if results else None,
            "top_score": results[0].score if results else 0.0,
            "latency_sec": round(elapsed, 4),
        })

    mrr = sum(reciprocal_ranks) / max(1, len(reciprocal_ranks))
    avg_latency = sum(latencies) / max(1, len(latencies))

    return {
        "language": lang_name,
        "total_queries": total,
        "answerable_queries": answered_count,
        "hit_at_1": hits_at_1,
        "hit_at_1_rate": round(hits_at_1 / max(1, answered_count), 4),
        "hit_at_3": hits_at_3,
        "hit_at_3_rate": round(hits_at_3 / max(1, answered_count), 4),
        "hit_at_5": hits_at_5,
        "hit_at_5_rate": round(hits_at_5 / max(1, answered_count), 4),
        "mrr": round(mrr, 4),
        "avg_latency_sec": round(avg_latency, 4),
        "correct_abstentions": abstained_count,
        "details": results_detail,
    }


def run_full_multilingual_evaluation() -> Dict[str, Any]:
    print("Running Full Multilingual Evaluation...")
    summary = {}

    hinglish_res = evaluate_dataset("app/evaluation/testcases_hinglish.json", "Hinglish")
    english_res = evaluate_dataset("app/evaluation/testcases_english.json", "English")

    summary["hinglish"] = hinglish_res
    summary["english"] = english_res

    # Output report
    report_file = Path("app/evaluation/multilingual_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n================ Multilingual Evaluation Report ================")
    print(f"Hinglish (60 Queries): Hit@1={hinglish_res['hit_at_1_rate']:.1%}, Hit@3={hinglish_res['hit_at_3_rate']:.1%}, Hit@5={hinglish_res['hit_at_5_rate']:.1%}, MRR={hinglish_res['mrr']}")
    print(f"English  (70 Queries): Hit@1={english_res['hit_at_1_rate']:.1%}, Hit@3={english_res['hit_at_3_rate']:.1%}, Hit@5={english_res['hit_at_5_rate']:.1%}, MRR={english_res['mrr']}")
    print(f"================================================================\n")
    print(f"Report saved to: {report_file}")
    return summary


if __name__ == "__main__":
    run_full_multilingual_evaluation()
