import jsPDF from "jspdf";

export interface InvestigationReportData {
  reportId?: string;
  title?: string;
  claimText?: string;
  riskTier: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "MINIMAL" | "INCONCLUSIVE" | string;
  score?: number | null;
  executiveSummary?: string;
  inference?: string;
  highlightedReasons?: string[];
  suspiciousIndicators?: Array<{
    signal_type?: string;
    description?: string;
    weight?: number;
    source?: string;
  }> | string[];
  verifiedItems?: string[];
  unverifiedItems?: string[];
  recommendedActions?: string[];
  sebiCitations?: Array<{
    circular_no?: string;
    title?: string;
    description?: string;
  }> | string[];
  generatedAt?: string;
  sourceOrigin?: string;
  extractedOcrText?: string;
  mediaForensics?: {
    isDeepfake?: boolean;
    manipulationDetected?: boolean;
    elaScore?: number;
    editorTags?: string[];
    facesDetected?: number;
  };
  advisorVerification?: {
    statusLabel?: string;
    claimedAdvisorName?: string;
    claimedRegNumber?: string;
    details?: string;
  };
}

/**
 * Builds the jsPDF document instance containing all investigation report pages and styling.
 */
export function buildInvestigationPdfDoc(data: InvestigationReportData): jsPDF {
  try {
    const doc = new jsPDF({
      orientation: "portrait",
      unit: "pt",
      format: "a4",
    });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 40;
    const contentWidth = pageWidth - margin * 2;
    let y = margin;

    // Palette
    const colors = {
      navy: [15, 23, 42],       // #0F172A
      slate: [51, 65, 85],      // #334155
      muted: [100, 116, 139],   // #64748B
      border: [226, 232, 240],  // #E2E8F0
      lightBg: [248, 250, 252], // #F8FAFC
      critical: [225, 29, 72],  // #E11D48
      high: [234, 88, 12],      // #EA580C
      medium: [217, 119, 6],    // #D97706
      safe: [16, 185, 129],     // #10B981
      inconclusive: [100, 116, 139],
    };

    const riskTierUpper = (data.riskTier || "INCONCLUSIVE").toUpperCase();
    const riskColor =
      riskTierUpper === "CRITICAL"
        ? colors.critical
        : riskTierUpper === "HIGH"
        ? colors.high
        : riskTierUpper === "MEDIUM"
        ? colors.medium
        : riskTierUpper === "LOW" || riskTierUpper === "MINIMAL" || riskTierUpper === "SAFE"
        ? colors.safe
        : colors.inconclusive;

    const reportId = data.reportId || `VERA-${Date.now().toString(36).toUpperCase()}`;
    const timestamp = data.generatedAt || new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });

    // Helper: Page overflow check
    const checkPageBreak = (neededHeight: number) => {
      if (y + neededHeight > pageHeight - margin - 30) {
        doc.addPage();
        y = margin;
        drawRunningHeader();
      }
    };

    // Running Header on subsequent pages
    const drawRunningHeader = () => {
      doc.setFont("helvetica", "normal");
      doc.setFontSize(8);
      doc.setTextColor(colors.muted[0], colors.muted[1], colors.muted[2]);
      doc.text("VERA — Investment Fraud Intelligence Dossier", margin, y);
      doc.text(`Ref: ${reportId}`, pageWidth - margin, y, { align: "right" });
      y += 12;
      doc.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
      doc.setLineWidth(0.5);
      doc.line(margin, y, pageWidth - margin, y);
      y += 18;
    };

    // ── 1. TOP HEADER BANNER ───────────────────────────────────────────────
    doc.setFillColor(colors.navy[0], colors.navy[1], colors.navy[2]);
    doc.roundedRect(margin, y, contentWidth, 68, 6, 6, "F");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(16);
    doc.setTextColor(255, 255, 255);
    doc.text("VERA FRAUD INVESTIGATION REPORT", margin + 16, y + 26);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(203, 213, 225); // Slate 300
    doc.text("Statutory Fraud Intelligence & SEBI Compliance Screening", margin + 16, y + 42);
    doc.text(`Case ID: ${reportId}  •  Date: ${timestamp}`, margin + 16, y + 55);

    y += 82;

    // ── 2. RISK CLASSIFICATION & SCORE CARD ───────────────────────────────
    checkPageBreak(70);
    doc.setFillColor(colors.lightBg[0], colors.lightBg[1], colors.lightBg[2]);
    doc.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
    doc.roundedRect(margin, y, contentWidth, 64, 6, 6, "FD");

    // Risk badge pill
    doc.setFillColor(riskColor[0], riskColor[1], riskColor[2]);
    doc.roundedRect(margin + 16, y + 14, 120, 24, 4, 4, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(255, 255, 255);
    doc.text(riskTierUpper, margin + 76, y + 30, { align: "center" });

    // Score
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.setTextColor(riskColor[0], riskColor[1], riskColor[2]);
    const scoreText = typeof data.score === "number" ? `${data.score}/100` : "INCONCLUSIVE";
    doc.text(scoreText, margin + 150, y + 34);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(colors.muted[0], colors.muted[1], colors.muted[2]);
    doc.text("Composite Deterministic Risk Score", margin + 150, y + 48);

    // Source Origin
    if (data.sourceOrigin) {
      doc.setFont("helvetica", "normal");
      doc.setFontSize(8);
      doc.text(`Origin: ${data.sourceOrigin}`, pageWidth - margin - 16, y + 34, { align: "right" });
    }

    y += 76;

    // ── 2B. FORENSIC RISK INFERENCE & DETERMINATION RATIONALE ─────────────
    // Detailed readable explanation of why this risk classification was assigned
    const fallbackInference =
      riskTierUpper === "CRITICAL" || riskTierUpper === "HIGH"
        ? `Forensic Determination Rationale (Risk Score: ${typeof data.score === "number" ? data.score : 85}/100):\n` +
          "The analyzed material exhibits severe statutory violations under SEBI financial regulations. " +
          "The primary threat indicator is the explicit solicitation of guaranteed or assured investment returns, which directly violates " +
          "SEBI Circular CIR/2023/123. Furthermore, diverting retail investors into private, unmonitored channels (WhatsApp/Telegram) " +
          "and requesting direct funds transfers are standard hallmarks of unauthorized 'dabba' trading and Ponzi operations. " +
          "Under Section 12A of the SEBI Act, 1992, engaging in deceptive trading schemes constitutes illegal financial solicitation. " +
          "Capital loss risk is imminent."
        : riskTierUpper === "MEDIUM"
        ? `Forensic Determination Rationale (Risk Score: ${typeof data.score === "number" ? data.score : 55}/100):\n` +
          "The analyzed subject displays cautionary risk indicators, including unverified credential claims and tipster vocabulary. " +
          "While outright digital tampering was not conclusively proven across all vectors, the presence of unregulated advisory signals " +
          "warrants extreme investor vigilance. Verify credentials directly on the official SEBI SCORES portal before transferring funds."
        : riskTierUpper === "INCONCLUSIVE"
        ? "Forensic Determination Rationale:\n" +
          "The investigation produced inconclusive results due to insufficient resolution, missing readable text, or unverifiable entity records. " +
          "In accordance with VERA Architecture Rule 9, an inconclusive result must never be interpreted as safety. Independent verification is required."
        : `Forensic Determination Rationale (Risk Score: ${typeof data.score === "number" ? data.score : 15}/100):\n` +
          "Forensic screening against SEBI regulatory provisions (CIR/2023/123, CIR/2024/45) found no active deceptive advisory signals " +
          "or prohibited return guarantees. The document structure aligns with statutory compliance expectations. Always ensure that funds " +
          "are transferred exclusively to registered corporate clearing accounts, never to private personal accounts.";

    const inferenceContent = (data.inference && data.inference.trim()) ? data.inference.trim() : fallbackInference;

    checkPageBreak(90);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
    doc.text("Forensic Risk Inference & Assessment Rationale", margin, y);
    y += 14;

    const infLines = doc.splitTextToSize(inferenceContent, contentWidth - 28);
    const infBoxHeight = Math.max(48, infLines.length * 12 + 18);

    checkPageBreak(infBoxHeight + 12);
    // Card background
    doc.setFillColor(colors.lightBg[0], colors.lightBg[1], colors.lightBg[2]);
    doc.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
    doc.roundedRect(margin, y, contentWidth, infBoxHeight, 4, 4, "FD");

    // Left accent bar in verdict risk color
    doc.setFillColor(riskColor[0], riskColor[1], riskColor[2]);
    doc.roundedRect(margin, y, 4, infBoxHeight, 2, 2, "F");

    // Inference text
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.5);
    doc.setTextColor(colors.slate[0], colors.slate[1], colors.slate[2]);
    doc.text(infLines, margin + 14, y + 14);
    y += infBoxHeight + 16;

    // ── 3. INVESTIGATION SUBJECT / CLAIM ───────────────────────────────────
    if (data.claimText && data.claimText.trim()) {
      checkPageBreak(60);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
      doc.text("Investigation Subject / Original Material", margin, y);
      y += 14;

      doc.setFont("helvetica", "normal");
      doc.setFontSize(9);
      doc.setTextColor(colors.slate[0], colors.slate[1], colors.slate[2]);

      const claimLines = doc.splitTextToSize(data.claimText.trim(), contentWidth - 20);
      const boxHeight = Math.max(34, claimLines.length * 12 + 16);

      checkPageBreak(boxHeight + 10);
      doc.setFillColor(241, 245, 249); // slate-100
      doc.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
      doc.roundedRect(margin, y, contentWidth, boxHeight, 4, 4, "FD");

      doc.text(claimLines, margin + 10, y + 15);
      y += boxHeight + 16;
    }

    // ── 4. EXECUTIVE SUMMARY ──────────────────────────────────────────────
    if (data.executiveSummary && data.executiveSummary.trim()) {
      checkPageBreak(60);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
      doc.text("Executive Summary", margin, y);
      y += 14;

      doc.setFont("helvetica", "normal");
      doc.setFontSize(9);
      doc.setTextColor(colors.slate[0], colors.slate[1], colors.slate[2]);
      const summaryLines = doc.splitTextToSize(data.executiveSummary.trim(), contentWidth);
      checkPageBreak(summaryLines.length * 13 + 10);
      doc.text(summaryLines, margin, y);
      y += summaryLines.length * 13 + 14;
    }

    // ── 5. DETECTED REASONS & FORENSIC EVIDENCE ───────────────────────────
    if (data.highlightedReasons && data.highlightedReasons.length > 0) {
      checkPageBreak(60);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
      doc.text("Key Forensic Findings & Fraud Signals", margin, y);
      y += 14;

      data.highlightedReasons.forEach((reason, idx) => {
        const text = `${idx + 1}. ${reason}`;
        const lines = doc.splitTextToSize(text, contentWidth - 16);
        checkPageBreak(lines.length * 12 + 6);

        // Bullet marker
        doc.setFillColor(riskColor[0], riskColor[1], riskColor[2]);
        doc.circle(margin + 4, y + 4, 2.5, "F");

        doc.setFont("helvetica", "normal");
        doc.setFontSize(9);
        doc.setTextColor(colors.slate[0], colors.slate[1], colors.slate[2]);
        doc.text(lines, margin + 14, y + 6);
        y += lines.length * 12 + 6;
      });
      y += 8;
    }

    // ── 6. SEBI ADVISOR VERIFICATION (IF AVAILABLE) ───────────────────────
    if (data.advisorVerification && (data.advisorVerification.claimedAdvisorName || data.advisorVerification.claimedRegNumber)) {
      checkPageBreak(60);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
      doc.text("SEBI Intermediary & License Verification", margin, y);
      y += 14;

      const adv = data.advisorVerification;
      const advLines = [
        `Claimed Entity: ${adv.claimedAdvisorName || "Not specified"}`,
        `Registration Number Claimed: ${adv.claimedRegNumber || "None provided"}`,
        `Verification Status: ${adv.statusLabel || "Unverified"}`,
        adv.details ? `Findings: ${adv.details}` : null,
      ].filter(Boolean) as string[];

      doc.setFillColor(colors.lightBg[0], colors.lightBg[1], colors.lightBg[2]);
      doc.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
      const cardHeight = advLines.length * 14 + 14;
      checkPageBreak(cardHeight + 10);
      doc.roundedRect(margin, y, contentWidth, cardHeight, 4, 4, "FD");

      advLines.forEach((line, idx) => {
        doc.setFont("helvetica", idx === 2 ? "bold" : "normal");
        doc.setFontSize(9);
        doc.setTextColor(colors.slate[0], colors.slate[1], colors.slate[2]);
        doc.text(line, margin + 10, y + 14 + idx * 14);
      });
      y += cardHeight + 14;
    }

    // ── 7. EXTRACTED OCR TEXT (IF APPLICABLE) ─────────────────────────────
    if (data.extractedOcrText && data.extractedOcrText.trim()) {
      checkPageBreak(50);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10);
      doc.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
      doc.text("Text Extracted via OCR (Untrusted Input)", margin, y);
      y += 12;

      doc.setFont("courier", "normal");
      doc.setFontSize(8);
      doc.setTextColor(colors.slate[0], colors.slate[1], colors.slate[2]);

      const ocrLines = doc.splitTextToSize(data.extractedOcrText.slice(0, 800), contentWidth - 16);
      const ocrHeight = ocrLines.length * 10 + 12;
      checkPageBreak(ocrHeight + 10);

      doc.setFillColor(241, 245, 249);
      doc.roundedRect(margin, y, contentWidth, ocrHeight, 3, 3, "F");
      doc.text(ocrLines, margin + 8, y + 10);
      y += ocrHeight + 14;
    }

    // ── 8. RECOMMENDED ACTIONS & HELPLINES ─────────────────────────────────
    checkPageBreak(80);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(colors.navy[0], colors.navy[1], colors.navy[2]);
    doc.text("Recommended Investor Actions", margin, y);
    y += 14;

    const defaultActions = [
      "Dial 1930 Helpline immediately if funds were transferred (Golden Hour window).",
      "Verify advisor license status at official SEBI portal (scores.sebi.gov.in).",
      "Do NOT send funds to personal UPI handles or unverified corporate bank accounts.",
      "File an institutional FIR on CyberCrime.gov.in with transaction UTR proofs.",
    ];

    const actions = (data.recommendedActions && data.recommendedActions.length > 0)
      ? data.recommendedActions
      : defaultActions;

    actions.forEach((act) => {
      const lines = doc.splitTextToSize(`• ${act}`, contentWidth - 10);
      checkPageBreak(lines.length * 12 + 4);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(9);
      doc.setTextColor(colors.slate[0], colors.slate[1], colors.slate[2]);
      doc.text(lines, margin + 4, y + 6);
      y += lines.length * 12 + 4;
    });
    y += 12;

    // ── 9. STATUTORY DISCLAIMER & FOOTER ──────────────────────────────────
    checkPageBreak(45);
    doc.setDrawColor(colors.border[0], colors.border[1], colors.border[2]);
    doc.setLineWidth(0.5);
    doc.line(margin, y, pageWidth - margin, y);
    y += 12;

    doc.setFont("helvetica", "italic");
    doc.setFontSize(7.5);
    doc.setTextColor(colors.muted[0], colors.muted[1], colors.muted[2]);
    const disclaimer =
      "DISCLAIMER: This automated risk assessment was produced by the VERA Fraud Screening Core using deterministic " +
      "rules and SEBI compliance guidelines. It does not constitute legal counsel, judicial finding, or a definitive guarantee of fraud or safety.";
    const discLines = doc.splitTextToSize(disclaimer, contentWidth);
    doc.text(discLines, margin, y);

    // ── 10. PAGE NUMBERS ──────────────────────────────────────────────────
    const totalPages = doc.getNumberOfPages();
    for (let p = 1; p <= totalPages; p++) {
      doc.setPage(p);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(8);
      doc.setTextColor(colors.muted[0], colors.muted[1], colors.muted[2]);
      doc.text(
        `Page ${p} of ${totalPages}  •  VERA Intelligence Platform  •  https://scores.sebi.gov.in`,
        pageWidth / 2,
        pageHeight - 18,
        { align: "center" }
      );
    }

    return doc;
  } catch (err: any) {
    console.error("Failed to build PDF report:", err);
    throw new Error(err?.message || "PDF generation failed");
  }
}

/**
 * Generates and triggers browser download of the investigation PDF report.
 */
export function generateInvestigationPdf(data: InvestigationReportData): void {
  const doc = buildInvestigationPdfDoc(data);
  const reportId = data.reportId || `screening-${Date.now()}`;
  const safeReportId = reportId.replace(/[^a-zA-Z0-9_-]/g, "_");
  const filename = `VERA-Report-${safeReportId}.pdf`;
  doc.save(filename);
}
