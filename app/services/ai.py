import mimetypes
from app.services.processors.image import ImageProcessor
from app.services.processors.text import TextProcessor
from app.utils.constants import MediaTypes


class ResQAIMediaProcessor:
    """
    Responsible for processing different types of media and extracting important information.
    May integrate with SVCA process in the future.
    """

    def __init__(self):
        """
        Initialize the media processor with necessary configurations.
        """
        self.supported_media_types = MediaTypes
        self.temp_file_path = "/tmp/"
        self.max_file_size = 100 * 1024 * 1024

    async def process_media(self, file_path, file_type):
        """
        Asynchronously process different types of media data.

        Args:
            file_path: The file path of the uploaded media

        Returns:
            Processed media information
        """
        try:
            # Check if the media_type is in any of the MediaTypes categories
            if file_type in self.supported_media_types["image"]:
                return await ImageProcessor().process(file_path)

            elif file_type in self.supported_media_types["video"]:
                return await self._process_video(file_path)

            elif file_type in self.supported_media_types["audio"]:
                return await self._process_audio(file_path)
            else:
                print("we found value error: ", file_type)
                raise ValueError(f"Unsupported media type: {file_type}")
        except Exception as e:
            raise RuntimeError(f"Failed to process media: {str(e)}")

    async def process_text(self, text_content):
        """Process text files and extract meaningful content."""
        return await TextProcessor().summarize_text(text_content)

    async def _process_video(self, video_file):
        """Process video files and identify content."""
        # Implementation will be added later
        return {"status": "Video processing not yet implemented"}

    async def _process_audio(self, audio_file):
        """Process audio files, transcribe content and perform sentiment analysis."""
        # Implementation will be added later
        return {"status": "Audio processing not yet implemented"}


class ResQAIReportSummarizer:
    """
    this would be responsible for generating actual meaningful content from pre processed media.
    """

    pass
