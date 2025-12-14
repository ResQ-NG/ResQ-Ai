from typing import List, Optional
from pydantic import BaseModel

class CategoryNode(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    parent_id: Optional[int] = None
    children: Optional[List["CategoryNode"]] = None

    class Config:
        from_attributes = True

# For recursive models, update forward references
CategoryNode.model_rebuild()



class StreamInformation(BaseModel):
    report_id: str
    recognized_categories: List[str]
    time_added: str
    is_final: bool
