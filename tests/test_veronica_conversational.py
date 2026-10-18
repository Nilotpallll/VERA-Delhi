"""Conversational turn compliance tests for Veronica.

Validates that Veronica naturally handles generic conversational dialogue:
- Greetings ("hi", "hello", "hey", "namaste") -> "how can I help you"
- Acknowledgments ("okay", "ok", "k", "got it", "thik hai") -> "thank you"
- Gratitude ("thank you", "thanks", "dhanyawad") -> "you're welcome"
- Bot Identity & Nature ("who are you", "are you human", "are you a bot")
- Well-being ("how are you")
- Capabilities ("what can you do", "help")
- Guidance ("what should I do", "now what")
- Reassurance & Small Talk ("sorry", "is this free", "are you there", "where is the scanner")
- Affirmations & Negations ("yes", "no")
- Farewells ("bye", "goodbye")
- Bilingual parity across English and Hindi
"""

import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.src.main import app

GENERIC_TURNS_EN = [
    ("hi", ["how can i help you", "veronica", "safety assistant"]),
    ("hello", ["how can i help you", "veronica"]),
    ("hey", ["how can i help you", "veronica"]),
    ("okay", ["thank you", "let me know if you need anything else"]),
    ("ok", ["thank you", "let me know if you need anything else"]),
    ("k", ["thank you", "let me know if you need anything else"]),
    ("got it", ["thank you", "let me know if you need anything else"]),
    ("understood", ["thank you", "let me know if you need anything else"]),
    ("thank you", ["welcome", "glad i could help"]),
    ("thanks", ["welcome", "glad i could help"]),
    ("how are you", ["doing great", "how can i assist you"]),
    ("who are you", ["veronica", "ai forensic guide"]),
    ("what is your name", ["veronica"]),
    ("what can you do", ["check messages", "verify sebi", "detect deepfakes"]),
    ("what should i do", ["screen suspicious content", "verify credentials", "1930"]),
    ("now what", ["screen suspicious content", "verify credentials", "1930"]),
    ("are you human", ["veronica", "ai assistant", "vera"]),
    ("are you a bot", ["veronica", "ai assistant", "vera"]),
    ("is this free", ["free", "zero cost"]),
    ("where is the scanner", ["scanner", "right on this page"]),
    ("are you there", ["i'm here", "ready to help"]),
    ("sorry", ["no need to apologize", "how can i help"]),
    ("yes", ["great", "how can i assist you"]),
    ("no", ["no problem", "safe day"]),
    ("bye", ["goodbye", "stay vigilant"]),
    ("cool", ["thank you", "assistance"]),
    ("great", ["thank you", "assistance"]),
    ("what's up", ["monitoring", "investments", "going"]),
    ("can we chat", ["chat", "glad to chat", "happy to chat"]),
    ("i am scared", ["deep breath", "not alone", "calmly"]),
    ("you are smart", ["thank you", "sharp", "forensics"]),
    ("why veronica", ["veronica", "veritas", "truth"]),
]

GENERIC_TURNS_HI = [
    ("नमस्ते", ["सहायता", "वेरोनिका"]),
    ("हेलो", ["सहायता", "वेरोनिका"]),
    ("ठीक है", ["धन्यवाद", "सहायता"]),
    ("ओके", ["धन्यवाद", "सहायता"]),
    ("धन्यवाद", ["स्वागत", "सुरक्षित"]),
    ("आप कैसी हैं", ["बिल्कुल ठीक", "सहायता"]),
    ("आप कौन हैं", ["वेरोनिका", "सुरक्षा सहायक"]),
    ("क्या आप इंसान हैं", ["वेरोनिका", "एआई सुरक्षा सहायक"]),
    ("क्या यह फ्री है", ["मुफ़्त", "निःशुल्क", "free"]),
    ("स्कैनर कहाँ है", ["स्कैनर", "पेज"]),
    ("हाँ", ["सहायता", "साझा"]),
    ("नहीं", ["कोई बात नहीं", "सुरक्षित"]),
    ("माफ करें", ["माफ़ी की कोई बात नहीं", "सहायता"]),
    ("अलविदा", ["अलविदा", "सतर्क"]),
    ("क्या चल रहा है", ["ठीक", "पैटर्न", "नज़र"]),
    ("बात कर सकती हो", ["बातचीत", "तैयार"]),
    ("डर लग रहा है", ["घबराएं नहीं", "शांत"]),
    ("तुम बहुत समझदार हो", ["धन्यवाद", "मार्गदर्शन"]),
    ("तुम्हारा नाम वेरोनिका क्यों है", ["वेरोनिका", "veritas", "सत्य"]),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_terms", GENERIC_TURNS_EN)
async def test_veronica_conversational_turns_en(query: str, expected_terms: list[str]):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "messages": [{"role": "user", "content": query}],
            "language": "en",
            "session_id": "test_conv_en"
        }
        resp = await client.post("/api/veronica/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] in ("canned", "gemini", "fallback")
        reply_lower = data["reply"].lower()
        # Verify at least one of the expected terms is present
        assert any(term in reply_lower for term in expected_terms), f"Query '{query}' reply did not contain any of {expected_terms}. Reply: {data['reply']}"
        # Verify actions and chips are returned for conversational continuity
        assert "suggested_chips" in data
        assert len(data["suggested_chips"]) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_terms", GENERIC_TURNS_HI)
async def test_veronica_conversational_turns_hi(query: str, expected_terms: list[str]):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "messages": [{"role": "user", "content": query}],
            "language": "hi",
            "session_id": "test_conv_hi"
        }
        resp = await client.post("/api/veronica/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "hi"
        reply = data["reply"]
        assert any(term.lower() in reply.lower() for term in expected_terms), f"Hindi Query '{query}' reply did not contain any of {expected_terms}. Reply: {reply}"
        assert "suggested_chips" in data
        assert len(data["suggested_chips"]) > 0
