# backend/models/schemas.py
from pydantic import BaseModel
from typing import Any, Dict

class MCPMessage(BaseModel):
    type: str
    sender: str
    receiver: str
    trace_id: str
    payload: Dict[str, Any]
