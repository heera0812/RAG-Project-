"""Parse Agent.md/master rule/difficult test case and export clean JSON benchmark dataset."""
import json
import re
from pathlib import Path


def parse_and_export_difficult_testcases():
    source_path = Path("Agent.md/master rule/difficult test case")
    out_path = Path("app/evaluation/difficult_testcases.json")

    with open(source_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Split into lines to associate each Q with its preceding Theme
    lines = text.split("\n")
    current_theme = "Advanced Metaphysics & Subtle Sound Science"
    
    # Blocks for each Q
    q_blocks = []
    current_block_lines = []
    current_q_num = None

    for line in lines:
        theme_m = re.match(r"^### \*\*([^\*]+)\*\*", line.strip())
        if theme_m:
            current_theme = theme_m.group(1).replace("&amp;", "&").strip()

        q_m = re.match(r"^#### \*\*Q(\d+)[\.\\]", line.strip())
        if q_m:
            if current_block_lines and current_q_num is not None:
                q_blocks.append((current_q_num, current_theme, "\n".join(current_block_lines)))
            current_q_num = int(q_m.group(1))
            current_block_lines = []
            continue

        if current_q_num is not None:
            current_block_lines.append(line)

    if current_block_lines and current_q_num is not None:
        q_blocks.append((current_q_num, current_theme, "\n".join(current_block_lines)))

    items = []
    for q_idx, (q_num, theme, block_text) in enumerate(q_blocks, start=1):
        # Extract Hindi
        hindi_m = re.search(r"\*\s*\*\*Hindi:\*\*\s*(.*?)\n\s*\*\s*\*\*उत्तर:\*\*\s*(.*?)(?=\n\s*\*|\Z)", block_text, re.DOTALL)
        # Extract English
        eng_m = re.search(r"\*\s*\*\*English:\*\*\s*(.*?)\n\s*\*\s*\*\*Answer:\*\*\s*(.*?)(?=\n\s*\*|\Z)", block_text, re.DOTALL)
        # Extract Hinglish
        hing_m = re.search(r"\*\s*\*\*Hinglish:\*\*\s*(.*?)\n\s*\*\s*\*\*Answer:\*\*\s*(.*?)(?=\n\s*\*|\Z)", block_text, re.DOTALL)

        if hindi_m:
            items.append({
                "id": f"DIFF_HI_{q_idx:03d}",
                "q_num": q_num,
                "q_global_index": q_idx,
                "theme": theme,
                "language": "hi",
                "question": hindi_m.group(1).strip(),
                "expected_answer": hindi_m.group(2).strip(),
                "answerable": True,
            })

        if eng_m:
            items.append({
                "id": f"DIFF_EN_{q_idx:03d}",
                "q_num": q_num,
                "q_global_index": q_idx,
                "theme": theme,
                "language": "en",
                "question": eng_m.group(1).strip(),
                "expected_answer": eng_m.group(2).strip(),
                "answerable": True,
            })

        if hing_m:
            items.append({
                "id": f"DIFF_HING_{q_idx:03d}",
                "q_num": q_num,
                "q_global_index": q_idx,
                "theme": theme,
                "language": "hinglish",
                "question": hing_m.group(1).strip(),
                "expected_answer": hing_m.group(2).strip(),
                "answerable": True,
            })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"Successfully exported {len(items)} clean difficult test cases across {len(q_blocks)} questions to {out_path}")
    return items


if __name__ == "__main__":
    parse_and_export_difficult_testcases()
