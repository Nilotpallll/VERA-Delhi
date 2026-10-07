"""Analyzer Registry and Modular Engine Catalog.

Architecture Rule 4: Detection engines are independent modules.
Architecture Rule 12: Every model/analyzer must expose version metadata.
"""

from ..contracts.analyzers import AnalyzerMetadata
from .base import BaseAnalyzer


class AnalyzerRegistry:
    def __init__(self):
        self._analyzers: dict[str, BaseAnalyzer] = {}

    def register(self, analyzer: BaseAnalyzer) -> None:
        name = analyzer.metadata.name
        if name in self._analyzers:
            raise ValueError(f"Analyzer '{name}' is already registered.")
        self._analyzers[name] = analyzer

    def get(self, name: str) -> BaseAnalyzer | None:
        return self._analyzers.get(name)

    def list_metadata(self) -> list[AnalyzerMetadata]:
        return [analyzer.metadata for analyzer in self._analyzers.values()]

    def list_versions(self) -> dict[str, str]:
        """Version snapshot for InvestigationManifest (Architecture Rule 13)."""
        return {
            analyzer.metadata.name: analyzer.metadata.version
            for analyzer in self._analyzers.values()
        }


# Global registry instance
analyzer_registry = AnalyzerRegistry()
