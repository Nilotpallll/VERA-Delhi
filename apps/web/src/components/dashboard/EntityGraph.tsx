"use client";

import React, { useState } from "react";
import {
  User,
  Building,
  Phone,
  CreditCard,
  Globe,
  Smartphone,
  MessageSquare,
  Video,
  FileCode,
  Share2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Info,
} from "lucide-react";

export interface GraphNode {
  id: string;
  label: string;
  type: "person" | "company" | "phone" | "UPI" | "domain" | "profile" | "APK" | "message" | "video";
  x: number;
  y: number;
  verified?: boolean | null;
  details?: string;
}

export interface GraphEdge {
  from: string;
  to: string;
  label: string;
  relationshipType: "solicits" | "routes_payment" | "promotes" | "hosts" | "operates" | "claims_affiliation" | "distributes";
}

const DEFAULT_NODES: GraphNode[] = [
  { id: "msg_1", label: "Telegram Message", type: "message", x: 100, y: 180, details: "Claims 40% guaranteed monthly returns" },
  { id: "person_1", label: "Rajesh Kumar (Alias)", type: "person", x: 260, y: 100, verified: false, details: "Alleged Senior Fund Manager" },
  { id: "company_1", label: "Apex Capital FX", type: "company", x: 440, y: 100, verified: false, details: "Unregistered broker entity" },
  { id: "upi_1", label: "apexinvest@icici", type: "UPI", x: 440, y: 260, verified: false, details: "Third-party personal mule UPI handle" },
  { id: "phone_1", label: "+91-9876543210", type: "phone", x: 260, y: 260, verified: false, details: "WhatsApp group admin contact" },
  { id: "domain_1", label: "apex-capital-fx.in", type: "domain", x: 620, y: 100, verified: false, details: "Registered 4 days ago on Namecheap" },
  { id: "apk_1", label: "ApexTrade.apk", type: "APK", x: 620, y: 240, verified: false, details: "Unsigned APK requesting SMS/overlay permissions" },
  { id: "profile_1", label: "@apex_signals_vip", type: "profile", x: 100, y: 320, details: "Channel with 12,000 bot subscribers" },
  { id: "video_1", label: "CEO_Endorsement.mp4", type: "video", x: 260, y: 400, details: "Synthetic deepfake lip-sync video" },
];

const DEFAULT_EDGES: GraphEdge[] = [
  { from: "msg_1", to: "person_1", label: "sent by", relationshipType: "solicits" },
  { from: "person_1", to: "company_1", label: "claims affiliation", relationshipType: "claims_affiliation" },
  { from: "msg_1", to: "phone_1", label: "originates from", relationshipType: "solicits" },
  { from: "msg_1", to: "upi_1", label: "requests deposit to", relationshipType: "routes_payment" },
  { from: "company_1", to: "domain_1", label: "hosts portal", relationshipType: "hosts" },
  { from: "domain_1", to: "apk_1", label: "distributes", relationshipType: "distributes" },
  { from: "profile_1", to: "msg_1", label: "broadcasts", relationshipType: "promotes" },
  { from: "video_1", to: "person_1", label: "impersonates", relationshipType: "operates" },
];

const TYPE_CONFIG: Record<
  GraphNode["type"],
  { icon: any; color: string; bg: string; border: string }
> = {
  person: { icon: User, color: "text-blue-400", bg: "bg-blue-950/70", border: "border-blue-600" },
  company: { icon: Building, color: "text-purple-400", bg: "bg-purple-950/70", border: "border-purple-600" },
  phone: { icon: Phone, color: "text-emerald-400", bg: "bg-emerald-950/70", border: "border-emerald-600" },
  UPI: { icon: CreditCard, color: "text-amber-400", bg: "bg-amber-950/70", border: "border-amber-600" },
  domain: { icon: Globe, color: "text-cyan-400", bg: "bg-cyan-950/70", border: "border-cyan-600" },
  profile: { icon: Share2, color: "text-pink-400", bg: "bg-pink-950/70", border: "border-pink-600" },
  APK: { icon: FileCode, color: "text-red-400", bg: "bg-red-950/70", border: "border-red-600" },
  message: { icon: MessageSquare, color: "text-indigo-400", bg: "bg-indigo-950/70", border: "border-indigo-600" },
  video: { icon: Video, color: "text-violet-400", bg: "bg-violet-950/70", border: "border-violet-600" },
};

export function EntityGraph({
  nodes = DEFAULT_NODES,
  edges = DEFAULT_EDGES,
}: {
  nodes?: GraphNode[];
  edges?: GraphEdge[];
}) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(nodes[0] || null);
  const [zoom, setZoom] = useState(1);
  const [activeFilter, setActiveFilter] = useState<string>("ALL");

  const filteredNodes =
    activeFilter === "ALL" ? nodes : nodes.filter((n) => n.type.toUpperCase() === activeFilter);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-4">
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Share2 className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-100">Forensic Entity &amp; Evidence Graph</h3>
          <span className="text-[11px] font-mono text-slate-500">
            ({nodes.length} nodes, {edges.length} relationships)
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-0.5 text-[11px]">
            {["ALL", "PERSON", "COMPANY", "UPI", "DOMAIN", "APK", "VIDEO"].map((filter) => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={`px-2 py-0.5 rounded ${
                  activeFilter === filter
                    ? "bg-indigo-600 text-white font-medium"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {filter}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-lg p-1">
            <button
              onClick={() => setZoom((z) => Math.min(1.5, z + 0.1))}
              className="p-1 text-slate-400 hover:text-slate-200"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoom((z) => Math.max(0.7, z - 0.1))}
              className="p-1 text-slate-400 hover:text-slate-200"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoom(1)}
              className="p-1 text-slate-400 hover:text-slate-200"
              title="Reset Zoom"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Canvas & Details Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* SVG Graph Viewport */}
        <div className="lg:col-span-8 h-[460px] bg-slate-950 rounded-lg border border-slate-800/80 relative overflow-hidden select-none">
          <svg
            className="w-full h-full cursor-grab active:cursor-grabbing"
            style={{ transform: `scale(${zoom})`, transformOrigin: "center center" }}
            viewBox="0 0 760 480"
          >
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-angle"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
              </marker>
            </defs>

            {/* Render Edges */}
            {edges.map((edge, i) => {
              const src = nodes.find((n) => n.id === edge.from);
              const dst = nodes.find((n) => n.id === edge.to);
              if (!src || !dst) return null;
              const midX = (src.x + dst.x) / 2;
              const midY = (src.y + dst.y) / 2;
              return (
                <g key={i}>
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={dst.x}
                    y2={dst.y}
                    stroke="#334155"
                    strokeWidth="1.8"
                    strokeDasharray={edge.relationshipType === "claims_affiliation" ? "4 4" : "none"}
                    markerEnd="url(#arrow)"
                  />
                  <text
                    x={midX}
                    y={midY - 4}
                    fill="#94a3b8"
                    fontSize="9"
                    fontFamily="monospace"
                    textAnchor="middle"
                    className="bg-slate-950 px-1"
                  >
                    {edge.label}
                  </text>
                </g>
              );
            })}

            {/* Render Nodes */}
            {filteredNodes.map((node) => {
              const cfg = TYPE_CONFIG[node.type] || TYPE_CONFIG.message;
              const isSelected = selectedNode?.id === node.id;
              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  onClick={() => setSelectedNode(node)}
                  className="cursor-pointer group"
                >
                  <circle
                    r={isSelected ? 20 : 16}
                    className={`transition-all ${
                      isSelected ? "fill-indigo-900 stroke-indigo-400 stroke-2" : "fill-slate-900 stroke-slate-700 stroke-1"
                    }`}
                  />
                  {node.verified === false && (
                    <circle r="4" cx="12" cy="-12" fill="#ef4444" />
                  )}
                  {node.verified === true && (
                    <circle r="4" cx="12" cy="-12" fill="#10b981" />
                  )}
                  <text
                    textAnchor="middle"
                    dy="4"
                    fontSize="10"
                    fill="#cbd5e1"
                    fontWeight="bold"
                    pointerEvents="none"
                  >
                    {node.type.slice(0, 3).toUpperCase()}
                  </text>
                  <text
                    textAnchor="middle"
                    dy="30"
                    fontSize="9.5"
                    fill={isSelected ? "#818cf8" : "#94a3b8"}
                    fontFamily="monospace"
                    pointerEvents="none"
                  >
                    {node.label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Selected Node Inspector */}
        <div className="lg:col-span-4 p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-semibold text-slate-300">Entity Details</span>
            <span className="text-[10px] font-mono text-slate-500">Inspection Panel</span>
          </div>

          {selectedNode ? (
            <div className="space-y-3 text-xs">
              <div className="flex items-center gap-2">
                {(() => {
                  const cfg = TYPE_CONFIG[selectedNode.type];
                  const Icon = cfg.icon;
                  return (
                    <div className={`p-2 rounded-lg border ${cfg.bg} ${cfg.border} ${cfg.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                  );
                })()}
                <div>
                  <h4 className="font-semibold text-slate-100">{selectedNode.label}</h4>
                  <span className="text-[10px] font-mono uppercase text-slate-400">
                    Type: {selectedNode.type}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1.5">
                <div className="text-[10px] text-slate-500">Registry Verification:</div>
                <div>
                  {selectedNode.verified === true ? (
                    <span className="text-emerald-400 font-mono font-medium">✓ SEBI REGISTERED ENTITY</span>
                  ) : selectedNode.verified === false ? (
                    <span className="text-rose-400 font-mono font-medium">✗ UNVERIFIED / UNREGISTERED</span>
                  ) : (
                    <span className="text-amber-400 font-mono font-medium">? REGISTRY UNAVAILABLE</span>
                  )}
                </div>
              </div>

              {selectedNode.details && (
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                  <div className="text-[10px] text-slate-500">Intelligence / Forensics:</div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">{selectedNode.details}</p>
                </div>
              )}

              {/* Connected Relationships */}
              <div className="space-y-1.5 pt-1">
                <span className="text-[10px] text-slate-500 font-medium">Direct Correlated Edges:</span>
                <div className="space-y-1">
                  {edges
                    .filter((e) => e.from === selectedNode.id || e.to === selectedNode.id)
                    .map((e, idx) => (
                      <div
                        key={idx}
                        className="p-1.5 rounded bg-slate-900 border border-slate-800 text-[10px] font-mono text-slate-400 flex items-center justify-between"
                      >
                        <span>{e.from === selectedNode.id ? `→ ${e.label} (${e.to})` : `← ${e.label} (${e.from})`}</span>
                        <span className="text-slate-500">{e.relationshipType}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500 text-xs">
              <Info className="w-5 h-5 mx-auto mb-2 opacity-50" />
              Click any node in the graph above to view its forensic properties and correlated relationships.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
