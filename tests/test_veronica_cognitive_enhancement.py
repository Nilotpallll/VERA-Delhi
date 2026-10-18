"""Verification suite for Veronica's enhanced cognitive capabilities,
entity extraction, emerging fraud typologies, and dynamic action generation.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.src.main import app
from apps.api.src.veronica.service import (
    extract_forensic_entities,
    generate_dynamic_actions,
    build_forensic_context,
)


def test_forensic_entity_extractor():
    # Test 1: UPI and APK extraction
    text1 = "Admin told me to send 5000 to trader99@okhdfcbank and download elite_trade.apk"
    entities1 = extract_forensic_entities(text1)
    assert any("trader99@okhdfcbank" in vpa for vpa in entities1["upi_vpas"])
    assert any("elite_trade.apk" in apk for apk in entities1["apks"])
    assert "Malicious Sideloaded APK (OTP Interception)" in entities1["typologies"]

    # Test 2: SEBI Registration and URL
    text2 = "Verify registration INH000012345 on https://sebi-verification.fake.com"
    entities2 = extract_forensic_entities(text2)
    assert "INH000012345" in entities2["sebi_ids"]
    assert any("https://sebi-verification.fake.com" in u for u in entities2["urls"])

    # Test 3: Digital Arrest Modus Operandi
    text3 = "Someone called on Skype video call claiming police digital arrest"
    entities3 = extract_forensic_entities(text3)
    assert "Digital Arrest & Impersonation Extortion" in entities3["typologies"]

    # Test 4: Task Scam Modus Operandi
    text4 = "They gave me 150 rs for youtube like task then asked for prepaid task"
    entities4 = extract_forensic_entities(text4)
    assert "Task / Rating / Prepaid Investment Trap" in entities4["typologies"]


def test_build_forensic_context():
    text = "Paying to quickprofit@ybl for pre-ipo fii quota allocation"
    entities = extract_forensic_entities(text)
    context = build_forensic_context(text, entities)
    assert "[VERA FORENSIC COGNITIVE ENGINE TELEMETRY]" in context
    assert "Pre-IPO" in context or "fii quota" in context.lower()
    assert "Cognitive Directives:" in context


def test_dynamic_action_generation():
    # UPI query should yield Scan UPI action
    text_upi = "Checking account fastprofit@paytm"
    entities_upi = extract_forensic_entities(text_upi)
    actions, chips = generate_dynamic_actions(text_upi, entities_upi, lang="en")
    assert any("UPI" in a.label for a in actions)

    # APK query should yield Scan APK action
    text_apk = "They sent me pro_trader.apk"
    entities_apk = extract_forensic_entities(text_apk)
    actions_apk, chips_apk = generate_dynamic_actions(text_apk, entities_apk, lang="en")
    assert any("APK" in a.label for a in actions_apk)

    # Emergency query should yield 1930 Call action
    text_emerg = "I sent money to scammer"
    entities_emerg = extract_forensic_entities(text_emerg)
    actions_emerg, chips_emerg = generate_dynamic_actions(text_emerg, entities_emerg, lang="en")
    assert any("1930" in a.label for a in actions_emerg)


@pytest.mark.asyncio
async def test_digital_arrest_canned_intent_en():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "messages": [{"role": "user", "content": "I got a police video call saying digital arrest"}],
            "language": "en",
            "session_id": "test_cognitive_da_en"
        }
        resp = await client.post("/api/veronica/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "canned"
        reply = data["reply"].lower()
        assert "digital arrest" in reply
        assert "1930" in reply
        assert "never conducts arrests" in reply or "zero legal validity" in reply


@pytest.mark.asyncio
async def test_digital_arrest_canned_intent_hi():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "messages": [{"role": "user", "content": "डिजिटल अरेस्ट क्या है? क्या पुलिस वीडियो कॉल करती है?"}],
            "language": "hi",
            "session_id": "test_cognitive_da_hi"
        }
        resp = await client.post("/api/veronica/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "canned"
        reply = data["reply"]
        assert "डिजिटल अरेस्ट" in reply
        assert "1930" in reply


@pytest.mark.asyncio
async def test_apk_scam_canned_intent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "messages": [{"role": "user", "content": "They sent me an apk to install for trading"}],
            "language": "en",
            "session_id": "test_cognitive_apk"
        }
        resp = await client.post("/api/veronica/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "canned"
        reply = data["reply"].lower()
        assert "apk" in reply
        assert "otp" in reply or "sms" in reply
        assert "google play" in reply or "app store" in reply


@pytest.mark.asyncio
async def test_task_scam_canned_intent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "messages": [{"role": "user", "content": "Is this telegram task scam legit where they pay for youtube like task?"}],
            "language": "en",
            "session_id": "test_cognitive_task"
        }
        resp = await client.post("/api/veronica/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "canned"
        reply = data["reply"].lower()
        assert "task" in reply
        assert "prepaid" in reply or "vip" in reply


@pytest.mark.asyncio
async def test_fake_ipo_allocation_canned_intent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "messages": [{"role": "user", "content": "Adviser is promising 100% ipo allotment scam via fii quota"}],
            "language": "en",
            "session_id": "test_cognitive_ipo"
        }
        resp = await client.post("/api/veronica/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "canned"
        reply = data["reply"].lower()
        assert "sebi" in reply
        assert "asba" in reply or "pooling" in reply or "allotment" in reply


@pytest.mark.asyncio
async def test_sebi_circular_canned_intent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "messages": [{"role": "user", "content": "What does SEBI circular CIR/2023/123 prohibit?"}],
            "language": "en",
            "session_id": "test_cognitive_circular"
        }
        resp = await client.post("/api/veronica/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "canned"
        reply = data["reply"]
        assert "CIR/2023/123" in reply
        assert "Pooling" in reply or "pooling" in reply
