from typing import Any, Dict, Optional
from app.core.exceptions import AIProcessingError
from app.domain.constants.media_constants import MediaTypes
from app.services.primitives.image_processing import ImageProcessor
from app.services.primitives.text_processing import TextProcessor
from app.infra.logger import main_logger, LoggerStatus
from app.domain.utils.main import flatten_json_to_string

def _media_type_lookup():
    return {
        "image": set(MediaTypes.IMAGE.value),
        "video": set(MediaTypes.VIDEO.value),
        "audio": set(MediaTypes.AUDIO.value),
        "text": set(MediaTypes.TEXT.value),
    }

class ResQAIProcessor:
    def __init__(self, logger=None):
        self.supported_media_types = _media_type_lookup()
        self.logger = logger if logger is not None else main_logger

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

    async def process_json_input(self, json_input: Any):
        """
        Flattens a JSON, gets summary (description), and generates a title.
        Returns dict with title and description.
        """
        flat_text = flatten_json_to_string(json_input)
        summary = await self.simple_summarize_text(flat_text)
        title = await self.generate_title(flat_text, summary)
        return {
            "title": title,
            "description": summary.get("summary_text", "")
        }

    async def generate_title(self, flat_text: str, summary: Optional[dict]) -> str:
        # Just pick first N tokens of summary for now, or use dumb rules
        # TODO pass this to a light llm.
        text = summary.get("summary_text", flat_text) if summary else flat_text
        words = text.strip().split()
        if not words:
            return "Untitled"
        # Simple: first 8 words capitalized
        return " ".join(words[:8]).capitalize() + ("..." if len(words) > 8 else "")

    async def categorize(self, title: str, description: str, metadata: Dict[str, Any]) -> str:
        """
        Naive categorization by matching simple keywords.
        Looks at title, description and metadata.
        """
        categories = {
            "finance": ["invoice", "price", "cost", "budget", "payment"],
            "health": ["doctor", "hospital", "health", "medicine", "disease"],
            "technology": ["software", "app", "ai", "computer", "network"],
            "education": ["school", "teacher", "learning", "exam", "university"],
            "media": ["image", "video", "audio", "picture"],
            "other": []
        }
        content_text = f"{title} {description}".lower()
        # Also consider maybe 'format' or 'type' in metadata
        metadata_str = " ".join(str(v) for v in metadata.values()).lower() if metadata else ""
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in content_text or kw in metadata_str:
                    return cat
        return "other"
