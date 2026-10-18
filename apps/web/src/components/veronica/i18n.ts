export interface VeronicaDictionary {
  assistantName: string;
  assistantTitle: string;
  onlineBadge: string;
  welcomeMessage: string;
  disclaimer: string;
  inputPlaceholder: string;
  sendButtonLabel: string;
  clearChatTitle: string;
  closePanelTitle: string;
  toggleLangTitle: string;
  copiedTooltip: string;
  copyCode: string;
  emergencyNotice: string;
  sampleChips: string[];
  errorFallback: string;
  typingIndicator: string;
}

export const VERONICA_STRINGS: Record<"en" | "hi", VeronicaDictionary> = {
  en: {
    assistantName: "Veronica",
    assistantTitle: "VERA Platform Guide & Fraud Assistant",
    onlineBadge: "Online • 24/7 Guide",
    welcomeMessage:
      "Hello! I am **Veronica**, your VERA fraud safety assistant. I can guide you on spotting WhatsApp scams, checking SEBI registrations, or testing URLs and APKs in our forensic scanner.\n\nHow can I help you stay safe today?",
    disclaimer: "Platform guidance only. Not financial or investment advice. Call 1930 for urgent cyber fraud.",
    inputPlaceholder: "Ask Veronica about fraud detection or VERA...",
    sendButtonLabel: "Send message",
    clearChatTitle: "Clear conversation",
    closePanelTitle: "Close Veronica assistant",
    toggleLangTitle: "Switch to हिन्दी",
    copiedTooltip: "Copied to clipboard!",
    copyCode: "Copy",
    emergencyNotice: "Transferred money to a scammer? Dial 1930 immediately.",
    sampleChips: [
      "How do I check a suspicious WhatsApp group?",
      "How does VERA verify SEBI registration?",
      "I already sent money. What do I do? 🚨",
      "Can VERA detect deepfake videos?",
    ],
    errorFallback: "Veronica is currently experiencing high inquiry volume. Please use the main scanner or call 1930.",
    typingIndicator: "Veronica is thinking...",
  },
  hi: {
    assistantName: "वेरोनिका",
    assistantTitle: "VERA प्लेटफॉर्म गाइड एवं सुरक्षा सहायक",
    onlineBadge: "ऑनलाइन • 24/7 मार्गदर्शक",
    welcomeMessage:
      "नमस्ते! मैं **वेरोनिका** हूँ, VERA की एआई सुरक्षा सहायक। मैं आपको डिजिटल वित्तीय धोखाधड़ी से बचने, व्हाट्सएप घोटालों की पहचान करने और सेबी (SEBI) सत्यापन में सहायता कर सकती हूँ।\n\nआज मैं आपकी क्या मदद कर सकती हूँ?",
    disclaimer: "केवल प्लेटफॉर्म मार्गदर्शन हेतु। कोई वित्तीय या निवेश सलाह नहीं। आपातकाल में 1930 पर कॉल करें।",
    inputPlaceholder: "वेरोनिका से धोखाधड़ी की पहचान या VERA के बारे में पूछें...",
    sendButtonLabel: "संदेश भेजें",
    clearChatTitle: "बातचीत साफ़ करें",
    closePanelTitle: "वेरोनिका बंद करें",
    toggleLangTitle: "Switch to English",
    copiedTooltip: "कॉपी हो गया!",
    copyCode: "कॉपी करें",
    emergencyNotice: "पैसे कट गए हैं? तुरंत 1930 पर कॉल करें।",
    sampleChips: [
      "संदिग्ध व्हाट्सएप ग्रुप की जांच कैसे करें?",
      "क्या VERA सेबी (SEBI) रजिस्ट्रेशन चेक करता है?",
      "मैंने पैसे भेज दिए हैं, मुझे क्या करना चाहिए? 🚨",
      "डीपफेक वीडियो की पहचान कैसे करें?",
    ],
    errorFallback: "वेरोनिका पर इस समय अधिक लोड है। कृपया मुख्य स्कैनर का उपयोग करें या 1930 पर संपर्क करें।",
    typingIndicator: "वेरोनिका लिख रही है...",
  },
};
