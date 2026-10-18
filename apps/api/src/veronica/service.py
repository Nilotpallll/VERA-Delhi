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

        # 2. Prompt Injection Guard
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

        # 3. Check Canned Answers (0 tokens, deterministic)
        canned = find_canned_response(masked_query, language=lang)
        if canned:
            return VeronicaChatResponse(
                reply=canned["reply"],
                language=lang,
                source="canned",
                actions=canned.get("actions", []),
                suggested_chips=canned.get("suggested_chips", [])
            )

        # 4. Check Query Cache (0 tokens)
        cached = veronica_budget.get_cache(masked_query, language=lang)
        if cached:
            return VeronicaChatResponse(
                reply=cached["reply"],
                language=lang,
                source="cached",
                actions=[VeronicaAction(**a) for a in cached.get("actions", [])],
                suggested_chips=cached.get("suggested_chips", [])
            )

        # 5. Check Free-Tier LLM Budget
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
                actions=[VeronicaAction(type="navigate", label="🔍 Go to Scanner", payload="#scanner-section")],
                suggested_chips=["What is VERA?", "How does VERA verify SEBI?", "Call 1930 Helpline"]
            )

        # 6. Call LLM Provider (Gemini Free Tier)
        system_prompt = SYSTEM_PROMPT_HI if lang == "hi" else SYSTEM_PROMPT_EN
        context_turns = []
        for m in request.messages[-5:]:
            role_label = "User" if m.role == "user" else "Assistant"
            context_turns.append(f"{role_label}: {sanitize_input(m.content, max_chars=300)}")
        conversation_context = "\n".join(context_turns)
        full_prompt = f"Conversation history:\n{conversation_context}\n\nUser Question: {masked_query}\n\nVeronica's Response:"

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

        # 7. Output Safety Filter & Post-Processing
        if not output_text:
            query_lower = masked_query.lower()
            if any(term in query_lower for term in ["buy", "sell", "stock", "shares", "crypto", "bitcoin", "invest", "portfolio", "nifty", "trading", "profit", "ipo", "forex", "fund", "return", "शेयर"]):
                output_text = REFUSAL_INVESTMENT_ADVICE_HI if lang == "hi" else REFUSAL_INVESTMENT_ADVICE_EN
            else:
                output_text = (
                    "मैं वेरोनिका हूँ, आपकी VERA सुरक्षा सहायक। मैं संदिग्ध निवेश संदेशों, सेबी पंजीकरण सत्यापन और धोखाधड़ी जांच में सहायता के लिए यहाँ हूँ। आप नीचे दिए गए VERA स्कैनर में संदिग्ध लिंक या संदेश डालकर भी त्वरित जांच कर सकते हैं। आज मैं आपकी कैसे सहायता कर सकती हूँ?"
                    if lang == "hi"
                    else "I am Veronica, your VERA fraud safety assistant. I can help you check suspicious investment messages, verify SEBI registrations, or inspect suspect links and APKs in our forensic scanner. How can I help you today?"
                )
            source_label = "fallback"
        else:
            filtered_text, was_flagged = filter_generated_output(output_text, language=lang)
            output_text = filtered_text
            source_label = "gemini"

        # Suggested actions and chips
        actions = [
            VeronicaAction(type="navigate", label="🔍 Open Scanner", payload="#scanner-section"),
            VeronicaAction(type="open_helpline", label="📞 Cyber Helpline 1930", payload="tel:1930")
        ]
        suggested_chips = (
            ["व्हाट्सएप ग्रुप की जांच", "SEBI रजिस्ट्रेशन चेक", "1930 हेल्पलाइन"]
            if lang == "hi"
            else ["Check WhatsApp group", "SEBI registration check", "1930 Helpline"]
        )

        response_data = {
            "reply": output_text,
            "language": lang,
            "actions": [a.model_dump() for a in actions],
            "suggested_chips": suggested_chips
        }

        # Cache valid generated responses
        if source_label == "gemini":
            veronica_budget.set_cache(masked_query, language=lang, response_data=response_data)

        return VeronicaChatResponse(
            reply=output_text,
            language=lang,
            source=source_label,
            actions=actions,
            suggested_chips=suggested_chips
        )
