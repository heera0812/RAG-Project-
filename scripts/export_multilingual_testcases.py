"""Parse and export Test Case Hinglish and Test Case ENGLISH into structured JSON datasets."""
import json
import re
from pathlib import Path


def parse_hinglish():
    source_path = Path("Agent.md/master rule/Test Case Hinglish")
    out_path = Path("app/evaluation/testcases_hinglish.json")

    with open(source_path, "r", encoding="utf-8") as f:
        text = f.read()

    lines = text.split("\n")
    section_map = {}
    curr_sec = "General"
    for line in lines:
        sec_m = re.match(r"### \*\*([^\*]+)\*\*", line)
        if sec_m:
            curr_sec = sec_m.group(1).replace("&amp;", "&").strip()
        q_m = re.match(r"\*\*Q(\d+):", line)
        if q_m:
            section_map[int(q_m.group(1))] = curr_sec

    pattern = r"\*\*Q(\d+):\s*(.*?)\*\*\s*\n+(.*?)(?=\n\*\*Q\d+:|\n### \*\*|\Z)"
    matches = list(re.finditer(pattern, text, re.DOTALL))

    items = []
    for m in matches:
        q_num = int(m.group(1))
        q_raw = m.group(2).strip()
        ans_raw = m.group(3).strip()

        # Clean answer: strip leading * **Ans:**
        ans_clean = re.sub(r"^\*\s*\*\*Ans:\*\*\s*", "", ans_raw)
        bold_terms = [
            t.strip()
            for t in re.findall(r"\*\*([^\*]+)\*\*", ans_raw)
            if t.strip() and t.strip() not in ("Ans:", "उत्तर:")
        ]

        items.append({
            "id": f"H_Q{q_num:03d}",
            "q_num": q_num,
            "section": section_map.get(q_num, "General"),
            "question": q_raw,
            "expected_answer": ans_clean.strip(),
            "expected_answer_raw": ans_raw,
            "bold_concepts": bold_terms,
            "language": "hinglish",
            "answerable": True,
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"Successfully exported {len(items)} Hinglish test cases to {out_path}")


def parse_english():
    source_path = Path("Agent.md/master rule/Test Case ENGLISH")
    out_path = Path("app/evaluation/testcases_english.json")

    with open(source_path, "r", encoding="utf-8") as f:
        text = f.read()

    lines = text.split("\n")
    section_map = {}
    curr_sec = "General"
    for line in lines:
        sec_m = re.match(r"### \*\*([^\*]+)\*\*", line)
        if sec_m:
            curr_sec = sec_m.group(1).replace("&amp;", "&").strip()
        q_m = re.match(r"#### \*\*Q(\d+)\\\.", line)
        if q_m:
            section_map[int(q_m.group(1))] = curr_sec

    pattern = r"#### \*\*Q(\d+)\\\.\s*(.*?)\*\*\s*\n+(.*?)(?=\n#### \*\*Q|\n### \*\*|\Z)"
    matches = list(re.finditer(pattern, text, re.DOTALL))

    items = []
    for m in matches:
        q_num = int(m.group(1))
        q_raw = m.group(2).strip()
        ans_raw = m.group(3).strip()

        # Clean answer: strip leading * **Answer:**
        ans_clean = re.sub(r"^\*\s*\*\*Answer:\*\*\s*", "", ans_raw)
        # Remove citation footnotes like [1][2]
        ans_text_only = re.sub(r"\[\d+\]", "", ans_clean)
        bold_terms = [
            t.strip()
            for t in re.findall(r"\*\*([^\*]+)\*\*", ans_raw)
            if t.strip() and t.strip() not in ("Answer:", "Ans:")
        ]

        items.append({
            "id": f"EN_Q{q_num:03d}",
            "q_num": q_num,
            "section": section_map.get(q_num, "General"),
            "question": q_raw,
            "expected_answer": ans_text_only.strip(),
            "expected_answer_raw": ans_raw,
            "bold_concepts": bold_terms,
            "language": "en",
            "answerable": True,
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"Successfully exported {len(items)} English test cases to {out_path}")


if __name__ == "__main__":
    parse_hinglish()
    parse_english()
