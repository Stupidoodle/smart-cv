from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class FunctionDefinition(BaseModel):
    name: str
    strict: Optional[bool] = False
    parameters: Dict[str, Any]
    description: Optional[str] = None


class ToolCreate(BaseModel):
    type: str  # e.g., 'function', 'code_interpreter'
    function: Optional[FunctionDefinition] = None


class AssistantCreate(BaseModel):
    name: str
    instructions: str
    model: str
    tools: Optional[List[ToolCreate]] = None
    response_format: Optional[BaseModel] = None


class ToolResponse(BaseModel):
    id: str
    type: str
    function: Optional[FunctionDefinition] = None

    class Config:
        orm_mode = True


class AssistantResponse(BaseModel):
    id: str
    name: str
    instructions: str
    model: str
    tools: List[ToolResponse]

    class Config:
        orm_mode = True
