"use client";

import React, { useState } from "react";
import { X, Upload, Globe, FileText, CheckCircle2, AlertTriangle, Hash } from "lucide-react";
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

  if (!isOpen) return null;

  const handleComputeSimHash = (val: string) => {
    setPayload(val);
    if (val.length > 5) {
      // Mock SHA-256 preview for UI display
      setSimulatedHash("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    } else {
      setSimulatedHash("");
    }
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
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Upload className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-slate-100">Ingest Evidence Artifact</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-400 font-medium mb-1">Evidence Media Type</label>
            <select
              value={mediaType}
              onChange={(e) => setMediaType(e.target.value as EvidenceMediaType)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
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
            <label className="block text-slate-400 font-medium mb-1">
              Payload / URL / Content
            </label>
            <textarea
              rows={3}
              value={payload}
              onChange={(e) => handleComputeSimHash(e.target.value)}
              placeholder="Paste suspect URL, file path, or transcript..."
              required
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500 font-mono text-[11px]"
            />
          </div>

          {simulatedHash && (
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 flex items-center gap-2 text-[10px] text-slate-400 font-mono">
              <Hash className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
              <span className="truncate">SHA-256: {simulatedHash}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 font-medium mb-1">Source Origin</label>
              <input
                type="text"
                value={sourceOrigin}
                onChange={(e) => setSourceOrigin(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500 text-xs"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Tags (comma-separated)</label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500 text-xs"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium"
            >
              Attach to Case
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
