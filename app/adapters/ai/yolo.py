"""
app.adapters.ai.yolo
--------------------

This module provides functionality to perform object detection and summarization on images
using the YOLO (You Only Look Once) deep learning model, powered by the `ultralytics` library.

The primary use case is extracting a list of detected objects (class, confidence, bounding box)
from an input image and generating a concise, human-readable summary of what objects are present
in the image.

Typical usage:
    - Initialize `YOLOImageSummarizer` (optionally specifying a preferred YOLO model checkpoint).
    - Call `summarize_image`, passing in a dictionary with an image `path`.
    - Receive a dictionary with:
        - `detections`: list of detected objects (with class, confidence, and bounding box)
        - `summary_text`: a text summary of detected items in the image

This is intended for downstream use cases where image contents need to be quickly interpreted
(e.g., for generative AI tasks, search, or reporting workflows).

Dependencies:
    - `ultralytics` (for YOLO)
    - Internal logging via injected logger

Example:
    summarizer = YOLOImageSummarizer(logger=my_logger)
    result = await summarizer.summarize_image({"path": "/tmp/image.png"})
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

from ultralytics import YOLO
from app.infra.logger import StructuredLogger, LoggerStatus
from app.core.exceptions import AIProcessingError


class ImageInfo(BaseModel):
    path: str


class Detection(BaseModel):
    class_: str = Field(..., alias="class")
    confidence: float
    bbox: List[float]


class SummarizeImageResult(BaseModel):
    detections: List[Detection]
    summary_text: str


class YOLOImageSummarizer:
    """
    Uses YOLO model to detect objects in images and generate summaries.
    """

    def __init__(
        self, logger: StructuredLogger, model_path: str = "yolov8n.pt"
    ) -> None:
        """
        Initialize the YOLO summarizer with a model and injected logger.

        Args:
            logger: StructuredLogger instance for internal logging
            model_path: Path to the YOLO model file, defaults to YOLOv8 nano
        """
        self.logger: StructuredLogger = logger
        try:
            self.model: YOLO = YOLO(model_path)
            self.logger.log(
                f"YOLO model initialized with {model_path}", LoggerStatus.INFO
            )
        except Exception as exc:
            self.logger.log(
                f"Failed to initialize YOLO model: {str(exc)}", LoggerStatus.ERROR
            )
            raise AIProcessingError(
                "Failed to initialize YOLO model.", details={"error": str(exc)}
            ) from exc

    async def summarize_image(self, image_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an image using YOLO and generate a summary of detected objects.

        Args:
            image_info: Dictionary containing image metadata including path

        Returns:
            Dictionary containing detection results and summary
        """
        try:
            parsed_info = ImageInfo(**image_info)
        except ValidationError as exc:
            self.logger.log("Validation error for input image_info", LoggerStatus.ERROR)
            raise AIProcessingError(
                "Invalid image info provided.",
                details={"errors": exc.errors(), "image_info": image_info},
            ) from exc

        image_path: str = parsed_info.path

        try:
            self.logger.log(f"Processing image: {image_path}", LoggerStatus.INFO)
            results = self.model(image_path)
        except Exception as exc:
            self.logger.log(
                f"YOLO inference failed for image '{image_path}': {str(exc)}",
                LoggerStatus.ERROR,
            )
            raise AIProcessingError(
                "YOLO inference failed.",
                details={"error": str(exc), "image_path": image_path},
            ) from exc

        detections: List[Detection] = []
        try:
            for result in results:
                names: Optional[Dict[int, str]] = getattr(result, "names", None)
                for box in getattr(result, "boxes", []):
                    try:
                        class_idx: int = int(box.cls[0])
                        detection_dict = {
                            "class": (
                                names[class_idx]
                                if names and class_idx in names
                                else str(class_idx)
                            ),
                            "confidence": float(box.conf[0]),
                            "bbox": box.xyxy[0].tolist(),
                        }
                        detection = Detection(**detection_dict)
                        detections.append(detection)
                    except (
                        AttributeError,
                        IndexError,
                        KeyError,
                        TypeError,
                        ValueError,
                        ValidationError,
                    ) as exc:
                        self.logger.log(
                            f"Failed to parse detection: {str(exc)}",
                            LoggerStatus.WARNING,
                            details={"box": str(box)},
                        )
        except Exception as exc:
            self.logger.log(
                f"Failed to extract detection information: {str(exc)}",
                LoggerStatus.ERROR,
                details={"results": str(results)},
            )
            raise AIProcessingError(
                "Failed to extract detection information.", details={"error": str(exc)}
            ) from exc

        # Generate a simple text summary
        try:
            summary_text: str = self._generate_summary_text(detections)
        except Exception as exc:
            self.logger.log(
                f"Failed to generate summary text: {str(exc)}",
                LoggerStatus.ERROR,
                details={"detections": [det.dict(by_alias=True) for det in detections]},
            )
            raise AIProcessingError(
                "Failed to generate summary text.", details={"error": str(exc)}
            ) from exc

        self.logger.log(
            f"Image analysis complete: {len(detections)} objects detected",
            LoggerStatus.SUCCESS,
        )
        result = SummarizeImageResult(detections=detections, summary_text=summary_text)
        return result.dict(by_alias=True)

    def _generate_summary_text(self, detections: List[Detection]) -> str:
        """
        Generate a human-readable summary from the detections.

        Args:
            detections: List of detected objects

        Returns:
            String summary of detected objects
        """
        if not detections:
            self.logger.log("No objects detected in the image", LoggerStatus.WARNING)
            return "No objects detected in the image."

        # Count objects by class
        object_counts: Dict[str, int] = {}
        for det in detections:
            obj_class: str = det.class_
            object_counts[obj_class] = object_counts.get(obj_class, 0) + 1

        # Create summary text
        summary_parts: List[str] = []
        for obj_class, count in object_counts.items():
            summary_parts.append(f"{count} {obj_class}{'s' if count > 1 else ''}")

        if len(summary_parts) == 1:
            return f"Detected {summary_parts[0]} in the image."
        else:
            last_part = summary_parts.pop()
            return f"Detected {', '.join(summary_parts)} and {last_part} in the image."
