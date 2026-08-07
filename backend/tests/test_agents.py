import pytest
from agents.graph import finops_agent
from agents.state import DisputeRecord
from agents.models.fast_classifier import FastEntityExtractor


@pytest.mark.asyncio
async def test_fast_entity_extractor():
    text = "Hello support, I was double charged for invoice INV-2026-001 in the amount of $150.00."
    extracted = FastEntityExtractor.extract_entities(text)
    assert extracted["invoice_id"] == "INV-2026-001"
    assert extracted["amount"] == 150.00
    assert extracted["intent"] == "DOUBLE_CHARGE"


@pytest.mark.asyncio
async def test_langgraph_auto_approve_flow():
    dispute = DisputeRecord(
        dispute_id="DISP-TEST-AUTO",
        customer_id="CUST-001",
        invoice_id="INV-2026-001",
        amount=150.00,
        currency="USD",
        reason="Double charged on credit card",
        status="PENDING_INVESTIGATION",
    )
    inputs = {
        "messages": [{"role": "user", "content": "I was double charged on INV-2026-001"}],
        "dispute": dispute,
    }
    result = await finops_agent.ainvoke(inputs)
    
    assert result["policy_verdict"] == "AUTO_APPROVE"
    assert result["dispute"].status == "EXECUTED"
    assert result["execution_result"]["success"] is True
    assert result["execution_result"]["payment_entry_id"].startswith("PE-REF-")


@pytest.mark.asyncio
async def test_langgraph_hitl_escalation_flow():
    # $850 exceeds $200 limit -> must trigger REQUIRE_HITL
    dispute = DisputeRecord(
        dispute_id="DISP-TEST-HIGH",
        customer_id="CUST-001",
        invoice_id="INV-2026-045",
        amount=850.00,
        currency="USD",
        reason="Disputing dedicated support invoice INV-2026-045",
        status="PENDING_INVESTIGATION",
    )
    inputs = {
        "messages": [{"role": "user", "content": "Disputing $850 on INV-2026-045"}],
        "dispute": dispute,
    }
    result = await finops_agent.ainvoke(inputs)
    
    assert result["policy_verdict"] == "REQUIRE_HITL"
    assert "Human-in-the-Loop" in result["policy_reason"]
