"use client";

import React, { useState } from "react";
import { X, Upload, Globe, FileText, CheckCircle2, AlertTriangle, Hash, Copy, Check } from "lucide-react";
import { EvidenceMediaType } from "@vera/contracts";

export function UploadEvidenceModal({
  isOpen,
  onClose,
  onAddEvidence,
}: {
  isOpen: boolean;
  onClose: () => void;
  onAddEvidence: (item: { mediaType: EvidenceMediaType; payload: string; source: string; tags: string[] }) => void;
}) {
  const [mediaType, setMediaType] = useState<EvidenceMediaType>(EvidenceMediaType.URL);
  const [payload, setPayload] = useState("");
  const [sourceOrigin, setSourceOrigin] = useState("Investigator Manual Upload");
  const [tags, setTags] = useState("phishing, suspect_telegram");
  const [simulatedHash, setSimulatedHash] = useState("");
  const [copiedHash, setCopiedHash] = useState(false);

  if (!isOpen) return null;

  const handleComputeSimHash = (val: string) => {
    setPayload(val);
    if (val.length > 5) {
      setSimulatedHash("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    } else {
      setSimulatedHash("");
    }
  };

  const handleCopyHash = () => {
    if (!simulatedHash) return;
    navigator.clipboard.writeText(simulatedHash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!payload.trim()) return;

    onAddEvidence({
      mediaType,
      payload: payload.trim(),
      source: sourceOrigin.trim(),
      tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
      <div className="w-full max-w-lg bg-white border border-[#E7E3D8] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl animate-scale-in relative overflow-hidden">
        <div className="flex items-center justify-between pb-4 border-b border-stone-200 relative z-10">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-orange-100 text-orange-600 border border-orange-200">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-stone-900 tracking-tight">Ingest Evidence Artifact</h3>
              <p className="text-xs text-stone-600">Attach digital artifact to immutable investigation ledger</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-600 hover:text-stone-900 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs relative z-10">
          <div>
            <label className="block text-stone-800 font-bold mb-1.5">Evidence Media Type</label>
            <select
              value={mediaType}
              onChange={(e) => setMediaType(e.target.value as EvidenceMediaType)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#FAF7F2] border border-stone-300 text-stone-900 focus:outline-none focus:border-orange-500 transition-colors font-sans"
            >
              <option value={EvidenceMediaType.URL}>Web Domain / URL</option>
              <option value={EvidenceMediaType.IMAGE}>Screenshot / Image File</option>
              <option value={EvidenceMediaType.TEXT}>Raw Text / Chat Transcript</option>
              <option value={EvidenceMediaType.VIDEO}>Video Clip / Deepfake Sample</option>
              <option value={EvidenceMediaType.AUDIO}>Voice Note / Audio File</option>
              <option value={EvidenceMediaType.APK}>APK Package / Android App</option>
            </select>
          </div>

          <div>
            <label className="block text-stone-800 font-bold mb-1.5">
              Payload / URL / Content
            </label>
            <textarea
              rows={3}
              value={payload}
              onChange={(e) => handleComputeSimHash(e.target.value)}
              placeholder="Paste suspect URL, file path, or transcript..."
              required
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#FAF7F2] border border-stone-300 text-stone-900 focus:outline-none focus:border-orange-500 font-mono text-xs transition-colors resize-none placeholder:text-stone-400"
            />
          </div>

          {simulatedHash && (
            <div className="p-3 rounded-xl bg-[#FAF7F2] border border-stone-200 flex items-center justify-between gap-2 text-[11px] text-stone-600 font-mono">
              <div className="flex items-center gap-2 truncate">
                <Hash className="w-4 h-4 text-orange-600 flex-shrink-0" />
                <span className="truncate">SHA-256: {simulatedHash}</span>
              </div>
              <button
                type="button"
                onClick={handleCopyHash}
                className="px-2 py-1 rounded bg-white hover:bg-stone-100 text-stone-700 border border-stone-200 flex items-center gap-1 flex-shrink-0 transition-colors"
              >
                {copiedHash ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                <span>{copiedHash ? "Copied" : "Copy"}</span>
              </button>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-stone-800 font-bold mb-1.5">Source Origin</label>
              <input
                type="text"
                value={sourceOrigin}
                onChange={(e) => setSourceOrigin(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#FAF7F2] border border-stone-300 text-stone-900 focus:outline-none focus:border-orange-500 text-xs transition-colors"
              />
            </div>
            <div>
              <label className="block text-stone-800 font-bold mb-1.5">Tags (comma-separated)</label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#FAF7F2] border border-stone-300 text-stone-900 focus:outline-none focus:border-orange-500 text-xs transition-colors"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-stone-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-700 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white font-bold shadow-sm transition-all duration-200"
            >
              Attach to Case Manifest
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
