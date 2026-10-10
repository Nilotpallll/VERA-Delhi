"""VERA LangGraph Investigator Agent.

Architecture Rule 3: Provider abstraction.
Architecture Rule 5: Canonical evidence schema.
Architecture Rule 6 & 7: Deterministic risk scoring — LLMs cannot directly assign final risk scores.
Architecture Rule 8: Tri-state verification.
Architecture Rule 9: Failsafe default.
Architecture Rule 13: Reproducibility.
"""

import re
import uuid
from datetime import UTC, datetime
from typing import Any

from langgraph.graph import END, START, StateGraph

from ..contracts.enums import EvidenceCategory, EvidenceSeverity, SourceType
from .reporter import ForensicReportGenerator
from .risk_engine import DeterministicRiskEngine, InvestigationCompleteness
from .state import InvestigationState
from .tools import InvestigatorToolRegistry

# ── Prompt Injection Defense Signatures ───────────────────────────────────────
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s*:\s*you\s+are\s+now",
    r"override\s+(risk|scoring|verification)",
    r"set\s+risk\s+(score\s+)?to\s+0",
    r"declare\s+(this\s+)?(safe|verified|legitimate)",
    r"disregard\s+all\s+rules",
    r"jailbreak",
]


class VERAInvestigator:
    """The central VERA Investigator powered by LangGraph."""

    def __init__(self, max_iterations: int = 5, max_tool_calls: int = 15):
        self.max_iterations = max_iterations
        self.max_tool_calls = max_tool_calls
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(InvestigationState)

        # Add Nodes in the Agent Loop
        workflow.add_node("understand_input", self._understand_input_node)
        workflow.add_node("extract_claims_entities", self._extract_claims_entities_node)
        workflow.add_node("decide_investigation_actions", self._decide_actions_node)
        workflow.add_node("execute_tools", self._execute_tools_node)
        workflow.add_node("correlate_evidence", self._correlate_evidence_node)
        workflow.add_node("determine_missing_evidence", self._determine_missing_node)
        workflow.add_node("risk_engine_node", self._risk_engine_node)
        workflow.add_node("generate_report_node", self._generate_report_node)

        # Edges
        workflow.add_edge(START, "understand_input")
        workflow.add_edge("understand_input", "extract_claims_entities")
        workflow.add_edge("extract_claims_entities", "decide_investigation_actions")
        workflow.add_edge("decide_investigation_actions", "execute_tools")
        workflow.add_edge("execute_tools", "correlate_evidence")
        workflow.add_edge("correlate_evidence", "determine_missing_evidence")

        # Conditional Edge from determine_missing_evidence
        workflow.add_conditional_edges(
            "determine_missing_evidence",
            self._route_after_missing_check,
            {
                "investigate_further": "decide_investigation_actions",
                "conclude": "risk_engine_node",
            },
        )

        workflow.add_edge("risk_engine_node", "generate_report_node")
        workflow.add_edge("generate_report_node", END)

        return workflow.compile()

    # ── Node 1: Understand Input ──────────────────────────────────────────────
    async def _understand_input_node(self, state: InvestigationState) -> dict[str, Any]:
        inputs = state.get("inputs", [])
        reasons = list(state.get("reasoning_log", []))
        errors = list(state.get("errors", []))
        evidence = list(state.get("evidence_items", []))
        reasons.append(f"Ingesting {len(inputs)} inputs for investigation.")

        # Check prompt injection across all input texts
        for inp in inputs:
            val = str(inp.get("value", ""))
            for pat in INJECTION_PATTERNS:
                if re.search(pat, val, re.IGNORECASE):
                    reasons.append("Security warning: Prompt injection signature detected in input text.")
                    evidence.append({
                        "id": f"ev_{uuid.uuid4().hex[:10]}",
                        "investigation_id": state.get("investigation_id", "inv"),
                        "type": "prompt_injection_attempt",
                        "category": EvidenceCategory.SECURITY.value if hasattr(EvidenceCategory, "SECURITY") else EvidenceCategory.SYSTEM_EVENT.value,
                        "severity": EvidenceSeverity.HIGH.value,
                        "confidence": 1.0,
                        "description": "Adversarial prompt injection pattern detected in user input.",
                        "source_type": SourceType.SYSTEM.value,
                        "source_reference": inp.get("id", "unknown"),
                        "created_at": datetime.now(UTC).isoformat(),
                    })
                    break

        return {
            "iteration_count": 0,
            "max_iterations": state.get("max_iterations") or self.max_iterations,
            "max_tool_calls": state.get("max_tool_calls") or self.max_tool_calls,
            "executed_tool_signatures": list(state.get("executed_tool_signatures", [])),
            "action_history": list(state.get("action_history", [])),
            "evidence_items": evidence,
            "reasoning_log": reasons,
            "errors": errors,
        }

    # ── Node 2: Extract Claims & Entities ─────────────────────────────────────
    async def _extract_claims_entities_node(self, state: InvestigationState) -> dict[str, Any]:
        inputs = state.get("inputs", [])
        entities: list[dict[str, Any]] = list(state.get("extracted_entities", []))
        claims: list[dict[str, Any]] = list(state.get("extracted_claims", []))
        reasons = list(state.get("reasoning_log", []))

        for inp in inputs:
            val = str(inp.get("value", ""))
            inp_id = inp.get("id", "inp")
            inp_type = inp.get("type", "TEXT")

            # Extract URLs
            urls = re.findall(r"https?://[^\s]+", val)
            for u in urls:
                entities.append({"type": "URL", "value": u, "source_input_id": inp_id})
                domain = re.sub(r"^https?://", "", u).split("/")[0]
                entities.append({"type": "DOMAIN", "value": domain, "source_input_id": inp_id})

            # Extract UPI IDs
            upis = re.findall(r"[\w.-]+@[\w.-]+", val)
            for upi in upis:
                if any(h in upi.lower() for h in ["upi", "paytm", "okaxis", "okhdfc", "icici", "ybl", "sbi"]):
                    entities.append({"type": "UPI", "value": upi, "source_input_id": inp_id})

            # Extract Phone Numbers
            phones = re.findall(r"(?:\+91|91)?[-.\s]?[6-9]\d{9}", val)
            for p in phones:
                entities.append({"type": "PHONE", "value": p.strip(), "source_input_id": inp_id})

            # Extract SEBI Registration numbers (e.g. INZ000031633, INA000000001, INH000000123)
            sebi_regs = re.findall(r"\bIN[A-Z]{1,3}\d{6,10}\b", val, re.IGNORECASE)
            for reg in sebi_regs:
                entities.append({"type": "SEBI_REGISTRATION", "value": reg.upper(), "source_input_id": inp_id})
                claims.append({
                    "id": f"claim_{uuid.uuid4().hex[:8]}",
                    "claim_text": f"Claims SEBI registration number {reg.upper()}",
                    "claim_type": "sebi_registration",
                    "source_input_id": inp_id,
                    "target": reg.upper(),
                })

            # Extract Company or Entity claims
            if "sebi" in val.lower() and not sebi_regs:
                claims.append({
                    "id": f"claim_{uuid.uuid4().hex[:8]}",
                    "claim_text": "Claims SEBI registered entity/adviser status",
                    "claim_type": "sebi_registration",
                    "source_input_id": inp_id,
                    "target": "SEBI Intermediary",
                })

            # Extract Guaranteed Return claims
            if any(w in val.lower() for w in ["guaranteed", "assured return", "100% profit", "zero risk", "2x return", "3x profit"]):
                claims.append({
                    "id": f"claim_{uuid.uuid4().hex[:8]}",
                    "claim_text": "Promised guaranteed investment return",
                    "claim_type": "guaranteed_return",
                    "source_input_id": inp_id,
                })

            # Extract Withdrawal fee claims
            if any(w in val.lower() for w in ["withdrawal fee", "release fee", "advance tax", "processing charge to withdraw"]):
                claims.append({
                    "id": f"claim_{uuid.uuid4().hex[:8]}",
                    "claim_text": "Requires fee or tax payment before withdrawal",
                    "claim_type": "withdrawal_fee",
                    "source_input_id": inp_id,
                })

            # Media specific inputs
            if inp_type == "APK":
                entities.append({"type": "APK", "value": val, "source_input_id": inp_id})
            elif inp_type == "IMAGE":
                entities.append({"type": "IMAGE", "value": val, "source_input_id": inp_id})
            elif inp_type == "VIDEO":
                entities.append({"type": "VIDEO", "value": val, "source_input_id": inp_id})
            elif inp_type == "AUDIO":
                entities.append({"type": "AUDIO", "value": val, "source_input_id": inp_id})

        reasons.append(f"Identified {len(entities)} entities and {len(claims)} claims.")
        return {
            "extracted_entities": entities,
            "extracted_claims": claims,
            "reasoning_log": reasons,
        }

    # ── Node 3: Decide Investigation Actions ──────────────────────────────────
    async def _decide_actions_node(self, state: InvestigationState) -> dict[str, Any]:
        entities = state.get("extracted_entities", [])
        claims = state.get("extracted_claims", [])
        inputs = state.get("inputs", [])
        executed_sigs = set(state.get("executed_tool_signatures", []))
        action_history = state.get("action_history", [])
        max_tool_calls = state.get("max_tool_calls", self.max_tool_calls)

        pending_actions: list[dict[str, Any]] = []

        def add_action(tool_name: str, args: dict[str, Any], rationale: str):
            if len(action_history) + len(pending_actions) >= max_tool_calls:
                return  # Tool limit reached
            sig = f"{tool_name}:{sorted(args.items())}"
            if sig not in executed_sigs:
                executed_sigs.add(sig)
                pending_actions.append({"tool_name": tool_name, "arguments": args, "rationale": rationale, "sig": sig})

        # 1. Dispatch modalities for direct inputs
        for inp in inputs:
            itype = inp.get("type", "TEXT")
            val = str(inp.get("value", ""))
            if itype == "TEXT":
                add_action("analyze_message", {"text": val}, "Analyze message heuristics and claims")
            elif itype == "IMAGE":
                add_action("analyze_image", {"image_path": val}, "Inspect image OCR and ELA manipulation")
            elif itype == "VIDEO":
                add_action("analyze_video", {"video_path": val}, "Inspect video for deepfake manipulation")
            elif itype == "AUDIO":
                add_action("transcribe_audio", {"audio_path": val}, "Transcribe speech and inspect audio artifacts")
            elif itype == "APK":
                add_action("analyze_apk", {"apk_path": val}, "Static analysis on suspicious APK binary")

        # 2. Dispatch verification for entities & claims
        for ent in entities:
            etype = ent.get("type")
            evalue = ent.get("value")
            if etype == "URL":
                add_action("analyze_url", {"url": evalue}, f"Analyze URL security for {evalue}")
            elif etype == "DOMAIN":
                add_action("verify_domain", {"domain_or_url": evalue}, f"Verify domain authenticity for {evalue}")
                add_action("lookup_indicator", {"indicator_type": "domain", "indicator_value": evalue}, f"Check threat blacklist for {evalue}")
            elif etype == "UPI":
                add_action("verify_payment", {"upi_id": evalue}, f"Verify UPI payment recipient {evalue}")
                add_action("lookup_indicator", {"indicator_type": "upi", "indicator_value": evalue}, f"Check threat blacklist for {evalue}")
            elif etype == "PHONE":
                add_action("lookup_indicator", {"indicator_type": "phone", "indicator_value": evalue}, f"Check phone threat intelligence for {evalue}")
            elif etype == "SEBI_REGISTRATION":
                add_action("verify_sebi_entity", {"entity_name": evalue, "registration_number": evalue}, f"Verify SEBI registry for {evalue}")
            elif etype == "COMPANY":
                add_action("verify_company", {"company_name": evalue}, f"Verify MCA incorporation for {evalue}")

        for clm in claims:
            ctype = clm.get("claim_type")
            if ctype == "sebi_registration":
                target = clm.get("target", "SEBI Representative")
                add_action("verify_sebi_entity", {"entity_name": target, "registration_number": clm.get("target")}, f"Verify claimed SEBI status for {target}")
                add_action("retrieve_guidance", {"query": "unregistered investment advisory prohibition"}, "Retrieve SEBI advisor circulars")
            elif ctype == "guaranteed_return":
                add_action("retrieve_guidance", {"query": "guaranteed or assured return prohibition"}, "Retrieve SEBI assured return regulations")

        reasons = list(state.get("reasoning_log", []))
        reasons.append(f"Decided {len(pending_actions)} new investigation tool calls.")

        return {
            "pending_actions": pending_actions,
            "executed_tool_signatures": list(executed_sigs),
            "reasoning_log": reasons,
        }

    # ── Node 4: Execute Tools ─────────────────────────────────────────────────
    async def _execute_tools_node(self, state: InvestigationState) -> dict[str, Any]:
        pending = state.get("pending_actions", [])
        evidence = list(state.get("evidence_items", []))
        verification_records = list(state.get("verification_records", []))
        action_history = list(state.get("action_history", []))
        citations = list(state.get("source_citations", [])) if "source_citations" in state else []
        has_unavail = state.get("has_unavailable_analyzer", False)
        reasons = list(state.get("reasoning_log", []))
        inv_id = state.get("investigation_id", "inv")

        for act in pending:
            tool_name = act["tool_name"]
            args = act["arguments"]
            reasons.append(f"Invoking tool {tool_name} with {args}")

            tool_fn = getattr(InvestigatorToolRegistry, tool_name, None)
            if not tool_fn:
                action_history.append({"tool_name": tool_name, "status": "FAILED", "error": f"Tool {tool_name} not found"})
                continue

            try:
                res = await tool_fn(**args, investigation_id=inv_id)
            except Exception as exc:
                res = InvestigatorToolRegistry._handle_tool_failure(tool_name, inv_id, str(exc))

            action_history.append({
                "tool_name": tool_name,
                "status": "SUCCESS" if res.success else "FAILED",
                "duration_ms": res.duration_ms,
                "evidence_count": len(res.evidence_items),
                "error": res.error,
            })

            if res.evidence_items:
                evidence.extend(res.evidence_items)
            if res.verification_record:
                verification_records.append(res.verification_record)
            if res.citations:
                citations.extend(res.citations)
            if res.is_unavailable:
                has_unavail = True

        return {
            "pending_actions": [],
            "evidence_items": evidence,
            "verification_records": verification_records,
            "action_history": action_history,
            "source_citations": citations,
            "has_unavailable_analyzer": has_unavail,
            "reasoning_log": reasons,
        }

    # ── Node 5: Correlate Evidence ────────────────────────────────────────────
    async def _correlate_evidence_node(self, state: InvestigationState) -> dict[str, Any]:
        evidence = list(state.get("evidence_items", []))
        claims = state.get("extracted_claims", [])
        entities = state.get("extracted_entities", [])
        reasons = list(state.get("reasoning_log", []))
        inv_id = state.get("investigation_id", "inv")

        # Determine scam lifecycle stage
        types = {e.get("type", "") for e in evidence}
        clm_types = {c.get("claim_type", "") for c in claims}

        if "withdrawal_fee" in clm_types or any("withdrawal" in e.get("type", "") for e in evidence):
            stage = "withdrawal_block"
        elif "payment_mismatch" in types or any(ent.get("type") == "UPI" for ent in entities):
            stage = "investment_ask"
        elif "deepfake_signal" in types or "unverified_entity" in types:
            stage = "trust_building"
        elif "guaranteed_return" in clm_types or "domain_mismatch" in types:
            stage = "hook"
        else:
            stage = "reconnaissance"

        # Multi-modal correlation: check if guaranteed return was confirmed
        for clm in claims:
            if clm.get("claim_type") == "guaranteed_return":
                if not any(e.get("type") == "guaranteed_return" for e in evidence):
                    evidence.append({
                        "id": f"ev_{uuid.uuid4().hex[:10]}",
                        "investigation_id": inv_id,
                        "type": "guaranteed_return",
                        "category": EvidenceCategory.CLAIM.value,
                        "severity": EvidenceSeverity.HIGH.value,
                        "confidence": 1.0,
                        "description": "Evidence confirms promise of guaranteed returns in contravention of SEBI norms.",
                        "source_type": SourceType.DETERMINISTIC_ANALYZER.value,
                        "source_reference": clm.get("source_input_id", "claim"),
                        "metadata": {"signal_type": "guaranteed_return"},
                        "created_at": datetime.now(UTC).isoformat(),
                    })

            if clm.get("claim_type") == "withdrawal_fee":
                if not any(e.get("type") == "withdrawal_fee" for e in evidence):
                    evidence.append({
                        "id": f"ev_{uuid.uuid4().hex[:10]}",
                        "investigation_id": inv_id,
                        "type": "withdrawal_fee",
                        "category": EvidenceCategory.FINANCIAL.value,
                        "severity": EvidenceSeverity.HIGH.value,
                        "confidence": 1.0,
                        "description": "Evidence confirms demand of advance fee or tax release payment.",
                        "source_type": SourceType.DETERMINISTIC_ANALYZER.value,
                        "source_reference": clm.get("source_input_id", "claim"),
                        "metadata": {"signal_type": "withdrawal_fee"},
                        "created_at": datetime.now(UTC).isoformat(),
                    })

        reasons.append(f"Correlated evidence. Classified scam lifecycle stage as '{stage}'.")
        return {
            "evidence_items": evidence,
            "scam_lifecycle_stage": stage,
            "reasoning_log": reasons,
        }

    # ── Node 6: Determine Missing Evidence & Termination ─────────────────────
    async def _determine_missing_node(self, state: InvestigationState) -> dict[str, Any]:
        iteration = state.get("iteration_count", 0) + 1
        max_iter = state.get("max_iterations", self.max_iterations)
        max_tool_calls = state.get("max_tool_calls", self.max_tool_calls)
        action_history = state.get("action_history", [])
        entities = state.get("extracted_entities", [])
        evidence = state.get("evidence_items", [])
        inputs = state.get("inputs", [])
        reasons = list(state.get("reasoning_log", []))

        missing: list[str] = []

        # Check what is missing
        if not inputs or (len(inputs) == 1 and not inputs[0].get("value")):
            is_sufficient = True
            missing.append("Complete input content is missing.")
        else:
            # Check if any detected URL hasn't been scanned
            for ent in entities:
                if ent.get("type") == "URL" and not any(e.get("source_reference") == ent.get("value") for e in evidence):
                    missing.append(f"Forensic scan for URL {ent.get('value')}")

            # Stop condition: if tool limit reached or iterations exceeded or no missing tools
            if iteration >= max_iter or len(action_history) >= max_tool_calls or not missing:
                is_sufficient = True
            else:
                is_sufficient = False

        reasons.append(f"Iteration {iteration}/{max_iter}. Sufficient={is_sufficient}. Missing={len(missing)}")

        return {
            "iteration_count": iteration,
            "is_sufficient": is_sufficient,
            "missing_evidence": missing,
            "reasoning_log": reasons,
        }

    def _route_after_missing_check(self, state: InvestigationState) -> str:
        if state.get("is_sufficient", True):
            return "conclude"
        return "investigate_further"

    # ── Node 7: Risk Engine Node (Deterministic) ──────────────────────────────
    async def _risk_engine_node(self, state: InvestigationState) -> dict[str, Any]:
        evidence = state.get("evidence_items", [])
        verifications = state.get("verification_records", [])
        has_unavail = state.get("has_unavailable_analyzer", False)
        inputs = state.get("inputs", [])

        # Failsafe check for insufficient evidence
        if not inputs or all(not str(i.get("value", "")).strip() for i in inputs):
            assessment = DeterministicRiskEngine.evaluate(
                evidence_items=[],
                verification_records=[],
                has_unavailable_analyzer=has_unavail,
            )
        else:
            assessment = DeterministicRiskEngine.evaluate(
                evidence_items=evidence,
                verification_records=verifications,
                has_unavailable_analyzer=has_unavail,
            )

        reasons = list(state.get("reasoning_log", []))
        reasons.append(f"Risk Engine evaluated: Score={assessment.risk_score:.1f}, Level={assessment.risk_level.value}")

        return {
            "risk_score": assessment.risk_score,
            "risk_level": assessment.risk_level.value,
            "investigation_status": assessment.investigation_completeness.value,
            "model_confidence": assessment.model_confidence,
            "risk_signals": [
                {
                    "signal_type": s.signal_type,
                    "rule_id": s.rule_id,
                    "weight": s.weight,
                    "description": s.description,
                    "source_reference": s.source_reference,
                }
                for s in assessment.active_signals
            ],
            "reasoning_log": reasons,
        }

    # ── Node 8: Generate Report Node ──────────────────────────────────────────
    async def _generate_report_node(self, state: InvestigationState) -> dict[str, Any]:
        from .risk_engine import (
            ComputedSignal,
            RiskAssessmentResult,
            RiskLevel,
        )

        signals = [
            ComputedSignal(
                signal_type=s["signal_type"],
                rule_id=s.get("rule_id", "RULE-CUSTOM"),
                weight=s["weight"],
                description=s["description"],
                source_reference=s.get("source_reference", ""),
            )
            for s in state.get("risk_signals", [])
        ]

        assessment = RiskAssessmentResult(
            risk_score=state.get("risk_score", 0.0),
            risk_level=RiskLevel(state.get("risk_level", "LOW")),
            investigation_completeness=InvestigationCompleteness(state.get("investigation_status", "COMPLETED")),
            model_confidence=state.get("model_confidence", 1.0),
            verification_status="MIXED",
            active_signals=signals,
            ruleset_version="rules.v2.0",
            has_unavailable_analyzer=state.get("has_unavailable_analyzer", False),
            summary="",
        )

        report = ForensicReportGenerator.generate(
            investigation_id=state.get("investigation_id", "inv"),
            risk_assessment=assessment,
            entities=state.get("extracted_entities", []),
            claims=state.get("extracted_claims", []),
            evidence=state.get("evidence_items", []),
            verification_records=state.get("verification_records", []),
            citations=state.get("source_citations", []),
            scam_lifecycle_stage=state.get("scam_lifecycle_stage", "unknown"),
            missing_evidence=state.get("missing_evidence", []),
        )

        return {"final_report": report}

    # ── Execution Entrypoint ──────────────────────────────────────────────────
    async def run_investigation(
        self,
        *,
        investigation_id: str,
        inputs: list[dict[str, Any]],
        max_iterations: int | None = None,
    ) -> dict[str, Any]:
        """Runs the complete VERA investigation state graph."""
        initial_state: InvestigationState = {
            "investigation_id": investigation_id,
            "inputs": inputs,
            "extracted_entities": [],
            "extracted_claims": [],
            "evidence_items": [],
            "verification_records": [],
            "pending_actions": [],
            "action_history": [],
            "executed_tool_signatures": [],
            "iteration_count": 0,
            "max_iterations": max_iterations or self.max_iterations,
            "max_tool_calls": self.max_tool_calls,
            "is_sufficient": False,
            "missing_evidence": [],
            "scam_lifecycle_stage": "unknown",
            "risk_signals": [],
            "risk_score": 0.0,
            "risk_level": "LOW",
            "investigation_status": "QUEUED",
            "model_confidence": 1.0,
            "has_unavailable_analyzer": False,
            "reasoning_log": [],
            "errors": [],
            "final_report": {},
        }

        final_state = await self.graph.ainvoke(initial_state)
        return final_state
