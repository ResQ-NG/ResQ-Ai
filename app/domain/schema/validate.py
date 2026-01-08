from pydantic import BaseModel


class AIPredictiveValidation(BaseModel):
    summary: str  # AI-generated summary explaining the assessment
    requires_human_review: bool  # Does this report need human review?
    confidence_score: float  # LLM confidence in assessment (0-100)
    final_validity_status: str  # 'valid', 'suspicious', 'invalid', 'requires_review'
    reasons: list[str]  # List of reasons explaining why the report is valid/invalid
    supporting_inferences: list[str]  # Inferences that back up the validity decision

class ValidationIssue(BaseModel):
    field: str
    message: str
    level: str  # "error", "warning", "info"


class ValidationInference(BaseModel):
    category: str               # Category of the inference
    observation: str            # Observation description
    level: str                  # "error", "warning", "info"

class ValidationMetadata(BaseModel):
    reporter_history_count: int
    rejected_reports_count: int
    device_fingerprint_match: bool
    average_evidence_distance: float
    report_frequency_score: int
    reporter_join_date: str | None = None  # ISO 8601 format

class DeterministicValidationData(BaseModel):
    trust_score: int
    is_valid: bool
    issues: list[ValidationIssue]
    inferences: list[ValidationInference]
    metadata: ValidationMetadata
    issues_count: int
    inferences_count: int

class AIPredictiveValidationRequest(BaseModel):
    report_id: int
    report_title: str
    report_summary: str
    categories: list[str]  # Category slugs
    deterministic_validation: DeterministicValidationData

class PredictiveValidationStreamInformation(BaseModel):
    report_id: int
    summary: str
    requires_human_review: bool
    confidence_score: float
    final_validity_status: str  # 'valid', 'suspicious', 'invalid', 'requires_review'
    reasons: list[str]  # List of reasons explaining the validity decision
    supporting_inferences: list[str]  # Inferences backing up the decision
    time_added: str
    is_final: bool
    correlated_id: str | None = None


class AIPredictiveValidationResponse(BaseModel):
    message: str
