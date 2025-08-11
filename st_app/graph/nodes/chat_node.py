"""
Chat Node - LLM 기반 기본 대화 처리
사용자와의 자연스러운 대화를 담당
"""
from __future__ import annotations
import json
from typing import Literal, Optional
from st_app.utils.state import State
from st_app.rag.llm import get_upstage_llm
from st_app.rag.prompt import get_chat_prompt

def _generate_chat_response(state: State, user_message: str) -> str:
    """
    LLM을 사용하여 자연스러운 대화 응답 생성
    """
    try:
        llm = get_upstage_llm(temperature=0.6)
        history = state.get("conversation_history", [])
        recent_history = history[-5:] if len(history) > 5 else history

        full_prompt = get_chat_prompt().format(user_message=user_message, conversation_history=recent_history)
        
        result = llm.invoke(full_prompt)
        return result.content.strip()
    except Exception as e:
        print(f"Chat 응답 LLM 호출 실패: {e}")
        return "롯데월드에 대해 궁금한 점이 있으시면 언제든 물어보세요!"

def chat_node(state: State) -> State:
    """
    Chat Node - LLM 기반 기본 대화 처리
    """
    state["current_node"] = "chat"
    user_message = state.get("user_input", "")
    if not user_message:
        return state

    try:
        chat_response = _generate_chat_response(state, user_message)
        state["result"] = chat_response

        conversation_history = state.get("conversation_history", [])
        conversation_history.append({"user": user_message, "assistant": chat_response})
        state["conversation_history"] = conversation_history

        print(f"Chat Node - 기본 대화 응답 생성")
    except Exception as e:
        error_message = "롯데월드에 대해 궁금한 점이 있으시면 언제든 물어보세요!"
        state["result"] = error_message
        state["error"] = str(e)

        conversation_history = state.get("conversation_history", [])
        conversation_history.append({"user": user_message, "assistant": error_message})
        state["conversation_history"] = conversation_history

    return state
