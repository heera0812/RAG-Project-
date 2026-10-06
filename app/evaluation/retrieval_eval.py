import json
import time
from pathlib import Path
from typing import Dict, Any, List

from app.config import settings
from app.retrieval.hybrid_search import hybrid_search_engine


def run_retrieval_evaluation(
    dataset_path: str = "app/evaluation/golden_questions.json",
    use_hybrid: bool = True,
) -> Dict[str, Any]:
    """Run retrieval evaluation measuring Hit@1, Hit@3, Hit@5, MRR, and Abstention accuracy."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        questions: List[Dict[str, Any]] = json.load(f)

    total_questions = len(questions)
    answerable_count = 0
    unanswerable_count = 0

    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    reciprocal_ranks = []
    latencies = []

    correct_abstentions = 0
    false_positives = 0

    detailed_results = []

    for q in questions:
        qid = q["id"]
        query_text = q["question"]
        is_answerable = q["answerable"]
        expected_pages = set(q.get("expected_pages", []))

        t0 = time.perf_counter()
        results, confidence = hybrid_search_engine.search(
            query=query_text,
            top_k=5,
            use_hybrid=use_hybrid,
        )
        elapsed = time.perf_counter() - t0
        latencies.append(elapsed)

        retrieved_pages = []
        for r in results:
            p_start = r.metadata.get("page_start", 0)
            p_end = r.metadata.get("page_end", 0)
            retrieved_pages.append((p_start, p_end))

        if is_answerable:
            answerable_count += 1
            # Check if any retrieved chunk overlaps with expected pages
            found_rank = None
            for idx, (p_s, p_e) in enumerate(retrieved_pages, start=1):
                chunk_page_set = set(range(p_s, p_e + 1))
                if chunk_page_set & expected_pages:
                    found_rank = idx
                    break

            if found_rank == 1:
                hits_at_1 += 1
            if found_rank and found_rank <= 3:
                hits_at_3 += 1
            if found_rank and found_rank <= 5:
                hits_at_5 += 1

            if found_rank:
                reciprocal_ranks.append(1.0 / found_rank)
            else:
                reciprocal_ranks.append(0.0)

            detailed_results.append(
                {
                    "id": qid,
                    "question": query_text,
                    "answerable": True,
                    "found_rank": found_rank,
                    "confidence": confidence,
                    "latency_sec": round(elapsed, 4),
                }
            )
        else:
            unanswerable_count += 1
            # Unanswerable query is correct if confidence is insufficient_evidence
            if confidence == "insufficient_evidence" or len(results) == 0:
                correct_abstentions += 1
            else:
                false_positives += 1

            detailed_results.append(
                {
                    "id": qid,
                    "question": query_text,
                    "answerable": False,
                    "correctly_abstained": (confidence == "insufficient_evidence"),
                    "confidence": confidence,
                    "latency_sec": round(elapsed, 4),
                }
            )

    hit_1_rate = round(hits_at_1 / answerable_count, 4) if answerable_count else 0.0
    hit_3_rate = round(hits_at_3 / answerable_count, 4) if answerable_count else 0.0
    hit_5_rate = round(hits_at_5 / answerable_count, 4) if answerable_count else 0.0
    mrr = round(sum(reciprocal_ranks) / answerable_count, 4) if answerable_count else 0.0
    abstention_rate = (
        round(correct_abstentions / unanswerable_count, 4) if unanswerable_count else 1.0
    )
    avg_latency = round(sum(latencies) / total_questions, 4) if total_questions else 0.0

    summary = {
        "total_questions": total_questions,
        "answerable_questions": answerable_count,
        "unanswerable_questions": unanswerable_count,
        "hit_at_1": hit_1_rate,
        "hit_at_3": hit_3_rate,
        "hit_at_5": hit_5_rate,
        "mrr": mrr,
        "abstention_correctness": abstention_rate,
        "avg_latency_seconds": avg_latency,
        "detailed_results": detailed_results,
    }

    # Save results to evals
    out_dir = Path("app/evaluation")
    with open(out_dir / "retrieval_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


if __name__ == "__main__":
    report = run_retrieval_evaluation()
    print("=== RETRIEVAL EVALUATION REPORT ===")
    print(f"Total Questions: {report['total_questions']}")
    print(f"Hit@1: {report['hit_at_1'] * 100:.1f}%")
    print(f"Hit@3: {report['hit_at_3'] * 100:.1f}%")
    print(f"Hit@5: {report['hit_at_5'] * 100:.1f}%")
    print(f"MRR: {report['mrr']:.4f}")
    print(f"Abstention Correctness: {report['abstention_correctness'] * 100:.1f}%")
    print(f"Avg Latency: {report['avg_latency_seconds']:.4f}s")
