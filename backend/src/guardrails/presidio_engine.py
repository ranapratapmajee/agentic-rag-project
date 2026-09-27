from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from backend.src.guardrails.regex_patterns import CUSTOM_RECOGNIZERS

def create_analyzer() -> AnalyzerEngine:
    """Initializes Presidio using the lightweight spaCy sm model."""
    nlp_engine = SpacyNlpEngine(models=[{"lang_code": "en", "model_name": "en_core_web_sm"}])
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    
    for recognizer in CUSTOM_RECOGNIZERS:
        analyzer.registry.add_recognizer(recognizer)
        
    return analyzer

presidio_analyzer = create_analyzer()