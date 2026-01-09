import os
from typing import List, Optional
from datetime import datetime, timezone
from app.core.exceptions import AIProcessingError, CacheError, MediaProcessingError
from app.domain.constants.media_constants import MediaTypes
from app.domain.constants.stream_constants import REDIS_STREAM_EVIDENCE_INFERENCE
from app.domain.schema.upload import (
    EvidenceDetectionFinding,
    EvidenceInferenceStreamInformation,
)
from app.services.primitives.image_processing import ImageProcessor
from app.services.primitives.text_processing import TextProcessor
from app.services.primitives.video_processing import VideoProcessor
from app.adapters.storage.s3 import S3Client
from app.adapters.cache.base import StreamInterface
from app.adapters.cache.utils import encode_redis_stream_payload
from app.infra.logger import main_logger, LoggerStatus
from app.domain.utils.main import flatten_list_to_string
from app.adapters.ai.llm.ollama import OllamaLLMEngine
from app.services.ai_categorizer import ResQAICategorizer
from app.core.config import config


def _media_type_lookup():
    return {
        "image": set(MediaTypes.IMAGE.value),
        "video": set(MediaTypes.VIDEO.value),
        "audio": set(MediaTypes.AUDIO.value),
        "text": set(MediaTypes.TEXT.value),
    }


class ResQAIProcessor:
    def __init__(
        self,
        logger=None,
        s3_client: Optional[S3Client] = None,
        stream: Optional[StreamInterface] = None,
    ):
        self.supported_media_types = _media_type_lookup()
        self.logger = logger if logger is not None else main_logger
        self.ollama_engine = OllamaLLMEngine(model="llava")
        self.categorizer = ResQAICategorizer(logger=self.logger)
        self.s3_client = s3_client
        self.stream = stream

    def _get_media_type(self, file_type: str) -> Optional[str]:
        """Determine the media category from MIME type."""
        for media_type, mime_types in self.supported_media_types.items():
            if file_type in mime_types:
                return media_type
        return None

    async def analyze_evidence(
        self,
        file_key: str,
        file_type: str,
        report_id: int,
        correlated_id: Optional[str] = None,
    ) -> None:
        """
        Analyze evidence file by downloading from S3 and routing to appropriate processor.
        Results are pushed to the Redis stream.

        Args:
            file_key: S3 object key for the evidence file (also used as evidence_id)
            file_type: MIME type of the file (e.g., "image/jpeg", "video/mp4")
            report_id: ID of the report this evidence belongs to
            correlated_id: Optional correlation ID for request tracking
        """
        media_type = self._get_media_type(file_type)

        if not media_type:
            self.logger.log(f"Unsupported file type: {file_type}", LoggerStatus.WARNING)
            await self._push_evidence_stream(
                evidence_id=file_key,
                report_id=report_id,
                findings=[],
                analysis_text=f"Unsupported file type: {file_type}",
                is_final=True,
                correlated_id=correlated_id,
            )
            return

        self.logger.log(
            f"Starting evidence analysis: key={file_key}, type={file_type}, media={media_type}",
            LoggerStatus.INFO,
        )

        # Verify S3 client is available
        if not self.s3_client:
            error_msg = "S3 client not configured"
            self.logger.log(error_msg, LoggerStatus.ERROR)
            await self._push_evidence_stream(
                evidence_id=file_key,
                report_id=report_id,
                findings=[],
                analysis_text=error_msg,
                is_final=True,
                correlated_id=correlated_id,
            )
            return

        file_path = None
        try:
            # Download file from S3
            bucket = config.AWS_BUCKET_NAME
            if not bucket:
                raise MediaProcessingError("AWS_BUCKET_NAME not configured")

            file_path = await self.s3_client.download_s3_file_async(
                bucket=bucket,
                key=file_key,
                fileType=file_type,
            )
            self.logger.log(f"Downloaded evidence to: {file_path}", LoggerStatus.DEBUG)

            # Route to appropriate processor
            analysis = await self.process_media(file_path, file_type)

            # Extract findings and analysis text from processor result
            findings, analysis_text = self._extract_findings_from_analysis(analysis)

            # Push final result to stream
            await self._push_evidence_stream(
                evidence_id=file_key,
                report_id=report_id,
                findings=findings,
                analysis_text=analysis_text,
                is_final=True,
                correlated_id=correlated_id,
            )

        except AIProcessingError as e:
            self.logger.log(f"Evidence analysis failed: {str(e)}", LoggerStatus.ERROR)
            await self._push_evidence_stream(
                evidence_id=file_key,
                report_id=report_id,
                findings=[],
                analysis_text=f"Analysis error: {str(e)}",
                is_final=True,
                correlated_id=correlated_id,
            )

        finally:
            # Cleanup temp file
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.log(f"Cleaned up temp file: {file_path}", LoggerStatus.DEBUG)
                except OSError:
                    pass

    def _extract_findings_from_analysis(
        self, analysis: dict
    ) -> tuple[List[EvidenceDetectionFinding], str]:
        """
        Extract findings and analysis text from processor result.

        Args:
            analysis: Raw analysis result from processor

        Returns:
            Tuple of (findings list, analysis text)
        """
        findings = []
        analysis_text = ""

        if analysis.get("status") == "error":
            return findings, analysis.get("error", "Unknown error")

        # Extract from image/video analysis with detections
        summary = analysis.get("summary", {})
        if isinstance(summary, dict):
            detections = summary.get("detections", [])
            for detection in detections:
                findings.append(
                    EvidenceDetectionFinding(
                        label=detection.get("class_", detection.get("label", "unknown")),
                        confidence=float(detection.get("confidence", 0.0)),
                        bounding_box=detection.get("bbox", detection.get("bounding_box", [])),
                    )
                )
            analysis_text = summary.get("summary_text", "")

        # Extract from text analysis
        if not analysis_text and "summary_text" in analysis:
            analysis_text = analysis["summary_text"]

        # Fallback message
        if not analysis_text:
            if findings:
                labels = [f.label for f in findings]
                analysis_text = f"Detected: {', '.join(labels)}"
            else:
                analysis_text = "No significant findings detected"

        return findings, analysis_text

    async def _push_evidence_stream(
        self,
        evidence_id: str,
        report_id: int,
        findings: List[EvidenceDetectionFinding],
        analysis_text: str,
        is_final: bool,
        correlated_id: Optional[str] = None,
    ) -> None:
        """Push evidence inference result to Redis stream."""
        if not self.stream:
            self.logger.log(
                "[STREAM] Stream not available, skipping push", LoggerStatus.DEBUG
            )
            return

        try:
            stream_payload = EvidenceInferenceStreamInformation(
                evidence_id=evidence_id,
                report_id=report_id,
                findings=findings,
                analysis_text=analysis_text,
                time_added=datetime.now(timezone.utc).isoformat(),
                is_final=is_final,
                correlated_id=correlated_id,
            ).model_dump()

            encoded_payload = encode_redis_stream_payload(stream_payload)

            self.logger.log(
                f"[STREAM] Pushing evidence inference for evidence_id={evidence_id}, "
                f"report_id={report_id}, findings={len(findings)}",
                LoggerStatus.DEBUG,
            )

            await self.stream.add_to_stream(REDIS_STREAM_EVIDENCE_INFERENCE, encoded_payload)

        except CacheError as e:
            self.logger.log(f"[STREAM] Failed to push evidence result: {str(e)}", LoggerStatus.ERROR)

    async def process_media(self, file_path: str, file_type: str) -> dict:
        """
        Process media file based on its type.

        Args:
            file_path: Local path to the file
            file_type: MIME type of the file

        Returns:
            dict: Processing result from the appropriate processor
        """
        try:
            if file_type in self.supported_media_types["image"]:
                return await ImageProcessor(logger=self.logger).process(file_path)

            if file_type in self.supported_media_types["video"]:
                return await VideoProcessor(logger=self.logger).process(file_path)

            if file_type in self.supported_media_types["audio"]:
                return {"status": "pending", "message": "Audio processing not yet implemented"}

            if file_type in self.supported_media_types["text"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return await self.simple_summarize_text(content)

            raise ValueError(f"Unsupported media type: {file_type}")

        except Exception as e:
            self.logger.log(f"Failed to process media: {str(e)}", LoggerStatus.ERROR)
            raise AIProcessingError(f"Failed to process media: {str(e)}") from e

    async def simple_summarize_text(self, content: str) -> dict:
        """Summarize text content using TextProcessor."""
        try:
            summary = await TextProcessor().summarize_text_on_dumb_ai(content)
            return summary
        except Exception as e:
            self.logger.log(f"Text summarization failed: {str(e)}", LoggerStatus.ERROR)
            raise

    async def process_report_tags(
        self, tags: List[str], extra_description: Optional[List[str]] = None
    ) -> dict:
        """
        Flattens a JSON, gets summary (description), and generates a title using Ollama LLM.
        Returns dict with title and description.
        """
        try:
            flat_text = flatten_list_to_string(tags)
            if extra_description and len(extra_description) > 0:
                flat_description = flatten_list_to_string(extra_description)
                extra_context = f"- report came with more information on {flat_description}"
            else:
                extra_context = "- user did not provide any extra information."

            text_with_context = f"user made a report and we found these items {flat_text} {extra_context}"

            self.logger.log("Generating title and description with Ollama", LoggerStatus.INFO)
            ollama_response = await self.ollama_engine.generate_report_summary(text_with_context)

            title, description = self.ollama_engine.parse_ollama_response(ollama_response)

            return {"title": title, "description": description}

        except AIProcessingError as e:
            self.logger.log(
                f"Ollama processing failed, falling back to simple method: {str(e)}",
                LoggerStatus.WARNING,
            )
            # Fallback to simple method if Ollama fails
            if extra_description and len(extra_description) > 0:
                flat_description = flatten_list_to_string(extra_description)
                extra_context = f"- report came with more information on {flat_description}"
            else:
                extra_context = "- user did not provide any extra information."
            text_with_context = f"user made a report and we found these items {flat_text} {extra_context}"
            summary = await self.simple_summarize_text(text_with_context)
            title = self._generate_fallback_title(text_with_context, summary)
            return {"title": title, "description": summary.get("summary_text", "")}

    def _generate_fallback_title(self, flat_text: str, summary: Optional[dict]) -> str:
        """
        Fallback method for generating titles when Ollama is not available.
        Simple: first 8 words capitalized
        """
        text = summary.get("summary_text", flat_text) if summary else flat_text
        words = text.strip().split()
        if not words:
            return "Untitled"
        return " ".join(words[:8]).capitalize() + ("..." if len(words) > 8 else "")
