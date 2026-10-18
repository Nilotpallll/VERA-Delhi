"""Vetted pre-compiled answers for common questions, navigation, and emergency triage.

These responses require zero LLM token consumption, protecting the Gemini free tier
while providing instant, 100% deterministic guidance.
"""

from typing import Any

from .schemas import VeronicaAction

CANNED_RESPONSES: dict[str, dict[str, Any]] = {
    "emergency_money_sent": {
        "keywords": [
            "sent money", "transferred money", "lost money", "already paid", "i was scammed",
            "scammed me", "cheated me", "money debited", "paid money", "stole my money",
            "fraud transaction", "took my savings", "took my money", "cheated by",
            "पैसे भेज दिए", "पैसे कट गए", "धोखा हो गया", "पैसे लूट लिए", "चले गए", "पैसे डूब गए",
            "रुपये चले गए", "रुपए चले गए", "पैसे चले गए"
        ],
        "en": {
            "reply": (
                "🚨 **EMERGENCY ACTION REQUIRED (GOLDEN HOUR)**\n\n"
                "If you have recently transferred funds to a fraudulent account, take these steps immediately:\n\n"
                "1. **Call 1930 Immediately**: Dial the National Cyber Crime Helpline **1930** right now. Early reporting allows law enforcement to freeze the fraudster's bank account before funds are siphoned off.\n"
                "2. **Lodge an Official Complaint**: Visit **[cybercrime.gov.in](https://cybercrime.gov.in)** and register an incident under the Financial Fraud category.\n"
                "3. **Contact Your Bank**: Call your bank's 24x7 fraud hotline immediately to block your card/netbanking and report the beneficiary account.\n"
                "4. **Preserve Evidence**: Save transaction UTR numbers, UPI IDs, chat screenshots, and phone numbers. Do not delete the conversation."
            ),
            "actions": [
                {"type": "open_helpline", "label": "📞 Call 1930 Helpline", "payload": "tel:1930"},
                {"type": "external_link", "label": "🌐 Cybercrime Portal", "payload": "https://cybercrime.gov.in"},
                {"type": "navigate", "label": "📋 File Evidence in VERA", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "What documents should I save?",
                "How does bank account freezing work?",
                "Can VERA scan the fraudster's number?"
            ]
        },
        "hi": {
            "reply": (
                "🚨 **तत्काल आपातकालीन कदम (गोल्डन ऑवर)**\n\n"
                "यदि आपने किसी संदिग्ध या फर्जी खाते में पैसे ट्रांसफर कर दिए हैं, तो तुरंत ये कदम उठाएं:\n\n"
                "1. **तुरंत 1930 पर कॉल करें**: राष्ट्रीय साइबर अपराध हेल्पलाइन नंबर **1930** पर तुरंत संपर्क करें। त्वरित सूचना मिलने पर पुलिस संदिग्ध बैंक खाते में पैसे फ्रीज करवा सकती है।\n"
                "2. **आधिकारिक शिकायत दर्ज करें**: आधिकारिक पोर्टल **[cybercrime.gov.in](https://cybercrime.gov.in)** पर वित्तीय धोखाधड़ी की शिकायत दर्ज करें।\n"
                "3. **अपने बैंक को सूचित करें**: अपने बैंक की 24x7 आपातकालीन हेल्पलाइन पर संपर्क करके लेन-देन की सूचना दें और अपने कार्ड/नेटबैंकिंग को सुरक्षित करें।\n"
                "4. **सबूत सुरक्षित रखें**: UTR नंबर, UPI आईडी, व्हाट्सएप चैट के स्क्रीनशॉट और फोन नंबर संभाल कर रखें।"
            ),
            "actions": [
                {"type": "open_helpline", "label": "📞 1930 हेल्पलाइन पर कॉल करें", "payload": "tel:1930"},
                {"type": "external_link", "label": "🌐 साइबरक्राइम पोर्टल", "payload": "https://cybercrime.gov.in"},
                {"type": "navigate", "label": "📋 VERA में सबूत जांचें", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "मुझे कौन से सबूत सुरक्षित रखने चाहिए?",
                "क्या VERA नंबर या लिंक की जांच कर सकता है?",
                "बैंक से पैसे वापस कैसे मिल सकते हैं?"
            ]
        }
    },
    "what_is_vera": {
        "keywords": [
            "what is vera", "about vera", "how does vera work", "how vera works",
            "what does this do", "what can you do", "who made vera", "what is this platform",
            "वेरा क्या है", "यह क्या करता है"
        ],
        "en": {
            "reply": (
                "**VERA (Verification & Evidence-based Risk Analysis)** is an agentic platform designed to protect Indian retail investors from digital financial crimes.\n\n"
                "Key capabilities:\n"
                "• **Multi-Modal Forensics**: Analyzes deceptive WhatsApp/Telegram texts, deepfake endorsement videos, fraudulent audio notes, and cloned APKs.\n"
                "• **SEBI Intermediary Verification**: Directly checks SEBI registration numbers, broker licenses, and RIA/RA credentials against official records.\n"
                "• **Deterministic Risk Fusion**: Generates an explainable 0–100 risk score based on factual heuristics rather than black-box guesses.\n"
                "• **Audit-Ready Evidence**: Produces cryptographically signed (SHA-256) forensic dossiers suitable for submitting to cyber cells or banks."
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Try the Scanner", "payload": "#scanner-section"},
                {"type": "run_sample", "label": "🧪 Load Sample Case", "payload": "sample_fake_advisory"}
            ],
            "suggested_chips": [
                "How do I check a suspicious WhatsApp group?",
                "How does VERA check SEBI registration?",
                "Can VERA detect deepfake videos?"
            ]
        },
        "hi": {
            "reply": (
                "**VERA (Verification & Evidence-based Risk Analysis)** भारतीय खुदरा निवेशकों को डिजिटल वित्तीय धोखाधड़ी से बचाने के लिए बनाया गया एक आधुनिक प्लेटफॉर्म है।\n\n"
                "मुख्य विशेषताएं:\n"
                "• **मल्टी-मोडल फोरेंसिक**: संदिग्ध व्हाट्सएप/टेलीग्राम संदेशों, फर्जी ट्रेडिंग ऐप्स (APK), ऑडियो और डीपफेक वीडियो की जांच।\n"
                "• **SEBI आधिकारिक सत्यापन**: सेबी पंजीकृत सलाहकारों, ब्रोकरों और रिसर्च एनालिस्टों के लाइसेंस नंबरों का आधिकारिक डेटाबेस से मिलान।\n"
                "• **पारदर्शी जोखिम स्कोर**: 0 से 100 तक का स्पष्ट और तथ्य-आधारित सुरक्षा स्कोर।\n"
                "• **कानूनी सबूत**: पुलिस या बैंक में शिकायत दर्ज करने योग्य SHA-256 सत्यापित रिपोर्ट।"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर का उपयोग करें", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप की जांच कैसे करें?",
                "SEBI पंजीकरण की जांच कैसे होती है?",
                "डीपफेक वीडियो की पहचान कैसे करें?"
            ]
        }
    },
    "check_whatsapp": {
        "keywords": [
            "whatsapp", "telegram", "group", "message", "chat", "trading tips", "guaranteed return",
            "व्हाट्सएप", "टेलीग्राम", "ग्रुप", "ट्रेडिंग टिप्स"
        ],
        "en": {
            "reply": (
                "**How to Check a Suspicious WhatsApp or Telegram Group:**\n\n"
                "1. **Copy the Message**: Copy the chat invitation, stock recommendations, or screenshots of abnormal profit claims.\n"
                "2. **Paste into VERA**: Scroll to the VERA screening tool on this page and paste the text into the **Message / Text tab**.\n"
                "3. **Look for Red Flags**: VERA automatically checks for classic scam indicators:\n"
                "   • Unrealistic guaranteed returns (e.g., '100% weekly profit')\n"
                "   • Urgency and pressure tactics ('VIP group closing today')\n"
                "   • Fake SEBI registration numbers or unverified admin accounts\n"
                "   • Direct payment requests to personal UPI IDs"
            ),
            "actions": [
                {"type": "navigate", "label": "📝 Paste Message in Scanner", "payload": "#scanner-section"},
                {"type": "run_sample", "label": "🧪 Test WhatsApp Sample", "payload": "sample_whatsapp_scam"}
            ],
            "suggested_chips": [
                "Why do scammers use personal UPI accounts?",
                "How does VERA verify SEBI registration?",
                "What if they shared an APK link?"
            ]
        },
        "hi": {
            "reply": (
                "**संदिग्ध व्हाट्सएप या टेलीग्राम ग्रुप की जांच कैसे करें:**\n\n"
                "1. **संदेश कॉपी करें**: ग्रुप में आए संदेश, गारंटीड मुनाफे के दावे या इनविटेशन लिंक को कॉपी करें।\n"
                "2. **VERA स्कैनर में पेस्ट करें**: इस पेज पर स्थित VERA टूल के **संदेश (Message)** टैब में पेस्ट करें।\n"
                "3. **प्रमुख खतरे के संकेत (Red Flags)**:\n"
                "   • अवास्तविक गारंटीड रिटर्न (जैसे 'हर हफ्ते 50% पक्का मुनाफा')\n"
                "   • जल्दबाजी का दबाव ('आज ही वीआईपी ग्रुप जॉइन करें')\n"
                "   • व्यक्तिगत यूपीआई (UPI) पर पैसे मंगाना"
            ),
            "actions": [
                {"type": "navigate", "label": "📝 स्कैनर में संदेश पेस्ट करें", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "व्यक्तिगत UPI पर पैसे भेजना सुरक्षित क्यों नहीं है?",
                "SEBI पंजीकरण की जांच कैसे होती है?",
                "यदि उन्होंने कोई ऐप डाउनलोड करने को कहा हो?"
            ]
        }
    },
    "check_sebi": {
        "keywords": [
            "sebi", "registration", "license", "ria", "research analyst", "investment adviser",
            "verify sebi", "check sebi", "सेबी", "पंजीकरण", "लाइसेंस"
        ],
        "en": {
            "reply": (
                "**How VERA Cross-Checks SEBI Registrations:**\n\n"
                "• **Intermediary Database**: VERA queries the official SEBI registry of registered Research Analysts (INH numbers), Investment Advisers (INA numbers), and Stock Brokers (INZ numbers).\n"
                "• **Entity Validation**: VERA matches both the numeric registration code and the registered legal entity name to catch scammers impersonating legitimate firms.\n"
                "• **Zero Forgery Tolerance**: If an entity uses a fake, expired, or someone else's SEBI number, VERA raises a high-severity red flag."
            ),
            "actions": [
                {"type": "external_link", "label": "🌐 Official SEBI Intermediary List", "payload": "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13"},
                {"type": "navigate", "label": "🔍 Screen Registration in VERA", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "What is the difference between RIA and RA?",
                "How do scammers fake SEBI certificates?",
                "Can you check a suspicious website URL?"
            ]
        },
        "hi": {
            "reply": (
                "**VERA द्वारा SEBI पंजीकरण की जांच कैसे की जाती है:**\n\n"
                "• **आधिकारिक डेटाबेस मिलान**: VERA सेबी के आधिकारिक रिकॉर्ड से रिसर्च एनालिस्ट (INH), निवेश सलाहकार (INA) और ब्रोकर (INZ) के लाइसेंस का मिलान करता है।\n"
                "• **नाम और नंबर दोनों का सत्यापन**: स्कैमर्स अक्सर असली कंपनियों के नाम या नंबर चुराते हैं। VERA कानूनी नाम और लाइसेंस नंबर दोनों की पुष्टि करता है।\n"
                "• **फर्जी लाइसेंस की पहचान**: यदि नंबर गलत, समाप्त या किसी और के नाम पर पाया जाता है, तो VERA तुरंत चेतावनी जारी करता है।"
            ),
            "actions": [
                {"type": "external_link", "label": "🌐 सेबी आधिकारिक पोर्टल", "payload": "https://www.sebi.gov.in"}
            ],
            "suggested_chips": [
                "क्या सेबी कभी गारंटीड रिटर्न का वादा करता है?",
                "व्हाट्सएप ग्रुप की जांच कैसे करें?",
                "डीपफेक वीडियो की पहचान कैसे करें?"
            ]
        }
    },
    "refusal_stock_tip": {
        "keywords": [
            "buy stock", "stock tip", "which share", "nifty", "banknifty", "multibagger",
            "crypto", "best stock", "recommend stock", "should i invest", "buy shares",
            "trading tip", "intraday", "portfolio", "target price", "penny stock",
            "algorithmic trading", "which ipo", "forex trading", "guaranteed profit",
            "guaranteed return", "शेयर खरीदें", "स्टॉक टिप", "शेयर खरीदने की सलाह",
            "शेयर खरीदने"
        ],
        "en": {
            "reply": (
                "**Policy Notice: VERA Does Not Provide Investment Advice**\n\n"
                "I am Veronica, a fraud detection assistant. I cannot recommend stocks, advise on trading calls, or evaluate investment profitability.\n\n"
                "If someone in a WhatsApp group or social media channel is offering you 'guaranteed tips' or insider stock picks, treat it with extreme caution. Genuine financial advice is only provided by SEBI-registered professionals who never promise guaranteed returns."
            ),
            "actions": [
                {"type": "external_link", "label": "🌐 Find SEBI Registered Advisers", "payload": "https://www.sebi.gov.in"}
            ],
            "suggested_chips": [
                "How do I check if an adviser is registered with SEBI?",
                "What are common investment scam red flags?",
                "How do I use VERA's scanner?"
            ]
        },
        "hi": {
            "reply": (
                "**नीतिगत सूचना: VERA निवेश सलाह नहीं देता है**\n\n"
                "मैं वेरोनिका हूँ, आपकी धोखाधड़ी सुरक्षा सहायक। मैं किसी शेयर की सिफारिश, ट्रेडिंग टिप्स या निवेश के मुनाफे का अनुमान नहीं दे सकती।\n\n"
                "यदि कोई आपको सोशल मीडिया या व्हाट्सएप पर 'पक्के मुनाफे' वाली स्टॉक टिप्स दे रहा है, तो बहुत सावधान रहें। वैध सलाह केवल SEBI-पंजीकृत सलाहकार ही दे सकते हैं, जो कभी भी निश्चित रिटर्न की गारंटी नहीं देते।"
            ),
            "actions": [
                {"type": "external_link", "label": "🌐 SEBI पंजीकृत सलाहकार खोजें", "payload": "https://www.sebi.gov.in"}
            ],
            "suggested_chips": [
                "SEBI पंजीकरण की जांच कैसे करें?",
                "व्हाट्सएप ग्रुप के खतरे के संकेत क्या हैं?",
                "VERA स्कैनर का उपयोग कैसे करें?"
            ]
        }
    }
}

PRIORITIZED_INTENTS = [
    "emergency_money_sent",
    "refusal_stock_tip",
    "what_is_vera",
    "check_sebi",
    "check_whatsapp"
]


def find_canned_response(text: str, language: str = "en") -> dict[str, Any] | None:
    """Matches text against vetted canned intents using normalized keyword scanning."""
    normalized = text.lower().strip()
    lang_key = "hi" if language == "hi" else "en"

    for intent_name in PRIORITIZED_INTENTS:
        intent_data = CANNED_RESPONSES.get(intent_name)
        if not intent_data:
            continue
        for kw in intent_data["keywords"]:
            if kw in normalized:
                content = intent_data.get(lang_key) or intent_data.get("en")
                if content:
                    return {
                        "intent": intent_name,
                        "reply": content["reply"],
                        "language": lang_key,
                        "actions": [VeronicaAction(**a) for a in content.get("actions", [])],
                        "suggested_chips": content.get("suggested_chips", []),
                        "source": "canned"
                    }
    return None
