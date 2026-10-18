"""Orchestration service for Veronica Chatbot.

Flow:
1. Sanitize & Mask PII
2. Prompt Injection Guard
3. Canned Intent Matcher (0 tokens)
4. Query Cache Hit (0 tokens)
5. Free-Tier Rate & Budget Enforcement (max 4 RPM)
6. Gemini / Provider Call
7. Output Safety Filter
8. Graceful Fallback if offline / quota reached
"""


import re
from typing import Any

from ..ai.factory import get_llm_provider
from ..core.observability import logger
from .budget import veronica_budget
from .canned import find_canned_response
from .guards import (
    check_prompt_injection,
    filter_generated_output,
    mask_pii,
    sanitize_input,
)
from .policy import (
    REFUSAL_INVESTMENT_ADVICE_EN,
    REFUSAL_INVESTMENT_ADVICE_HI,
    SYSTEM_PROMPT_EN,
    SYSTEM_PROMPT_HI,
)
from .schemas import (
    VeronicaAction,
    VeronicaChatRequest,
    VeronicaChatResponse,
)


def extract_forensic_entities(text: str) -> dict[str, Any]:
    """Extracts suspected forensic entities and flags scam typologies from input text."""
    lowered = text.lower()

    # 1. UPI VPAs: e.g. trader99@okhdfcbank, wealth.advisor@ybl, 9876543210@paytm
    upi_vpas = re.findall(r'\b[a-zA-Z0-9.\-_]{2,64}@[a-zA-Z0-9.\-_]{2,32}\b', text)
    upi_candidates = [
        vpa for vpa in upi_vpas
        if not vpa.lower().endswith(('.com', '.org', '.net', '.edu', '.gov', '.io'))
        or any(h in vpa.lower() for h in ['@upi', '@okhdfcbank', '@oksbi', '@okaxis', '@okicici', '@paytm', '@ybl', '@axl', '@ibl'])
    ]

    # 2. SEBI Registration IDs: INA/INH/INZ/INM followed by digits/letters
    sebi_ids = re.findall(r'\bIN[A-Z0-9]{8,12}\b', text.upper())

    # 3. URLs and Domains
    urls = re.findall(r'https?://[^\s]+|t\.me/[^\s]+|wa\.me/[^\s]+', text)

    # 4. APK references
    apk_matches = re.findall(r'\b[\w\-]+\.apk\b|\bapk\b|\bsideload\b', lowered)

    # 5. Detected Modus Operandi Typologies
    detected_typologies = []
    if any(k in lowered for k in ["digital arrest", "police video call", "cbi video", "ed video", "skype arrest", "कॉल पुलिस", "डिजिटल अरेस्ट"]):
        detected_typologies.append("Digital Arrest & Impersonation Extortion")
    if any(k in lowered for k in ["youtube like", "hotel rating", "task scam", "prepaid task", "टास्क स्कैम", "लाइक टास्क"]):
        detected_typologies.append("Task / Rating / Prepaid Investment Trap")
    if any(k in lowered for k in ["pre-ipo", "pre ipo", "fii quota", "institutional quota", "संस्थागत कोटा"]):
        detected_typologies.append("Pre-IPO / FII Quota Allocation Bluff")
    if apk_matches:
        detected_typologies.append("Malicious Sideloaded APK (OTP Interception)")
    if any(k in lowered for k in ["guaranteed return", "100% profit", "double money", "पक्का मुनाफा", "निश्चित रिटर्न"]):
        detected_typologies.append("Unrealistic Guaranteed Return Trap (SEBI Violation)")
    if any(k in lowered for k in ["sent money", "transferred", "lost money", "already paid", "पैसे कट गए", "पैसे भेज दिए"]):
        detected_typologies.append("Financial Loss Incident (Golden Hour Priority)")

    return {
        "upi_vpas": upi_candidates,
        "sebi_ids": sebi_ids,
        "urls": urls,
        "apks": apk_matches,
        "typologies": detected_typologies,
    }


def build_forensic_context(query: str, entities: dict[str, Any]) -> str:
    """Formats forensic entities into an internal cognitive reasoning scratchpad for Veronica."""
    lines = ["[VERA FORENSIC COGNITIVE ENGINE TELEMETRY]"]
    if entities["typologies"]:
        lines.append(f"- Detected Modus Operandi: {', '.join(entities['typologies'])}")
    if entities["upi_vpas"]:
        lines.append(f"- Suspect UPI VPAs: {', '.join(entities['upi_vpas'])}")
    if entities["sebi_ids"]:
        lines.append(f"- Suspect SEBI Registration Codes: {', '.join(entities['sebi_ids'])}")
    if entities["urls"]:
        lines.append(f"- Extracted Links/Domains: {', '.join(entities['urls'])}")
    if entities["apks"]:
        lines.append("- Detected Sideloaded/APK references: Extreme risk of SMS/Accessibility OTP interception.")

    lines.append("- Cognitive Directives:")
    lines.append("  1. Threat Identification: Clearly label the fraud mechanism.")
    lines.append("  2. Forensic Red Flags: Cite specific indicators (e.g. fund pooling, personal UPI, fake seals, OTP theft).")
    lines.append("  3. Immediate Actionable Defense: Tell the user exactly what to do (disconnect, freeze card, dial 1930 if money was sent).")
    lines.append("  4. Regulatory Standard: Remind that SEBI rules prohibit guaranteed returns, fund pooling (CIR/2023/123), and out-of-store broker APKs.")
    return "\n".join(lines)


def generate_dynamic_actions(query: str, entities: dict[str, Any], lang: str = "en") -> tuple[list[VeronicaAction], list[str]]:
    """Builds context-aware action chips and suggested next prompts."""
    is_hi = lang == "hi"
    actions: list[VeronicaAction] = []
    chips: list[str] = []

    # Priority 1: Emergency or money lost
    if "Financial Loss Incident (Golden Hour Priority)" in entities["typologies"] or any(k in query.lower() for k in ["sent money", "lost", "paid", "पैसे"]):
        actions.append(VeronicaAction(
            type="open_helpline",
            label="📞 1930 पर कॉल करें" if is_hi else "📞 Call 1930 Helpline",
            payload="tel:1930"
        ))
        actions.append(VeronicaAction(
            type="external_link",
            label="🌐 साइबरक्राइम पोर्टल" if is_hi else "🌐 Cybercrime Portal",
            payload="https://cybercrime.gov.in"
        ))
        actions.append(VeronicaAction(
            type="navigate",
            label="📋 VERA में सबूत जांचें" if is_hi else "📋 File Evidence in VERA",
            payload="#scanner-section"
        ))
        chips = (
            ["सबूत कैसे सुरक्षित रखें?", "बैंक खाता फ्रीज कैसे कराएं?", "VERA स्कैनर का उपयोग कैसे करें?"]
            if is_hi else
            ["How do I preserve evidence?", "How to freeze bank accounts?", "How to use VERA scanner?"]
        )
        return actions, chips

    # Priority 2: Digital Arrest / Extortion
    if "Digital Arrest & Impersonation Extortion" in entities["typologies"]:
        actions.append(VeronicaAction(
            type="open_helpline",
            label="📞 1930 हेल्पलाइन पर कॉल करें" if is_hi else "📞 Call 1930 Helpline",
            payload="tel:1930"
        ))
        actions.append(VeronicaAction(
            type="external_link",
            label="🌐 साइबरक्राइम पोर्टल" if is_hi else "🌐 Cybercrime Portal",
            payload="https://cybercrime.gov.in"
        ))
        actions.append(VeronicaAction(
            type="navigate",
            label="🔍 VERA में कॉलर नंबर जांचें" if is_hi else "🔍 Scan Caller Number in VERA",
            payload="#scanner-section"
        ))
        chips = (
            ["क्या पुलिस वीडियो कॉल पर अरेस्ट कर सकती है?", "अगर पैसे भेज दिए तो क्या करें? 🚨", "फर्जी वारंट की पहचान कैसे करें?"]
            if is_hi else
            ["Can police arrest via video call?", "What if I already sent money? 🚨", "How do scammers fake arrest warrants?"]
        )
        return actions, chips

    # Priority 3: Sideloaded APK detected
    if entities["apks"] or "Malicious Sideloaded APK (OTP Interception)" in entities["typologies"]:
        actions.append(VeronicaAction(
            type="navigate",
            label="🛡️ VERA में APK जांचें" if is_hi else "🛡️ Scan APK in VERA",
            payload="#scanner-section"
        ))
        actions.append(VeronicaAction(
            type="open_helpline",
            label="📞 1930 हेल्पलाइन पर कॉल करें" if is_hi else "📞 Call 1930 Helpline",
            payload="tel:1930"
        ))
        chips = (
            ["फर्जी ऐप्स ओटीपी कैसे चुराते हैं?", "वैध ट्रेडिंग ऐप की पहचान कैसे करें?", "फोन से मैलवेयर कैसे हटाएं?"]
            if is_hi else
            ["How do malicious APKs steal OTPs?", "How to verify broker app on Google Play?", "How to clean infected phone?"]
        )
        return actions, chips

    # Priority 4: UPI VPA detected
    if entities["upi_vpas"]:
        actions.append(VeronicaAction(
            type="navigate",
            label="🔍 VERA में UPI जांचें" if is_hi else "🔍 Scan UPI in VERA",
            payload="#scanner-section"
        ))
        actions.append(VeronicaAction(
            type="open_helpline",
            label="📞 1930 हेल्पलाइन पर कॉल करें" if is_hi else "📞 Call 1930 Helpline",
            payload="tel:1930"
        ))
        chips = (
            ["व्यक्तिगत UPI पर पैसे मांगना गैर-कानूनी क्यों है?", "म्यूल बैंक अकाउंट क्या होता है?", "SEBI फंड पूलिंग नियम"]
            if is_hi else
            ["Why is routing money to personal UPI prohibited?", "What is a mule account?", "SEBI fund pooling rules"]
        )
        return actions, chips

    # Priority 5: SEBI ID detected
    if entities["sebi_ids"]:
        actions.append(VeronicaAction(
            type="external_link",
            label="🏛️ SEBI आधिकारिक पोर्टल" if is_hi else "🏛️ Official SEBI Registry",
            payload="https://www.sebi.gov.in"
        ))
        actions.append(VeronicaAction(
            type="navigate",
            label="🔍 VERA में लाइसेंस जांचें" if is_hi else "🔍 Verify License in VERA",
            payload="#scanner-section"
        ))
        chips = (
            ["RIA और RA में क्या अंतर है?", "फर्जी SEBI सर्टिफिकेट कैसे पहचानें?", "क्या सेबी कभी गारंटीड रिटर्न देता है?"]
            if is_hi else
            ["What is the difference between RIA and RA?", "How do scammers fake SEBI certificates?", "Does SEBI ever promise returns?"]
        )
        return actions, chips

    # Default versatile actions
    actions.append(VeronicaAction(
        type="navigate",
        label="🔍 स्कैनर खोलें" if is_hi else "🔍 Open Scanner",
        payload="#scanner-section"
    ))
    actions.append(VeronicaAction(
        type="open_helpline",
        label="📞 1930 हेल्पलाइन पर कॉल करें" if is_hi else "📞 Cyber Helpline 1930",
        payload="tel:1930"
    ))
    chips = (
        ["व्हाट्सएप ग्रुप की जांच", "SEBI रजिस्ट्रेशन चेक", "1930 हेल्पलाइन"]
        if is_hi else
        ["Check WhatsApp group", "SEBI registration check", "1930 Helpline"]
    )
    return actions, chips


def generate_conversational_fallback(query: str, lang: str = "en") -> str:
    """Provides short, poised, and professional conversational replies for normal interactions."""
    q = query.lower()
    is_hi = lang == "hi"

    # 1. Worries / Anxiety
    if any(k in q for k in ["worried", "scared", "nervous", "anxious", "fear", "डर", "चिंता", "परेशान", "घबराहट"]):
        return (
            "शांत रहें, घबराने की कोई बात नहीं है। स्कैमर्स अक्सर डर और जल्दबाजी का माहौल बनाते हैं। मुझे पूरी बात बताएं, हम मिलकर स्थिति की जांच करेंगे।"
            if is_hi else
            "Please take a deep breath. Scammers rely on manufactured urgency and panic. Tell me what happened, and we'll calmly review the details together."
        )

    # 2. Compliments / Appreciation
    if any(k in q for k in ["smart", "intelligent", "clever", "great job", "awesome", "good agent", "समझदार", "अच्छा काम", "शानदार"]):
        return (
            "बहुत धन्यवाद! मेरा लक्ष्य आपको सटीक और सुरक्षित वित्तीय मार्गदर्शन देना है। क्या आपके पास कोई संदेश या लिंक है जिसकी आप जांच करना चाहते हैं?"
            if is_hi else
            "Thank you! I strive to be sharp, accurate, and helpful in keeping your investments safe. Is there anything specific you'd like to check?"
        )

    # 3. Willingness to chat
    if any(k in q for k in ["chat", "talk", "speak", "बात", "गपशप"]):
        return (
            "बिल्कुल, मैं बात करने के लिए तैयार हूँ। आप किसी भी निवेश ऑफर, ट्रेडिंग ग्रुप या सुरक्षा नियम के बारे में पूछ सकते हैं।"
            if is_hi else
            "Of course! I'm right here and happy to chat. Feel free to ask about any message, investment scheme, or safety guidelines."
        )

    # 4. Questions about platform, identity, or purpose
    if any(k in q for k in ["vera", "who", "what do you do", "scanner", "वेरा", "आप क्या"]):
        return (
            "मैं VERA सुरक्षा सहायक हूँ। मैं किसी भी संदिग्ध संदेश, सेबी पंजीकरण या लिंक की तुरंत जांच करने में आपकी मदद कर सकती हूँ। आप क्या जानना चाहते हैं?"
            if is_hi else
            "I'm here as your VERA fraud prevention guide. I can help examine suspect messages, verify SEBI credentials, or analyze unknown links. What would you like to explore?"
        )

    # 5. General short, poised & professional conversational turn
    return (
        "नमस्ते! मैं वेरोनिका हूँ, आपकी VERA सुरक्षा सहायक। मैं सामान्य बातचीत और संदिग्ध निवेशों की फोरेंसिक जांच दोनों के लिए यहाँ हूँ। आज मैं आपकी क्या सहायता करूँ?"
        if is_hi else
        "Hello! I am Veronica, your VERA fraud safety assistant. I'm right here to answer questions, chat, or inspect suspect messages in our forensic scanner. How can I help you today?"
    )


class VeronicaService:
    @staticmethod
    async def process_chat(request: VeronicaChatRequest) -> VeronicaChatResponse:
        user_turn = request.messages[-1].content if request.messages else ""
        lang = request.language if request.language in ("en", "hi") else "en"

        # 1. Sanitize & Mask
        clean_query = sanitize_input(user_turn, max_chars=500)
        masked_query = mask_pii(clean_query)

        if not masked_query:
            reply = "कृपया अपना प्रश्न लिखें।" if lang == "hi" else "Please enter your question or request."
            return VeronicaChatResponse(reply=reply, language=lang, source="canned")

        # 2. Extract Forensic Telemetry & Entities
        forensic_entities = extract_forensic_entities(masked_query)

        # 3. Prompt Injection Guard
        if check_prompt_injection(masked_query):
            logger.warning("Prompt injection detected in Veronica chat: %s", clean_query[:50])
            reply = (
                "मैं वेरोनिका हूँ, VERA की सुरक्षा सहायक। मैं सुरक्षा नियमों को बदलने या सिस्टम प्रॉम्प्ट प्रकट करने के निर्देशों का पालन नहीं कर सकती। मैं धोखाधड़ी की जांच में आपकी कैसे सहायता कर सकती हूँ?"
                if lang == "hi"
                else "I am Veronica, VERA's platform assistant. I cannot follow instructions to bypass safety rules or reveal system prompts. How can I assist you with fraud detection today?"
            )
            return VeronicaChatResponse(
                reply=reply,
                language=lang,
                source="guard",
                suggested_chips=["How does VERA work?", "Check a WhatsApp group", "SEBI registration verify"]
            )

        # 4. Check Canned Answers (0 tokens, deterministic)
        canned = find_canned_response(masked_query, language=lang)
        if canned:
            return VeronicaChatResponse(
                reply=canned["reply"],
                language=lang,
                source="canned",
                actions=canned.get("actions", []),
                suggested_chips=canned.get("suggested_chips", [])
            )

        # 5. Check Query Cache (0 tokens)
        cached = veronica_budget.get_cache(masked_query, language=lang)
        if cached:
            return VeronicaChatResponse(
                reply=cached["reply"],
                language=lang,
                source="cached",
                actions=[VeronicaAction(**a) for a in cached.get("actions", [])],
                suggested_chips=cached.get("suggested_chips", [])
            )

        # 6. Generate Dynamic Actions and Chips
        dynamic_actions, dynamic_chips = generate_dynamic_actions(masked_query, forensic_entities, lang=lang)

        # 7. Check Free-Tier LLM Budget
        allowed, budget_msg = veronica_budget.check_llm_budget(session_id=request.session_id)
        if not allowed:
            logger.info("Veronica budget check denied request: %s", budget_msg)
            reply = (
                budget_msg if budget_msg else (
                    "वेरोनिका इस समय व्यस्त है। कृपया कुछ सेकंड बाद पुनः प्रयास करें या मुख्य स्कैनर का उपयोग करें।"
                    if lang == "hi"
                    else "Veronica is currently operating under high investor volume. Please wait a moment or use the main scanner below."
                )
            )
            return VeronicaChatResponse(
                reply=reply,
                language=lang,
                source="fallback",
                actions=dynamic_actions,
                suggested_chips=dynamic_chips
            )

        # 8. Call LLM Provider (Gemini Free Tier) with Forensic Telemetry
        system_prompt = SYSTEM_PROMPT_HI if lang == "hi" else SYSTEM_PROMPT_EN
        context_turns = []
        for m in request.messages[-5:]:
            role_label = "User" if m.role == "user" else "Assistant"
            context_turns.append(f"{role_label}: {sanitize_input(m.content, max_chars=300)}")
        conversation_context = "\n".join(context_turns)
        forensic_context = build_forensic_context(masked_query, forensic_entities)

        full_prompt = (
            f"{forensic_context}\n\n"
            f"Conversation history:\n{conversation_context}\n\n"
            f"User Question: {masked_query}\n\n"
            f"Veronica's Response:"
        )

        try:
            provider = get_llm_provider("gemini")
            if not await provider.is_available():
                # Try fallback configured provider
                provider = get_llm_provider()

            result = await provider.generate(prompt=full_prompt, system_prompt=system_prompt)
            output_text = result.output_text.strip() if result.output_text else ""
            veronica_budget.record_llm_usage(session_id=request.session_id)

        except Exception as e:
            logger.error("Error generating Veronica response from LLM provider: %s", e)
            output_text = ""

        # 9. Output Safety Filter & Post-Processing
        if not output_text:
            query_lower = masked_query.lower()
            if any(term in query_lower for term in ["buy", "sell", "stock", "shares", "crypto", "bitcoin", "invest", "portfolio", "nifty", "trading", "profit", "ipo", "forex", "fund", "return", "शेयर"]):
                output_text = REFUSAL_INVESTMENT_ADVICE_HI if lang == "hi" else REFUSAL_INVESTMENT_ADVICE_EN
            else:
                output_text = generate_conversational_fallback(masked_query, lang=lang)
            source_label = "fallback"
        else:
            filtered_text, was_flagged = filter_generated_output(output_text, language=lang)
            output_text = filtered_text
            source_label = "gemini"

        response_data = {
            "reply": output_text,
            "language": lang,
            "actions": [a.model_dump() for a in dynamic_actions],
            "suggested_chips": dynamic_chips
        }

        # Cache valid generated responses
        if source_label == "gemini":
            veronica_budget.set_cache(masked_query, language=lang, response_data=response_data)

        return VeronicaChatResponse(
            reply=output_text,
            language=lang,
            source=source_label,
            actions=dynamic_actions,
            suggested_chips=dynamic_chips
        )

