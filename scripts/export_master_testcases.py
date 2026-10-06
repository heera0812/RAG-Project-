"""Script to parse Agent.md/master rule/Test case and export to app/evaluation/master_testcases.json."""
import json
import re
from pathlib import Path

def parse_and_export():
    source_path = Path("Agent.md/master rule/Test case")
    output_path = Path("app/evaluation/master_testcases.json")
    
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

        # Clean answer: strip leading * **उत्तर:** or * **उत्तर:**
        ans_clean = re.sub(r"^\*\s*\*\*उत्तर:\*\*\s*", "", ans_raw)
        
        # Remove markdown citation anchors like [1][2], [7][8] for pure concept matching
        ans_text_only = re.sub(r"\[\d+\]", "", ans_clean)

        # Extract bold concepts (filtering out the 'उत्तर:' label itself)
        bold_terms = [
            t.strip()
            for t in re.findall(r"\*\*([^\*]+)\*\*", ans_raw)
            if t.strip() and t.strip() != "उत्तर:"
        ]

        # Determine section
        section = section_map.get(q_num, "General")

        items.append({
            "id": f"Q{q_num:03d}",
            "q_num": q_num,
            "section": section,
            "question": q_raw,
            "expected_answer": ans_text_only.strip(),
            "expected_answer_raw": ans_raw,
            "bold_concepts": bold_terms,
            "language": "hi",
            "answerable": True
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"Successfully exported {len(items)} test cases to {output_path}")

if __name__ == "__main__":
    parse_and_export()
