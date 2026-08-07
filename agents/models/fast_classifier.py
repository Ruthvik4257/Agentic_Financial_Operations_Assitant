import re
from typing import Dict, Any, Optional, Tuple


class FastEntityExtractor:
    """
    Sub-5ms deterministic token extractor for financial operations.
    Extracts invoice numbers (INV-YYYY-XXX), amounts ($XXX.XX), and transaction hashes.
    """

    INVOICE_REGEX = re.compile(r"\b(INV-\d{4}-\d{3,4})\b", re.IGNORECASE)
    AMOUNT_REGEX = re.compile(r"(?:\$|USD\s*)(\d+(?:\.\d{1,2})?)", re.IGNORECASE)
    TX_HASH_REGEX = re.compile(r"\b(TX-[A-Z0-9-]+|0x[a-fA-F0-9]{8,64})\b", re.IGNORECASE)
    
    INTENT_KEYWORDS = {
        "DOUBLE_CHARGE": ["double", "charged twice", "two times", "duplicate", "billed twice"],
        "REFUND_REQUEST": ["refund", "money back", "reimburse", "return funds"],
        "INVOICE_STATUS": ["status", "check invoice", "where is", "is paid", "outstanding"],
        "OVERCHARGE": ["overcharge", "wrong amount", "too much", "incorrect"],
    }

    @classmethod
    def extract_entities(cls, text: str) -> Dict[str, Any]:
        invoice_match = cls.INVOICE_REGEX.search(text)
        amount_match = cls.AMOUNT_REGEX.search(text)
        tx_match = cls.TX_HASH_REGEX.search(text)

        invoice_id = invoice_match.group(1).upper() if invoice_match else None
        amount = float(amount_match.group(1)) if amount_match else None
        tx_hash = tx_match.group(1) if tx_match else None

        # Intent detection
        lower_text = text.lower()
        detected_intent = "GENERAL_INQUIRY"
        for intent, keywords in cls.INTENT_KEYWORDS.items():
            if any(kw in lower_text for kw in keywords):
                detected_intent = intent
                break

        return {
            "invoice_id": invoice_id,
            "amount": amount,
            "tx_hash": tx_hash,
            "intent": detected_intent,
            "raw_text": text,
        }
