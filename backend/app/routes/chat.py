from fastapi import APIRouter

from app.services.jarvis_service import process_query

router = APIRouter()

@router.post("/chat")
def chat(req: dict):
    message = req.get("message")
    return process_query(message)