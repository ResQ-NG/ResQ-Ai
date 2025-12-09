"""
app.adapters.ai.sumy_lib
------------------------

This module provides an asynchronous text summarization utility using the Sumy library,
specifically employing the Latent Semantic Analysis (LSA) algorithm. It is intended for use
in AI pipelines where concise summaries of longer English text content are required, such as
user-facing summarization features, automated report generation, or downstream LLM prompt construction.

Key features:
    - Uses the Sumy library's LSA summarizer for extractive summaries.
    - Handles NLTK dependency management for required tokenization data.
    - Wraps summarization logic in an async-friendly class for integration with modern Python web stacks.
    - Logs major errors via an injected logger for observability and debugging.
    - Intended for English-language texts.

Typical Usage:
    from app.infra.logger import main_logger
    processor = SumyProcessor(logger=main_logger)
    summary = await processor.summarize_text(SumyInput(text_content=long_text, sentences_count=3))

Dependencies:
    - sumy
    - nltk (for sentence tokenization)
    - pydantic (for input/output typing)
"""

import nltk
from typing import Optional

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

from pydantic import BaseModel, Field

from app.infra.logger import StructuredLogger, LoggerStatus, main_logger
from app.core.exceptions import AIProcessingError

# Download required NLTK data
try:
    nltk.download("punkt", quiet=True)
except Exception as exc:
    main_logger.log(f"Failed to download NLTK punkt: {str(exc)}", LoggerStatus.ERROR)
    raise AIProcessingError(
        "Failed to download NLTK punkt.", details={"error": str(exc)}
    ) from exc


class SumyInput(BaseModel):
    text_content: str = Field(..., description="The text to summarize")
    sentences_count: int = Field(2, ge=1, description="Number of sentences in the summary")


class SumySummaryResult(BaseModel):
    summary_text: str


class SumyProcessor:
    """
    Text summarization processor using the Sumy library with the LSA algorithm.

    This class exposes a single async method for summarizing text input, meant for English-language
    sources. The summary will extract a configurable number of sentences that best represent the
    core content of the input.

    Args:
        logger: StructuredLogger instance for logging errors and info (optional, defaults to main_logger)
    """

    def __init__(self, logger: Optional[StructuredLogger] = None):
        self.logger = logger or main_logger

    async def summarize_text(
        self, input_data: SumyInput
    ) -> SumySummaryResult:
        """
        Summarize the provided text content.

        Args:
            input_data: SumyInput Pydantic model containing the text and summary config.

        Returns:
            SumySummaryResult containing the summarized text.

        Raises:
            AIProcessingError: If an error occurs during summarization.
        """
        if not input_data.text_content or not input_data.text_content.strip():
            return SumySummaryResult(summary_text="No text content to summarize.")

        try:
            parser = PlaintextParser.from_string(input_data.text_content, Tokenizer("english"))
            summarizer = LsaSummarizer(Stemmer("english"))
            summarizer.stop_words = get_stop_words("english")

            summary = summarizer(parser.document, input_data.sentences_count)
            # Convert summary sentences to a readable string
            summary_text = " ".join(str(sentence) for sentence in summary)

            return SumySummaryResult(summary_text=summary_text)

        except Exception as exc:
            error_msg = f"Error in text summarization: {str(exc)}"
            self.logger.log(error_msg, LoggerStatus.ERROR)
            raise AIProcessingError(
                "Failed to generate summary.", details={"error": str(exc)}
            ) from exc
