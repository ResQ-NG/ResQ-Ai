from ultralytics import YOLO
from app.utils.logger import main_logger, Status


class YOLOImageSummarizer:
    """
    Uses YOLO model to detect objects in images and generate summaries.
    """

    def __init__(self, model_path="yolov8n.pt"):
        """
        Initialize the YOLO summarizer with a model.

        Args:
            model_path: Path to the YOLO model file, defaults to YOLOv8 nano
        """
        self.model = YOLO(model_path)
        main_logger.log(f"YOLO model initialized with {model_path}", Status.INFO)


    async def summarize_image(self, image_info):
        """
        Analyze an image using YOLO and generate a summary of detected objects.

        Args:
            image_info: Dictionary containing image metadata including path

        Returns:
            Dictionary containing detection results and summary
        """
        image_path = image_info["path"]
        main_logger.log(f"Processing image: {image_path}", Status.INFO)
        results = self.model(image_path)



        # Extract detection information
        detections = []
        for result in results:
            for box in result.boxes:
                obj = {
                    "class": result.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bbox": box.xyxy[0].tolist()
                }
                detections.append(obj)


        # Generate a simple text summary
        summary_text = self._generate_summary_text(detections)

        main_logger.log(f"Image analysis complete: {len(detections)} objects detected", Status.SUCCESS)
        return {
            "detections": detections,
            "summary_text": summary_text
        }

    def _generate_summary_text(self, detections):
        """
        Generate a human-readable summary from the detections.

        Args:
            detections: List of detected objects

        Returns:
            String summary of detected objects
        """
        if not detections:
            main_logger.log("No objects detected in the image", Status.WARNING)
            return "No objects detected in the image."

        # Count objects by class
        object_counts = {}
        for det in detections:
            obj_class = det["class"]
            object_counts[obj_class] = object_counts.get(obj_class, 0) + 1



        # Create summary text
        summary_parts = []
        for obj_class, count in object_counts.items():
            summary_parts.append(f"{count} {obj_class}{'s' if count > 1 else ''}")

        if len(summary_parts) == 1:
            return f"Detected {summary_parts[0]} in the image."
        else:
            last_part = summary_parts.pop()
            return f"Detected {', '.join(summary_parts)} and {last_part} in the image."
