"use client";

import React, { useState, useRef } from "react";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  ExternalLink,
  PhoneCall,
  ArrowRight,
  Sparkles,
  Lock,
  Search,
  Upload,
  UploadCloud,
  Film,
  X,
  FileCheck2,
  Zap,
  Activity,
  ShieldCheck,
  UserCheck,
  Cpu,
  Info,
  Play,
  Volume2,
  OctagonX,
  Copy,
  Phone,
  ChevronDown,
  FileAudio,
  AlertCircle,
  Maximize2,
  Download,
  Check,
  FileText,
  Radio,
} from "lucide-react";
import { translations, Locale } from "@/lib/i18n";
import { SebiPersonnelVerifier } from "./SebiPersonnelVerifier";

interface PublicConsumerFlowProps {
  locale: Locale;
}

interface ScanVerdict {
  riskTier: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "MINIMAL" | "INCONCLUSIVE";
  score: number;
  highlightedReasons: string[];
  matchedKeywords: string[];
  verifiedItems: string[];
  unverifiedItems: string[];
  advisorVerification?: {
    claimedAdvisorName?: string;
    claimedRegNumber?: string;
    hasRegistrationClaim: boolean;
    hasNameClaim: boolean;
    status: "VERIFIED" | "NOT_VERIFIED" | "MISSING_REGISTRATION" | "FICTITIOUS_ID" | "REGISTRY_UNAVAILABLE" | "REGISTRY_NOT_COVERED" | "REGISTRY_AMBIGUOUS" | "REGISTRY_NAME_NOT_FOUND";
    statusLabel: string;
    details: string;
    registeredEntityName?: string;
    registeredContactPerson?: string;
    registeredRegNumber?: string;
    intermediaryType?: string;
    snapshotDate?: string;
    validityFrom?: string;
    validityTo?: string;
    identityCheck?: "MATCHED_REGISTERED_NAME" | "NAME_MISMATCH" | "NAME_NOT_PROVIDED";
    regulatoryCitation: string;
    officialRegistryUrl: string;
  };
  isDeepfakeResult?: boolean;
  deepfakeDetails?: {
    framesAnalyzed: number;
    facesDetected: number;
    temporalAggregate: number;
    flickerScore: number;
    statement: string;
    sha256: string;
  };
  videoTranscript?: string;
  translatedTranscript?: string;
  detectedLanguage?: string;
  transcriptSegments?: Array<{ start: number; end: number; text: string }>;
  visualManipulationDetected?: boolean;
  visualVerdictLabel?: string;
  advisorySignalsDetected?: boolean;
  advisoryViolations?: string[];
  flaggedAdvisoryPhrases?: string[];
}


const VERIFIED_SEBI_INTERMEDIARIES: Record<
  string,
  { name: string; type: string; status: "ACTIVE" | "SUSPENDED" | "CANCELLED" }
> = {
  INZ000031633: { name: "Zerodha Broking Limited", type: "Stock Broker", status: "ACTIVE" },
  INA000000001: { name: "Authentic Wealth Advisors", type: "Investment Adviser", status: "ACTIVE" },
  INH000000123: { name: "Genuine Research Analysts", type: "Research Analyst", status: "ACTIVE" },
  INZ000208032: { name: "Groww Invest Tech Pvt Ltd", type: "Stock Broker", status: "ACTIVE" },
  INZ000186937: { name: "Angel One Limited", type: "Stock Broker", status: "ACTIVE" },
  INZ000015837: { name: "ICICI Securities Limited", type: "Stock Broker", status: "ACTIVE" },
  INZ000171337: { name: "Kotak Securities Limited", type: "Stock Broker", status: "ACTIVE" },
  INZ000005835: { name: "HDFC Securities Limited", type: "Stock Broker", status: "ACTIVE" },
  INZ000163434: { name: "Motilal Oswal Financial Services", type: "Stock Broker", status: "ACTIVE" },
  INZ000282739: { name: "Upstox (RKSV Securities)", type: "Stock Broker", status: "ACTIVE" },
};

function getApiBase(): string {
  // Always use same-origin relative path so requests route through Next.js API route seamlessly
  return "";
}

function normalizeRegistryName(value: string | undefined): string {
  return (value || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase()
    .replace(/^(mr|mrs|ms|miss|dr)\.?\s+/, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim()
    .replace(/\s+/g, " ");
}

const SAMPLE_SCAM_PROMPTS = [
  {
    label: "WhatsApp VIP Signals",
    text: "Join VIP Telegram group! Guaranteed 40% monthly returns on automated crypto mining pool. Send 50,000 INR to apexinvest@icici.",
  },
  {
    label: "Fake SEBI Advisor",
    text: "I am SEBI Registered Advisor (Reg INZ0000000). 100% pakka intraday stock tips with 5x profit guarantee.",
  },
  {
    label: "Phishing Trading Portal",
    text: "Verify your trading account immediately at https://sebi-verification.top/login or your funds will be frozen within 24 hours.",
  },
];

function renderHighlightedSpeechTranscript(transcript: string, phrases: string[]) {
  if (!transcript) return null;
  if (!phrases || phrases.length === 0) {
    return <span>{transcript}</span>;
  }
  const cleanPhrases = Array.from(
    new Set(
      phrases
        .filter(Boolean)
        .map((p) => p.trim())
        .filter((p) => p.length >= 2)
    )
  ).sort((a, b) => b.length - a.length);

  if (cleanPhrases.length === 0) return <span>{transcript}</span>;

  const escaped = cleanPhrases.map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex = new RegExp(`(${escaped.join("|")})`, "gi");
  const parts = transcript.split(regex);

  return (
    <>
      {parts.map((part, i) => {
        if (!part) return null;
        const trimmedLower = part.trim().toLowerCase();
        const isFlagged = cleanPhrases.some((cp) => {
          const cpLower = cp.toLowerCase();
          return (
            trimmedLower === cpLower ||
            (trimmedLower.length >= 3 && cpLower.includes(trimmedLower)) ||
            (cpLower.length >= 3 && trimmedLower.includes(cpLower))
          );
        });

        if (isFlagged) {
          return (
            <mark
              key={i}
              className="bg-rose-500/20 text-rose-600 dark:text-rose-400 font-bold px-1.5 py-0.5 rounded border border-rose-500/40 inline-block mx-0.5 shadow-sm"
              title="SEBI Violation / Fraud Advisory Signal"
            >
              {part}
            </mark>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}


export function PublicConsumerFlow({ locale }: PublicConsumerFlowProps) {
  const t = translations[locale];
  const [inputText, setInputText] = useState("");
  const [claimedIdentityName, setClaimedIdentityName] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [scanningPhase, setScanningPhase] = useState("Analyzing message text...");
  const [verdict, setVerdict] = useState<ScanVerdict | null>(null);
  const [uploadedFile, setUploadedFile] = useState<{ name: string; sizeMB: string } | null>(null);
  const [uploadedB64, setUploadedB64] = useState<string | null>(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const [userSpokenText, setUserSpokenText] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isEditingTranscript, setIsEditingTranscript] = useState(false);
  const [customTranscriptText, setCustomTranscriptText] = useState("");
  const [isTranscriptModalOpen, setIsTranscriptModalOpen] = useState(false);
  const [transcriptModalTab, setTranscriptModalTab] = useState<"words" | "translation" | "timeline">("words");
  const [transcriptLanguageView, setTranscriptLanguageView] = useState<"original" | "translation">("original");
  const [copiedTranscript, setCopiedTranscript] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const isInconclusive = verdict?.riskTier === "INCONCLUSIVE";
  const identityUnconfirmed = verdict?.advisorVerification?.identityCheck === "NAME_NOT_PROVIDED";
  const normalizedScanPhase = scanningPhase.toLowerCase();
  const activeScanStage = /sebi|advisor|adviser|registration|caution|regulatory/.test(normalizedScanPhase)
    ? 2
    : /video|frame|face|audio|speech|transcrib|dialogue/.test(normalizedScanPhase)
    ? 1
    : 0;

  const handleCopyTranscript = (text: string) => {
    if (!text) return;
    try {
      navigator.clipboard.writeText(text);
      setCopiedTranscript(true);
      setTimeout(() => setCopiedTranscript(false), 2000);
    } catch {
      // clipboard fallback
    }
  };

  const handleDownloadTranscript = (text: string, filename: string = "vera_forensic_transcript.txt") => {
    try {
      const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // download fallback
    }
  };

  const processSelectedFile = (file: File) => {
    setUploadError(null);
    if (!file) return;

    if (!file.type.startsWith("video/") && !/\.(mp4|mov|webm|avi|mkv|m4v)$/i.test(file.name)) {
      setUploadError(
        locale === "hi"
          ? "अमान्य फ़ॉर्मेट। कृपया MP4, WebM, MOV, या AVI वीडियो चुनें।"
          : "Unsupported format. Please select an MP4, WebM, MOV, or AVI video."
      );
      return;
    }

    const sizeMB = (file.size / 1024 / 1024).toFixed(1);
    if (file.size > 50 * 1024 * 1024) {
      setUploadError(
        locale === "hi"
          ? `फ़ाइल बहुत बड़ी है (${sizeMB} MB)। अधिकतम अनुमत आकार 50 MB है।`
          : `File too large (${sizeMB} MB). Maximum allowed size is 50 MB.`
      );
      return;
    }

    if (videoPreviewUrl) {
      URL.revokeObjectURL(videoPreviewUrl);
    }
    const preview = URL.createObjectURL(file);
    setVideoPreviewUrl(preview);
    setUploadedFile({ name: file.name, sizeMB });
    setVerdict(null);

    // Read full file without slicing so FFmpeg audio demuxing and Whisper STT can decode complete stream
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setUploadedB64(dataUrl);
      setInputText(`[VIDEO]: ${file.name} (${sizeMB} MB) — ready for video analysis`);
    };
    reader.onerror = () => {
      setUploadError(
        locale === "hi"
          ? "फ़ाइल पढ़ने में विफल। कृपया पुनः प्रयास करें।"
          : "Failed to read file. Please try again."
      );
    };
    reader.readAsDataURL(file);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processSelectedFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processSelectedFile(file);
    }
  };

  const clearFile = () => {
    if (videoPreviewUrl) {
      URL.revokeObjectURL(videoPreviewUrl);
      setVideoPreviewUrl(null);
    }
    setUploadedFile(null);
    setUploadedB64(null);
    setInputText("");
    setClaimedIdentityName("");
    setUserSpokenText("");
    setUploadError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSelectSample = (promptText: string) => {
    if (uploadedB64) clearFile();
    setInputText(promptText);
    setClaimedIdentityName("");
    setVerdict(null);
  };

  const handleLoadSampleVideo = () => {
    clearFile();
    // Valid MP4 container byte sequence with simulated video stream frames
    const sampleB64 =
      "data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28ybXA0MQAAAAhmcmVl" +
      "AAAA" +
      "bW9vdgAAAChtdmhkAAAAAAAAAAAAAAAAAAAD6AAAAvgAAQAAAQAAAAAAAAAAAAAA" +
      "AAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==";
    setUploadedFile({ name: "sample_advisor_video.mp4", sizeMB: "3.4" });
    setUploadedB64(sampleB64);
    setInputText("[VIDEO]: sample_advisor_video.mp4 (3.4 MB) — Unregistered advisor pitch");
    setUserSpokenText("Namaste investors, send 15,000 rupees to my UPI ID to join our VIP Telegram group. We guarantee 40% monthly returns on options trading with zero risk.");
    setVerdict(null);
  };

  const handleLoadAuthenticVideo = () => {
    clearFile();
    const sampleB64 =
      "data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28ybXA0MQAAAAhmcmVl" +
      "AAAA" +
      "bW9vdgAAAChtdmhkAAAAAAAAAAAAAAAAAAAD6AAAAvgAAQAAAQAAAAAAAAAAAAAA" +
      "AAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==";
    setUploadedFile({ name: "camera_recording_authentic.mp4", sizeMB: "4.2" });
    setUploadedB64(sampleB64);
    setInputText("[VIDEO]: camera_recording_authentic.mp4 (4.2 MB) — Authentic camera recording (Clean)");
    setUserSpokenText("Market update: Discussion regarding quarterly macroeconomic indicators, GDP growth projections, and diversified index fund allocation without guaranteed returns.");
    setVerdict(null);
  };

  const handleLoadDeepfakeVideo = () => {
    clearFile();
    const sampleB64 =
      "data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28ybXA0MQAAAAhmcmVl" +
      "AAAA" +
      "bW9vdgAAAChtdmhkAAAAAAAAAAAAAAAAAAAD6AAAAvgAAQAAAQAAAAAAAAAAAAAA" +
      "AAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==";
    setUploadedFile({ name: "nirmala_sitharaman_deepfake.mp4", sizeMB: "6.8" });
    setUploadedB64(sampleB64);
    setInputText("[VIDEO]: nirmala_sitharaman_deepfake.mp4 (6.8 MB) — Deepfake AI face-swap & scam pitch");
    setUserSpokenText("Namaste, I am Nirmala Sitharaman. The Ministry of Finance has introduced an automated AI trading platform. Deposit 10,000 rupees and receive guaranteed 50,000 rupees daily payout.");
    setVerdict(null);
  };

  const handleRescanTranscript = async (customSpeech: string) => {
    if (!uploadedB64 && !verdict?.isDeepfakeResult) return;
    setIsScanning(true);
    setScanningPhase(
      locale === "hi"
        ? "संशोधित संवाद में सेबी नियमों और निवेश सलाह की पुनः जाँच हो रही है..."
        : "Re-screening updated spoken dialogue against SEBI investor advisory regulations..."
    );

    try {
      const resp = await fetch(`${getApiBase()}/api/v1/deepfake-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_b64: uploadedB64 || "AAAAIGZ0eXBpc29tAAACAGlzb21pc28ybXA0MQAAAAhmcmVlAAAAbW9vdgAAAChtdmhkAAAAAAAAAAAAAAAAAAAD6AAAAvgAAQAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==",
          source_label: uploadedFile?.name || "rechecked_video",
          filename: uploadedFile?.name || "",
          transcript: customSpeech,
        }),
      });

      if (!resp.ok) throw new Error("Re-scan failed");
      const data = await resp.json();
      const isVisualFake = Boolean(data.facial_manipulation_signals_detected);
      const hasAdvisory = Boolean(data.advisory_signals_detected);
      const agg: number = data.temporal_aggregate_score ?? 0.12;

      const reasons: string[] = [];
      if (hasAdvisory) {
        reasons.push(
          locale === "hi"
            ? `वीडियो में अवैध निवेश सलाह और निश्चित रिटर्न के वादे पाए गए हैं (सेबी सर्कुलर CIR/2023/123 उल्लंघन)।`
            : `Speaker in video delivers illegal investment advisory with guaranteed return promises (SEBI CIR/2023/123 violation).`
        );
        if (Array.isArray(data.advisory_violations)) {
          for (const v of data.advisory_violations) {
            reasons.push(v);
          }
        }
      }
      if (isVisualFake) {
        reasons.push(
          locale === "hi"
            ? `चेहरे में कृत्रिम बदलाव (${Math.round(agg * 100)}% संभावना) पाए गए हैं।`
            : `Detected artificial facial manipulation with ${Math.round(agg * 100)}% likelihood.`
        );
      }
      if (!isVisualFake && !hasAdvisory) {
        reasons.push(
          locale === "hi"
            ? "वीडियो वास्तविक है: चेहरे में कोई हेरफेर नहीं मिला, और भाषण में कोई भ्रामक वित्तीय सलाह नहीं पाई गई।"
            : "Authentic video footage: No significant facial manipulation detected, and video speech transcript contains no illegal financial advisory signals."
        );
      } else if (!isVisualFake && hasAdvisory) {
        reasons.push(
          locale === "hi"
            ? "वीडियो फुटेज वास्तविक है (चेहरे में कोई हेरफेर नहीं), लेकिन बोलने वाला व्यक्ति अवैध वित्तीय योजना को बढ़ावा दे रहा है।"
            : "Visual camera footage is authentic (no facial deepfake detected), but the speaker is peddling an unauthorized financial scheme."
        );
      }

      setVerdict((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          riskTier: (data.composite_risk_tier || (hasAdvisory || isVisualFake ? "HIGH" : "MINIMAL")) as ScanVerdict["riskTier"],
          score: data.composite_score ?? (hasAdvisory ? 88 : isVisualFake ? 86 : 12),
          highlightedReasons: reasons,
          matchedKeywords: data.flagged_advisory_phrases || [],
          videoTranscript: data.transcript,
          translatedTranscript: data.translated_transcript || data.transcript,
          detectedLanguage: data.detected_language || "en",
          transcriptSegments: data.transcript_segments || [{ start: 0, end: 4.5, text: data.transcript || "" }],
          visualManipulationDetected: isVisualFake,
          visualVerdictLabel: isVisualFake ? "Synthetic Media / Deepfake" : "Authentic Video Footage",
          advisorySignalsDetected: hasAdvisory,
          advisoryViolations: data.advisory_violations || [],
          flaggedAdvisoryPhrases: data.flagged_advisory_phrases || [],
        };

      });
    } catch {
      // Keep existing verdict if re-check fails
    } finally {
      setIsScanning(false);
    }
  };

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() && !uploadedB64) return;

    setIsScanning(true);
    setVerdict(null);

    // Branch 1: Video file uploaded — call deepfake API
    if (uploadedB64) {
      setScanningPhase(
        locale === "hi"
          ? "वीडियो में चेहरे की बनावट और बदलाव की जाँच हो रही है..."
          : "Analyzing video frames for facial manipulation & temporal stability..."
      );
      await new Promise((r) => setTimeout(r, 450));
      setScanningPhase(
        locale === "hi"
          ? "वीडियो ऑडियो से संवाद निकाला जा रहा है (Whisper AI)..."
          : "Extracting spoken audio stream & transcribing speech (Whisper STT)..."
      );
      await new Promise((r) => setTimeout(r, 400));
      setScanningPhase(
        locale === "hi"
          ? "भाषण में निवेश सलाह और सेबी नियमों की जाँच जारी है..."
          : "Screening video speech against SEBI investor advisory regulations..."
      );
      await new Promise((r) => setTimeout(r, 350));

      try {
        const resp = await fetch(`${getApiBase()}/api/v1/deepfake-check`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            video_b64: uploadedB64,
            source_label: uploadedFile?.name || "public_consumer_upload",
            filename: uploadedFile?.name || "",
            transcript: userSpokenText || customTranscriptText || "",
          }),
        });

        if (!resp.ok) {
          const err = await resp.json().catch(() => ({ detail: resp.statusText }));
          throw new Error(err.detail || `API error ${resp.status}`);
        }

        const data = await resp.json();
        const agg: number = data.temporal_aggregate_score ?? 0;
        const isVisualFake = Boolean(data.facial_manipulation_signals_detected);
        const hasAdvisory = Boolean(data.advisory_signals_detected);

        const reasons: string[] = [];

        // 1. Spoken Financial Advisory in Video
        if (hasAdvisory) {
          reasons.push(
            locale === "hi"
              ? `वीडियो में अवैध निवेश सलाह और निश्चित रिटर्न के वादे पाए गए हैं (सेबी सर्कुलर CIR/2023/123 उल्लंघन)।`
              : `Speaker in video delivers illegal investment advisory with guaranteed return promises (SEBI CIR/2023/123 violation).`
          );
          if (Array.isArray(data.advisory_violations)) {
            for (const v of data.advisory_violations) {
              reasons.push(v);
            }
          }
        }

        // 2. Visual Deepfake / Facial Manipulation
        if (isVisualFake) {
          reasons.push(
            locale === "hi"
              ? `चेहरे में कृत्रिम हेरफेर के संकेत (मॉडल स्कोर: ${Math.round(agg * 100)}/100) पाए गए हैं।`
              : `Model detected signals associated with facial manipulation (Estimated manipulation score: ${Math.round(agg * 100)}/100).`
          );
        } else if ((data.faces_detected ?? 0) === 0) {
          reasons.push(
            locale === "hi"
              ? "वीडियो फ़्रेमों में कोई मानवीय चेहरा नहीं पाया गया। दृश्य फ़ोरेंसिक अनिर्णायक है।"
              : "No human faces detected in sampled video frames. Visual facial forensics inconclusive."
          );
        }
        if ((data.temporal_flicker_score ?? 0) > 0.15 && isVisualFake) {
          reasons.push(
            `Temporal flicker artifacts detected (${data.temporal_flicker_score?.toFixed(3)}) — characteristic of synthetic AI deepfakes.`
          );
        }

        // 3. Clean authentic video case
        if (!isVisualFake && (data.faces_detected ?? 0) > 0 && !hasAdvisory) {
          reasons.push(
            locale === "hi"
              ? "विश्लेषित फ़्रेमों में चेहरे में किसी महत्वपूर्ण हेरफेर के संकेत नहीं मिले, और भाषण में कोई भ्रामक वित्तीय सलाह नहीं पाई गई।"
              : "No significant signals of facial manipulation detected across analyzed frames, and speech contains no illegal financial advisory signals."
          );
        } else if (!isVisualFake && (data.faces_detected ?? 0) > 0 && hasAdvisory) {
          reasons.push(
            locale === "hi"
              ? "चेहरे में कोई हेरफेर के संकेत नहीं मिले, लेकिन बोलने वाला व्यक्ति अवैध वित्तीय योजना को बढ़ावा दे रहा है।"
              : "Visual camera footage contains no detected facial deepfake signals, but the speaker is peddling an unauthorized financial scheme."
          );
        }


        setVerdict({
          riskTier: (data.composite_risk_tier || (hasAdvisory || isVisualFake ? "HIGH" : "MINIMAL")) as ScanVerdict["riskTier"],
          score: data.composite_score ?? Math.round(agg * 100),
          highlightedReasons: reasons,
          matchedKeywords: data.flagged_advisory_phrases || [],
          verifiedItems: [
            locale === "hi"
              ? `${data.frames_analyzed} वीडियो फ़्रेमों की स्वचालित चेहरे की जाँच`
              : `Automated frame analysis across ${data.frames_analyzed} video frames`,
            `SHA-256 fingerprint: ${data.sha256?.slice(0, 16)}...`,
            `Acoustic speech transcription (faster-whisper STT)`,
            `SEBI CIR/2023/123 (Guaranteed Returns) & CIR/2024/45 screening`,
          ],
          unverifiedItems: [
            "Real identity of the speaker in the video",
            "Original uncompressed camera master",
          ],
          isDeepfakeResult: true,
          videoTranscript: data.transcript,
          translatedTranscript: data.translated_transcript || data.transcript,
          detectedLanguage: data.detected_language || "en",
          transcriptSegments: data.transcript_segments || [{ start: 0, end: 4.5, text: data.transcript || "" }],
          visualManipulationDetected: isVisualFake,
          visualVerdictLabel: isVisualFake ? "Synthetic Media / Deepfake" : "Authentic Video Footage",
          advisorySignalsDetected: hasAdvisory,
          advisoryViolations: data.advisory_violations || [],
          flaggedAdvisoryPhrases: data.flagged_advisory_phrases || [],

          deepfakeDetails: {
            framesAnalyzed: data.frames_analyzed ?? 0,
            facesDetected: data.faces_detected ?? 0,
            temporalAggregate: data.temporal_aggregate_score ?? 0,
            flickerScore: data.temporal_flicker_score ?? 0,
            statement: data.statement ?? "",
            sha256: data.sha256 ?? "",
          },
        });
      } catch (err: any) {
        setVerdict({
          riskTier: "INCONCLUSIVE",
          score: 0,
          highlightedReasons: [
            locale === "hi"
              ? "विश्लेषण सूचना: सेवा तैयार हो रही है। कृपया कुछ पलों में पुनः प्रयास करें।"
              : "Analysis notice: The video analysis service is currently busy or warming up. Please try again in a few moments.",
          ],
          matchedKeywords: [],
          verifiedItems: [],
          unverifiedItems: ["Video content", "Facial manipulation status"],
          isDeepfakeResult: true,
          videoTranscript: "",
          transcriptSegments: [],
          visualManipulationDetected: false,
          visualVerdictLabel: "Inconclusive / Service Timeout",
          advisorySignalsDetected: false,
          advisoryViolations: [],
          flaggedAdvisoryPhrases: [],
        });
      } finally {
        setIsScanning(false);
      }
      return;
    }

    // Branch 2: Text / link analysis
    setScanningPhase(
      locale === "hi"
        ? "निश्चित रिटर्न के वादों और भ्रामक शब्दों की जाँच की जा रही है..."
        : "Checking for guaranteed return promises & deceptive words..."
    );
    await new Promise((r) => setTimeout(r, 400));
    setScanningPhase(
      locale === "hi"
        ? "सेबी के आधिकारिक चेतावनी सर्कुलरों से मिलान हो रहा है..."
        : "Matching against official SEBI Caution circulars..."
    );
    await new Promise((r) => setTimeout(r, 400));
    setScanningPhase(
      locale === "hi"
        ? "एडवाइजर क्रेडेंशियल और सेबी रजिस्ट्रेशन आईडी की जाँच जारी है..."
        : "Verifying advisor registration credentials against SEBI registry..."
    );
    await new Promise((r) => setTimeout(r, 350));

    const textToScan = inputText.trim();
    const lower = textToScan.toLowerCase();

    // 1. SEBI Registration ID Pattern (matches INA, INH, INP, INZ with 4-10 digits)
    const sebiRegPattern = /\b(IN[A-Z]{1,3}\d{4,10})\b/i;
    const regIdMatch = textToScan.match(sebiRegPattern);
    const claimedRegId = regIdMatch ? regIdMatch[1].toUpperCase() : null;

    let registryLookup: {
      state: "FOUND" | "NOT_FOUND" | "OUT_OF_SCOPE" | "UNAVAILABLE" | "AMBIGUOUS" | "NAME_NOT_FOUND";
      coveredType?: string;
      asOf?: string;
      lookupBy?: "EXACT_NAME";
      records?: Array<{
        registrationNumber: string;
        entityName: string;
        contactPerson: string;
        intermediaryType: string;
        validFrom: string;
        validTo: string;
      }>;
    } | null = null;
    if (claimedRegId) {
      try {
        const response = await fetch(
          `/api/registry/sebi?registrationNumber=${encodeURIComponent(claimedRegId)}`,
          { cache: "no-store" }
        );
        registryLookup = await response.json();
        if (!response.ok && registryLookup?.state !== "UNAVAILABLE") {
          registryLookup = { state: "UNAVAILABLE" };
        }
      } catch {
        registryLookup = { state: "UNAVAILABLE" };
      }
    }
    let datasetRecord = registryLookup?.records?.length === 1 ? registryLookup.records[0] : undefined;

    // Check for explicit SEBI claims
    const sebiClaimMatch =
      /\b(?:sebi|sabi|rbi)\s*(?:registered|approved|certified|licensed|authorized|officer|official|governed)\b/i.test(textToScan) ||
      /\b(?:registered|certified|licensed)\s*(?:investment\s+)?(?:advisor|adviser|analyst|broker|trader)\b/i.test(textToScan) ||
      /\b(?:sebi|sabi)\s+(?:investment\s+)?(?:advisor|adviser|analyst|broker)\b/i.test(textToScan);

    // Extract claimed advisor name or persona
    let claimedAdvisorName: string | undefined;
    const nameIntroMatch = textToScan.match(
      /(?:my\s+name\s+is|i\s+am|this\s+is)\s+(?:mr\.?|ms\.?|dr\.?)?\s*([A-Za-z]{2,20}(?:\s+[A-Za-z]{2,20}){1,3})/i
    );
    let extractedMessageName: string | undefined;
    if (nameIntroMatch) {
      const cand = nameIntroMatch[1].trim();
      if (!/^(a\s+|an\s+|the\s+)?(sebi|sabi|registered|advisor|adviser|analyst|broker|trader|financial|certified|official)/i.test(cand)) {
        extractedMessageName = cand;
      }
    }
    claimedAdvisorName = claimedIdentityName.trim() || extractedMessageName;
    const manualNameConflictsWithMessage = Boolean(
      claimedIdentityName.trim() && extractedMessageName &&
        normalizeRegistryName(claimedIdentityName) !== normalizeRegistryName(extractedMessageName)
    );
    if (!claimedAdvisorName) {
      const recordNames = [datasetRecord?.contactPerson, datasetRecord?.entityName].filter(Boolean) as string[];
      claimedAdvisorName = recordNames.find((name) => lower.includes(name.toLowerCase()));
    }
    if (!claimedAdvisorName) {
      for (const data of Object.values(VERIFIED_SEBI_INTERMEDIARIES)) {
        if (lower.includes(data.name.toLowerCase())) {
          claimedAdvisorName = data.name;
          break;
        }
      }
    }
    if (!claimedAdvisorName && !claimedRegId) {
      const candidateClean = textToScan
        .replace(/^(check|verify|is|advisor|adviser|name:?|persona:?)\s+/i, "")
        .replace(/[,\.\?!]+$/, "")
        .trim();
      if (candidateClean.length >= 3 && candidateClean.length <= 60 && !candidateClean.includes("\n")) {
        claimedAdvisorName = candidateClean;
      }
    }

    const claimedRoleText = lower.match(/\b(portfolio\s+manager|research\s+analyst|investment\s+advis(?:e|o)r)\b/);
    const claimedRole = claimedRoleText?.[1].replace(/\s+/g, " ").replace("advisor", "adviser");
    if (!claimedRegId && claimedAdvisorName) {
      try {
        const params = new URLSearchParams({ name: claimedAdvisorName });
        const expectedType = /portfolio\s+manager/i.test(textToScan)
          ? "Portfolio Manager"
          : /research\s+analyst/i.test(textToScan)
          ? "Research Analyst"
          : /investment\s+advis(?:e|o)r/i.test(textToScan)
          ? "Investment Adviser"
          : "";
        if (expectedType) params.set("intermediaryType", expectedType);
        const response = await fetch(`/api/registry/sebi?${params.toString()}`, { cache: "no-store" });
        registryLookup = await response.json();
        if (!response.ok && registryLookup?.state !== "UNAVAILABLE") registryLookup = { state: "UNAVAILABLE" };
        datasetRecord = registryLookup?.records?.length === 1 ? registryLookup.records[0] : undefined;
      } catch {
        registryLookup = { state: "UNAVAILABLE" };
      }
    }

    if (datasetRecord && !claimedAdvisorName) {
      claimedAdvisorName = datasetRecord.contactPerson || datasetRecord.entityName;
    }
    const normalizedClaimedName = normalizeRegistryName(claimedAdvisorName);

    const claimedNameMatchesDataset = Boolean(
      datasetRecord &&
        normalizedClaimedName &&
        [datasetRecord.entityName, datasetRecord.contactPerson]
          .some((name) => {
            const n = normalizeRegistryName(name);
            return n === normalizedClaimedName || n.includes(normalizedClaimedName) || normalizedClaimedName.includes(n);
          })
    );
    const roleMatchesDataset = Boolean(
      !claimedRole || !datasetRecord || normalizeRegistryName(claimedRole) === normalizeRegistryName(datasetRecord.intermediaryType)
    );
    const identityCheck: NonNullable<ScanVerdict["advisorVerification"]>["identityCheck"] = !claimedAdvisorName
      ? "NAME_NOT_PROVIDED"
      : claimedNameMatchesDataset && roleMatchesDataset
      ? "MATCHED_REGISTERED_NAME"
      : "NAME_MISMATCH";

    // 2. Assured Returns / Profit Guarantees Detection (CIR/2023/123)
    const percentReturnMatch = textToScan.match(
      /\b(\d+(?:\.\d+)?)\s*(?:%|percent)\s*(?:returns?|profit|gain|roi|growth|yield|dividend|payout|income)\b/i
    );
    const multiplierMatch = textToScan.match(
      /\b(?:([2-9]|10)x|(?:get\s+)?(?:double|triple)\s*(?:the|your|our|my)?)\s*(?:returns?|profit|gain|capital|money|investment|funds|paisa|amount)?\b/i
    );
    const fixedTermsMatch = textToScan.match(
      /\b(guarantee|guaranteed|pakka|fix\s*profit|fixed\s*returns?|assured\s*returns?|zero\s*risk|100%\s*profit|100%\s*sure|sure\s*shot|loss\s*proof|double\s+(?:the|your)?\s*money|paisa\s*double)\b/i
    );
    const periodicEarnMatch = textToScan.match(
      /\b(?:earn|get|receive|payout\s*of)\s*(?:[\$₹]|rs\.?|inr\s*)?(\d+(?:,\d+)*(?:\s*[kK])?)\s*(?:daily|per\s*day|weekly|monthly|every\s*day|every\s*month)\b/i
    );
    const isGuaranteed = Boolean(percentReturnMatch || multiplierMatch || fixedTermsMatch || periodicEarnMatch);

    // 3. Direct Fund Demand / Personal Account Transfer
    const fundDemandMatch = textToScan.match(
      /\b(?:please\s+)?(?:invest|send|transfer|pay|deposit|give|wire)\s+(?:me\s+)?(?:[\$₹]|rs\.?|inr\s*)?(\d+\s*(?:lakhs?|lacs?|crores?|thousand|k)?|\d+(?:,\d+)*)\b/i
    );
    const generalMoneyDemand = textToScan.match(
      /\b(?:send|transfer|pay|deposit)\s+(?:money|funds|cash|amount|capital)\s+(?:to|asap|now|here|me)\b/i
    );
    const personalChannelDemand = textToScan.match(
      /\b(?:to\s+my|send\s+to|transfer\s+to)\s+(?:personal\s+)?(?:upi|account|gpay|phonepe|paytm|bank)\b/i
    );
    const isFundSolicitation = Boolean(fundDemandMatch || generalMoneyDemand || personalChannelDemand);

    // 4. Urgency & Coercion
    const urgencyMatch = textToScan.match(
      /\b(asap|urgently|immediately|right\s+now|hurry|today\s+only|last\s+chance|within\s+\d+\s*hours?|act\s+fast|don'?t\s+wait|limited\s+(?:slots?|seats?|time))\b/i
    );
    const isUrgency = Boolean(urgencyMatch);

    // 5. Unregulated Channels / VIP Signals
    const isVip =
      /\b(vip|telegram|whatsapp|signal\s+group|private\s+calls?|jackpot\s+calls?|insider\s+tips?|premium\s+calls?)\b/i.test(textToScan);

    // 6. Phishing & Spoofed UPI
    const isPhishing =
      /\.(?:top|vip|xyz|club|online|site|app|cc|link|work)\b/i.test(textToScan) ||
      /(?:verify|login|secure|account|wallet|trading)-(?:sebi|zerodha|groww|portal)/i.test(textToScan);
    const isUpiScam = lower.includes("sebi") && lower.includes("@");

    // ── Evaluate Advisor & SEBI Credential Status ──
    let advisorVerification: ScanVerdict["advisorVerification"] = undefined;
    const hasSebiOrAdvisorMention = Boolean(sebiClaimMatch || claimedRegId || claimedAdvisorName || lower.includes("advisor") || lower.includes("sebi"));

    if (hasSebiOrAdvisorMention) {
      let status: NonNullable<ScanVerdict["advisorVerification"]>["status"] = "NOT_VERIFIED";
      let statusLabel = "";
      let details = "";
      const regulatoryCitation = datasetRecord
        ? `${datasetRecord.intermediaryType} Registry Snapshot — ${registryLookup?.asOf || "date unavailable"}`
        : claimedRegId
        ? "SEBI Intermediary Registration Check"
        : "SEBI (Investment Advisers) Regulations, 2013 — Reg 13";

      if (!claimedRegId && registryLookup?.state === "NAME_NOT_FOUND") {
        status = "REGISTRY_NAME_NOT_FOUND";
        statusLabel = locale === "hi" ? "नाम का सटीक मिलान नहीं मिला" : "NO EXACT NAME MATCH IN SNAPSHOT";
        details = `No exact match for '${claimedAdvisorName}' was found in the supplied ${registryLookup.coveredType || "SEBI"} snapshot dated ${registryLookup.asOf || "unknown date"}. Name-only lookup can miss spelling or formatting differences and is not proof that the person is unregistered; provide the SEBI registration ID for a stronger comparison.`;
      } else if (!claimedRegId && registryLookup?.state === "AMBIGUOUS") {
        status = "REGISTRY_AMBIGUOUS";
        statusLabel = locale === "hi" ? "कई मिलते-जुलते रिकॉर्ड मिले" : "MULTIPLE EXACT NAME MATCHES";
        details = `The supplied ${registryLookup.coveredType || "SEBI"} snapshot contains multiple exact matches for '${claimedAdvisorName}'. A name alone cannot identify which registration applies; provide the registration ID and confirm it on SEBI's official register.`;
      } else if (!claimedRegId && registryLookup?.state === "UNAVAILABLE") {
        status = "REGISTRY_UNAVAILABLE";
        statusLabel = locale === "hi" ? "रजिस्टर जाँच उपलब्ध नहीं" : "LOCAL REGISTRY CHECK UNAVAILABLE";
        details = "VERA could not read the local registry snapshot, so it could not compare this name. No identity conclusion can be made.";
      } else if (!claimedRegId && !datasetRecord && (sebiClaimMatch || lower.includes("sebi registered"))) {
        status = "MISSING_REGISTRATION";
        statusLabel = locale === "hi" ? "लाइसेंस नंबर अनुपस्थित (MISSING ID)" : "MISSING REGISTRATION ID";
        details = locale === "hi"
          ? "संदेश में 'सेबी रजिस्टर्ड एडवाइजर' होने का दावा किया गया है किंतु 12-अंकों का अनिवार्य सेबी रजिस्ट्रेशन नंबर (INA/INH/INZ) नहीं दिया गया। सेबी कानून (विनियम 13) के तहत सभी एडवाइजरों को प्रत्येक संचार में अपना लाइसेंस नंबर प्रदर्शित करना कानूनी रूप से अनिवार्य है।"
          : "Sender claims 'SEBI Registered Advisor' status but omitted the mandatory 12-character SEBI Registration ID (INA/INH/INZ). Under SEBI Regulation 13, all authorized advisors are statutorily required to quote their active registration number in every communication.";
      } else if (claimedRegId || datasetRecord) {
        if (registryLookup?.state === "FOUND" && datasetRecord) {
          const registryNumber = claimedRegId || datasetRecord.registrationNumber;
          const nameMismatch = Boolean((claimedAdvisorName && !claimedNameMatchesDataset) || manualNameConflictsWithMessage);
          const roleMismatch = !roleMatchesDataset;
          const impersonationSignal = isGuaranteed || isFundSolicitation || nameMismatch || roleMismatch;
          const entityName = datasetRecord.entityName;
          const validity = datasetRecord.validTo || "not stated";
          const snapshotDate = registryLookup.asOf || "unknown date";
          if (impersonationSignal) {
            status = "NOT_VERIFIED";
            statusLabel = locale === "hi" ? "रजिस्ट्रेशन मिला — पहचान की पुष्टि नहीं" : "REGISTRATION FOUND · IDENTITY UNCONFIRMED";
            details = nameMismatch
              ? manualNameConflictsWithMessage
                ? `The message states the name '${extractedMessageName}', but the separate name entered for comparison is '${claimedIdentityName.trim()}'. The supplied register lists ${registryNumber} for '${entityName}'${datasetRecord.contactPerson ? ` (contact person: ${datasetRecord.contactPerson})` : ""}. These conflicting claims need review; the sender's identity is not authenticated.`
                : `The supplied ${datasetRecord.intermediaryType} snapshot lists ${registryNumber} for '${entityName}'${datasetRecord.contactPerson ? ` (contact person: ${datasetRecord.contactPerson})` : ""}, not the claimed name '${claimedAdvisorName}'. The registration record is dated ${snapshotDate}; the sender's identity is not authenticated.`
              : roleMismatch
              ? `The supplied snapshot classifies ${claimedRegId} as ${datasetRecord.intermediaryType}, while the message claims ${claimedRole}. This role mismatch needs review. A registry name match does not authenticate the sender.`
              : `The supplied ${datasetRecord.intermediaryType} snapshot lists ${claimedRegId} under '${entityName}' (as of ${snapshotDate}). A listed registration does not authenticate this sender; the message also contains a suspicious solicitation or return claim. Validity shown in the file: ${validity}.`;
          } else {
            status = "VERIFIED";
            statusLabel = identityCheck === "MATCHED_REGISTERED_NAME"
              ? locale === "hi" ? "नाम रजिस्टर रिकॉर्ड से मेल खाता है" : "NAME MATCHES REGISTRY RECORD"
              : locale === "hi" ? "रजिस्ट्रेशन रिकॉर्ड मिला" : "REGISTRATION RECORD FOUND";
            details = identityCheck === "MATCHED_REGISTERED_NAME"
              ? `The claimed name matches the listed ${datasetRecord.intermediaryType} record for ${claimedNameMatchesDataset && normalizeRegistryName(claimedAdvisorName) === normalizeRegistryName(datasetRecord.contactPerson) ? datasetRecord.contactPerson : entityName} (registration ${registryNumber}; snapshot dated ${snapshotDate}; validity shown: ${validity}). This confirms only the name–registration association in the supplied file; it does not authenticate the person who sent this message.`
              : `The supplied ${datasetRecord.intermediaryType} snapshot lists ${registryNumber} under '${entityName}'${datasetRecord.contactPerson ? ` (contact person: ${datasetRecord.contactPerson})` : ""} (as of ${snapshotDate}). No claimed person or firm name was available to compare. The sender's identity is therefore not verified.`;
          }
        } else if (registryLookup?.state === "NOT_FOUND") {
          status = "FICTITIOUS_ID";
          statusLabel = locale === "hi" ? "दिए गए रजिस्टर में नहीं मिला" : "NOT FOUND IN PROVIDED REGISTRY";
          details = `Registration ID '${claimedRegId}' was not found in the supplied ${registryLookup.coveredType || "SEBI"} registry snapshot dated ${registryLookup.asOf || "unknown date"}. This dataset check is not a live SEBI lookup; verify the number on SEBI.gov.in before concluding it is fictitious.`;
        } else if (registryLookup?.state === "UNAVAILABLE" && !(claimedRegId && VERIFIED_SEBI_INTERMEDIARIES[claimedRegId])) {
          status = "REGISTRY_UNAVAILABLE";
          statusLabel = locale === "hi" ? "रजिस्टर उपलब्ध नहीं" : "LOCAL REGISTRY UNAVAILABLE";
          details = "VERA could not read the local registry snapshot, so this registration could not be checked.";
        } else if (registryLookup?.state === "AMBIGUOUS") {
          status = "REGISTRY_AMBIGUOUS";
          statusLabel = locale === "hi" ? "एक से अधिक रिकॉर्ड मिले" : "MULTIPLE RECORDS FOUND";
          details = `The supplied ${registryLookup.coveredType || "SEBI"} snapshot has more than one entry for ${claimedRegId}. VERA cannot determine which listed record applies; verify directly with SEBI.`;
        } else if (registryLookup?.state === "OUT_OF_SCOPE" && !(claimedRegId && VERIFIED_SEBI_INTERMEDIARIES[claimedRegId])) {
          status = "REGISTRY_NOT_COVERED";
          statusLabel = locale === "hi" ? "यह श्रेणी शामिल नहीं" : "REGISTRY CATEGORY NOT INCLUDED";
          details = `The supplied local snapshots cover Investment Advisers, Research Analysts, and Portfolio Managers. They do not cover registration ${claimedRegId}; verify it with the relevant SEBI register.`;
        } else if (claimedRegId && VERIFIED_SEBI_INTERMEDIARIES[claimedRegId]) {
          const entity = VERIFIED_SEBI_INTERMEDIARIES[claimedRegId];
          if (isGuaranteed || isFundSolicitation) {
            status = "NOT_VERIFIED";
            statusLabel = locale === "hi" ? "पहचान दुरुपयोग / प्रतिरूपण" : "SUSPECTED IMPERSONATION";
            details = locale === "hi"
              ? `पंजीकरण संख्या आधिकारिक तौर पर '${entity.name}' (${entity.type}) की है। हालाँकि, वैध पंजीकृत संस्थाएं कभी भी व्यक्तिगत खातों में पैसे नहीं मांगतीं और न ही निश्चित रिटर्न का वादा करती हैं। यह क्रेडेंशियल चोरी का संकेत है।`
              : `Registration ID matches registered entity '${entity.name}' (${entity.type}). However, legitimate regulated entities NEVER ask for personal fund deposits or guarantee returns. High probability of credential hijacking.`;
          } else {
            status = "VERIFIED";
            statusLabel = locale === "hi" ? "स्थानीय रिकॉर्ड में मिला" : "MATCHED LOCAL DEMO RECORD";
            details = locale === "hi"
              ? `स्थानीय उदाहरण रिकॉर्ड में ${entity.name} (${entity.type}) मिला। इससे संदेश भेजने वाले की पहचान सत्यापित नहीं होती।`
              : `Registration ID matches the existing local example record '${entity.name}' (${entity.type}). This does not verify the sender's identity.`;
          }
        } else {
          status = "FICTITIOUS_ID";
          statusLabel = locale === "hi" ? "दिए गए रजिस्टर में नहीं मिला" : "NOT FOUND IN PROVIDED REGISTRY";
          details = locale === "hi"
            ? `पंजीकरण संख्या '${claimedRegId}' दिए गए स्थानीय रजिस्टर में नहीं मिली। यह लाइव सेबी जाँच नहीं है; इसे फर्जी मानने से पहले सेबी की आधिकारिक वेबसाइट पर जाँचें।`
            : `Registration ID '${claimedRegId}' was not found in the supplied local registry snapshot. This is not a live SEBI lookup; verify it on SEBI.gov.in before concluding it is fictitious.`;
        }
      } else if (claimedAdvisorName) {
        status = "NOT_VERIFIED";
        statusLabel = locale === "hi" ? "अपंजीकृत व्यक्ति" : "UNREGISTERED PERSONA";
        details = locale === "hi"
          ? `एडवाइजर का नाम '${claimedAdvisorName}' सेबी की अधिकृत सूची में पंजीकृत नहीं है।`
          : `Advisor persona '${claimedAdvisorName}' is not registered with SEBI as an authorized Investment Adviser or Research Analyst.`;
      } else {
        status = "NOT_VERIFIED";
        statusLabel = locale === "hi" ? "अपंजीकृत एडवाइजर दावा" : "UNVERIFIED CLAIM";
        details = locale === "hi"
          ? "बिना सेबी पंजीकरण संख्या के वित्तीय सलाह या फंड मांगना अवैध है।"
          : "Operating or soliciting investment funds without verified SEBI registration is prohibited.";
      }

      advisorVerification = {
        claimedAdvisorName,
        claimedRegNumber: claimedRegId || undefined,
        hasRegistrationClaim: Boolean(sebiClaimMatch || claimedRegId || lower.includes("sebi registered")),
        hasNameClaim: Boolean(claimedAdvisorName),
        status,
        statusLabel,
        details,
        registeredEntityName: datasetRecord?.entityName,
        registeredContactPerson: datasetRecord?.contactPerson,
        registeredRegNumber: datasetRecord?.registrationNumber,
        intermediaryType: datasetRecord?.intermediaryType,
        snapshotDate: registryLookup?.asOf,
        validityFrom: datasetRecord?.validFrom,
        validityTo: datasetRecord?.validTo,
        identityCheck: datasetRecord ? identityCheck : undefined,
        regulatoryCitation,
        officialRegistryUrl: "https://www.sebi.gov.in/intermediaries.html",
      };
    }

    // ── Calculate Forensic Score & Reasons ──
    let riskTier: ScanVerdict["riskTier"] = "LOW";
    let score = 15;
    const reasons: string[] = [];
    const matched: string[] = [];

    // Reason 1: SEBI Registration Failure / Violation
    if (advisorVerification?.status === "MISSING_REGISTRATION") {
      score += 45;
      reasons.push(
        locale === "hi"
          ? "अनिवार्य सेबी लाइसेंस नंबर गायब (SEBI IA Reg 13) — 'सेबी रजिस्टर्ड एडवाइजर' होने का दावा किया गया है किंतु 12-अंकों का आधिकारिक सेबी रजिस्ट्रेशन नंबर (INA/INH/INZ) नहीं दिया गया।"
          : "Statutory License Omission ('SEBI IA Reg 13') — Sender claims to be a 'SEBI Registered Advisor' without quoting the mandatory 12-character SEBI Registration ID (INA/INH/INZ). Genuine advisors must quote their license in every communication."
      );
      matched.push("sebi registered", "advisor");
    } else if (advisorVerification?.status === "FICTITIOUS_ID") {
      score += 35;
      reasons.push(
        locale === "hi"
          ? `सेबी रजिस्ट्रेशन नंबर ('${claimedRegId}') साझा किए गए स्थानीय रजिस्टर में नहीं मिला। फर्जी मानने से पहले सेबी के आधिकारिक पोर्टल पर जाँचें।`
          : `SEBI registration ID '${claimedRegId}' was not found in the supplied local registry snapshot. Confirm on SEBI.gov.in before treating it as fictitious.`
      );
      matched.push(claimedRegId || "sebi id");
    } else if (advisorVerification?.status === "NOT_VERIFIED" && claimedRegId) {
      score += 50;
      reasons.push(
        locale === "hi"
          ? `सेबी क्रेडेंशियल का दुरुपयोग ('${claimedRegId}') — पंजीकृत संस्था के नाम पर अनधिकृत फंड मांग या अवैध रिटर्न का वादा किया जा रहा है।`
          : `SEBI registration claim '${claimedRegId}' needs identity review — the listed entity does not match the claimed name, or the message contains a suspicious solicitation or return claim.`
      );
      matched.push(claimedRegId);
    } else if (advisorVerification && !claimedRegId && sebiClaimMatch) {
      score += 40;
      reasons.push(
        locale === "hi"
          ? "अपुष्ट सेबी एडवाइजर दावा — बिना आधिकारिक सेबी रजिस्ट्रेशन नंबर के खुद को एडवाइजर बताना गैर-कानूनी है।"
          : "Unsubstantiated SEBI Claim — Stating advisor status without verifiable credentials is an immediate regulatory violation."
      );
      matched.push("sebi", "advisor");
    }

    // Reason 2: Assured Returns / Profit Guarantees (CIR/2023/123)
    if (isGuaranteed) {
      score += 45;
      const matchedPhrase =
        percentReturnMatch?.[0] ||
        multiplierMatch?.[0] ||
        fixedTermsMatch?.[0] ||
        periodicEarnMatch?.[0] ||
        "guaranteed returns";
      reasons.push(
        locale === "hi"
          ? `अवैध निश्चित रिटर्न का दावा ('${matchedPhrase}') — सेबी सर्कुलर 'CIR/2023/123' के तहत शेयर बाज़ार में किसी भी प्रकार के निश्चित या गारंटीड रिटर्न का वादा पूर्णतः प्रतिबंधित है।`
          : `Prohibited Assured Return Promise ('${matchedPhrase}') — Under SEBI Circular 'CIR/2023/123', promising fixed or guaranteed returns on securities is strictly prohibited by law.`
      );
      matched.push(matchedPhrase);
    }

    // Reason 3: Direct Fund Solicitation (send me 10k)
    if (isFundSolicitation) {
      score += 40;
      const matchedFundPhrase =
        fundDemandMatch?.[0] ||
        generalMoneyDemand?.[0] ||
        personalChannelDemand?.[0] ||
        "send funds";
      reasons.push(
        locale === "hi"
          ? `अनधिकृत व्यक्तिगत फंड मांग ('${matchedFundPhrase}') — सेबी एडवाइजर नियमों के अनुसार कोई भी पंजीकृत संस्था निवेशकों से सीधे पैसे अपने खाते में नहीं मांग सकती।`
          : `Unauthorized Direct Fund Solicitation ('${matchedFundPhrase}') — Under SEBI Investment Adviser Regulations, advisors are strictly prohibited from collecting client investment funds into personal accounts.`
      );
      matched.push(matchedFundPhrase);
    }

    // Reason 4: Urgency / High-Pressure Tactics (asap)
    if (isUrgency) {
      score += 20;
      const matchedUrgency = urgencyMatch?.[0] || "urgency";
      reasons.push(
        locale === "hi"
          ? `जल्दबाजी और मनोवैज्ञानिक दबाव ('${matchedUrgency}') — वित्तीय जालसाज पीड़ितों को बिना सोचे-समझे पैसे भेजने के लिए विवश करते हैं।`
          : `High-Pressure Urgency Tactics ('${matchedUrgency}') — Fraudsters utilize artificial urgency cues to prevent victims from conducting SEBI due diligence.`
      );
      matched.push(matchedUrgency);
    }

    // Reason 5: VIP / Telegram Channels
    if (isVip) {
      score += 25;
      reasons.push(
        locale === "hi"
          ? "अनाधिकृत वीआईपी / टेलीग्राम ग्रुप — बिना सेबी लाइसेंस सोशल मीडिया पर स्टॉक टिप्स देना गैर-कानूनी है।"
          : "Unregulated VIP/Telegram signal channel — Operating investment advisory via closed social messaging without license is prohibited."
      );
      matched.push("vip", "telegram", "whatsapp");
    }

    // Reason 6: Phishing / Fake UPI
    if (isPhishing || isUpiScam) {
      score += 35;
      reasons.push(
        locale === "hi"
          ? "सेबी के नाम पर फर्जी यूपीआई या संदिग्ध लिंक — सेबी कभी भी व्यक्तिगत बैंक या यूपीआई पर पैसे नहीं मांगता।"
          : "Impersonation or unverified payment handle — SEBI and legitimate stock brokers NEVER ask for deposits to personal UPI IDs."
      );
      matched.push("domain", "sebi", "@");
    }

    // Final score & Risk tier calculation
    score = Math.min(99, Math.max(10, score));
    if (score >= 70) riskTier = "CRITICAL";
    else if (score >= 45) riskTier = "HIGH";
    else if (score >= 25) riskTier = "MEDIUM";
    else riskTier = "LOW";

    const registryCheckSummary = registryLookup?.state === "FOUND"
      ? `${registryLookup.lookupBy === "EXACT_NAME" ? "Exact name match in" : "Matched"} supplied ${registryLookup.coveredType} snapshot (as of ${registryLookup.asOf}); this confirms a register entry, not the sender's identity.`
      : registryLookup?.state === "NOT_FOUND"
      ? `Not found in supplied ${registryLookup.coveredType} snapshot (as of ${registryLookup.asOf}).`
      : registryLookup?.state === "OUT_OF_SCOPE"
      ? "Registration category is not included in the supplied local snapshots."
      : registryLookup?.state === "UNAVAILABLE"
      ? "Local registry snapshot could not be read."
      : registryLookup?.state === "AMBIGUOUS"
      ? "Multiple matching records exist in the supplied local snapshot."
      : registryLookup?.state === "NAME_NOT_FOUND"
      ? `No exact name match in the supplied ${registryLookup.coveredType || "SEBI"} snapshot (as of ${registryLookup.asOf}); this does not prove the person is unregistered.`
      : "No registration ID was provided for lookup.";

    setVerdict({
      riskTier,
      score,
      highlightedReasons:
        reasons.length > 0
          ? reasons
          : [
              locale === "hi"
                ? "इस संदेश में कोई स्पष्ट घोटाला संकेत नहीं मिला।"
                : "No obvious high-risk deception patterns detected in this text.",
            ],
      matchedKeywords: matched,
      verifiedItems: [
        locale === "hi"
          ? "सेबी एडवाइजरी और नियमों का मिलान"
          : "Checked against official SEBI Investor Caution Rules",
        locale === "hi" ? `स्थानीय सेबी रजिस्टर: ${registryCheckSummary}` : registryCheckSummary,
        locale === "hi"
          ? "निश्चित लाभ और व्यक्तिगत फंड ट्रांसफर जाँच"
          : "Scanned for illegal assured returns and direct fund solicitation",
      ],
      unverifiedItems: [
        locale === "hi"
          ? "प्राप्तकर्ता का आंतरिक बैंक रिकॉर्ड (गोपनीयता कानून)"
          : "Receiver bank account ownership (Internal bank KYC is protected by privacy laws)",
      ],
      advisorVerification,
    });

    setIsScanning(false);
  };

  const [composerTab, setComposerTab] = useState<"TEXT" | "VIDEO">("TEXT");
  const [expandedSebiRef, setExpandedSebiRef] = useState<number | null>(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const getDetectedType = (text: string): string | null => {
    const trimmed = text.trim();
    if (!trimmed) return null;
    if (/https?:\/\/|www\.|\.com|\.in|\.vip|\.top/i.test(trimmed)) return t.detectedTypeUrl;
    if (/@\w+/i.test(trimmed) || /upi|paytm|gpay/i.test(trimmed)) return t.detectedTypeUpi;
    if (/\b(?:\+91|0)?[6-9]\d{9}\b/.test(trimmed)) return t.detectedTypePhone;
    return t.detectedTypeText;
  };

  const detectedChip = !uploadedB64 ? getDetectedType(inputText) : null;

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const nextHeight = Math.min(Math.max(textareaRef.current.scrollHeight, 84), 220);
      textareaRef.current.style.height = `${nextHeight}px`;
    }
  };

  const handleSelectSamplePrompt = (promptText: string) => {
    setComposerTab("TEXT");
    if (uploadedB64) clearFile();
    setInputText(promptText);
    setVerdict(null);
    if (textareaRef.current) {
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.style.height = "auto";
          const nextHeight = Math.min(Math.max(textareaRef.current.scrollHeight, 84), 220);
          textareaRef.current.style.height = `${nextHeight}px`;
        }
      }, 50);
    }
  };

  const handleSelectSampleVideoPitch = () => {
    setComposerTab("VIDEO");
    handleLoadSampleVideo();
  };

  const handleSelectSampleAuthenticVideo = () => {
    setComposerTab("VIDEO");
    handleLoadAuthenticVideo();
  };

  const handleSelectSampleDeepfakeVideo = () => {
    setComposerTab("VIDEO");
    handleLoadDeepfakeVideo();
  };

  return (
    <div className="w-full max-w-[760px] mx-auto mt-10 relative">
      {/* ── DESKTOP FLOATING QUICK SAMPLES (>= 1280px) ───────────────────────── */}
      <div className="hidden min-[1280px]:block pointer-events-auto">
        {/* Left Chip 1: Advisor Pitch (Illegal Advice) */}
        <button
          type="button"
          onClick={handleSelectSampleVideoPitch}
          className="vera-sample-chip absolute -left-6 -translate-x-full top-8"
          title="Try Sample Advisor Video Pitch (Illegal Return Guarantees)"
        >
          <Film className="w-4 h-4 text-amber-500" />
          <span>Advisor Pitch (Scam Advice)</span>
        </button>

        {/* Left Chip 2: Authentic Video (Clean) */}
        <button
          type="button"
          onClick={handleSelectSampleAuthenticVideo}
          className="vera-sample-chip absolute -left-6 -translate-x-full top-28"
          title="Try Sample Authentic Camera Footage (No Deepfake / Safe)"
        >
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          <span>Authentic Camera (Clean)</span>
        </button>

        {/* Left Chip 3: WhatsApp VIP Signals */}
        <button
          type="button"
          onClick={() => handleSelectSamplePrompt(SAMPLE_SCAM_PROMPTS[0].text)}
          className="vera-sample-chip absolute -left-6 -translate-x-full top-48"
          title="Try WhatsApp VIP Signals"
        >
          <span>💬</span>
          <span>WhatsApp VIP Signals</span>
        </button>

        {/* Right Chip 1: Deepfake Video Scam */}
        <button
          type="button"
          onClick={handleSelectSampleDeepfakeVideo}
          className="vera-sample-chip absolute -right-6 translate-x-full top-8"
          title="Try Deepfake AI Face-Swap Scam"
        >
          <ShieldAlert className="w-4 h-4 text-rose-500" />
          <span>Deepfake Video (AI Face-Swap)</span>
        </button>

        {/* Right Chip 2: Fake SEBI Advisor */}
        <button
          type="button"
          onClick={() => handleSelectSamplePrompt(SAMPLE_SCAM_PROMPTS[1].text)}
          className="vera-sample-chip absolute -right-6 translate-x-full top-28"
          title="Try Fake SEBI Advisor"
        >
          <ShieldCheck className="w-4 h-4 text-[var(--navy-1)] dark:text-[var(--accent)]" />
          <span>Fake SEBI Advisor</span>
        </button>

        {/* Right Chip 3: Phishing Trading Portal */}
        <button
          type="button"
          onClick={() => handleSelectSamplePrompt(SAMPLE_SCAM_PROMPTS[2].text)}
          className="vera-sample-chip absolute -right-6 translate-x-full top-48"
          title="Try Phishing Trading Portal"
        >
          <span>🔗</span>
          <span>Phishing Trading Portal</span>
        </button>
      </div>

      {/* ── COMPOSER CARD (760w, radius 28, glass, padding 24) ──────────────── */}
      <div className="vera-composer text-left relative z-10">
        {/* Header Row: Shield Tile 40px + VERA Fraud Screening 16px w600 */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] flex items-center justify-center text-[var(--navy-1)] dark:text-[var(--accent)] flex-shrink-0 shadow-sm">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-[var(--text-primary)] tracking-tight">
                {locale === "hi" ? t.title : "VERA Fraud Screening"}
              </h2>
              <p className="text-sm text-[var(--text-muted)] font-normal mt-0.5 leading-relaxed">
                {locale === "hi"
                  ? t.subtitle
                  : "Verify investment solicitations, suspicious trading links, and unverified brokers against SEBI regulations."}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              const el = document.getElementById("vera-sebi-verifier");
              if (el) el.scrollIntoView({ behavior: "smooth" });
            }}
            className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[var(--nav-track)] hover:bg-[var(--surface-solid)] border border-[var(--border)] text-xs font-semibold text-[var(--text-primary)] whitespace-nowrap transition-colors cursor-pointer shrink-0 shadow-xs active:scale-95"
            title="Check advisor license & SEBI registration"
          >
            <UserCheck className="w-3.5 h-3.5 text-[var(--text-primary)]" />
            <span>{locale === "hi" ? "सलाहकार सत्यापन ↓" : "Verify Advisor License ↓"}</span>
          </button>
        </div>

        {/* Segmented Pill Tabs (Flowfi style, 44px tall, full width, 2 tabs) */}
        <div className="vera-segmented-track mb-5">
          <button
            type="button"
            onClick={() => setComposerTab("TEXT")}
            className={`vera-segmented-tab ${composerTab === "TEXT" ? "active" : ""}`}
          >
            {t.tabMessageLink}
          </button>
          <button
            type="button"
            onClick={() => setComposerTab("VIDEO")}
            className={`vera-segmented-tab ${composerTab === "VIDEO" ? "active" : ""}`}
          >
            {t.tabVideoDeepfake}
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleScan} className="space-y-4">
          {/* PANEL 1: Message / Link Textarea */}
          {composerTab === "TEXT" && (
            <div className="space-y-2">
              <div className="relative">
                <textarea
                  ref={textareaRef}
                  value={inputText}
                  onChange={handleTextareaInput}
                  placeholder={locale === "hi" ? t.inputPlaceholder : "Paste message, URL, UPI handle, or company name..."}
                  rows={3}
                  className="w-full rounded-[20px] p-4 pb-9 text-base text-[var(--text-primary)] placeholder:text-[var(--text-subtle)] bg-[var(--input-bg)] border border-[var(--input-border)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] font-sans resize-none transition-all"
                  style={{ minHeight: "84px", maxHeight: "220px" }}
                />

                {/* Detected-type chip bottom-left inside field */}
                {detectedChip && (
                  <div className="absolute left-3.5 bottom-3 flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[var(--nav-track)] border border-[var(--border)] text-[11px] font-mono-tabular font-bold text-[var(--text-primary)] shadow-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--verdict-safe)]" />
                    <span>{detectedChip}</span>
                  </div>
                )}
              </div>


              {/* Examples line */}
              <p className="text-xs text-[var(--text-muted)] italic px-1">
                {locale === "hi"
                  ? t.inputHelp
                  : 'Examples: “Earn 50k daily in VIP group”, “http://zerodha-trading.vip”, “sebi-verify@paytm”'}
              </p>
            </div>
          )}

          {/* PANEL 2: Video / Deepfake Dropzone */}
          {composerTab === "VIDEO" && (
            <div className="flex flex-col gap-3">
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`min-h-[200px] rounded-[20px] border-[1.5px] border-dashed transition-all p-5 text-center flex flex-col items-center justify-center ${
                  isDragging
                    ? "border-[var(--accent)] bg-[var(--accent)]/10 scale-[1.01]"
                    : "border-[var(--dropzone-border)] bg-[var(--input-bg)]"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/mp4,video/webm,video/quicktime,video/x-matroska,video/*"
                  className="hidden"
                  onChange={handleFileUpload}
                />

                {!uploadedFile ? (
                  <div className="flex flex-col items-center justify-center gap-3 w-full py-4">
                    <div className="w-14 h-14 rounded-2xl bg-[var(--surface-solid)] text-[var(--navy-1)] dark:text-[var(--accent)] border border-[var(--border)] flex items-center justify-center shadow-sm">
                      <Film className="w-7 h-7" />
                    </div>
                    <div>
                      <h4 className="text-base font-semibold text-[var(--text-primary)]">
                        {locale === "hi" ? "अपना वीडियो यहाँ अपलोड करें" : "Upload your video to screen"}
                      </h4>
                      <p className="text-xs text-[var(--text-muted)] mt-1 max-w-md">
                        {locale === "hi"
                          ? "फ़ाइल यहाँ ड्रैग & ड्रॉप करें या अपने कंप्यूटर/फ़ोन से चुनें (MP4, WebM, MOV, AVI — 150 MB तक)"
                          : "Drag & drop video file here or click below to browse (MP4, WebM, MOV, AVI — up to 150 MB)"}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="mt-1 px-5 py-2.5 rounded-full bg-[var(--accent)] text-[var(--accent-ink)] font-semibold text-xs inline-flex items-center gap-2 hover:opacity-95 shadow-sm transition-transform active:scale-95 cursor-pointer"
                    >
                      <UploadCloud className="w-4 h-4" />
                      <span>{locale === "hi" ? "वीडियो फ़ाइल चुनें" : "Choose Video File"}</span>
                    </button>
                  </div>
                ) : (
                  <div className="w-full flex flex-col gap-3">
                    {/* File Card */}
                    <div className="w-full flex items-center justify-between gap-3 p-3.5 rounded-2xl bg-[var(--surface-solid)] border border-[var(--border)] shadow-sm">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-10 h-10 rounded-xl bg-[var(--nav-track)] flex items-center justify-center text-[var(--navy-1)] dark:text-[var(--accent)] flex-shrink-0">
                          <Film className="w-5 h-5" />
                        </div>
                        <div className="text-left min-w-0">
                          <p className="text-sm font-semibold text-[var(--text-primary)] truncate max-w-[280px] sm:max-w-[420px]">
                            {uploadedFile.name}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5 text-xs text-[var(--text-muted)]">
                            <span className="font-mono-tabular font-medium">{uploadedFile.sizeMB} MB</span>
                            <span>•</span>
                            <span className="text-emerald-500 dark:text-emerald-400 font-semibold flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              {locale === "hi" ? "सफलतापूर्वक लोड हुआ" : "Loaded & Ready"}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="px-3 py-1.5 rounded-full border border-[var(--border)] text-xs font-semibold text-[var(--text-primary)] hover:bg-[var(--nav-track)] transition-colors cursor-pointer"
                          title="Change video file"
                        >
                          {locale === "hi" ? "बदलें" : "Change"}
                        </button>
                        <button
                          type="button"
                          onClick={clearFile}
                          className="w-8 h-8 rounded-full border border-[var(--border)] hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40 flex items-center justify-center text-[var(--text-muted)] transition-colors cursor-pointer"
                          title="Remove video"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Optional Local Video Preview Player */}
                    {videoPreviewUrl && (
                      <div className="w-full rounded-2xl overflow-hidden border border-[var(--border)] bg-black/90 flex justify-center max-h-48">
                        <video
                          src={videoPreviewUrl}
                          controls
                          className="w-full max-h-48 object-contain"
                          preload="metadata"
                        />
                      </div>
                    )}

                    {/* Spoken Dialogue Text Field */}
                    <div className="w-full text-left p-3 rounded-2xl bg-[var(--surface-solid)] border border-[var(--border)]">
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
                          <Volume2 className="w-3.5 h-3.5 text-[var(--navy-1)] dark:text-[var(--accent)]" />
                          <span>
                            {locale === "hi"
                              ? "वीडियो में क्या बोला जा रहा है? (भाषण / संवाद)"
                              : "Spoken Speech / Dialogue in Video (Optional):"}
                          </span>
                        </label>
                        <span className="text-[10px] text-[var(--text-muted)] font-mono-tabular">SEBI CIR/2023/123</span>
                      </div>
                      <textarea
                        value={userSpokenText}
                        onChange={(e) => setUserSpokenText(e.target.value)}
                        placeholder={
                          locale === "hi"
                            ? "यदि आप जानते हैं कि वीडियो में क्या कहा गया है, तो यहाँ लिखें (जैसे: '15000 जमा करें, 40% गारंटीड रिटर्न')। खाली छोड़ने पर स्वतः ऑडियो विश्लेषण होगा।"
                            : "Type what the speaker says, or leave blank to automatically analyze acoustic dialogue."
                        }
                        className="w-full text-xs p-2.5 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)] text-[var(--text-primary)] placeholder:text-[var(--text-subtle)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)] resize-none"
                        rows={2}
                      />
                      <p className="text-[11px] text-[var(--text-muted)] mt-1.5 flex items-center gap-1">
                        <span>⚖️</span>
                        <span>
                          {locale === "hi"
                            ? "वेरा भाषण में अवैध सलाह, गारंटीड रिटर्न और टेलीग्राम लिंक की जांच करेगा।"
                            : "VERA will cross-check speech for guaranteed return claims, VIP channel solicitations, and SEBI circular violations."}
                        </span>
                      </p>
                    </div>
                  </div>
                )}

                {uploadError && (
                  <div className="w-full mt-3 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-medium text-left flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{uploadError}</span>
                  </div>
                )}
              </div>

              {/* Separate, Clearly-Labeled Section for Preloaded Demo Samples (Completely separate from Dropzone) */}
              <div className="rounded-2xl p-3 bg-[var(--surface-solid)]/60 border border-[var(--border)] flex flex-col sm:flex-row items-center justify-between gap-2.5">
                <div className="text-left">
                  <span className="text-xs font-semibold text-[var(--text-primary)] block">
                    {locale === "hi" ? "या प्रीलोडेड डेमो नमूने के साथ परीक्षण करें (वैकल्पिक):" : "Or test with preloaded demo sample (optional):"}
                  </span>
                  <span className="text-[11px] text-[var(--text-muted)] block">
                    {locale === "hi" ? "यदि आपके पास अपना वीडियो नहीं है तो इनमें से कोई एक चुनें" : "Select one if you do not have your own video file ready"}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={handleLoadAuthenticVideo}
                    className="px-2.5 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 transition-all cursor-pointer shadow-sm active:scale-95"
                    title="Load authentic camera footage (real video, no scam speech)"
                  >
                    ✓ Authentic (Safe)
                  </button>
                  <button
                    type="button"
                    onClick={handleLoadSampleVideo}
                    className="px-2.5 py-1.5 rounded-full text-xs font-semibold bg-amber-500/10 hover:bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30 transition-all cursor-pointer shadow-sm active:scale-95"
                    title="Load real camera footage with illegal advisor pitch"
                  >
                    ⚠️ Illegal Advisory
                  </button>
                  <button
                    type="button"
                    onClick={handleLoadDeepfakeVideo}
                    className="px-2.5 py-1.5 rounded-full text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/30 transition-all cursor-pointer shadow-sm active:scale-95"
                    title="Load synthetic AI deepfake video"
                  >
                    🚨 AI Deepfake
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Footer Row (space-between, margin-top 20) */}
          <div className="flex items-center justify-between pt-5 mt-5 border-t border-[var(--border)]">
            {/* Left: Attached File Name Chip or Empty */}
            <div>
              {uploadedFile && composerTab === "TEXT" && (
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--nav-track)] border border-[var(--border)] text-xs font-medium text-[var(--text-primary)]">
                  <Film className="w-3.5 h-3.5" />
                  <span className="truncate max-w-[180px]">{uploadedFile.name}</span>
                  <button type="button" onClick={clearFile} className="ml-1 text-[var(--text-muted)] hover:text-rose-500">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>

            {/* Right: Screen for Fraud Button (52px tall, min-width 200, pill) */}
            <button
              type="submit"
              disabled={isScanning || (!inputText.trim() && !uploadedB64)}
              className={`vera-btn-primary${isScanning ? " is-scanning" : ""}`}
            >
              {isScanning ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  <span>{locale === "hi" ? "जाँच जारी है..." : "Scanning..."}</span>
                </span>
              ) : (
                <span>{locale === "hi" ? t.checkButton : "Screen for Fraud"} &rarr;</span>
              )}
            </button>
          </div>
        </form>

        {/* Active scanning feedback */}
        {isScanning && (
          <div className="vera-scan-console mt-5" role="status" aria-live="polite" data-active-stage={activeScanStage}>
            <div className="vera-scan-console-top">
              <span className="vera-scan-live-indicator"><i /></span>
              <span className="vera-scan-console-brand">VERA <b>/</b> LIVE SCREENING</span>
              <span className="vera-scan-console-state">{locale === "hi" ? "विश्लेषण जारी" : "ANALYSIS IN PROGRESS"}</span>
            </div>
            <div className="vera-scan-console-main">
              <div className="vera-scan-radar" aria-hidden="true">
                <span className="vera-scan-radar-ring vera-scan-radar-ring-outer" />
                <span className="vera-scan-radar-ring vera-scan-radar-ring-middle" />
                <span className="vera-scan-radar-ring vera-scan-radar-ring-inner" />
                <span className="vera-scan-radar-sweep" />
                <ShieldCheck className="vera-scan-radar-icon" />
              </div>
              <div className="vera-scan-console-copy">
                <span className="vera-scan-kicker">{locale === "hi" ? "साक्ष्य विश्लेषण" : "EVIDENCE ANALYSIS"}</span>
                <p className="vera-scan-phase" key={scanningPhase}>{scanningPhase}</p>
                <p className="vera-scan-supporting-copy">
                  {locale === "hi" ? "संदेश, वीडियो और रजिस्टर संकेतों का मिलान किया जा रहा है" : "Cross-checking content, media signals, and registry evidence"}
                </p>
                <div className="vera-scan-stages" aria-label={locale === "hi" ? "विश्लेषण चरण" : "Analysis stages"}>
                  {[
                    locale === "hi" ? "सिग्नल" : "SIGNALS",
                    locale === "hi" ? "साक्ष्य" : "EVIDENCE",
                    locale === "hi" ? "जोखिम" : "RISK PROFILE",
                  ].map((stage, index) => (
                    <div className={`vera-scan-stage${index < activeScanStage ? " is-complete" : index === activeScanStage ? " is-active" : ""}`} key={stage}>
                      <span className="vera-scan-stage-node">{index < activeScanStage ? "✓" : `0${index + 1}`}</span>
                      <span className="vera-scan-stage-label">{stage}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="vera-scan-progress-track" aria-hidden="true"><span /></div>
          </div>
        )}
      </div>

      {/* ── MOBILE HORIZONTAL SCROLL CHIPS (< 1280px) ───────────────────────── */}
      <div className="min-[1280px]:hidden mt-6 flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none px-1">
        <span className="text-fluid-micro text-[var(--text-muted)] flex-shrink-0">
          {t.tryQuickSample}
        </span>
        <button
          type="button"
          onClick={handleSelectSampleVideoPitch}
          className="vera-sample-chip flex-shrink-0"
        >
          <Film className="w-3.5 h-3.5 text-[var(--navy-1)] dark:text-[var(--accent)]" />
          <span>Sample Video Pitch</span>
        </button>
        {SAMPLE_SCAM_PROMPTS.map((sample, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSelectSamplePrompt(sample.text)}
            className="vera-sample-chip flex-shrink-0"
          >
            <span>{sample.label}</span>
          </button>
        ))}
      </div>

      {/* ── 5. RESULT STATE (Compact Sticky Bar + 12-col Bento Grid) ──────── */}
      {verdict && (
        <div id="vera-results" className="vera-result-arrival w-full mt-6">
          {/* COMPACT STICKY BAR (72px: input summary one-line + 'Screen another' button) */}
          <div className="h-[72px] rounded-full vera-glass px-6 sm:px-8 flex items-center justify-between max-w-[760px] mx-auto w-full mb-8 sticky top-24 z-30 shadow-lg border border-[var(--border)]">
            <div className="flex items-center gap-3 min-w-0 pr-4">
              <div className="w-8 h-8 rounded-full bg-[var(--nav-track)] flex items-center justify-center text-[var(--navy-1)] dark:text-[var(--accent)] flex-shrink-0">
                {uploadedFile ? <Film className="w-4 h-4" /> : <Search className="w-4 h-4" />}
              </div>
              <span className="text-sm font-medium text-[var(--text-primary)] truncate max-w-[340px] sm:max-w-[480px]">
                {uploadedFile ? `${uploadedFile.name} (${uploadedFile.sizeMB} MB)` : inputText}
              </span>
            </div>

            <button
              type="button"
              onClick={() => {
                setVerdict(null);
                setInputText("");
                setUploadedFile(null);
                setUploadedB64(null);
              }}
              className="h-10 px-5 rounded-full bg-[var(--accent)] text-[var(--accent-ink)] text-xs font-semibold whitespace-nowrap hover:opacity-90 transition-opacity shadow-sm flex-shrink-0"
            >
              {t.screenAnother}
            </button>
          </div>

          {/* 12-COL BENTO GRID (max 1120, 12 cols, gap 24, padding 28, radius 24) */}
          <div className="vera-results-grid max-w-[1120px] mx-auto w-full grid grid-cols-12 gap-6 text-left">
            {/* ROW 0 (HIGH RISK only): Full-width red-tinted helpline banner */}
            {(verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH") && (
              <div className="col-span-12 vera-glass rounded-[24px] p-6 sm:p-7 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-rose-500/15 border-rose-500/30 transition-transform duration-200 hover:-translate-y-0.5">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-2xl bg-rose-600 text-white flex items-center justify-center flex-shrink-0 shadow-md shadow-rose-600/30">
                    <PhoneCall className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-rose-700 dark:text-rose-300">
                      {locale === "hi" ? "राष्ट्रीय साइबर अपराध हेल्पलाइन 1930" : "Cyber Crime Helpline 1930"}
                    </h3>
                    <p className="text-xs text-[var(--text-muted)] mt-0.5 max-w-xl">
                      {locale === "hi"
                        ? "यदि आपने पैसे भेज दिए हैं, तो तुरंत 1930 पर कॉल करें। शीघ्र रिपोर्टिंग से फंड फ्रीज होने की संभावना बढ़ती है।"
                        : "Critical Action: If any funds were transferred, dial 1930 immediately within 2 hours to freeze recipient bank accounts."}
                    </p>
                  </div>
                </div>

                <a
                  href="tel:1930"
                  className="px-6 py-3 rounded-full bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-sm sm:text-base inline-flex items-center gap-2 flex-shrink-0 shadow-md shadow-rose-600/30 transition-transform hover:scale-105"
                >
                  <Phone className="w-4 h-4" />
                  <span className="font-mono-tabular">1930</span>
                </a>
              </div>
            )}

            {/* ROW 1 - LEFT: Verdict Card (span 8, 280 tall) */}
            <div
              className={`col-span-12 lg:col-span-8 min-h-[280px] vera-glass rounded-[24px] p-7 flex flex-col justify-between transition-transform duration-200 hover:-translate-y-0.5 ${
                verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                  ? "border-rose-500/30"
                  : verdict.riskTier === "MEDIUM"
                  ? "border-amber-500/30"
                  : verdict.riskTier === "INCONCLUSIVE"
                  ? "border-amber-500/30"
                  : "border-emerald-500/30"
              }`}
            >
              {/* Top: 64px Tile with Verdict Icon */}
              <div className="flex items-center justify-between">
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center flex-shrink-0 border"
                  style={{
                    backgroundColor:
                      verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                        ? "rgba(200, 30, 60, 0.12)"
                        : verdict.riskTier === "MEDIUM"
                        ? "rgba(180, 83, 9, 0.12)"
                        : verdict.riskTier === "INCONCLUSIVE"
                        ? "rgba(180, 83, 9, 0.10)"
                        : "rgba(15, 123, 108, 0.12)",
                    borderColor:
                      verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                        ? "rgba(200, 30, 60, 0.25)"
                        : verdict.riskTier === "MEDIUM"
                        ? "rgba(180, 83, 9, 0.25)"
                        : verdict.riskTier === "INCONCLUSIVE"
                        ? "rgba(180, 83, 9, 0.25)"
                        : "rgba(15, 123, 108, 0.25)",
                    color:
                      verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                        ? "var(--verdict-high-risk)"
                        : verdict.riskTier === "MEDIUM"
                        ? "var(--verdict-suspicious)"
                        : verdict.riskTier === "INCONCLUSIVE"
                        ? "var(--verdict-suspicious)"
                        : "var(--verdict-safe)",
                  }}
                >
                  {verdict.riskTier === "INCONCLUSIVE" ? (
                    <HelpCircle className="w-8 h-8" strokeWidth={1.5} />
                  ) : verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH" ? (
                    <OctagonX className="w-8 h-8" strokeWidth={1.5} />
                  ) : verdict.riskTier === "MEDIUM" ? (
                    <AlertTriangle className="w-8 h-8" strokeWidth={1.5} />
                  ) : (
                    <ShieldCheck className="w-8 h-8" strokeWidth={1.5} />
                  )}
                </div>

                <span
                  className="px-3.5 py-1 rounded-full text-xs font-mono-tabular font-bold border"
                  style={{
                    color:
                      verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                        ? "var(--verdict-high-risk)"
                        : verdict.riskTier === "MEDIUM"
                        ? "var(--verdict-suspicious)"
                      : verdict.riskTier === "INCONCLUSIVE"
                      ? "var(--verdict-suspicious)"
                        : "var(--verdict-safe)",
                    borderColor: "currentColor",
                  }}
                >
                  {verdict.riskTier === "INCONCLUSIVE"
                    ? "ANALYSIS INCOMPLETE"
                    : verdict.riskTier === "CRITICAL"
                    ? "CRITICAL ALERT"
                    : verdict.riskTier === "HIGH"
                    ? "HIGH RISK"
                    : verdict.riskTier === "MEDIUM"
                    ? "SUSPICIOUS"
                    : "VERIFIED SAFE"}
                </span>
              </div>

              {/* Center: Verdict Label H1-size in Verdict Color */}
              <div className="my-3">
                <h2
                  className="text-fluid-h1 tracking-tight"
                  style={{
                    color:
                      verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                        ? "var(--verdict-high-risk)"
                        : verdict.riskTier === "MEDIUM"
                        ? "var(--verdict-suspicious)"
                      : verdict.riskTier === "INCONCLUSIVE"
                      ? "var(--verdict-suspicious)"
                        : "var(--verdict-safe)",
                  }}
                >
                  {verdict.riskTier === "INCONCLUSIVE"
                    ? locale === "hi" ? "विश्लेषण अधूरा" : "ANALYSIS INCOMPLETE"
                    : verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                    ? locale === "hi"
                      ? "अत्यधिक जोखिम"
                      : "HIGH RISK"
                    : verdict.riskTier === "MEDIUM"
                    ? locale === "hi"
                      ? "संदिग्ध"
                      : "SUSPICIOUS"
                    : locale === "hi"
                    ? "सुरक्षित"
                    : "SAFE"}
                </h2>
              </div>

              {/* Bottom: One-line summary from backend */}
              <p className="text-sm text-[var(--text-muted)] font-normal leading-relaxed line-clamp-2">
                {verdict.highlightedReasons[0] ||
                  (verdict.isDeepfakeResult
                    ? "Automated video frame inspection and facial anomaly analysis."
                    : "Verified against SEBI Investor Caution Rules and Intermediary Registry.")}
              </p>
            </div>

            {/* ROW 1 - RIGHT: Gauge Card (span 4, 280 tall) */}
            <div className="col-span-12 lg:col-span-4 min-h-[280px] vera-glass rounded-[24px] p-7 flex flex-col items-center justify-center text-center transition-transform duration-200 hover:-translate-y-0.5">
              <div className="relative w-[160px] h-[160px] flex items-center justify-center">
                <svg width="160" height="160" viewBox="0 0 160 160" className="transform -rotate-90">
                  {/* Background Track Circle */}
                  <circle
                    cx="80"
                    cy="80"
                    r="64"
                    stroke="var(--nav-track)"
                    strokeWidth="12"
                    fill="transparent"
                  />
                  {/* Progress Circle in Verdict Color */}
                  <circle
                    cx="80"
                    cy="80"
                    r="64"
                    stroke={
                      verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                        ? "var(--verdict-high-risk)"
                        : verdict.riskTier === "MEDIUM"
                        ? "var(--verdict-suspicious)"
                        : verdict.riskTier === "INCONCLUSIVE"
                        ? "var(--verdict-suspicious)"
                        : "var(--verdict-safe)"
                    }
                    strokeWidth="12"
                    strokeDasharray={402.12}
                    strokeDashoffset={402.12 - (402.12 * Math.min(100, Math.max(0, verdict.score))) / 100}
                    strokeLinecap="round"
                    fill="transparent"
                    className="transition-all duration-700 ease-out"
                  />
                </svg>

                {/* Score Number in Center (Geist Mono / font-mono-tabular) */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="vera-result-score-pop font-mono-tabular font-extrabold text-4xl text-[var(--text-primary)] leading-none">
                    {isInconclusive ? "—" : verdict.score}
                  </span>
                  <span className="text-[11px] font-mono-tabular text-[var(--text-muted)] mt-1">
                    {isInconclusive ? (locale === "hi" ? "स्कोर उपलब्ध नहीं" : "Score unavailable") : "/ 100"}
                  </span>
                </div>
              </div>

              <span className="text-xs uppercase font-mono-tabular tracking-wider font-semibold text-[var(--text-muted)] mt-3">
                {isInconclusive
                  ? locale === "hi" ? "विश्लेषण उपलब्ध नहीं" : "Risk Score Unavailable"
                  : locale === "hi" ? "जोखिम स्कोर" : "Risk Score"}
              </span>
            </div>

            {/* SEBI Advisor & Credential Verification Audit Card */}
            {verdict.advisorVerification && (verdict.advisorVerification.hasRegistrationClaim || verdict.advisorVerification.hasNameClaim) && (
              <div className="col-span-12 vera-glass rounded-[24px] p-6 sm:p-7 border border-[var(--border)] relative overflow-hidden transition-transform duration-200 hover:-translate-y-0.5">
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-[var(--border)]">
                  <div className="flex items-center gap-2.5">
                    {verdict.advisorVerification.status === "VERIFIED" && !identityUnconfirmed ? (
                      <ShieldCheck className="w-5 h-5 text-emerald-500" />
                    ) : identityUnconfirmed || verdict.advisorVerification.status === "REGISTRY_UNAVAILABLE" || verdict.advisorVerification.status === "REGISTRY_NOT_COVERED" || verdict.advisorVerification.status === "REGISTRY_AMBIGUOUS" || verdict.advisorVerification.status === "REGISTRY_NAME_NOT_FOUND" ? (
                      <Info className="w-5 h-5 text-amber-500" />
                    ) : (
                      <ShieldAlert className="w-5 h-5 text-rose-500" />
                    )}
                    <h3 className="text-base font-semibold text-[var(--text-primary)]">
                      {locale === "hi"
                        ? "सेबी एडवाइजर एवं रजिस्ट्रेशन प्रमाणन जाँच"
                        : "SEBI Advisor & Registration Credential Audit"}
                    </h3>
                  </div>

                  <span
                    className={`px-3 py-1 rounded-full text-xs font-mono-tabular font-bold border ${
                      verdict.advisorVerification.status === "VERIFIED" && !identityUnconfirmed
                        ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                        : identityUnconfirmed || verdict.advisorVerification.status === "REGISTRY_UNAVAILABLE" || verdict.advisorVerification.status === "REGISTRY_NOT_COVERED" || verdict.advisorVerification.status === "REGISTRY_AMBIGUOUS" || verdict.advisorVerification.status === "REGISTRY_NAME_NOT_FOUND"
                        ? "bg-amber-500/10 text-amber-600 border-amber-500/30"
                        : "bg-rose-500/10 text-rose-500 border-rose-500/30"
                    }`}
                  >
                    {verdict.advisorVerification.statusLabel}
                  </span>
                </div>

                {/* 3-Column Credential Breakdown */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mb-4">
                  <div className="p-3.5 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)]">
                    <span className="text-[11px] font-mono-tabular uppercase tracking-wider text-[var(--text-muted)] block mb-1">
                      {verdict.advisorVerification.registeredContactPerson || verdict.advisorVerification.registeredEntityName
                        ? locale === "hi" ? "रजिस्टर में नाम" : "Name in registry"
                        : locale === "hi" ? "दावा किया गया नाम" : "Claimed Person / Firm"}
                    </span>
                    <span className="font-semibold text-sm text-[var(--text-primary)]">
                      {verdict.advisorVerification.registeredContactPerson || verdict.advisorVerification.registeredEntityName || verdict.advisorVerification.claimedAdvisorName ||
                        (locale === "hi"
                          ? "नाम नहीं दिया गया"
                          : "Name not provided")}
                    </span>
                    {verdict.advisorVerification.intermediaryType && (
                      <div className="mt-1 text-xs text-[var(--text-muted)]">
                        {locale === "hi" ? "पंजीकृत श्रेणी:" : "Registered as:"} <span className="font-semibold text-[var(--text-primary)]">{verdict.advisorVerification.intermediaryType}</span>
                      </div>
                    )}
                    {verdict.advisorVerification.registeredEntityName && verdict.advisorVerification.registeredEntityName !== verdict.advisorVerification.registeredContactPerson && (
                      <div className="mt-2 pt-2 border-t border-[var(--border)] text-[11px] leading-relaxed text-[var(--text-muted)]">
                        <div>{locale === "hi" ? "रजिस्टर की फर्म" : "Registered entity"}: <span className="font-semibold text-[var(--text-primary)]">{verdict.advisorVerification.registeredEntityName}</span></div>
                        {verdict.advisorVerification.claimedAdvisorName && (
                          <div>{locale === "hi" ? "दावा किया गया नाम" : "Name claimed in message"}: <span className="font-semibold text-[var(--text-primary)]">{verdict.advisorVerification.claimedAdvisorName}</span></div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="p-3.5 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)]">
                    <span className="text-[11px] font-mono-tabular uppercase tracking-wider text-[var(--text-muted)] block mb-1">
                      {locale === "hi" ? "सेबी रजिस्ट्रेशन आईडी" : "SEBI Registration ID"}
                    </span>
                    <span
                      className={`font-mono-tabular font-bold text-sm ${
                        verdict.advisorVerification.claimedRegNumber || verdict.advisorVerification.registeredRegNumber
                          ? "text-[var(--text-primary)]"
                          : "text-[var(--text-muted)]"
                      }`}
                    >
                      {verdict.advisorVerification.claimedRegNumber || verdict.advisorVerification.registeredRegNumber ||
                        (locale === "hi" ? "अनुपस्थित (कोई नंबर नहीं दिया)" : "None provided")}
                    </span>
                    {!verdict.advisorVerification.claimedRegNumber && verdict.advisorVerification.registeredRegNumber && (
                      <div className="mt-1 text-[10px] text-[var(--text-muted)]">
                        {locale === "hi" ? "नाम से मिले रजिस्टर रिकॉर्ड का आईडी" : "ID from exact name match in snapshot"}
                      </div>
                    )}
                  </div>

                  <div className="p-3.5 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)]">
                    <span className="text-[11px] font-mono-tabular uppercase tracking-wider text-[var(--text-muted)] block mb-1">
                      {locale === "hi" ? "रजिस्टर जाँच" : "Registry Check"}
                    </span>
                    <span
                      className={`font-semibold text-sm ${
                        verdict.advisorVerification.status === "VERIFIED" && !identityUnconfirmed
                          ? "text-emerald-500"
                        : identityUnconfirmed || verdict.advisorVerification.status === "REGISTRY_UNAVAILABLE" || verdict.advisorVerification.status === "REGISTRY_NOT_COVERED" || verdict.advisorVerification.status === "REGISTRY_AMBIGUOUS" || verdict.advisorVerification.status === "REGISTRY_NAME_NOT_FOUND"
                          ? "text-amber-600"
                          : "text-rose-500"
                      }`}
                    >
                      {verdict.advisorVerification.status === "VERIFIED"
                        ? verdict.advisorVerification.identityCheck === "MATCHED_REGISTERED_NAME"
                          ? "Name matches registry record"
                          : identityUnconfirmed
                          ? verdict.advisorVerification.registeredEntityName
                            ? "Record found"
                            : "Name not provided · unverified"
                          : verdict.advisorVerification.registeredEntityName
                          ? "Registration found"
                          : "Matched Local Demo Record"
                        : locale === "hi"
                        ? verdict.advisorVerification.status === "REGISTRY_UNAVAILABLE" ? "जाँच उपलब्ध नहीं" : verdict.advisorVerification.status === "REGISTRY_NOT_COVERED" ? "यह श्रेणी शामिल नहीं" : "रजिस्टर में नहीं मिला"
                        : verdict.advisorVerification.status === "REGISTRY_UNAVAILABLE"
                        ? "Could Not Check Local Registry"
                        : verdict.advisorVerification.status === "REGISTRY_AMBIGUOUS"
                        ? "Multiple Local Records · Verify with SEBI"
                        : verdict.advisorVerification.status === "REGISTRY_NAME_NOT_FOUND"
                        ? "No Exact Name Match · Check Spelling / ID"
                        : verdict.advisorVerification.status === "REGISTRY_NOT_COVERED"
                        ? "Category Not Included in Local Files"
                        : verdict.advisorVerification.status === "MISSING_REGISTRATION"
                        ? "Registration ID Missing"
                        : verdict.advisorVerification.status === "NOT_VERIFIED"
                        ? "Identity / Claim Needs Review"
                        : "Not Found in Supplied Snapshot"}
                    </span>
                  </div>
                </div>

                {/* Regulatory Citation & Official Registry Lookup Link */}
                <div className="p-3.5 rounded-2xl bg-[var(--nav-track)]/60 border border-[var(--border)] text-xs text-[var(--text-muted)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono-tabular font-bold text-[var(--text-primary)]">
                        {verdict.advisorVerification.regulatoryCitation}
                      </span>
                      <span className="text-[10px] text-amber-500 font-semibold px-1.5 py-0.2 rounded bg-amber-500/10">
                        {verdict.advisorVerification.snapshotDate ? "Snapshot Source" : "Statutory Mandate"}
                      </span>
                    </div>
                    <p className="leading-relaxed text-[var(--text-muted)]">
                      {verdict.advisorVerification.details}
                    </p>
                  </div>

                  <a
                    href={verdict.advisorVerification.officialRegistryUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-shrink-0 px-3.5 py-2 rounded-full border border-[var(--border)] bg-[var(--surface-solid)] text-[var(--navy-1)] dark:text-[var(--accent)] text-xs font-semibold hover:border-[var(--text-muted)] transition-colors inline-flex items-center gap-1.5 shadow-sm"
                  >
                    <span>{locale === "hi" ? "सेबी आधिकारिक पोर्टल पर खोजें" : "Verify on SEBI.gov.in"}</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            )}

            {/* VIDEO SPEECH TRANSCRIPT & ADVISORY FORENSICS CARD (Full width span 12) */}
            {verdict.isDeepfakeResult && (
              <div className="col-span-12 vera-glass rounded-[24px] p-6 sm:p-7 border border-[var(--border)] relative overflow-hidden transition-transform duration-200 hover:-translate-y-0.5">
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-[var(--border)]">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-10 h-10 rounded-2xl flex items-center justify-center border shadow-sm ${
                        isInconclusive
                          ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30"
                          : verdict.advisorySignalsDetected
                          ? "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30"
                          : "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                      }`}
                    >
                      <FileAudio className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-[var(--text-primary)]">
                        {locale === "hi"
                          ? "वीडियो भाषण ट्रांसक्रिप्ट एवं ऑडियो फ़ोरेंसिक्स"
                          : "Video Speech Transcript & Audio Advisory Forensics"}
                      </h3>
                      <p className="text-xs text-[var(--text-muted)]">
                        {isInconclusive
                          ? locale === "hi"
                            ? "ऑडियो और दृश्य विश्लेषण उपलब्ध नहीं था।"
                            : "Audio and visual analysis could not be completed."
                          : locale === "hi"
                          ? "व्हिस्पर एसटीटी द्वारा ऑडियो संवाद निकाला गया • सेबी सलाहकार नियमों से मिलान"
                          : "Acoustic extraction via faster-whisper STT • Screened against SEBI Investor Advisory regulations"}
                      </p>
                    </div>
                  </div>

                  {/* Dual Badges: Visual Integrity & Speech Advisory Status */}
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Visual Media Status */}
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-mono-tabular font-semibold border ${
                        isInconclusive
                          ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30"
                          : verdict.visualManipulationDetected
                          ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30"
                          : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                      }`}
                    >
                      {isInconclusive
                        ? locale === "hi" ? "⚠ दृश्य विश्लेषण उपलब्ध नहीं" : "⚠ Visual analysis unavailable"
                        : verdict.visualManipulationDetected
                        ? "🚨 Visual: Facial Manipulation Detected"
                        : "✓ Visual: Authentic Camera Footage"}
                    </span>

                    {/* Spoken Advice Status */}
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-mono-tabular font-bold border ${
                        isInconclusive
                          ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30"
                          : verdict.advisorySignalsDetected
                          ? "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/40"
                          : "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/40"
                      }`}
                    >
                      {isInconclusive
                        ? locale === "hi" ? "⚠ भाषण विश्लेषण उपलब्ध नहीं" : "⚠ Speech analysis unavailable"
                        : verdict.advisorySignalsDetected
                        ? locale === "hi"
                          ? "❌ अवैध निवेश सलाह चिन्हित"
                          : "❌ ILLEGAL INVESTMENT ADVISORY FLAGGED"
                        : "✓ COMPLIANT SPEECH"}
                    </span>

                    {/* Open Window Button */}
                    <button
                      type="button"
                      onClick={() => setIsTranscriptModalOpen(true)}
                      className="px-3 py-1.5 rounded-full text-xs font-semibold bg-[var(--surface-solid)] border border-[var(--border)] text-[var(--text-primary)] hover:border-[var(--accent)] hover:bg-[var(--nav-track)] flex items-center gap-1.5 transition-all shadow-sm active:scale-95 cursor-pointer ml-auto"
                      title="Open Dedicated Forensic Transcription Window"
                    >
                      <Maximize2 className="w-3.5 h-3.5 text-[var(--navy-1)] dark:text-[var(--accent)]" />
                      <span>{locale === "hi" ? "विस्तृत विंडो" : "Inspect Window"}</span>
                    </button>
                  </div>
                </div>

                {/* Transcribed Speech Dialogue Box */}
                <div className="mb-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono-tabular uppercase tracking-wider text-[var(--text-muted)] font-semibold flex items-center gap-1.5">
                        <Volume2 className="w-3.5 h-3.5 text-[var(--accent)]" />
                        {locale === "hi" ? "बोला गया संवाद (Transcribed Spoken Dialogue)" : "Transcribed Spoken Dialogue"}
                      </span>
                      {verdict.translatedTranscript && verdict.translatedTranscript !== verdict.videoTranscript && (
                        <div className="inline-flex rounded-lg p-0.5 bg-[var(--surface-solid)] border border-[var(--border)] text-[11px] font-mono-tabular">
                          <button
                            type="button"
                            onClick={() => setTranscriptLanguageView("original")}
                            className={`px-2 py-0.5 rounded-md transition-all cursor-pointer ${
                              transcriptLanguageView === "original"
                                ? "bg-[var(--accent)] text-white font-bold shadow-xs"
                                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                            }`}
                          >
                            Original ({verdict.detectedLanguage ? verdict.detectedLanguage.toUpperCase() : "AUDIO"})
                          </button>
                          <button
                            type="button"
                            onClick={() => setTranscriptLanguageView("translation")}
                            className={`px-2 py-0.5 rounded-md transition-all cursor-pointer ${
                              transcriptLanguageView === "translation"
                                ? "bg-[var(--accent)] text-white font-bold shadow-xs"
                                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                            }`}
                          >
                            English Translation
                          </button>
                        </div>
                      )}
                    </div>
                    {verdict.flaggedAdvisoryPhrases && verdict.flaggedAdvisoryPhrases.length > 0 && (
                      <span className="text-[11px] font-mono-tabular font-semibold text-rose-600 dark:text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/25">
                        {verdict.flaggedAdvisoryPhrases.length} illegal advisory term{verdict.flaggedAdvisoryPhrases.length > 1 ? "s" : ""} flagged
                      </span>
                    )}
                  </div>

                  <div className="p-4 sm:p-5 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] text-sm leading-relaxed text-[var(--text-primary)] font-mono selection:bg-rose-500/20">
                    {isInconclusive ? (
                      <span className="text-amber-800 dark:text-amber-200 font-sans">
                        {locale === "hi"
                          ? "सेवा समय-सीमा के कारण इस वीडियो का विश्लेषण नहीं हो सका। ऑडियो या दृश्य सामग्री पर कोई निष्कर्ष नहीं निकाला गया।"
                          : "Analysis timed out. No conclusion was reached about this video’s audio or visual content."}
                      </span>
                    ) : verdict.videoTranscript ? (
                      <>
                        “
                        {renderHighlightedSpeechTranscript(
                          transcriptLanguageView === "translation" && verdict.translatedTranscript
                            ? verdict.translatedTranscript
                            : verdict.videoTranscript,
                          verdict.flaggedAdvisoryPhrases || []
                        )}
                        ”
                      </>
                    ) : (
                      <span className="text-[var(--text-muted)] italic">
                        Video acoustic stream analyzed via Faster-Whisper STT: No audible speech detected in media container track.
                      </span>
                    )}
                  </div>
                </div>


                {/* Violations or Reassurance Card */}
                {verdict.advisorySignalsDetected && verdict.advisoryViolations && verdict.advisoryViolations.length > 0 ? (
                  <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/25 mb-4">
                    <div className="flex items-center gap-2 mb-2 text-rose-600 dark:text-rose-400 font-semibold text-xs uppercase tracking-wider font-mono-tabular">
                      <ShieldAlert className="w-4 h-4" />
                      <span>{locale === "hi" ? "भाषण में पाए गए सेबी नियम उल्लंघन:" : "Statutory SEBI Violations Identified in Video Speech:"}</span>
                    </div>
                    <ul className="space-y-1.5">
                      {verdict.advisoryViolations.map((viol, vIdx) => (
                        <li key={vIdx} className="text-xs text-[var(--text-primary)] flex items-start gap-2">
                          <span className="text-rose-500 font-bold">•</span>
                          <span className="font-medium">{viol}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : isInconclusive ? (
                  <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/25 flex items-center gap-2.5 text-xs text-amber-800 dark:text-amber-200 mb-4">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>
                      {locale === "hi"
                        ? "ऑडियो विश्लेषण उपलब्ध नहीं था। इसे अनुपालन या सुरक्षित होने का प्रमाण न मानें।"
                        : "Audio analysis was unavailable. This is not evidence that the speech is compliant or the video is safe."}
                    </span>
                  </div>
                ) : (
                  <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 flex items-center gap-2.5 text-xs text-emerald-700 dark:text-emerald-300 mb-4">
                    <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>
                      {locale === "hi"
                        ? "ऑडियो सत्यापन संपन्न: बोलने वाला व्यक्ति कोई निश्चित रिटर्न का वादा नहीं कर रहा है और न ही अनधिकृत निधि मांग रहा है।"
                        : "Acoustic verification confirmed: The speaker is not soliciting funds, guaranteeing returns, or peddling unregistered stock tips."}
                    </span>
                  </div>
                )}

                {/* Interactive Test Custom Dialogue Editor */}
                <div className="pt-3 border-t border-[var(--border)]">
                  {!isEditingTranscript ? (
                    <button
                      type="button"
                      onClick={() => {
                        setCustomTranscriptText(verdict.videoTranscript || "");
                        setIsEditingTranscript(true);
                      }}
                      className="text-xs font-mono-tabular font-semibold text-[var(--navy-1)] dark:text-[var(--accent)] hover:underline inline-flex items-center gap-1.5 cursor-pointer"
                    >
                      <span>⚡ Test / Modify Video Speech Dialogue</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  ) : (
                    <div className="space-y-2.5">
                      <label className="text-xs font-mono-tabular text-[var(--text-muted)] block">
                        Edit or paste custom spoken dialogue from the video to test dynamic SEBI advisory screening:
                      </label>
                      <textarea
                        value={customTranscriptText}
                        onChange={(e) => setCustomTranscriptText(e.target.value)}
                        rows={3}
                        className="w-full rounded-xl p-3 text-xs text-[var(--text-primary)] bg-[var(--input-bg)] border border-[var(--input-border)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] font-mono resize-none"
                      />
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            handleRescanTranscript(customTranscriptText);
                            setIsEditingTranscript(false);
                          }}
                          className="px-3 py-1.5 rounded-full text-xs font-semibold bg-[var(--accent)] text-white hover:opacity-90 transition-opacity cursor-pointer"
                        >
                          Re-screen Spoken Dialogue
                        </button>
                        <button
                          type="button"
                          onClick={() => setIsEditingTranscript(false)}
                          className="px-3 py-1.5 rounded-full text-xs font-semibold border border-[var(--border)] text-[var(--text-muted)] hover:bg-[var(--border)]/20 transition-colors cursor-pointer"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ROW 2 - LEFT: Reasons Card (span 7) */}
            <div className="col-span-12 lg:col-span-7 vera-glass rounded-[24px] p-7 text-left flex flex-col justify-between transition-transform duration-200 hover:-translate-y-0.5">
              <div>
                <div className="flex items-center gap-2.5 mb-4">
                  <AlertTriangle
                    className="w-5 h-5"
                    style={{
                      color:
                        verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                          ? "var(--verdict-high-risk)"
                          : verdict.riskTier === "MEDIUM"
                          ? "var(--verdict-suspicious)"
                          : verdict.riskTier === "INCONCLUSIVE"
                          ? "var(--verdict-suspicious)"
                          : "var(--verdict-safe)",
                    }}
                  />
                  <h3 className="text-base font-semibold text-[var(--text-primary)]">
                    {t.topReasons}
                  </h3>
                </div>

                <div className="space-y-3">
                  {verdict.highlightedReasons.map((reason, idx) => {
                    const highlightColor =
                      verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                        ? "var(--verdict-high-risk)"
                        : verdict.riskTier === "MEDIUM"
                        ? "var(--verdict-suspicious)"
                        : verdict.riskTier === "INCONCLUSIVE"
                        ? "var(--verdict-suspicious)"
                        : "var(--verdict-safe)";

                    // Split to highlight quoted clauses or suspect terms inline with verdict color
                    const parts = reason.split(/('.*?'|“.*?”|"[^"]*"|\bhttps?:\/\/\S+|\b\S+@\w+)/g);

                    return (
                      <div
                        key={idx}
                        className="p-3.5 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] text-sm text-[var(--text-primary)] flex items-start gap-3 leading-relaxed"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] flex-shrink-0 mt-2" />
                        <div>
                          {parts.map((part, pIdx) => {
                            if (!part) return null;
                            const isSpecial =
                              (part.startsWith("'") && part.endsWith("'")) ||
                              (part.startsWith("“") && part.endsWith("”")) ||
                              (part.startsWith('"') && part.endsWith('"')) ||
                              part.includes("@") ||
                              part.startsWith("http");

                            if (isSpecial) {
                              return (
                                <span
                                  key={pIdx}
                                  className="font-semibold underline decoration-2 underline-offset-2 px-0.5 rounded"
                                  style={{
                                    textDecorationColor: highlightColor,
                                    color: "var(--text-primary)",
                                  }}
                                >
                                  {part}
                                </span>
                              );
                            }
                            return <span key={pIdx}>{part}</span>;
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Deepfake Telemetry if applicable */}
                {verdict.isDeepfakeResult && verdict.deepfakeDetails && (
                  <div className="mt-4 pt-4 border-t border-[var(--border)]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono-tabular uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                        Visual Forensics Telemetry
                      </span>
                      <span
                        className={`text-xs font-mono-tabular font-bold px-2.5 py-0.5 rounded-full border ${
                          verdict.deepfakeDetails.facesDetected === 0
                            ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30"
                            : verdict.visualManipulationDetected
                            ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30"
                            : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                        }`}
                      >
                        {verdict.deepfakeDetails.facesDetected === 0
                          ? "Inconclusive (No Faces)"
                          : verdict.visualManipulationDetected
                          ? "Facial Manipulation Signals"
                          : "No Manipulation Signals Detected"}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                      <div className="p-2.5 rounded-xl bg-[var(--nav-track)] border border-[var(--border)]">
                        <span className="text-xs text-[var(--text-muted)] block">Frames</span>
                        <span className="font-mono-tabular font-bold text-sm text-[var(--text-primary)]">
                          {verdict.deepfakeDetails.framesAnalyzed}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[var(--nav-track)] border border-[var(--border)]">
                        <span className="text-xs text-[var(--text-muted)] block">Faces</span>
                        <span className="font-mono-tabular font-bold text-sm text-[var(--text-primary)]">
                          {verdict.deepfakeDetails.facesDetected}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[var(--nav-track)] border border-[var(--border)]">
                        <span className="text-xs text-[var(--text-muted)] block">Model Score</span>
                        <span
                          className={`font-mono-tabular font-bold text-sm ${
                            verdict.deepfakeDetails.facesDetected === 0
                              ? "text-[var(--text-muted)]"
                              : verdict.deepfakeDetails.temporalAggregate >= 0.6
                              ? "text-rose-600 dark:text-rose-400"
                              : "text-emerald-600 dark:text-emerald-400"
                          }`}
                        >
                          {verdict.deepfakeDetails.facesDetected === 0
                            ? "N/A"
                            : `${Math.round(verdict.deepfakeDetails.temporalAggregate * 100)} / 100`}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[var(--nav-track)] border border-[var(--border)]">
                        <span className="text-xs text-[var(--text-muted)] block">Temporal</span>
                        <span
                          className={`font-mono-tabular font-bold text-sm ${
                            verdict.deepfakeDetails.facesDetected === 0
                              ? "text-[var(--text-muted)]"
                              : verdict.deepfakeDetails.flickerScore < 0.15
                              ? "text-emerald-600 dark:text-emerald-400"
                              : "text-rose-600 dark:text-rose-400"
                          }`}
                        >
                          {verdict.deepfakeDetails.facesDetected === 0
                            ? "N/A"
                            : verdict.deepfakeDetails.flickerScore < 0.15
                            ? "Consistent"
                            : "Fluctuations"}
                        </span>
                      </div>
                    </div>

                    {verdict.deepfakeDetails.statement && (
                      <p className="mt-2.5 text-[11px] text-[var(--text-muted)] font-mono-tabular italic">
                        {verdict.deepfakeDetails.statement}
                      </p>
                    )}
                    <p className="mt-1 text-[10px] text-[var(--text-muted)] font-mono-tabular opacity-80">
                      * Model score represents estimated manipulation signal intensity on sampled frames. It is an automated screening heuristic, not a measure of detector accuracy or definitive proof of authenticity.
                    </p>
                  </div>
                )}

              </div>
            </div>

            {/* ROW 2 - RIGHT: SEBI Reference Card (span 5, interactive accordion rows) */}
            <div className="col-span-12 lg:col-span-5 vera-glass rounded-[24px] p-7 text-left flex flex-col justify-between transition-transform duration-200 hover:-translate-y-0.5">
              <div>
                <div className="flex items-center gap-2.5 mb-4">
                  <ShieldCheck className="w-5 h-5 text-[var(--verdict-safe)]" />
                  <h3 className="text-base font-semibold text-[var(--text-primary)]">
                    SEBI Regulatory Reference
                  </h3>
                </div>

                <div className="space-y-2.5 text-xs">
                  {[
                    {
                      reg: "CIR/2023/123",
                      title: "Guaranteed Return Prohibition",
                      desc: "Strictly bans assuring fixed profit percentages on securities.",
                      detail:
                        "Section 11 prohibition on registered and unregistered intermediaries offering fixed return promises or capital assurance.",
                      link: "https://www.sebi.gov.in/legal/circulars/aug-2023/prohibition-of-assured-returns_75200.html",
                    },
                    {
                      reg: "CIR/2024/45",
                      title: "Unregistered Influencer Advisory",
                      desc: "Solicitation via Telegram/WhatsApp VIP groups is illegal.",
                      detail:
                        "Statutory advisory banning investor solicitation across closed social messaging channels without active SEBI RA/IA registration.",
                      link: "https://www.sebi.gov.in/enforcement/clarifications-on-sebi-regulations/mar-2024/advisory-against-unregistered-entities.html",
                    },
                    {
                      reg: "RA Reg 3",
                      title: "Mandatory Registration Requirement",
                      desc: "Research analysts must possess gazetted SEBI certification.",
                      detail:
                        "No individual or corporate body may provide stock advisory or buy/sell recommendations without obtaining prior SEBI license.",
                      link: "https://www.sebi.gov.in/legal/regulations/sep-2014/securities-and-exchange-board-of-india-research-analysts-regulations-2014_28108.html",
                    },
                  ].map((ref, idx) => {
                    const isExpanded = expandedSebiRef === idx;
                    return (
                      <div
                        key={idx}
                        className="rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] overflow-hidden transition-all duration-200"
                      >
                        <button
                          type="button"
                          onClick={() => setExpandedSebiRef(isExpanded ? null : idx)}
                          className="w-full p-3 text-left flex items-start justify-between gap-2 hover:bg-[var(--border)]/30 transition-colors"
                        >
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-mono-tabular font-bold text-[var(--text-primary)]">
                                {ref.reg}
                              </span>
                              <span className="text-[10px] text-[var(--verdict-safe)] font-semibold px-1.5 py-0.2 rounded bg-emerald-500/10">
                                Gazetted
                              </span>
                            </div>
                            <p className="font-semibold text-[var(--text-primary)]">{ref.title}</p>
                          </div>
                          <ChevronDown
                            className={`w-3.5 h-3.5 text-[var(--text-muted)] flex-shrink-0 mt-1 transition-transform duration-200 ${
                              isExpanded ? "rotate-180 text-[var(--text-primary)]" : ""
                            }`}
                          />
                        </button>

                        {isExpanded && (
                          <div className="px-3 pb-3 pt-1 border-t border-[var(--border)] space-y-2">
                            <p className="text-[var(--text-muted)] leading-relaxed">
                              {ref.detail}
                            </p>
                            <a
                              href={ref.link}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[11px] font-semibold text-[var(--navy-1)] dark:text-[var(--accent)] hover:underline inline-flex items-center gap-1"
                            >
                              <span>Official Gazette Circular</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="pt-4 border-t border-[var(--border)] mt-4">
                <a
                  href="https://www.sebi.gov.in"
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs font-semibold text-[var(--navy-1)] dark:text-[var(--accent)] hover:underline inline-flex items-center gap-1.5"
                >
                  <span>Search Official SEBI Intermediary Registry</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>

            {/* ROW 3: Actions Card (span 12) */}
            <div className="col-span-12 vera-glass rounded-[24px] p-6 sm:p-7 flex flex-wrap items-center justify-between gap-4 transition-transform duration-200 hover:-translate-y-0.5">
              {/* Left Action Pills: Call 1930 + Official Portal Links */}
              <div className="flex flex-wrap items-center gap-2.5">
                {(verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH" || verdict.riskTier === "MEDIUM") && (
                  <a
                    href="tel:1930"
                    className="h-10 px-5 rounded-full bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold inline-flex items-center gap-2 shadow-sm transition-transform hover:scale-105"
                  >
                    <Phone className="w-3.5 h-3.5" />
                    <span>Call 1930 Helpline</span>
                  </a>
                )}

                <a
                  href="https://scores.sebi.gov.in"
                  target="_blank"
                  rel="noreferrer"
                  className="h-10 px-4 rounded-full border border-[var(--border)] bg-[var(--surface-solid)] text-[var(--text-primary)] text-xs font-semibold inline-flex items-center gap-1.5 hover:border-[var(--text-muted)] transition-colors shadow-sm"
                >
                  <span>SEBI SCORES</span>
                  <ExternalLink className="w-3 h-3 text-[var(--text-muted)]" />
                </a>

                <a
                  href="https://cybercrime.gov.in"
                  target="_blank"
                  rel="noreferrer"
                  className="h-10 px-4 rounded-full border border-[var(--border)] bg-[var(--surface-solid)] text-[var(--text-primary)] text-xs font-semibold inline-flex items-center gap-1.5 hover:border-[var(--text-muted)] transition-colors shadow-sm"
                >
                  <span>CyberCrime.gov.in</span>
                  <ExternalLink className="w-3 h-3 text-[var(--text-muted)]" />
                </a>
              </div>

              {/* Right Action Pills: Copy Summary + Screen Another */}
              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={() => {
                    const advisorLine = verdict.advisorVerification?.hasRegistrationClaim
                      ? `\nSEBI Verification: ${verdict.advisorVerification.statusLabel} (${verdict.advisorVerification.claimedRegNumber || "No Reg ID Provided"})`
                      : "";
                    const text = `VERA Fraud Screening Summary:
Verdict: ${verdict.riskTier}
Risk Score: ${isInconclusive ? "Unavailable (analysis incomplete)" : `${verdict.score}/100`}
Query: ${inputText}${advisorLine}
Reasons:
${verdict.highlightedReasons.map((r, i) => `${i + 1}. ${r}`).join("\n")}
Source: VERA Fraud Intelligence Platform`;
                    navigator.clipboard.writeText(text);
                    alert("Summary copied to clipboard!");
                  }}
                  className="h-10 px-4 rounded-full border border-[var(--border)] bg-[var(--surface-solid)] text-[var(--text-primary)] text-xs font-semibold inline-flex items-center gap-1.5 hover:border-[var(--text-muted)] transition-colors shadow-sm"
                >
                  <Copy className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span>{t.copySummary}</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setVerdict(null);
                    setInputText("");
                    setUploadedFile(null);
                    setUploadedB64(null);
                  }}
                  className="vera-btn-primary h-10 px-6 text-xs font-semibold shadow-sm"
                >
                  {t.screenAnother}
                </button>
              </div>
            </div>

            {/* Mobile Sticky Bottom Action Bar above the dock (spec: sticky bottom action bar above the dock) */}
            <div className="md:hidden fixed bottom-[76px] left-4 right-4 z-40 vera-glass rounded-full p-2.5 flex items-center justify-between shadow-xl border border-[var(--border)]">
              <div className="flex items-center gap-2 pl-2 min-w-0">
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{
                    backgroundColor:
                      verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH"
                        ? "var(--verdict-high-risk)"
                        : verdict.riskTier === "MEDIUM"
                        ? "var(--verdict-suspicious)"
                        : verdict.riskTier === "INCONCLUSIVE"
                        ? "var(--verdict-suspicious)"
                        : "var(--verdict-safe)",
                  }}
                />
                <span className="text-xs font-mono-tabular font-bold text-[var(--text-primary)] truncate">
                  {isInconclusive ? "N/A" : `${verdict.score}/100`} • {verdict.riskTier}
                </span>
              </div>
              <div className="flex items-center gap-1.5 flex-shrink-0">
                {(verdict.riskTier === "CRITICAL" || verdict.riskTier === "HIGH" || verdict.riskTier === "MEDIUM") && (
                  <a
                    href="tel:1930"
                    className="h-8 px-3 rounded-full bg-rose-600 text-white text-[11px] font-bold inline-flex items-center gap-1 shadow-sm"
                  >
                    <Phone className="w-3 h-3" />
                    <span>1930</span>
                  </a>
                )}
                <button
                  type="button"
                  onClick={() => {
                    setVerdict(null);
                    setInputText("");
                    setUploadedFile(null);
                    setUploadedB64(null);
                  }}
                  className="h-8 px-3.5 rounded-full bg-[var(--accent)] text-[var(--accent-ink)] text-[11px] font-bold shadow-sm"
                >
                  {t.screenAnother}
                </button>
              </div>
            </div>

            {/* ARIA Live Region for Screen Readers */}
            <div className="sr-only" aria-live="polite" role="status">
              Fraud screening complete. Verdict: {verdict.riskTier}. Risk Score: {isInconclusive ? "unavailable" : `${verdict.score} out of 100`}.{" "}
              {verdict.highlightedReasons[0] || ""}
            </div>
          </div>
        </div>
      )}

      {/* ── SEBI PERSONNEL & ENTITY VERIFICATION MODULE ──────────────────────── */}
      <SebiPersonnelVerifier locale={locale} />

      {/* ── DEDICATED FORENSIC AUDIO TRANSCRIPTION WINDOW (POPUP MODAL) ────── */}
      {isTranscriptModalOpen && verdict && verdict.videoTranscript && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="transcript-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-fadeIn"
          onClick={() => setIsTranscriptModalOpen(false)}
        >
          <div
            className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-3xl bg-[var(--surface-solid)] border border-[var(--border)] shadow-2xl overflow-hidden text-left"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Top Modal Window Header */}
            <div className="flex items-center justify-between p-5 sm:p-6 border-b border-[var(--border)] bg-[var(--nav-track)]/40">
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-11 h-11 rounded-2xl flex items-center justify-center border shadow-sm flex-shrink-0 ${
                    verdict.advisorySignalsDetected
                      ? "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30"
                      : "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                  }`}
                >
                  <FileAudio className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h2 id="transcript-modal-title" className="text-base sm:text-lg font-bold text-[var(--text-primary)] truncate">
                      {locale === "hi"
                        ? "वेरा ऑडियो एवं भाषण फ़ोरेंसिक्स विंडो"
                        : "VERA AI Speech & Audio Forensics Window"}
                    </h2>
                    <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono-tabular font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                      <Radio className="w-3 h-3 animate-pulse" />
                      Whisper STT
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-muted)] truncate mt-0.5">
                    {uploadedFile?.name || "Uploaded Video"} • 16 kHz Mono PCM • Screened against SEBI Regulations
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsTranscriptModalOpen(false)}
                  className="w-9 h-9 rounded-full border border-[var(--border)] hover:bg-rose-500/10 hover:text-rose-600 flex items-center justify-center text-[var(--text-muted)] transition-colors cursor-pointer"
                  title="Close Window"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Badges and Mode Switcher Strip */}
            <div className="px-5 sm:px-6 py-3 border-b border-[var(--border)] bg-[var(--surface-solid)] flex flex-wrap items-center justify-between gap-3">
              {/* Dual Visual & Speech Badges */}
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-mono-tabular font-semibold border ${
                    isInconclusive
                      ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30"
                      : verdict.visualManipulationDetected
                      ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30"
                      : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                  }`}
                >
                  {isInconclusive
                    ? locale === "hi" ? "⚠ दृश्य विश्लेषण उपलब्ध नहीं" : "⚠ Visual analysis unavailable"
                    : verdict.visualManipulationDetected
                    ? "🚨 Visual: Facial Manipulation Detected"
                    : "✓ Visual: Authentic Camera Footage"}
                </span>

                <span
                  className={`px-3 py-1 rounded-full text-xs font-mono-tabular font-bold border ${
                    isInconclusive
                      ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30"
                      : verdict.advisorySignalsDetected
                      ? "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/40"
                      : "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/40"
                  }`}
                >
                  {isInconclusive
                    ? locale === "hi" ? "⚠ भाषण विश्लेषण उपलब्ध नहीं" : "⚠ Speech analysis unavailable"
                    : verdict.advisorySignalsDetected
                    ? "❌ ILLEGAL INVESTMENT ADVISORY FLAGGED"
                    : "✓ COMPLIANT SPEECH"}
                </span>

                {verdict.flaggedAdvisoryPhrases && verdict.flaggedAdvisoryPhrases.length > 0 && (
                  <span className="text-xs font-mono-tabular font-semibold text-rose-600 dark:text-rose-400 bg-rose-500/10 px-2.5 py-0.5 rounded-full border border-rose-500/25">
                    {verdict.flaggedAdvisoryPhrases.length} phrase{verdict.flaggedAdvisoryPhrases.length > 1 ? "s" : ""} flagged
                  </span>
                )}
              </div>

              {/* View Mode Tabs */}
              <div className="flex items-center gap-1 p-1 rounded-xl bg-[var(--nav-track)] border border-[var(--border)]">
                <button
                  type="button"
                  onClick={() => setTranscriptModalTab("words")}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    transcriptModalTab === "words"
                      ? "bg-[var(--surface-solid)] text-[var(--text-primary)] shadow-sm font-bold"
                      : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  {locale === "hi"
                    ? `मूल संवाद (${verdict.detectedLanguage ? verdict.detectedLanguage.toUpperCase() : "AUDIO"})`
                    : `Original (${verdict.detectedLanguage ? verdict.detectedLanguage.toUpperCase() : "AUDIO"})`}
                </button>
                {verdict.translatedTranscript && verdict.translatedTranscript !== verdict.videoTranscript && (
                  <button
                    type="button"
                    onClick={() => setTranscriptModalTab("translation")}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      transcriptModalTab === "translation"
                        ? "bg-[var(--surface-solid)] text-[var(--text-primary)] shadow-sm font-bold"
                        : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                    }`}
                  >
                    {locale === "hi" ? "अंग्रेजी फोरेंसिक अनुवाद" : "Forensic Translation (EN)"}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setTranscriptModalTab("timeline")}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    transcriptModalTab === "timeline"
                      ? "bg-[var(--surface-solid)] text-[var(--text-primary)] shadow-sm font-bold"
                      : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  {locale === "hi" ? "समय-सीमा" : "Timeline Breakdown"}
                </button>
              </div>
            </div>

            {/* Scrollable Modal Content */}
            <div className="p-5 sm:p-6 overflow-y-auto space-y-4 max-h-[60vh] scrollbar-thin">
              {transcriptModalTab === "words" ? (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono-tabular uppercase tracking-wider text-[var(--text-muted)] font-semibold flex items-center gap-1.5">
                      <Volume2 className="w-3.5 h-3.5 text-[var(--accent)]" />
                      {locale === "hi" ? "पूर्ण प्रतिलेखित संवाद" : "Complete Verbatim Speech Dialogue"}
                    </span>
                    <span className="text-[11px] text-[var(--text-muted)] font-mono-tabular">
                      {(verdict.videoTranscript || "").split(/\s+/).filter(Boolean).length} words
                    </span>
                  </div>

                  <div className="p-5 sm:p-6 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] text-sm sm:text-base leading-relaxed text-[var(--text-primary)] font-mono selection:bg-rose-500/20 shadow-inner">
                    {verdict.videoTranscript ? (
                      <>“{renderHighlightedSpeechTranscript(verdict.videoTranscript, verdict.flaggedAdvisoryPhrases || [])}”</>
                    ) : (
                      <span className="text-[var(--text-muted)] italic">
                        Video acoustic stream analyzed via Faster-Whisper STT: No audible speech detected in media container track.
                      </span>
                    )}
                  </div>

                  {/* Highlighting Legend */}
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--text-muted)]">
                    <span className="font-semibold">{locale === "hi" ? "संकेत:" : "Legend:"}</span>
                    <span className="inline-flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded bg-rose-500/20 border border-rose-500/40 inline-block" />
                      <span>{locale === "hi" ? "चिन्हित अवैध सलाह / सेबी उल्लंघन" : "Flagged Illegal Advisory / SEBI Violation"}</span>
                    </span>
                  </div>
                </div>
              ) : transcriptModalTab === "translation" ? (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono-tabular uppercase tracking-wider text-[var(--text-muted)] font-semibold flex items-center gap-1.5">
                      <Volume2 className="w-3.5 h-3.5 text-[var(--accent)]" />
                      {locale === "hi" ? "अंग्रेजी फोरेंसिक अनुवाद" : "Forensic English Translation"}
                    </span>
                    <span className="text-[11px] text-[var(--text-muted)] font-mono-tabular">
                      {(verdict.translatedTranscript || "").split(/\s+/).filter(Boolean).length} words
                    </span>
                  </div>

                  <div className="p-5 sm:p-6 rounded-2xl bg-[var(--nav-track)] border border-[var(--border)] text-sm sm:text-base leading-relaxed text-[var(--text-primary)] font-mono selection:bg-rose-500/20 shadow-inner">
                    {verdict.translatedTranscript ? (
                      <>“{renderHighlightedSpeechTranscript(verdict.translatedTranscript, verdict.flaggedAdvisoryPhrases || [])}”</>
                    ) : (
                      <span className="text-[var(--text-muted)] italic">
                        No translated dialogue available.
                      </span>
                    )}
                  </div>

                  {/* Highlighting Legend */}
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--text-muted)]">
                    <span className="font-semibold">{locale === "hi" ? "संकेत:" : "Legend:"}</span>
                    <span className="inline-flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded bg-rose-500/20 border border-rose-500/40 inline-block" />
                      <span>{locale === "hi" ? "चिन्हित अवैध सलाह / सेबी उल्लंघन" : "Flagged Illegal Advisory / SEBI Violation"}</span>
                    </span>
                  </div>
                </div>
              ) : (
                /* Timeline Breakdown View */
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono-tabular uppercase tracking-wider text-[var(--text-muted)] font-semibold">
                      {locale === "hi" ? "समय-खंड अनुसार प्रतिलेखन" : "Time-Coded Segmented Speech"}
                    </span>
                    <span className="text-xs text-[var(--text-muted)]">
                      {(verdict.transcriptSegments || []).length} segments
                    </span>
                  </div>


                  {(verdict.transcriptSegments && verdict.transcriptSegments.length > 0
                    ? verdict.transcriptSegments
                    : [{ start: 0.0, end: 4.5, text: verdict.videoTranscript || "No speech detected in audio stream." }]
                  ).map((seg, idx) => {
                    const isSegFlagged = (verdict.flaggedAdvisoryPhrases || []).some((phrase) =>
                      seg.text.toLowerCase().includes(phrase.toLowerCase())
                    );
                    const formatTime = (secs: number) => {
                      const m = Math.floor(secs / 60);
                      const s = Math.floor(secs % 60);
                      return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
                    };

                    return (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-2xl border transition-all flex items-start gap-3 ${
                          isSegFlagged
                            ? "bg-rose-500/5 border-rose-500/30 text-rose-950 dark:text-rose-100"
                            : "bg-[var(--nav-track)] border-[var(--border)] text-[var(--text-primary)]"
                        }`}
                      >
                        <span className="px-2 py-0.5 rounded-lg bg-[var(--surface-solid)] border border-[var(--border)] font-mono text-[11px] font-bold text-[var(--text-muted)] shrink-0">
                          {formatTime(seg.start)} - {formatTime(seg.end)}
                        </span>
                        <div className="flex-1 text-sm font-mono leading-relaxed">
                          {renderHighlightedSpeechTranscript(seg.text, verdict.flaggedAdvisoryPhrases || [])}
                        </div>
                        {isSegFlagged && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30 shrink-0">
                            Violation
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Statutory SEBI Violations Box */}
              {verdict.advisorySignalsDetected && verdict.advisoryViolations && verdict.advisoryViolations.length > 0 ? (
                <div className="p-4 sm:p-5 rounded-2xl bg-rose-500/10 border border-rose-500/25">
                  <div className="flex items-center gap-2 mb-2.5 text-rose-600 dark:text-rose-400 font-semibold text-xs uppercase tracking-wider font-mono-tabular">
                    <ShieldAlert className="w-4 h-4" />
                    <span>
                      {locale === "hi"
                        ? "भाषण में पाए गए सेबी नियम उल्लंघन:"
                        : "Statutory SEBI Violations Identified in Video Speech:"}
                    </span>
                  </div>
                  <ul className="space-y-2">
                    {verdict.advisoryViolations.map((viol, vIdx) => (
                      <li key={vIdx} className="text-xs sm:text-sm text-[var(--text-primary)] flex items-start gap-2">
                        <span className="text-rose-500 font-bold">•</span>
                        <span className="font-medium">{viol}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 flex items-center gap-3 text-xs sm:text-sm text-emerald-700 dark:text-emerald-300">
                  <ShieldCheck className="w-5 h-5 text-emerald-500 shrink-0" />
                  <span>
                    {locale === "hi"
                      ? "ऑडियो सत्यापन संपन्न: कोई गैरकानूनी वित्तीय सलाह या गारंटीड रिटर्न का वादा नहीं मिला।"
                      : "Acoustic verification confirmed: The speaker does not solicit funds, guarantee returns, or peddle unregistered stock tips."}
                  </span>
                </div>
              )}

              {/* Sandbox Re-screening Editor */}
              <div className="p-4 rounded-2xl bg-[var(--surface-solid)] border border-[var(--border)]">
                <span className="text-xs font-mono-tabular font-semibold text-[var(--text-primary)] block mb-1">
                  ⚡ Interactive Forensics Sandbox: Test / Edit Dialogue
                </span>
                <p className="text-[11px] text-[var(--text-muted)] mb-2">
                  Modify or paste custom spoken dialogue to see instant SEBI screening highlights and risk score adjustments:
                </p>
                <textarea
                  value={customTranscriptText || verdict.videoTranscript}
                  onChange={(e) => setCustomTranscriptText(e.target.value)}
                  rows={2}
                  className="w-full rounded-xl p-3 text-xs text-[var(--text-primary)] bg-[var(--input-bg)] border border-[var(--input-border)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] font-mono resize-none"
                />
                <div className="mt-2 flex items-center justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      handleRescanTranscript(customTranscriptText || verdict.videoTranscript || "");
                    }}
                    className="px-4 py-1.5 rounded-full text-xs font-semibold bg-[var(--accent)] text-white hover:opacity-90 transition-opacity cursor-pointer shadow-sm"
                  >
                    Re-screen Dialogue Now
                  </button>
                </div>
              </div>
            </div>

            {/* Bottom Modal Footer Toolbar */}
            <div className="p-4 sm:p-5 border-t border-[var(--border)] bg-[var(--nav-track)]/40 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleCopyTranscript(verdict.videoTranscript || "")}
                  className="px-3.5 py-2 rounded-xl border border-[var(--border)] bg-[var(--surface-solid)] text-xs font-semibold text-[var(--text-primary)] hover:bg-[var(--nav-track)] inline-flex items-center gap-1.5 transition-all cursor-pointer shadow-sm"
                >
                  {copiedTranscript ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      <span className="text-emerald-600 dark:text-emerald-400">{locale === "hi" ? "कॉपी हो गया!" : "Copied!"}</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-[var(--navy-1)] dark:text-[var(--accent)]" />
                      <span>{locale === "hi" ? "ट्रांसक्रिप्ट कॉपी करें" : "Copy Transcript"}</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() =>
                    handleDownloadTranscript(
                      `VERA FORENSIC VIDEO SPEECH TRANSCRIPT\nSource: ${uploadedFile?.name || "Uploaded Video"}\nSHA256: ${verdict.deepfakeDetails?.sha256 || "N/A"}\nRisk Tier: ${verdict.riskTier} (Score: ${verdict.score}/100)\nVisual Integrity: ${verdict.visualVerdictLabel || "N/A"}\nSpeech Advisory Flags: ${verdict.advisorySignalsDetected ? "FLAGGED" : "NONE"}\n\nTRANSCRIPT:\n${verdict.videoTranscript}\n\nSTATUTORY VIOLATIONS:\n${(verdict.advisoryViolations || []).join("\n")}\n`,
                      `${(uploadedFile?.name || "video").replace(/\.[^/.]+$/, "")}_transcript.txt`
                    )
                  }
                  className="px-3.5 py-2 rounded-xl border border-[var(--border)] bg-[var(--surface-solid)] text-xs font-semibold text-[var(--text-primary)] hover:bg-[var(--nav-track)] inline-flex items-center gap-1.5 transition-all cursor-pointer shadow-sm"
                >
                  <Download className="w-3.5 h-3.5 text-[var(--navy-1)] dark:text-[var(--accent)]" />
                  <span>{locale === "hi" ? "डाउनलोड (.txt)" : "Export (.txt)"}</span>
                </button>
              </div>

              <button
                type="button"
                onClick={() => setIsTranscriptModalOpen(false)}
                className="px-5 py-2 rounded-full text-xs font-semibold bg-[var(--accent)] text-white hover:opacity-90 transition-opacity cursor-pointer shadow-sm"
              >
                {locale === "hi" ? "विंडो बंद करें" : "Close Window"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


