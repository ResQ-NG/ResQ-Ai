from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
import nltk
from app.utils.logger import main_logger, Status


# Download required NLTK data
try:
    nltk.download("punkt", quiet=True)
except Exception as e:
    main_logger.log(f"Failed to download NLTK punkt: {str(e)}", Status.ERROR)


class SumyProcessor:
    """
    Text summarization processor using the Sumy library with LSA algorithm.
    """

    async def summarize_text(self, text_content: str, sentences_count=2):
        """
        Summarize the provided text content.

        Args:
            text_content: The text to summarize
            sentences_count: Number of sentences to include in the summary

        Returns:
            String containing the summarized text
        """
        try:
            if not text_content or not text_content.strip():
                return "No text content to summarize."

            parser = PlaintextParser.from_string(text_content, Tokenizer("english"))
            summarizer = LsaSummarizer(Stemmer("english"))
            summarizer.stop_words = get_stop_words("english")

            summary = summarizer(parser.document, sentences_count)
            # Convert summary sentences to a readable string
            summary_text = " ".join([str(sentence) for sentence in summary])

            return summary_text

        except Exception as e:
            main_logger.log(f"Error in text summarization: {str(e)}", Status.ERROR)
            return "Failed to generate summary due to an error."
