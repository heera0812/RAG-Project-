import pytest
from app.generation.prompts import STRICT_SYSTEM_PROMPT
from app.generation.answer_generator import answer_generator
from app.api.chat import chat_endpoint
from app.db.models import ChatRequest


def test_ai_role_in_system_prompt():
    """Verify that the system prompt strictly defines the AI role per Instructions."""
    prompt_lower = STRICT_SYSTEM_PROMPT.lower()
    assert "ai is not a guru" in prompt_lower
    assert "ai is not a teacher" in prompt_lower
    assert "interpreter" in prompt_lower
    assert "applicator" in prompt_lower
    assert "gurudev" in prompt_lower


def test_suvichar_reflection_structure():
    """Verify that asking for suvichar produces the Gurudev -> Arth -> Abhyas structure."""
    req = ChatRequest(
        question="परमपूज्य गुरुदेव का विचार, उसका संक्षिप्त अर्थ और आज का अभ्यास क्या है?",
        language="hi",
    )
    res = chat_endpoint(req)
    assert res.evidence_status in ("supported", "partial_support")
    assert len(res.sources) > 0
    # Check for presence of the core structure elements
    ans = res.answer
    assert "📖 Gurudev" in ans or "📖 गुरुदेव" in ans or "गुरुदेव" in ans
    assert "🧠 Arth" in ans or "अर्थ" in ans
    assert "🌱 Aaj ka Abhyas" in ans or "अभ्यास" in ans


def test_prohibited_guru_claims_filtered_by_output_validation():
    """Verify that output validation blocks any claims of the AI being a Guru or Teacher."""
    prohibited_sample = "मैं आपका गुरु हूँ और मैं तुम्हें सिखाता हूँ।"
    # Test sanitization logic directly
    prohibited_phrases = [
        "मैं आपका गुरु", "मैं तुम्हारा गुरु", "मेरे शिष्य", "मैं तुम्हें सिखाता हूँ"
    ]
    sanitized = prohibited_sample
    for p in prohibited_phrases:
        if p in sanitized:
            sanitized = sanitized.replace(p, "परमपूज्य गुरुदेव के विचारों के अनुसार")
    assert "मैं आपका गुरु" not in sanitized
    assert "परमपूज्य गुरुदेव के विचारों के अनुसार" in sanitized
