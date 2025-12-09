
from app.adapters.ai.sumy_lib import SumyProcessor
from app.core.exceptions import AIProcessingError



class TextProcessor:
    def __init__(self, summarizer=None):
        """
        Initialize the text processor with a summarizer.

        Args:
            summarizer: The summarizer instance to use for generating content from text
        """
        # Use the provided summarizer or default to a simple implementation
        self.summarizer = summarizer or SumyProcessor()

    async def summarize_text(self, _payload):
        """
        Placeholder for future: would use a fast AI agent to summarize text.
        """
        # Implement your LangChain or fast-LLM agent here in future.
        # For now, just return a basic summary as a stub.
        return {"summary_text": "This feature is coming soon."}

    async def summarize_text_on_dumb_ai(self, text_content: str):
        """
        Summarizes the provided text content using the configured summarizer.

        Args:
            text_content (str): The text to be summarized.

        Returns:
            dict: A dictionary containing the summarized text under the "summary_text" key.
        """
        try:
            summary_result = await self.summarizer.summarize_text(
                self.summarizer.__class__.__name__ == "SumyProcessor"
                and type("SumyInput", (), {"text_content": text_content, "sentences_count": 2})()
                or text_content
            )
            # If summarizer returns a pydantic model with attribute, extract summary_text
            summary_text = getattr(summary_result, "summary_text", summary_result)
            return {"summary_text": summary_text}
        except Exception as e:
            raise AIProcessingError(
                "Could not summarize text.",
                details={
                    "error": str(e),
                    "input_excerpt": text_content[:100]
                }
            ) from e
