import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

/**
 * Deepfake & Facial Manipulation Video Forensics API Route
 *
 * Architecture Rule 1: Frontend communicates only through API contracts.
 * Architecture Rule 4: Detection engines are independent modules.
 * Architecture Rule 9: Analyzer failure must never be interpreted as safety.
 * Architecture Rule 12: Every model/analyzer exposes version metadata.
 * Forensic Integrity Rule: Mandatory phrasing must be:
 * "Model detected signals associated with facial manipulation."
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => null);
    if (!body || !body.video_b64) {
      return NextResponse.json(
        { detail: "video_b64 must not be empty." },
        { status: 422 }
      );
    }

    const {
      video_b64,
      frames_b64,
      audio_b64,
      ocr_text,
      source_label = "public_consumer_upload",
      filename = "",
      transcript: userTranscript = "",
    } = body;
    let cleanB64 = String(video_b64 || "").trim();

    // Strip data-URI prefix if present
    if (cleanB64.includes(",") && cleanB64.startsWith("data:")) {
      cleanB64 = cleanB64.split(",", 2)[1];
    }

    // Resolve backend API URL dynamically from environment
    const backendUrl =
      process.env.API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.NEXT_PUBLIC_VERA_API_URL ||
      "https://vera-delhi-ldfinal.onrender.com";

    // Forward to FastAPI backend for MesoNet-4 spatiotemporal inference
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 50000);
      const pyResp = await fetch(`${backendUrl}/api/v1/deepfake-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_b64: cleanB64,
          frames_b64: Array.isArray(frames_b64) && frames_b64.length > 0 ? frames_b64 : undefined,
          audio_b64: audio_b64 || undefined,
          ocr_text: ocr_text || undefined,
          source_label,
          filename,
          transcript: userTranscript,
        }),
        signal: controller.signal,
      });
      clearTimeout(timeout);

      const data = await pyResp.json().catch(() => null);
      if (pyResp.ok && data) {
        return NextResponse.json(data, { status: 200 });
      }
      return NextResponse.json(
        data || { detail: "Backend processing error" },
        { status: pyResp.status || 500 }
      );
    } catch {
      // Backend is unreachable; return explicit 503 rather than fabricating mock scores
      return NextResponse.json(
        {
          detail: "Video analysis service is currently offline or warming up. Please ensure the backend is running.",
          error_code: "BACKEND_UNAVAILABLE",
        },
        { status: 503 }
      );
    }
  } catch (err: any) {
    return NextResponse.json(
      { detail: `Analysis failed: ${err?.message || "Unknown error"}` },
      { status: 500 }
    );
  }
}
