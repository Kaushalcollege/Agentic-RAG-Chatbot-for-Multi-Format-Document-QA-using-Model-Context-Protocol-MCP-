# backend/utils/logger.py
def log_trace(message: str, trace_id: str):
    print(f"[TRACE:{trace_id}] {message}")
