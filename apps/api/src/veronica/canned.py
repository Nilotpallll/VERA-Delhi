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
            "what does this do", "who made vera", "what is this platform",
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
            "whatsapp", "telegram", "group chat", "whatsapp group", "telegram group",
            "trading group", "vip group", "advisory group", "suspicious message", "whatsapp message",
            "telegram message", "trading tips", "guaranteed return",
            "व्हाट्सएप", "टेलीग्राम", "व्हाट्सएप ग्रुप", "टेलीग्राम ग्रुप", "ट्रेडिंग टिप्स"
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
            "guaranteed return", "good buy", "should i buy", "worth buying", "invest in",
            "buy", "sell", "शेयर खरीदें", "स्टॉक टिप", "शेयर खरीदने की सलाह",
            "शेयर खरीदने", "शेयर बेचें"
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
    },
    "help_capabilities": {
        "keywords": [
            "help", "help me", "how can you help", "what can you do", "what do you do",
            "menu", "options", "features", "commands",
            "मदद", "सहायता", "आप क्या कर सकती हैं", "मेरी मदद करें", "क्या सहायता कर सकती हैं"
        ],
        "en": {
            "reply": (
                "Here is how I can assist you:\n\n"
                "• **Check Messages & Groups**: Paste suspect WhatsApp or Telegram group chats to detect scam patterns and fake profit claims.\n"
                "• **Verify SEBI Licenses**: Cross-check research analysts, brokers, and advisors against official SEBI records.\n"
                "• **Detect Deepfakes & Cloned APKs**: Spot celebrity video endorsements and fake investment applications.\n"
                "• **Emergency Guidance**: Step-by-step guidance if money was already transferred (calling 1930, bank freeze).\n\n"
                "What would you like to investigate?"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Open Scanner", "payload": "#scanner-section"},
                {"type": "open_helpline", "label": "📞 Call 1930 Helpline", "payload": "tel:1930"}
            ],
            "suggested_chips": [
                "How do I check a suspicious WhatsApp group?",
                "How does VERA verify SEBI registration?",
                "I already sent money. What should I do? 🚨"
            ]
        },
        "hi": {
            "reply": (
                "मैं निम्नलिखित कार्यों में आपकी सहायता कर सकती हूँ:\n\n"
                "• **संदेशों की जांच**: व्हाट्सएप या टेलीग्राम ग्रुप संदेशों में पक्के मुनाफे या धोखाधड़ी के संकेतों की पहचान।\n"
                "• **SEBI लाइसेंस सत्यापन**: आधिकारिक रिकॉर्ड से रिसर्च एनालिस्ट या एडवाइजर के लाइसेंस की पुष्टि।\n"
                "• **डीपफेक और नकली ट्रेडिंग ऐप्स (APK)**: नकली प्रचार वीडियो और अनधिकृत ऐप्स की पहचान।\n"
                "• **आपातकालीन सहायता**: यदि पैसे कट गए हैं, तो तत्काल 1930 पर शिकायत और बैंक खाता फ्रीज कराने के निर्देश।\n\n"
                "आप किसकी जांच करना चाहते हैं?"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर खोलें", "payload": "#scanner-section"},
                {"type": "open_helpline", "label": "📞 1930 हेल्पलाइन पर कॉल करें", "payload": "tel:1930"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप की जांच कैसे करें?",
                "SEBI रजिस्ट्रेशन चेक करें",
                "मैंने पैसे भेज दिए हैं, मुझे क्या करना चाहिए? 🚨"
            ]
        }
    },
    "bot_identity": {
        "keywords": [
            "who are you", "what is your name", "who r u", "what are you",
            "introduce yourself", "tell me about yourself", "your name", "who made you",
            "आप कौन हैं", "तुम्हारा नाम क्या है", "आपका नाम क्या है", "तुम कौन हो"
        ],
        "en": {
            "reply": (
                "I am **Veronica**, the official AI forensic guide for the VERA platform. I assist retail investors in identifying financial fraud, verifying SEBI regulatory credentials, detecting deepfakes, and taking immediate emergency actions if scammed."
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Try the Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "How does VERA verify SEBI?",
                "Check a WhatsApp group",
                "What is VERA?"
            ]
        },
        "hi": {
            "reply": (
                "मैं **वेरोनिका** हूँ, VERA प्लेटफॉर्म की आधिकारिक एआई सुरक्षा सहायक। मैं खुदरा निवेशकों को वित्तीय धोखाधड़ी पहचानने, सेबी लाइसेंस सत्यापित करने, डीपफेक पकड़ने और आपात स्थिति में मार्गदर्शन देने में मदद करती हूँ।"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर आज़माएं", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "SEBI पंजीकरण की जांच कैसे होती है?",
                "व्हाट्सएप ग्रुप की जांच कैसे करें?",
                "VERA क्या है?"
            ]
        }
    },
    "how_are_you": {
        "keywords": [
            "how are you", "how are you doing", "how r u", "how do you do",
            "how is it going", "how's it going", "how are u", "how you doing",
            "आप कैसी हैं", "आप कैसे हैं", "क्या हाल है", "सब कैसा है", "कैसी हो", "कैसे हो"
        ],
        "en": {
            "reply": (
                "I'm doing great, thank you for asking! I'm here and fully operational to help you analyze suspect investments, verify SEBI credentials, or check fraudulent messages. How can I assist you today?"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Go to Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "Check a suspicious WhatsApp group",
                "Verify SEBI registration",
                "What is VERA?"
            ]
        },
        "hi": {
            "reply": (
                "मैं बिल्कुल ठीक हूँ, पूछने के लिए धन्यवाद! मैं संदिग्ध निवेशों के विश्लेषण, सेबी पंजीकरण जांच और धोखाधड़ी से सुरक्षा में मदद के लिए तैयार हूँ। आज मैं आपकी कैसे सहायता कर सकती हूँ?"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर पर जाएं", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप की जांच करें",
                "SEBI रजिस्ट्रेशन चेक करें",
                "VERA क्या है?"
            ]
        }
    },
    "greeting": {
        "keywords": [
            "hi", "hello", "hey", "heya", "howdy", "hola", "namaste", "namaskar",
            "good morning", "good afternoon", "good evening", "gm", "greetings",
            "नमस्ते", "नमस्कार", "हेलो", "हाय", "प्रणाम", "शुभ प्रभात", "शुभ संध्या"
        ],
        "en": {
            "reply": (
                "Hello! How can I help you today? I am **Veronica**, your VERA fraud safety assistant.\n\n"
                "I can help you check suspicious investment messages, verify SEBI registrations, screen unknown trading links, or test an APK in our scanner. What would you like to investigate?"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Open Scanner", "payload": "#scanner-section"},
                {"type": "run_sample", "label": "🧪 Try Sample Case", "payload": "sample_whatsapp_scam"}
            ],
            "suggested_chips": [
                "How do I check a suspicious WhatsApp group?",
                "How does VERA verify SEBI registration?",
                "What is VERA?"
            ]
        },
        "hi": {
            "reply": (
                "नमस्ते! मैं आपकी कैसे सहायता कर सकती हूँ? मैं **वेरोनिका** हूँ, आपकी VERA सुरक्षा सहायक।\n\n"
                "मैं संदिग्ध निवेश संदेशों, सेबी (SEBI) पंजीकृत सलाहकारों के सत्यापन, डीपफेक वीडियो और फर्जी ऐप्स (APK) की पहचान में आपकी मदद कर सकती हूँ। आप क्या जांचना चाहते हैं?"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर खोलें", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप की जांच कैसे करें?",
                "SEBI रजिस्ट्रेशन चेक करें",
                "वेरा क्या है?"
            ]
        }
    },
    "gratitude": {
        "keywords": [
            "thank you", "thanks", "thx", "thank u", "many thanks", "thank you so much",
            "appreciate it", "thanks a lot", "grateful", "dhanyawad", "shukriya",
            "धन्यवाद", "शुक्रिया", "बहुत धन्यवाद", "थैंक यू", "थैंक्स", "आभार"
        ],
        "en": {
            "reply": (
                "You're very welcome! Glad I could help. Protecting investors from financial fraud is what VERA is here for. Stay safe, and always verify before you invest!"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Open Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "What are common scam red flags?",
                "Can you check a suspicious website URL?",
                "How does bank account freezing work?"
            ]
        },
        "hi": {
            "reply": (
                "आपका बहुत-बहुत स्वागत है! मदद करके मुझे प्रसन्नता हुई। खुदरा निवेशकों को घोटालों से सुरक्षित रखना ही VERA का मुख्य उद्देश्य है। सुरक्षित रहें और हमेशा निवेश से पहले सत्यापन करें!"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर खोलें", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "सामान्य धोखाधड़ी के लक्षण क्या हैं?",
                "संदिग्ध वेबसाइट की जांच कैसे करें?",
                "बैंक खाता फ्रीज कैसे होता है?"
            ]
        }
    },
    "acknowledgment": {
        "keywords": [
            "okay", "ok", "k", "got it", "understood", "sure", "alright", "all right",
            "fine", "noted", "sounds good", "i see", "i understand", "thik hai", "theek hai",
            "sahi hai", "achha", "accha", "ठीक है", "ओके", "समझ गया", "समझ गई", "सही है", "अच्छा"
        ],
        "en": {
            "reply": (
                "Thank you! Let me know if you need anything else or if you have any suspicious links, group chats, or advisor credentials you'd like to check."
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Go to Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "How do I check a suspicious WhatsApp group?",
                "How does VERA verify SEBI registration?",
                "What are common investment scam red flags?"
            ]
        },
        "hi": {
            "reply": (
                "धन्यवाद! यदि आपको किसी और लिंक, ग्रुप संदेश या निवेश सलाहकार की जांच करनी हो, तो मुझे अवश्य बताएं। मैं आपकी मदद के लिए सदैव तैयार हूँ।"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर पर जाएं", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप के खतरे के संकेत क्या हैं?",
                "SEBI पंजीकरण की जांच कैसे करें?",
                "VERA स्कैनर का उपयोग कैसे करें?"
            ]
        }
    },
    "farewell": {
        "keywords": [
            "bye", "goodbye", "good bye", "see you", "see ya", "take care",
            "have a nice day", "have a good day", "cya", "gn", "good night", "alvida",
            "अलविदा", "बाय", "शुभ रात्रि", "फिर मिलेंगे", "अपना ध्यान रखें"
        ],
        "en": {
            "reply": (
                "Goodbye! Stay vigilant against unverified investment schemes and suspicious trading tips. Have a wonderful and safe day!"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Keep Scanner Handy", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "Call 1930 Helpline",
                "How does VERA work?"
            ]
        },
        "hi": {
            "reply": (
                "अलविदा! फर्जी निवेश योजनाओं और संदिग्ध ट्रेडिंग ग्रुप्स से हमेशा सतर्क रहें। आपका दिन शुभ और सुरक्षित हो!"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर खुला रखें", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "1930 हेल्पलाइन पर कॉल करें",
                "VERA कैसे काम करता है?"
            ]
        }
    },
    "praise_positive": {
        "keywords": [
            "great", "awesome", "cool", "nice", "good", "super", "excellent",
            "wonderful", "perfect", "amazing", "shabash", "badhiya",
            "बढ़िया", "बहुत अच्छा", "शाबाश", "शानदार", "सुपर"
        ],
        "en": {
            "reply": (
                "Thank you! I'm here whenever you need assistance. Stay vigilant, and don't hesitate to screen any suspicious offers in our forensic scanner."
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Go to Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "How does VERA verify SEBI registration?",
                "Check a WhatsApp group",
                "What is VERA?"
            ]
        },
        "hi": {
            "reply": (
                "धन्यवाद! आपकी सहायता के लिए मैं सदैव तत्पर हूँ। सुरक्षित रहें और किसी भी संदिग्ध ऑफर की जांच हमारे स्कैनर से अवश्य करें।"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर पर जाएं", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "SEBI पंजीकरण की जांच कैसे करें?",
                "व्हाट्सएप ग्रुप के खतरे के संकेत क्या हैं?",
                "VERA स्कैनर का उपयोग कैसे करें?"
            ]
        }
    },
    "affirmation": {
        "keywords": [
            "yes", "yep", "yeah", "haan", "ha", "sure thing", "definitely",
            "हाँ", "हा", "अवश्य", "ज़रूर"
        ],
        "en": {
            "reply": (
                "Great! How can I assist you further? Feel free to paste any message, URL, or advisor name you'd like to check."
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Open Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "Check a suspicious WhatsApp group",
                "Verify SEBI registration",
                "How does VERA work?"
            ]
        },
        "hi": {
            "reply": (
                "बहुत अच्छा! मैं आगे आपकी कैसे सहायता करूँ? आप कोई भी संदेश, लिंक या सलाहकार का नाम यहाँ साझा कर सकते हैं।"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर खोलें", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप की जांच करें",
                "SEBI रजिस्ट्रेशन चेक करें",
                "VERA क्या है?"
            ]
        }
    },
    "negation": {
        "keywords": [
            "no", "nah", "nope", "nahi", "not now", "nothing",
            "नहीं", "ना", "कुछ नहीं"
        ],
        "en": {
            "reply": (
                "No problem! Let me know if you ever need help verifying an investment or checking suspicious claims. Have a safe day!"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Keep Scanner Ready", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "Emergency 1930 Helpline",
                "What is VERA?"
            ]
        },
        "hi": {
            "reply": (
                "कोई बात नहीं! यदि आपको कभी भी किसी निवेश सत्यापन या धोखाधड़ी जांच में सहायता चाहिए, तो मुझे अवश्य बताएं। सुरक्षित रहें!"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर तैयार रखें", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "1930 हेल्पलाइन",
                "VERA कैसे काम करता है?"
            ]
        }
    },
    "where_is_scanner": {
        "keywords": [
            "where is the scanner", "where is scanner", "how to use scanner", "open scanner",
            "show scanner", "access scanner", "find scanner", "स्कैनर कहाँ है", "स्कैनर कैसे उपयोग करें",
            "स्कैनर खोलें", "स्कैनर दिखाएं"
        ],
        "en": {
            "reply": (
                "The VERA forensic scanner is located right on this page! You can scroll up to the scanner section or click the button below to paste text, verify URLs, test APKs, or scan audio/video for fraud signals."
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Go to Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "How do I check a suspicious WhatsApp group?",
                "How does VERA verify SEBI registration?",
                "What is VERA?"
            ]
        },
        "hi": {
            "reply": (
                "VERA फोरेंसिक स्कैनर इसी पेज पर उपलब्ध है! आप ऊपर स्क्रॉल कर सकते हैं या नीचे दिए गए बटन पर क्लिक करके संदिग्ध संदेश, वेबसाइट लिंक, मोबाइल ऐप (APK) या वीडियो की जांच कर सकते हैं।"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर पर जाएं", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप की जांच कैसे करें?",
                "SEBI रजिस्ट्रेशन चेक करें",
                "VERA क्या है?"
            ]
        }
    },
    "what_next": {
        "keywords": [
            "what should i do", "what next", "what to do", "now what", "how to proceed",
            "what can i do", "guide me", "ab kya kare", "ab kya karu", "अब क्या करें",
            "अब क्या करूँ", "आगे क्या करें", "मुझे क्या करना चाहिए"
        ],
        "en": {
            "reply": (
                "Here is how you can proceed right now:\n\n"
                "1. **Screen Suspicious Content**: If you have a suspicious stock tip, group link, or APK, paste it into our forensic scanner below for an instant risk score.\n"
                "2. **Verify Credentials**: Check if the person or entity giving advice is genuinely registered with SEBI.\n"
                "3. **If Money Was Transferred**: Call the National Cyber Crime Helpline **1930** immediately so authorities can attempt an emergency account freeze.\n\n"
                "How can I assist you with the next step?"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Open Scanner", "payload": "#scanner-section"},
                {"type": "open_helpline", "label": "📞 Call 1930 Helpline", "payload": "tel:1930"}
            ],
            "suggested_chips": [
                "How do I check a suspicious WhatsApp group?",
                "How does VERA verify SEBI registration?",
                "What are common investment scam red flags?"
            ]
        },
        "hi": {
            "reply": (
                "आप आगे ये कदम उठा सकते हैं:\n\n"
                "1. **संदिग्ध सामग्री की जांच**: यदि आपको कोई स्टॉक टिप, ग्रुप लिंक या ऐप मिला है, तो उसे नीचे VERA स्कैनर में डालकर जांचें।\n"
                "2. **लाइसेंस की पुष्टि**: सेबी की आधिकारिक सूची में जांचें कि क्या सलाहकार अधिकृत है।\n"
                "3. **यदि पैसे ट्रांसफर कर दिए हैं**: बिना देर किए **1930** हेल्पलाइन पर कॉल करें ताकि पुलिस तुरंत संबंधित बैंक खाते को फ्रीज कर सके।\n\n"
                "मैं इनमें से किसमें आपकी सहायता करूँ?"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर खोलें", "payload": "#scanner-section"},
                {"type": "open_helpline", "label": "📞 1930 हेल्पलाइन पर कॉल करें", "payload": "tel:1930"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप की जांच कैसे करें?",
                "SEBI रजिस्ट्रेशन चेक करें",
                "धोखाधड़ी के मुख्य लक्षण क्या हैं?"
            ]
        }
    },
    "bot_nature": {
        "keywords": [
            "are you human", "are you a robot", "are you a bot", "are you real", "are you ai",
            "are you automated", "are u human", "are u a bot", "क्या आप इंसान हैं", "क्या तुम रोबोट हो",
            "क्या तुम एआई हो", "क्या तुम इंसान हो"
        ],
        "en": {
            "reply": (
                "I am **Veronica**, an AI assistant built specifically for the VERA investor protection platform. While I am an AI, I am powered by deterministic forensic analysis engines, pattern matching for cyber fraud, and direct verification against official SEBI records."
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Try the Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "What is VERA?",
                "How does VERA verify SEBI registration?",
                "Check a suspicious WhatsApp group"
            ]
        },
        "hi": {
            "reply": (
                "मैं **वेरोनिका** हूँ, VERA निवेशक सुरक्षा प्लेटफॉर्म के लिए बनाई गई एक एआई सहायक। मैं वित्तीय घोटालों की पहचान, सेबी रिकॉर्ड सत्यापन और खुदरा निवेशकों को सुरक्षित रखने के लिए फोरेंसिक तकनीकों का उपयोग करती हूँ।"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर आज़माएं", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "VERA क्या है?",
                "SEBI रजिस्ट्रेशन कैसे चेक करें?",
                "व्हाट्सएप ग्रुप की जांच कैसे करें?"
            ]
        }
    },
    "is_free_service": {
        "keywords": [
            "is this free", "is vera free", "do you charge", "is it paid", "pricing",
            "charges", "fees", "how much does it cost", "subscription", "free to use",
            "क्या यह फ्री है", "पैसे लगेंगे", "कोई शुल्क है", "क्या यह मुफ्त है"
        ],
        "en": {
            "reply": (
                "Yes, **VERA is 100% free** for Indian retail investors! You can check suspicious messages, verify SEBI credentials, scan APKs, and generate audit-ready forensic dossiers without any subscription or hidden fees."
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Use Free Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "How does VERA work?",
                "How do I check a suspicious WhatsApp group?",
                "Verify SEBI registration"
            ]
        },
        "hi": {
            "reply": (
                "हाँ, **VERA खुदरा निवेशकों के लिए 100% निःशुल्क (Free) है!** आप बिना किसी शुल्क या सब्सक्रिप्शन के व्हाट्सएप संदेशों, सेबी लाइसेंस और संदिग्ध मोबाइल ऐप्स (APK) की फोरेंसिक जांच कर सकते हैं।"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 मुफ्त स्कैनर का उपयोग करें", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "VERA कैसे काम करता है?",
                "व्हाट्सएप ग्रुप की जांच करें",
                "SEBI रजिस्ट्रेशन चेक करें"
            ]
        }
    },
    "check_presence": {
        "keywords": [
            "are you there", "you there", "anyone there", "hello?", "can you hear me",
            "sun rahe ho", "क्या आप सुन रहे हैं", "सुनो", "सुन रहे हो"
        ],
        "en": {
            "reply": (
                "Yes, I'm here and ready to help! How can I assist you with fraud screening or verifying an investment today?"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Open Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "Check a suspicious WhatsApp group",
                "Verify SEBI registration",
                "What is VERA?"
            ]
        },
        "hi": {
            "reply": (
                "हाँ, मैं यहीं हूँ और आपकी सहायता के लिए तैयार हूँ! आज मैं आपकी सुरक्षा या निवेश जांच में कैसे मदद करूँ?"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर खोलें", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप की जांच करें",
                "SEBI रजिस्ट्रेशन चेक करें",
                "VERA क्या है?"
            ]
        }
    },
    "has_question": {
        "keywords": [
            "i have a question", "can i ask a question", "one question", "have a query",
            "have a doubt", "ek sawal", "sawal hai", "एक सवाल है", "एक प्रश्न है",
            "पूछना है", "सवाल है"
        ],
        "en": {
            "reply": (
                "Of course! Please go ahead and ask your question, or paste any suspicious message, website link, or advisor name you'd like to verify. I'm right here to help!"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Go to Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "How do I check a suspicious WhatsApp group?",
                "How does VERA verify SEBI registration?",
                "What are common investment scam red flags?"
            ]
        },
        "hi": {
            "reply": (
                "बिल्कुल! कृपया अपना प्रश्न पूछें, या कोई भी संदिग्ध लिंक, संदेश या सलाहकार का नाम यहाँ साझा करें। मैं सहायता के लिए तैयार हूँ!"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर पर जाएं", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप की जांच कैसे करें?",
                "SEBI रजिस्ट्रेशन चेक करें",
                "VERA क्या है?"
            ]
        }
    },
    "apology": {
        "keywords": [
            "sorry", "my bad", "apologies", "excuse me", "pardon", "माफ करें",
            "माफ़ी", "माफ कीजिए", "सॉरी", "गलती हो गई"
        ],
        "en": {
            "reply": (
                "No need to apologize at all! How can I help you today? Feel free to ask any question or paste any investment message you'd like to check."
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 Go to Scanner", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "Check a suspicious WhatsApp group",
                "Verify SEBI registration",
                "What is VERA?"
            ]
        },
        "hi": {
            "reply": (
                "माफ़ी की कोई बात नहीं है! मैं आगे आपकी कैसे सहायता करूँ? आप कोई भी सवाल पूछ सकते हैं या संदिग्ध संदेश की जांच कर सकते हैं।"
            ),
            "actions": [
                {"type": "navigate", "label": "🔍 स्कैनर पर जाएं", "payload": "#scanner-section"}
            ],
            "suggested_chips": [
                "व्हाट्सएप ग्रुप की जांच करें",
                "SEBI रजिस्ट्रेशन चेक करें",
                "VERA क्या है?"
            ]
        }
    }
}

PRIORITIZED_INTENTS = [
    # 1. Critical Emergency & Legal Refusals (Highest Priority)
    "emergency_money_sent",
    "refusal_stock_tip",

    # 2. Specific Platform & Regulatory Inquiries
    "what_is_vera",
    "check_sebi",
    "where_is_scanner",
    "check_whatsapp",
    "what_next",

    # 3. Conversational Capabilities & Bot Identity
    "help_capabilities",
    "bot_identity",
    "bot_nature",
    "is_free_service",
    "how_are_you",
    "check_presence",
    "has_question",
    "apology",

    # 4. Standard Conversational Turns
    "greeting",
    "gratitude",
    "acknowledgment",
    "farewell",
    "praise_positive",
    "affirmation",
    "negation",
]

import re


def _extract_tokens(text: str) -> set[str]:
    """Extracts lowercase tokens stripped of punctuation."""
    return set(re.findall(r'[^\s.,!?:;"\'`()\[\]{}]+', text.lower()))


def _normalize_padded(text: str) -> str:
    """Returns space-padded string with normalized punctuation for multi-word phrase matching."""
    cleaned = re.sub(r'[\s.,!?:;"\'`()\[\]{}]+', ' ', text.lower()).strip()
    return f" {cleaned} " if cleaned else " "


def find_canned_response(text: str, language: str = "en") -> dict[str, Any] | None:
    """Matches text against vetted canned intents using token and phrase boundary scanning."""
    tokens = _extract_tokens(text)
    padded = _normalize_padded(text)
    lang_key = "hi" if language == "hi" else "en"

    for intent_name in PRIORITIZED_INTENTS:
        intent_data = CANNED_RESPONSES.get(intent_name)
        if not intent_data:
            continue
        for kw in intent_data["keywords"]:
            kw_norm = kw.strip().lower()
            if not kw_norm:
                continue

            matched = False
            if " " in kw_norm:
                # Multi-word phrase: match as space-bounded subphrase
                matched = f" {kw_norm} " in padded
            else:
                # Single token: exact token match (prevents false matches like 'ok' in 'book' or 'hi' in 'this')
                matched = kw_norm in tokens

            if matched:
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
