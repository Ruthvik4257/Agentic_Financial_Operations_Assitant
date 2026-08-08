import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from backend.app.core.config import settings
from agents.state import FraudAssessment
from agents.models.hf_financial_models import hf_financial_model

logger = logging.getLogger("FinOpsLLM")



class GeminiForensicClient:
    """
    Google Gemini Client for multi-step forensic financial reasoning,
    anomaly detection, and dispute analysis with sub-second fallback protection.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client = None
        
        if self.api_key and not self.api_key.startswith("your_"):
            try:
                # pyrefly: ignore [missing-import]
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model_name)
                logger.info("Gemini AI client successfully initialized with model %s", self.model_name)
            except Exception as e:
                logger.warning("Failed to initialize Google Gemini client: %s. Using heuristic fallback.", e)

    async def analyze_dispute(
        self,
        customer_id: str,
        invoice_id: str,
        amount: float,
        dispute_reason: str,
        erp_invoice: Optional[Dict[str, Any]],
        erp_payments: Optional[list],
        customer_profile: Optional[Dict[str, Any]],
    ) -> FraudAssessment:
        """
        Executes forensic fraud analysis on dispute evidence with timeout protection.
        """
        # 1. Deterministic Ledger Checks (Absolute Ground Truth)
        is_duplicate = False
        if erp_payments and len(erp_payments) >= 2:
            total_paid = sum(p.get("paid_amount", 0.0) for p in erp_payments)
            invoice_total = erp_invoice.get("grand_total", 0.0) if erp_invoice else 0.0
            if total_paid > invoice_total and invoice_total > 0:
                is_duplicate = True

        prompt = f"""
        You are an expert Forensic Financial Auditor for Enterprise ERP operations.
        Analyze the following payment dispute and output strict JSON.
        Dispute: Invoice {invoice_id}, Amount ${amount}, Reason: "{dispute_reason}", Duplicate: {is_duplicate}.
        Evaluate risk score between 0.00 and 1.00.
        Return ONLY valid JSON:
        {{
            "risk_score": 0.08,
            "risk_tier": "LOW",
            "duplicate_payment_confirmed": {str(is_duplicate).lower()},
            "anomaly_flags": ["DUPLICATE_GATEWAY_CAPTURE"],
            "forensic_summary": "ERPNext confirms duplicate payment entry.",
            "accounting_justification": "Reverse Payment Entry balances ledger 2110 with 1110."
        }}
        """

        if self._client:
            try:
                # Wrap in asyncio.to_thread with 3.5s timeout for fast execution
                def _generate():
                    return self._client.generate_content(
                        prompt,
                        generation_config={"response_mime_type": "application/json"},
                    )
                
                response = await asyncio.wait_for(asyncio.to_thread(_generate), timeout=3.5)
                text = response.text.strip()
                parsed = json.loads(text)
                return FraudAssessment(
                    risk_score=float(parsed.get("risk_score", 0.08 if is_duplicate else 0.45)),
                    risk_tier=str(parsed.get("risk_tier", "LOW" if is_duplicate else "MEDIUM")),
                    duplicate_payment_confirmed=bool(parsed.get("duplicate_payment_confirmed", is_duplicate)),
                    anomaly_flags=list(parsed.get("anomaly_flags", ["DUPLICATE_PAYMENT_ENTRY_MATCHED" if is_duplicate else "STANDARD_DISPUTE"])),
                    forensic_summary=str(parsed.get("forensic_summary", "Analyzed via Gemini 2.0 Flash.")),
                    accounting_justification=str(parsed.get("accounting_justification", "Reconciled with ERPNext ledger.")),
                )
            except Exception as e:
                logger.warning("Gemini call timed out or failed: %s. Using Hugging Face Financial helper model.", e)

        # Hugging Face Financial Helper Model Integration
        hf_risk = await hf_financial_model.analyze_dispute_risk(
            amount=amount,
            dispute_reason=dispute_reason,
            is_duplicate=is_duplicate,
            customer_profile=customer_profile,
        )

        return FraudAssessment(
            risk_score=float(hf_risk["risk_score"]),
            risk_tier=str(hf_risk["risk_tier"]),
            duplicate_payment_confirmed=bool(is_duplicate),
            anomaly_flags=list(hf_risk["anomaly_flags"]),
            forensic_summary=str(hf_risk["forensic_summary"]),
            accounting_justification=str(hf_risk["accounting_justification"]),
        )


llm_client = GeminiForensicClient()


def get_langchain_gemini_llm(model_name: Optional[str] = None, temperature: float = 0.1):
    """
    Returns a LangChain ChatGoogleGenerativeAI instance using the unified GEMINI_API_KEY.
    Provides logical reasoning, thinking brain capabilities, and chain/agent compatibility.
    """
    api_key = settings.GEMINI_API_KEY
    chosen_model = model_name or settings.GEMINI_MODEL

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        if api_key and not api_key.startswith("your_"):
            return ChatGoogleGenerativeAI(
                model=chosen_model,
                google_api_key=api_key,
                temperature=temperature,
            )
    except Exception as e:
        logger.warning("Could not initialize langchain_google_genai (%s). Falling back to direct Gemini client.", e)

    return llm_client


