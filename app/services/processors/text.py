from app.modules.sumy import SumyProcessor


class TextProcessor:
    def __init__(self, summarizer=None):
        """
        Initialize the image processor with a summarizer.

        Args:
            summarizer: The summarizer instance to use for generating content from processed images
        """
        # this would be a llm transformer
        self.summarizer = summarizer or SumyProcessor()

    async def summarize_text(self, text_content: str):
        """this would use the summarizer class to summarize a specific text content"""
        try:
            result = await self.summarizer.summarize_text(text_content)
            return {"summary_text": result}
        except Exception as e:
            from app.utils.logger import main_logger, Status

            main_logger.log(f"Error summarizing text: {str(e)}", Status.ERROR)
            return {"summary_text": "Failed to generate summary due to an error."}
