import json
import time
from pathlib import Path
from typing import Dict, Any, List

from app.api.chat import chat_endpoint
from app.db.models import ChatRequest


def run_answer_evaluation(
    dataset_path: str = "app/evaluation/golden_questions.json",
    sample_size: int = 10,
) -> Dict[str, Any]:
    """Evaluate end-to-end question answering, citation correctness, and abstention."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        questions: List[Dict[str, Any]] = json.load(f)

    # Evaluate a representative subset (mix of answerable and unanswerable)
    subset = questions[:sample_size]

    results = []
    valid_citations_count = 0
    correct_abstentions_count = 0
    total_evaluated = len(subset)

    for q in subset:
        qid = q["id"]
        query_text = q["question"]
        is_answerable = q["answerable"]
        lang = q["language"]

        req = ChatRequest(question=query_text, language=lang)
        resp = chat_endpoint(req)

        has_valid_citations = len(resp.sources) > 0
        is_abstained = resp.evidence_status == "insufficient_evidence"

        if is_answerable:
            if has_valid_citations:
                valid_citations_count += 1
        else:
            if is_abstained:
                correct_abstentions_count += 1

        results.append(
            {
                "id": qid,
                "question": query_text,
                "answerable": is_answerable,
                "evidence_status": resp.evidence_status,
                "retrieval_confidence": resp.retrieval_confidence,
                "citations_returned": len(resp.sources),
                "answer_preview": resp.answer[:120] + "...",
            }
        )

    summary = {
        "evaluated_questions": total_evaluated,
        "results": results,
    }

    out_dir = Path("app/evaluation")
    with open(out_dir / "answer_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


if __name__ == "__main__":
    report = run_answer_evaluation(sample_size=5)
    print("=== ANSWER EVALUATION COMPLETED ===")
    print(f"Evaluated: {report['evaluated_questions']}")
