"""Interactive Terminal CLI for Shantikunj AI Knowledge Assistant.

Usage:
  1. Interactive mode:
     python -m app.cli

  2. Direct query mode:
     python -m app.cli "गायत्री को चारों वेदों की माता क्यों कहा जाता है?"
     python -m app.cli "What is the meaning of Gayatri mantra?" --lang en
"""

import sys
import argparse
from typing import Optional

# Ensure UTF-8 output in Windows terminal
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.api.chat import chat_endpoint
from app.db.models import ChatRequest
from app.ingestion.language import detect_language


def ask_question(question: str, language: Optional[str] = None):
    """Query the RAG system and display the answer with citations in the terminal."""
    q_clean = question.strip()
    if not q_clean:
        return

    lang = language or detect_language(q_clean)
    if lang not in ("hi", "en"):
        lang = "hi"

    is_suvichar = q_clean.lower() in ("suvichar", "aaj ka suvichar", "sandesh", "aaj ka sandesh", "thought of the day")
    query_to_send = (
        "परमपूज्य गुरुदेव का विचार, उसका संक्षिप्त अर्थ और दैनिक जीवन में आज का अभ्यास क्या है?"
        if is_suvichar else q_clean
    )

    print("\n" + "=" * 65)
    if is_suvichar:
        print("🌅 AAJ KA SUVICHAR & DAILY SADHANA")
    else:
        print(f"❓ QUESTION: {q_clean}")
    print(f"🌐 DETECTED LANGUAGE: {lang.upper()}")
    print("-" * 65)
    print("⏳ Searching literature and synthesizing verified answer...")

    req = ChatRequest(question=query_to_send, language=lang)
    response = chat_endpoint(req)

    print("\n" + "-" * 65)
    print(f"📊 EVIDENCE STATUS:     {response.evidence_status.upper()}")
    print(f"🎯 RETRIEVAL CONFIDENCE: {response.retrieval_confidence.upper()}")
    print("-" * 65)

    if not (response.answer.startswith("📜 ANSWER:") or response.answer.startswith("📜 उत्तर:")):
        print("\n📜 ANSWER:")
    else:
        print()
    print(response.answer)

    if response.sources:
        print("\n" + "-" * 65)
        print(f"📚 VERIFIED CITATIONS ({len(response.sources)} source chunks):")
        for idx, src in enumerate(response.sources, start=1):
            page_info = f"Page {src.page_start}" if src.page_start == src.page_end else f"Pages {src.page_start}-{src.page_end}"
            print(f"  [{idx}] Book: \"{src.book}\"")
            if src.chapter:
                print(f"      Chapter: {src.chapter}")
            print(f"      Location: {page_info} | Chunk ID: {src.chunk_id[:8]}...")
    elif response.evidence_status == "insufficient_evidence":
        print("\n" + "-" * 65)
        print("ℹ️  NOTE: The system abstained because no verified matching evidence")
        print("          was found in the currently indexed literature.")

    print("=" * 65 + "\n")


from app.retrieval.notebooklm_engine import notebooklm_engine


def interactive_loop(default_lang: Optional[str] = None):
    """Run an interactive conversation loop in the terminal."""
    nlm_auth = notebooklm_engine.is_authenticated()
    nlm_status = "🟢 Connected (Google Gemini Notebook)" if nlm_auth else "⚪ Ready (type 'login' or run 'python -m notebooklm login' to connect)"

    print("=" * 65)
    print("    🕊️  SHANTIKUNJ AI — INTERACTIVE TERMINAL ASSISTANT  🕊️")
    print("=" * 65)
    print("Role: Interpreter & Applicator of Gurudev's Thoughts (AI is NOT Guru)")
    print("Formula: Gurudev ka Sandesh → Samajhna → Jeevan me Lagu Karna")
    print(f"Gemini NotebookLM: {nlm_status}")
    print("-" * 65)
    print("Ask questions in Hindi, Hinglish, or English.")
    print("Tip: Type 'suvichar' or 'aaj ka sandesh' for daily reflection.")
    print("Type 'exit', 'quit', or 'q' to end the session.\n")

    while True:
        try:
            prompt = "Shantikunj AI > "
            user_input = input(prompt).strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("\nExiting Shantikunj AI session. Namaste! 🙏\n")
                break

            ask_question(user_input, default_lang)
        except (KeyboardInterrupt, EOFError):
            print("\n\nSession terminated. Namaste! 🙏\n")
            break
        except Exception as e:
            print(f"\n❌ Error processing query: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="Query the Shantikunj AI assistant from the terminal.")
    parser.add_argument("query", nargs="?", type=str, help="Question to ask (optional, starts interactive mode if omitted)")
    parser.add_argument("--lang", "-l", choices=["hi", "en"], default=None, help="Force language (hi or en)")

    args = parser.parse_args()

    if args.query:
        ask_question(args.query, args.lang)
    else:
        interactive_loop(args.lang)


if __name__ == "__main__":
    main()
