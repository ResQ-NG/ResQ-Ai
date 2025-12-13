import os
from PIL import Image
from app.adapters.ai.yolo import YOLOImageSummarizer
from app.core.exceptions import ServiceException
from app.infra.logger import main_logger, LoggerStatus


class ImageProcessor:
    """
    Responsible for processing image files and extracting relevant information.
    Works with a summarizer to generate meaningful content from processed images.
    """

    def __init__(self, summarizer=None, logger=None):
        """
        Initialize the image processor with a summarizer and logger.

        Args:
            summarizer: The summarizer instance to use for generating content from processed images
            logger: StructuredLogger instance for internal logging (optional)
        """
        self.logger = logger or main_logger

        # Pass logger into YOLOImageSummarizer if not provided
        if summarizer is None:
            self.summarizer = YOLOImageSummarizer(logger=self.logger)
        else:
            self.summarizer = summarizer

    async def process(self, image_path):
        """
        Process an image file and extract relevant information.

        Args:
            image_path: The file path of the image to process

        Returns:
            Dictionary containing processed image information
        """
        try:
            self.logger.log(
                f"Starting image processing: {image_path}", LoggerStatus.INFO
            )

            image_info = self._extract_image_metadata(image_path)
            self.logger.log(
                f"Extracted image metadata: {image_info}", LoggerStatus.DEBUG
            )

            # Use the summarizer to generate content from the image
            summary = await self.summarizer.summarize_image(image_info)
            self.logger.log(
                f"Image summarized. Keys: {list[str](summary.keys())}",
                LoggerStatus.INFO,
            )

            result = {"status": "success", "metadata": image_info, "summary": summary}
            self.logger.log(
                f"Image processing complete for: {image_path}", LoggerStatus.SUCCESS
            )
            return result

        except ServiceException as e:
            self.logger.log(
                f"Error during image processing: {str(e)}",
                LoggerStatus.ERROR,
                details={"image_path": image_path},
            )
            return {"status": "error", "error": str(e)}

    def _extract_image_metadata(self, image_path):
        """
        Extract metadata from an image file.

        Args:
            image_path: The file path of the image

        Returns:
            Dictionary containing image metadata
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format
                file_size = os.path.getsize(image_path) / 1024  # size in KB

                metadata = {
                    "path": image_path,
                    "format": format_name,
                    "dimensions": f"{width}x{height}",
                    "size_kb": round(file_size, 2),
                }
                self.logger.log(
                    f"Metadata extracted for {image_path}: {metadata}",
                    LoggerStatus.DEBUG,
                )
                return metadata
        except ServiceException as e:
            self.logger.log(
                f"Failed to extract metadata for {image_path}: {str(e)}",
                LoggerStatus.WARNING,
            )
            # Fallback to basic info if PIL fails
            return {
                "path": image_path,
                "format": "unknown",
                "dimensions": "unknown",
                "size_kb": "unknown",
            }
