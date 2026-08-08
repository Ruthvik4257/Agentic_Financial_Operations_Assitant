import re
from typing import Dict, Any, Optional
from agents.models.hf_financial_models import HuggingFaceFinancialModel, hf_financial_model


class FastEntityExtractor:
    """
    High-accuracy Financial Entity & Token Extractor powered by
    Hugging Face Financial helper models and multi-pattern NLP tokenizers.
    Extracts invoice numbers (INV-YYYY-XXX), natural language amounts ($200, 200 dollars, two hundred),
    transaction hashes, and financial dispute intents.
    """

    @classmethod
    def extract_entities(cls, text: str) -> Dict[str, Any]:
        extracted = HuggingFaceFinancialModel.extract_financial_entities(text)
        extracted["raw_text"] = text
        return extracted

