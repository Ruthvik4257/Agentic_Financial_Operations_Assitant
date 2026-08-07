import hashlib
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models.audit import AuditLog
from backend.app.models.dispute import Dispute
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/compliance", tags=["Compliance & Audit"])


def calculate_merkle_root(hashes: List[str]) -> str:
    """Computes the cryptographic Merkle Root of a list of audit hashes."""
    if not hashes:
        return AuditService.GENESIS_HASH
    
    current_level = hashes
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = hashlib.sha256(f"{left}:{right}".encode("utf-8")).hexdigest()
            next_level.append(combined)
        current_level = next_level
    return current_level[0]


@router.get("/certificate/{dispute_id}")
async def generate_audit_certificate(
    dispute_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a cryptographically verified compliance certificate containing the Merkle Root,
    SHA-256 hash chain, and ERPNext balance sheet impact.
    """
    # 1. Fetch Dispute
    stmt_d = select(Dispute).where(Dispute.id == dispute_id)
    res_d = await db.execute(stmt_d)
    dispute = res_d.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")

    # 2. Fetch all audit logs
    stmt_a = select(AuditLog).where(AuditLog.dispute_id == dispute_id).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc())
    res_a = await db.execute(stmt_a)
    logs = res_a.scalars().all()

    # 3. Verify Chain Integrity
    is_valid = await AuditService.verify_chain(db, dispute_id)
    all_hashes = [l.current_hash for l in logs]
    merkle_root = calculate_merkle_root(all_hashes)

    return {
        "certificate_id": f"CERT-SOX-{dispute_id}",
        "dispute_id": dispute_id,
        "customer_id": dispute.customer_id,
        "invoice_id": dispute.invoice_id,
        "amount_usd": dispute.amount,
        "status": dispute.status.value,
        "erp_payment_entry": dispute.erp_payment_entry_id,
        "chain_integrity_verified": is_valid,
        "total_audit_events": len(logs),
        "merkle_root": merkle_root,
        "head_hash": all_hashes[-1] if all_hashes else AuditService.GENESIS_HASH,
        "events": [l.to_dict() for l in logs],
        "compliance_standards": ["SOX Section 404", "PCI-DSS v4.0 Requirement 10 (Audit Logging)"],
    }
