# backend/utils/mcp.py
import uuid
from typing import Any, Dict

def generate_trace_id() -> str:
    return f"trace-{uuid.uuid4()}"

def build_mcp_message(sender: str, receiver: str, msg_type: str, payload: Dict[str, Any], trace_id: str = None) -> Dict:
    return {
        "type": msg_type,
        "sender": sender,
        "receiver": receiver,
        "trace_id": trace_id or generate_trace_id(),
        "payload": payload
    }
