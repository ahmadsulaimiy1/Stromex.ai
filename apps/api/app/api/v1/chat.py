from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rate_limit import RateLimiter
from app.db.base import get_db
from app.db.models.user import User
from app.schemas.conversation import ChatRequest, ChatResponse, MessageRead
from app.services.chat_service import run_chat_turn
from app.services.llm.base import ProviderError

router = APIRouter(prefix="/chat", tags=["chat"])

_chat_rate_limit = RateLimiter(times=30, seconds=60, bucket="chat")


@router.post("", response_model=ChatResponse, dependencies=[Depends(_chat_rate_limit)])
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    try:
        conversation, assistant_message = await run_chat_turn(
            db,
            user=user,
            conversation_id=payload.conversation_id,
            user_message=payload.message,
            mode=payload.mode,
            force_provider=payload.force_provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No model provider could handle this request: {exc}",
        ) from exc

    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageRead.model_validate(assistant_message),
    )
