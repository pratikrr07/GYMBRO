"""
Chat routes — POST /api/chat for the fitness chatbot.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.chatbot import get_chat_response, get_suggested_questions
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    source: str
    matched_topic: str | None = None


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    """Handle a chat message and return a fitness-related response."""
    result = await get_chat_response(req.message, user)
    return ChatResponse(**result)


@router.get("/suggestions")
async def suggestions(user: dict = Depends(get_current_user)):
    """Return 5 random suggested questions for the chat UI."""
    questions = await get_suggested_questions()
    return {"suggestions": questions}
