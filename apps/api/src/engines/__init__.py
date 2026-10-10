"""Engines module for VERA forensics and detection."""

from .apk_analyzer import APKAnalyzer
from .audio_analyzer import AudioAnalyzer
from .base import BaseAnalyzer
from .evaluation import ModelEvaluationReport, ModelEvaluator, model_evaluator
from .image_analyzer import ImageAnalyzer
from .message_analyzer import MessageAnalyzer
from .ocr_engine import PaddleOCREngine
from .profile_analyzer import ProfileAnalyzer
from .registry import AnalyzerRegistry, analyzer_registry, register_default_engines
from .stt_engine import FasterWhisperEngine
from .url_analyzer import URLAnalyzer
from .video_analyzer import VideoAnalyzer

__all__ = [
    "BaseAnalyzer",
    "AnalyzerRegistry",
    "analyzer_registry",
    "register_default_engines",
    "PaddleOCREngine",
    "FasterWhisperEngine",
    "MessageAnalyzer",
    "ImageAnalyzer",
    "VideoAnalyzer",
    "AudioAnalyzer",
    "URLAnalyzer",
    "APKAnalyzer",
    "ProfileAnalyzer",
    "ModelEvaluator",
    "ModelEvaluationReport",
    "model_evaluator",
]

# Auto-register all default detection engines on package load
register_default_engines()
