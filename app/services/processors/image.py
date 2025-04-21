from PIL import Image
import os
from app.modules.yolo import YOLOImageSummarizer




class ImageProcessor:
    """
    Responsible for processing image files and extracting relevant information.
    Works with a summarizer to generate meaningful content from processed images.
    """

    def __init__(self, summarizer=None):
        """
        Initialize the image processor with a summarizer.

        Args:
            summarizer: The summarizer instance to use for generating content from processed images
        """
        self.summarizer = summarizer or YOLOImageSummarizer()



    async def process(self, image_path):
        """
        Process an image file and extract relevant information.

        Args:
            image_path: The file path of the image to process

        Returns:
            Dictionary containing processed image information
        """
        try:
            # Basic implementation - to be expanded with actual image processing
            image_info = self._extract_image_metadata(image_path)

            # Use the summarizer to generate content from the image
            summary = await self.summarizer.summarize_image(image_info)

            result = {
                "status": "success",
                "metadata": image_info,
                "summary": summary
            }
            return result
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

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


                return {
                    "path": image_path,
                    "format": format_name,
                    "dimensions": f"{width}x{height}",
                    "size_kb": round(file_size, 2)
                }
        except Exception as e:
            # Fallback to basic info if PIL fails
            return {
                "path": image_path,
                "format": "unknown",
                "dimensions": "unknown",
                "size_kb": "unknown"
            }
