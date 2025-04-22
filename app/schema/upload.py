from typing import List
from pydantic import BaseModel


class MediaRequest(BaseModel):
    file_key: str
    file_type: str


class Detection(BaseModel):
    class_: str
    confidence: float
    bbox: List[float]


class Summary(BaseModel):
    detections: List[Detection]
    summary_text: str


class Metadata(BaseModel):
    path: str
    format: str
    dimensions: str
    size_kb: float


class AIResponse(BaseModel):
    status: str
    metadata: Metadata
    summary: Summary


class ProcessTextContentRequest(BaseModel):
    summary: str
