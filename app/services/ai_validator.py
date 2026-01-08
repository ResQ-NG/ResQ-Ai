from typing import Optional
from datetime import datetime, timezone
from app.domain.schema.validate import (
    AIPredictiveValidation,
    AIPredictiveValidationRequest,
    PredictiveValidationStreamInformation,
)
from app.domain.constants.stream_constants import REDIS_STREAM_REPORT_PREDICTIVE_VALIDATION
from app.adapters.ai.llm.ollama import OllamaLLMEngine
from app.adapters.cache.base import StreamInterface
from app.adapters.cache.utils import encode_redis_stream_payload
from app.infra.logger import main_logger
from app.core.exceptions import AIProcessingError, CacheError


class ResQAIValidator:
    def __init__(
        self,
        logger=None,
        llm_engine: Optional[OllamaLLMEngine] = None,
        stream: Optional[StreamInterface] = None,
    ):
        """
        Initialize the AI validator.

        Args:
            logger: Optional logger instance (defaults to main_logger)
            llm_engine: Optional LLM engine instance (defaults to OllamaLLMEngine)
            stream: Optional stream interface for pushing validation results
        """
        self.logger = logger if logger is not None else main_logger
        self.llm_engine = llm_engine or OllamaLLMEngine(model="llama2-uncensored")
        self.stream = stream

    async def validate_report(
        self, req_body: AIPredictiveValidationRequest, correlated_id: Optional[str] = None
    ) -> AIPredictiveValidation:
        """
        Runs predictive validation using AI for the given report data.

        Args:
            req_body: An instance of AIPredictiveValidationRequest (from schema)
            correlated_id: Optional correlation ID for logging/tracing

        Returns:
            AIPredictiveValidation: Result of the AI validation
        """
        try:
            self.logger.debug(
                f"[VALIDATION] Starting predictive validation for report_id={req_body.report_id}"
            )

            # Prepare deterministic validation data for LLM (excluding is_valid - AI decides independently)
            deterministic_data = {
                "trust_score": req_body.deterministic_validation.trust_score,
                "issues_count": req_body.deterministic_validation.issues_count,
                "inferences_count": req_body.deterministic_validation.inferences_count,
                "metadata": req_body.deterministic_validation.metadata.model_dump(),
                "issues": [
                    issue.model_dump() for issue in req_body.deterministic_validation.issues
                ],
                "inferences": [
                    inference.model_dump()
                    for inference in req_body.deterministic_validation.inferences
                ],
            }

            # Call LLM for predictive validation - returns structured ValidationResponse
            llm_result = await self.llm_engine.validate_report(
                title=req_body.report_title,
                summary=req_body.report_summary,
                categories=req_body.categories,
                deterministic_data=deterministic_data,
            )

            # Log parsed LLM result for debugging
            self.logger.debug("\n" + "=" * 80)
            self.logger.debug("[VALIDATION] AI Validation Result:")
            self.logger.debug("=" * 80)
            self.logger.debug(f"Summary: {llm_result.summary}")
            self.logger.debug(f"Requires Human Review: {llm_result.requires_human_review}")
            self.logger.debug(f"Confidence Score: {llm_result.confidence_score}")
            self.logger.debug(f"Final Validity Status: {llm_result.final_validity_status}")
            self.logger.debug(f"Reasons ({len(llm_result.reasons)}):")
            for i, reason in enumerate(llm_result.reasons, 1):
                self.logger.debug(f"  {i}. {reason}")
            self.logger.debug(f"Supporting Inferences ({len(llm_result.supporting_inferences)}):")
            for i, inference in enumerate(llm_result.supporting_inferences, 1):
                self.logger.debug(f"  {i}. {inference}")
            self.logger.debug("=" * 80 + "\n")

            # Map LLM response directly to schema (types already match)
            validation_result = AIPredictiveValidation(
                summary=llm_result.summary,
                requires_human_review=llm_result.requires_human_review,
                confidence_score=llm_result.confidence_score,
                final_validity_status=llm_result.final_validity_status,
                reasons=llm_result.reasons,
                supporting_inferences=llm_result.supporting_inferences,
            )

            self.logger.debug(
                f"[VALIDATION] Completed validation for report_id={req_body.report_id}. "
                f"Status: {validation_result.final_validity_status}, "
                f"Confidence: {validation_result.confidence_score}%"
            )

            # Push final result to stream if stream is available
            if self.stream:
                await self._push_to_stream(req_body.report_id, validation_result, correlated_id)

            return validation_result

        except AIProcessingError as e:
            self.logger.log(
                f"Error during predictive validation for report_id={req_body.report_id}: {e}",
                "ERROR",
            )
            # Create a safe fallback response
            fallback_result = AIPredictiveValidation(
                summary=f"Validation error occurred: {str(e)}",
                requires_human_review=True,
                confidence_score=0.0,
                final_validity_status="requires_review",
                reasons=[f"An error occurred during validation: {str(e)}"],
                supporting_inferences=[],
            )

            # Push error result to stream if stream is available
            if self.stream:
                await self._push_to_stream(req_body.report_id, fallback_result, correlated_id)

            return fallback_result

    async def _push_to_stream(
        self,
        report_id: int,
        validation_result: AIPredictiveValidation,
        correlated_id: Optional[str],
    ) -> None:
        """Push validation result to Redis stream."""
        try:
            stream_payload = PredictiveValidationStreamInformation(
                report_id=report_id,
                summary=validation_result.summary,
                requires_human_review=validation_result.requires_human_review,
                confidence_score=validation_result.confidence_score,
                final_validity_status=validation_result.final_validity_status,
                reasons=validation_result.reasons,
                supporting_inferences=validation_result.supporting_inferences,
                time_added=datetime.now(timezone.utc).isoformat(),
                is_final=True,
                correlated_id=correlated_id,
            ).model_dump()
            encoded_payload = encode_redis_stream_payload(stream_payload)
            self.logger.debug(
                f"[STREAM] Pushing validation result for report_id={report_id}: "
                f"Status={validation_result.final_validity_status}, "
                f"Confidence={validation_result.confidence_score}%"
            )
            await self.stream.add_to_stream(
                REDIS_STREAM_REPORT_PREDICTIVE_VALIDATION, encoded_payload
            )
        except CacheError as e:
            self.logger.debug(f"[STREAM] Failed to push validation result: {str(e)}")
