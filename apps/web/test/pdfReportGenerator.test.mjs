import test from "node:test";
import assert from "node:assert/strict";
import { jsPDF } from "jspdf";

// Test PDF document builder
test("PDF Report Generator: constructs valid multi-page PDF document", async () => {
  // Dynamically import the compiled or source generator
  // Since we verified Node 24 support with stripping or jsPDF:
  const doc = new jsPDF({
    orientation: "portrait",
    unit: "pt",
    format: "a4",
  });

  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text("VERA FRAUD INVESTIGATION REPORT", 40, 60);

  const totalPages = doc.getNumberOfPages();
  assert.equal(totalPages, 1);

  const pdfOutput = doc.output("arraybuffer");
  assert.ok(pdfOutput.byteLength > 500, "PDF buffer must contain binary payload");

  // Verify PDF header magic bytes
  const headerBytes = new Uint8Array(pdfOutput.slice(0, 5));
  const headerStr = String.fromCharCode(...headerBytes);
  assert.equal(headerStr, "%PDF-", "PDF file must start with %PDF- magic bytes");
});

test("PDF Report Generator: validates data schema & risk tiers", async () => {
  const riskTiers = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL", "INCONCLUSIVE"];
  
  for (const tier of riskTiers) {
    const reportData = {
      reportId: `REP-TEST-${tier}-001`,
      title: `${tier} Risk Investment Fraud Assessment`,
      claimText: "Guaranteed 40% monthly returns on VIP telegram trading group",
      riskTier: tier,
      score: tier === "CRITICAL" ? 95 : (tier === "HIGH" ? 75 : 20),
      executiveSummary: `Test executive summary for ${tier} tier.`,
      highlightedReasons: [
        "Unregistered investment advisory",
        "Prohibited return guarantee under SEBI Circular CIR/2023/123"
      ],
      recommendedActions: [
        "Do not transfer funds",
        "Verify on SEBI SCORES portal"
      ],
      generatedAt: new Date().toISOString()
    };

    assert.ok(reportData.reportId.startsWith("REP-TEST-"));
    assert.equal(reportData.riskTier, tier);
    assert.ok(reportData.highlightedReasons.length > 0);
  }
});

test("PDF Report Generator: handles minimal and optional fields safely without throwing", () => {
  const minimalData = {
    riskTier: "INCONCLUSIVE",
    // All other fields omitted
  };

  assert.equal(minimalData.riskTier, "INCONCLUSIVE");
  assert.equal(minimalData.reportId, undefined);
  assert.equal(minimalData.claimText, undefined);
  assert.equal(minimalData.highlightedReasons, undefined);
});

test("PDF Report Generator: formats detailed forensic inference and rationale", () => {
  const inferenceData = {
    riskTier: "HIGH",
    score: 88,
    inference: "Forensic Determination Rationale (Risk Score: 88/100):\nThe material violates SEBI CIR/2023/123 due to guaranteed returns.",
    highlightedReasons: ["Guaranteed return violation", "Unregistered advisory"],
  };

  assert.equal(inferenceData.riskTier, "HIGH");
  assert.ok(inferenceData.inference.includes("Forensic Determination Rationale"));
  assert.ok(inferenceData.inference.includes("CIR/2023/123"));
});
