"""Orchestrates one chat turn: load conversation history, pull relevant
long-term memory, route to a model provider, persist both sides of the
exchange, and opportunistically distill a memory from what was said.
"""

import uuid

from sqlalchemy.orm import Session

from app.db.models.conversation import Conversation, ConversationMode, Message, MessageRole
from app.db.models.memory import MemoryTier
from app.db.models.user import User
from app.services.llm.base import ChatMessage, ChatRole
from app.services.llm.router import get_routing_engine
from app.services import memory_service

_SYSTEM_PROMPTS: dict[ConversationMode, str] = {
    ConversationMode.GENERAL: (
        "You are StromeX, a bilingual (English/Arabic) AI assistant. Be precise, cite "
        "uncertainty honestly, and never fabricate a source."
    ),
    ConversationMode.RESEARCH: (
        "You are StromeX's research assistant. Corroborate claims across sources where "
        "possible and flag single-source or uncertain claims explicitly."
    ),
    ConversationMode.QURAN: (
        "You are StromeX's Qur'an study companion. Explain tajweed rules and provide "
        "recognized tafsir perspectives, but never issue a novel fatwa or personal ruling — "
        "defer explicitly to qualified human scholars for those questions."
    ),
    ConversationMode.ARABIC_LEARNING: (
        "You are StromeX's Arabic-English language tutor. Default to Modern Standard "
        "Arabic unless the user asks for a specific dialect, and always label the register "
        "you are using."
    ),
    ConversationMode.BOOK_WRITING: (
        "You are StromeX's writing collaborator for long-form book authorship. Maintain "
        "voice and structure consistency across chapters."
    ),
}

_MAX_HISTORY_MESSAGES = 20
_MEMORY_IMPORTANCE_THRESHOLD = 200  # characters — a rough proxy for "worth remembering"


def _get_or_create_conversation(
    db: Session, *, user: User, conversation_id: uuid.UUID | None, mode: ConversationMode
) -> Conversation:
    if conversation_id is not None:
        conversation = db.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user.id:
            raise ValueError("Conversation not found")
        return conversation

    conversation = Conversation(user_id=user.id, mode=mode, title="New conversation")
    db.add(conversation)
    db.flush()
    return conversation


async def run_chat_turn(
    db: Session,
    *,
    user: User,
    conversation_id: uuid.UUID | None,
    user_message: str,
    mode: ConversationMode,
    force_provider: str | None = None,
) -> tuple[Conversation, Message]:
    conversation = _get_or_create_conversation(
        db, user=user, conversation_id=conversation_id, mode=mode
    )

    if conversation.title == "New conversation":
        conversation.title = user_message[:80]

    user_row = Message(conversation_id=conversation.id, role=MessageRole.USER, content=user_message)
    db.add(user_row)
    db.flush()

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(_MAX_HISTORY_MESSAGES)
        .all()
    )
    history.reverse()

    relevant_memories = await memory_service.search_memory(
        db, user_id=user.id, query=user_message, limit=5
    )

    system_sections = [_SYSTEM_PROMPTS.get(mode, _SYSTEM_PROMPTS[ConversationMode.GENERAL])]
    if relevant_memories:
        memory_block = "\n".join(f"- {item.summary}" for item, _score in relevant_memories)
        system_sections.append(
            "Relevant things you already know about this user:\n" + memory_block
        )

    messages = [ChatMessage(role=ChatRole.SYSTEM, content="\n\n".join(system_sections))]
    for row in history:
        role = ChatRole.ASSISTANT if row.role == MessageRole.ASSISTANT else ChatRole.USER
        messages.append(ChatMessage(role=role, content=row.content))

    engine = get_routing_engine()
    reply, routing_reason = await engine.route_and_complete(
        messages, mode=mode, force_provider=force_provider
    )

    assistant_row = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=reply.content,
        provider=reply.provider,
        model=reply.model,
        routing_reason=routing_reason,
        token_usage=(
            {"input": reply.input_tokens, "output": reply.output_tokens}
            if reply.input_tokens is not None
            else None
        ),
    )
    db.add(assistant_row)
    db.commit()
    db.refresh(assistant_row)
    db.refresh(conversation)

    if len(user_message) >= _MEMORY_IMPORTANCE_THRESHOLD:
        await memory_service.create_memory(
            db,
            user_id=user.id,
            tier=MemoryTier.CONVERSATION,
            summary=user_message[:1000],
            source_conversation_id=conversation.id,
            importance=0.4,
        )

    return conversation, assistant_row
