from typing import List, Optional
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


class AIResponseLightSummarizationResponse(BaseModel):
    title: str
    description: str


class AIResponseLightSummarizationRequest(BaseModel):
    tags: List[str]
    extra_description: Optional[List[str]] = None


class AILightCategorizeResponse(BaseModel):
    message: str


class AILightCategorizeRequest(BaseModel):
    report_id: str
    title: str
    description: str
    cache_key: Optional[str] = "categories:tree"
