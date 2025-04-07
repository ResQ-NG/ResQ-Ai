import mimetypes
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


    def _get_media_type(self, file_path):
        """
        Determine the media type based on the file content.

        Args:
            file_path: The file path of the media file

        Returns:
            The media type as a string
        """
        # Extract the file extension from the file name
        file_type = mimetypes.guess_type(file_path)
        print("evil: ", file_type)
        for media_category, file_types in self.supported_media_types.items():
            if file_type in file_types:
                return media_category
        return None



    async def process_media(self, file_path, file_type):
        """
        Asynchronously process different types of media data.

        Args:
            file_path: The file path of the uploaded media

        Returns:
            Processed media information
        """
        try:

            print("processing")
            # Check if the media_type is in any of the MediaTypes categories
            if file_type in self.supported_media_types["image"]:
                return await self._process_image(file_path)
            elif file_type in self.supported_media_types["video"]:
                return await self._process_video(file_path)
            elif file_type in self.supported_media_types["text"]:
                return await self._process_text(file_path)
            elif file_type in self.supported_media_types["audio"]:
                return await self._process_audio(file_path)
            else:
                print("we found value error: ", file_type)
                raise ValueError(f"Unsupported media type: {file_type}")
        except Exception as e:
            raise RuntimeError(f"Failed to process media: {str(e)}")


    async def _process_image(self, image_file):
        """Process image files and extract relevant information."""
        # Implementation will be added later
        return {"status": "Image processing not yet implemented"}

    async def _process_video(self, video_file):
        """Process video files and identify content."""
        # Implementation will be added later
        return {"status": "Video processing not yet implemented"}

    async def _process_text(self, text_file):
        """Process text files and extract meaningful content."""
        # Implementation will be added later
        return {"status": "Text processing not yet implemented"}

    async def _process_audio(self, audio_file):
        """Process audio files, transcribe content and perform sentiment analysis."""
        # Implementation will be added later
        return {"status": "Audio processing not yet implemented"}


class ResQAIReportSummarizer:
    """
    this would be responsible for generating actual meaningful content from pre processed media.
    """

    pass
