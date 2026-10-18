"""Centralized Feature Flags Configuration for VERA.

Architecture Rule 1: No deletion or replacement of existing models, libraries, or routes.
Upgrades are additive and layered behind config flags with fallback to legacy baseline behavior.
"""

import os


class FeatureFlags:
    """Toggles for Phase 3 additive accuracy improvements."""

    # Video Upgrades (MesoNet-4)
    ENABLE_TTA_FACE_ENSEMBLE: bool = (
        os.getenv("ENABLE_TTA_FACE_ENSEMBLE", "true").lower() == "true"
    )
    ENABLE_TEMPORAL_TRIMMED_AGGREGATION: bool = (
        os.getenv("ENABLE_TEMPORAL_TRIMMED_AGGREGATION", "true").lower() == "true"
    )
    ENABLE_TEMPERATURE_CALIBRATION: bool = (
        os.getenv("ENABLE_TEMPERATURE_CALIBRATION", "true").lower() == "true"
    )

    # Text Forensics & Heuristics Upgrades
    ENABLE_MULTILINGUAL_EXPANSION: bool = (
        os.getenv("ENABLE_MULTILINGUAL_EXPANSION", "true").lower() == "true"
    )
    ENABLE_ADVERSARIAL_DEOBFUSCATION: bool = (
        os.getenv("ENABLE_ADVERSARIAL_DEOBFUSCATION", "true").lower() == "true"
    )
    ENABLE_RED_FLAG_OVERRIDE: bool = (
        os.getenv("ENABLE_RED_FLAG_OVERRIDE", "true").lower() == "true"
    )

    # Regulatory & Intermediary Verification Upgrades
    ENABLE_GROUNDING_VERIFIER: bool = (
        os.getenv("ENABLE_GROUNDING_VERIFIER", "true").lower() == "true"
    )
    ENABLE_INTERMEDIARY_FORMAT_VALIDATION: bool = (
        os.getenv("ENABLE_INTERMEDIARY_FORMAT_VALIDATION", "true").lower() == "true"
    )

    # Deterministic Scoring & Fusion Upgrades
    ENABLE_MONOTONIC_RISK_FUSION: bool = (
        os.getenv("ENABLE_MONOTONIC_RISK_FUSION", "true").lower() == "true"
    )
