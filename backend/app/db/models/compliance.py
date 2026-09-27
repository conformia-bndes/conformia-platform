"""Database models for Compliance Checks and Audit Trail."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(String(100), nullable=False, index=True)
    rule_title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    
    # Status: COMPLIANT, NON_COMPLIANT, MANUAL_REVIEW_REQUIRED, NOT_APPLICABLE
    status = Column(String(50), nullable=False, default="MANUAL_REVIEW_REQUIRED", index=True)
    confidence_score = Column(Float, nullable=False, default=1.0)
    
    evidence = Column(JSON, nullable=True)
    findings = Column(Text, nullable=True)
    checker_type = Column(String(50), nullable=False, default="DETERMINISTIC")  # DETERMINISTIC, LLM_SEMANTIC, MAKER_CHECKER
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="compliance_checks")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    performed_by = Column(String(100), nullable=False, default="SYSTEM_HARNESS")
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
