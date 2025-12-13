from typing import Any, Dict, List, Optional
from app.core.exceptions import AIProcessingError
from app.domain.constants.media_constants import MediaTypes
from app.services.primitives.image_processing import ImageProcessor
from app.services.primitives.text_processing import TextProcessor
from app.infra.logger import main_logger, LoggerStatus
from app.domain.utils.main import flatten_list_to_string
from app.adapters.ai.llm.ollama import OllamaLLMEngine


def _media_type_lookup():
    return {
        "image": set[str](MediaTypes.IMAGE.value),
        "video": set[str](MediaTypes.VIDEO.value),
        "audio": set[str](MediaTypes.AUDIO.value),
        "text": set[str](MediaTypes.TEXT.value),
    }


class ResQAIProcessor:
    def __init__(self, logger=None):
        self.supported_media_types = _media_type_lookup()
        self.logger = logger if logger is not None else main_logger
        self.ollama_engine = OllamaLLMEngine()

    async def process_media(self, file_path: str, file_type: str):
        try:
            if file_type in self.supported_media_types["image"]:
                return await ImageProcessor(logger=self.logger).process(file_path)
            if file_type in self.supported_media_types["video"]:
                return {"status": "Video processing not implemented"}
            if file_type in self.supported_media_types["audio"]:
                return {"status": "Audio processing not implemented"}
            if file_type in self.supported_media_types["text"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return await self.simple_summarize_text(content)
            raise ValueError(f"Unsupported media type: {file_type}")
        except Exception as e:
            self.logger.log(f"Failed to process media: {str(e)}", LoggerStatus.ERROR)
            raise AIProcessingError(f"Failed to process media: {str(e)}") from e

    async def simple_summarize_text(self, content: str):
        try:
            summary = await TextProcessor().summarize_text_on_dumb_ai(content)
            return summary
        except Exception as e:
            self.logger.log(f"Text summarization failed: {str(e)}", LoggerStatus.ERROR)
            raise

    async def process_report_tags(
        self, tags: List[str], extra_description: Optional[List[str]] = None
    ):
        """
        Flattens a JSON, gets summary (description), and generates a title using Ollama LLM.
        Returns dict with title and description.
        extra_description is optional. If not provided, mention that the user did not provide extra info.
        """
        try:
            flat_text = flatten_list_to_string(tags)
            if extra_description and len(extra_description) > 0:
                flat_description = flatten_list_to_string(extra_description)
                extra_context = (
                    f"- report came with more information on {flat_description}"
                )
            else:
                extra_context = "- user did not provide any extra information."

            text_with_context = f"user made a report and we found these items {flat_text} {extra_context}"

            # Use Ollama LLM for better title and description generation
            self.logger.log(
                "Generating title and description with Ollama", LoggerStatus.INFO
            )
            ollama_response = await self.ollama_engine.generate_report_summary(
                text_with_context
            )

            # Parse the response (format: "Title: ...\nDescription: ...")
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
                extra_context = (
                    f"- report came with more information on {flat_description}"
                )
            else:
                extra_context = "- user did not provide any extra information."
            text_with_context = f"user made a report and we found these items {flat_text} {extra_context}"
            summary = await self.simple_summarize_text(text_with_context)
            title = await self.generate_title(text_with_context, summary)
            return {"title": title, "description": summary.get("summary_text", "")}


    async def generate_title(self, flat_text: str, summary: Optional[dict]) -> str:
        """
        Fallback method for generating titles when Ollama is not available.
        Simple: first 8 words capitalized
        """
        text = summary.get("summary_text", flat_text) if summary else flat_text
        words = text.strip().split()
        if not words:
            return "Untitled"
        return " ".join(words[:8]).capitalize() + ("..." if len(words) > 8 else "")

    async def categorize_report(
        self, title: str, description: str, metadata: Dict[str, Any]
    ) -> str:
        """
        Naive categorization by matching simple keywords.
        Looks at title, description and metadata.
        """

        # grab the category from the redis. first in a recursion. top grouping then down.
        categories = {
            "finance": ["invoice", "price", "cost", "budget", "payment"],
            "health": ["doctor", "hospital", "health", "medicine", "disease"],
            "technology": ["software", "app", "ai", "computer", "network"],
            "education": ["school", "teacher", "learning", "exam", "university"],
            "media": ["image", "video", "audio", "picture"],
            "other": [],
        }
        content_text = f"{title} {description}".lower()
        # Also consider maybe 'format' or 'type' in metadata
        metadata_str = (
            " ".join(str(v) for v in metadata.values()).lower() if metadata else ""
        )
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in content_text or kw in metadata_str:
                    return cat
        return "other"
