/**
 * Canonical Evidence Schema.
 * Architecture Rule 5: Evidence uses one canonical schema.
 * Architecture Rule 10: Persistent files must never depend on Render local filesystem.
 */

import { VerificationResult } from "./verification";

export enum EvidenceMediaType {
  TEXT = "TEXT",
  URL = "URL",
  IMAGE = "IMAGE",
  VIDEO = "VIDEO",
  AUDIO = "AUDIO",
  APK = "APK",
  DOCUMENT = "DOCUMENT"
}

export interface StorageReference {
  /** Bucket name in Supabase Storage or S3-compatible store */
  bucket: string;
  /** Immutable object path/key within the bucket */
  storagePath: string;
  /** Storage backend provider identifier, e.g. "supabase_storage" */
  provider: "supabase_storage" | "external_url";
  /** Content MIME type */
  mimeType: string;
  /** Size in bytes */
  sizeBytes: number;
}

export interface CanonicalEvidenceItem {
  id: string;
  investigationId: string;
  mediaType: EvidenceMediaType;
  /** SHA-256 cryptographic digest of the raw evidence payload */
  sha256: string;
  /** Human-readable title or label */
  title: string;
  /** Original source (e.g. user upload, telegram message, scraped web url) */
  sourceOrigin: string;
  /** Object storage reference (null for pure text/urls without detached assets) */
  storageRef?: StorageReference;
  /** Inline text content or transcribed body */
  contentPayload?: string;
  /** Extracted structured entities (e.g., IFSC codes, SEBI numbers, URLs, phone numbers) */
  extractedEntities: Record<string, string[]>;
  /** Verification tracking attached to this piece of evidence */
  verification: VerificationResult;
  /** ISO-8601 creation timestamp */
  createdAt: string;
  /** Custom extensible tags */
  tags: string[];
}
