"""
Chat Node - LLM 기반 기본 대화 처리
사용자와의 자연스러운 대화를 담당하며, 필요시 다른 노드로의 라우팅을 위한 의도 분석 수행
"""
from __future__ import annotations
import json
from typing import Literal, Optional
from st_app.utils.state import State
from st_app.rag.llm import get_upstage_llm
from st_app.rag.prompt import get_intent_classification_prompt
from st_app.rag.prompt import get_chat_prompt

# 단일 도메인: 롯데월드
PARK_NAME = "롯데월드"
PARK_SYNONYMS = ["롯데 월드", "lotte world", "lotteworld", "Lotte World"]

# 폴백용 키워드 세트
SUBJECT_HINT = ["가격","요금","티켓","운영","운영시간","위치","입장","할인","편의시설","주소","지도"]
REVIEW_HINT = ["후기","리뷰","평가","장단점","사람 많","대기","줄","혼잡","비교","추천","만족","불만","재밌"]

def _classify_intent_fallback(user_message: str) -> Literal["chat", "subject_info", "rag_review"]:
    """
    키워드 기반 폴백 의도 분류
    """
    t = user_message.lower()
    if any(w in t for w in REVIEW_HINT):
        return "rag_review"
    if any(w in t for w in SUBJECT_HINT):
        return "subject_info"
    return "chat"

def _classify_intent_with_llm(user_message: str) -> Literal["chat", "subject_info", "rag_review"]:
    """
    LLM을 사용하여 사용자 의도 분류 (JSON 형식으로 엄격 파싱 + 폴백)
    """
    try:
        llm = get_upstage_llm(temperature=0.0)
        prompt = get_intent_classification_prompt(user_message)
        result = llm.invoke(prompt)
        resp = result.content.strip()
        intent_data = json.loads(resp)
        intent = intent_data.get("intent", "chat")
        if intent in {"chat", "subject_info", "rag_review"}:
            return intent
        return _classify_intent_fallback(user_message)
    except Exception:
        print(f"의도 분류 LLM 호출 실패, 키워드 기반으로 폴백")
        return _classify_intent_fallback(user_message)

def _rule_based_reply(intent: str) -> str:
    """
    API 실패 시 규칙 기반 폴백 응답
    """
    if intent == "subject_info":
        return "롯데월드 기본정보 중 어떤 걸 보시겠어요? 위치·티켓(요금)·운영시간·편의시설 중에서요?"
    if intent == "rag_review":
        return "후기 기준으로 정리해드릴게요. 스릴·가족·대기줄·야간 퍼레이드 중 무엇이 더 중요하신가요?"
    return "롯데월드 기준으로 도와드릴게요. 기본정보와 후기 중 어떤 관점부터 볼까요?"

def _generate_chat_response(state: State, user_message: str, intent: str) -> str:
    """
    LLM을 사용하여 자연스러운 대화 응답 생성 (폴백 포함)
    """
    try:
        llm = get_upstage_llm(temperature=0.6)
        history = state.get("conversation_history", [])
        recent_history = history[-5:] if len(history) > 5 else history

        full_prompt = get_chat_prompt().format(user_message=user_message, conversation_history=recent_history)
        
        result = llm.invoke(full_prompt)
        return result.content.strip()
    except Exception:
        print(f"Chat 응답 LLM 호출 실패, 규칙 기반으로 폴백")
        return _rule_based_reply(intent)

def chat_node(state: State) -> State:
    """
    Chat Node - LLM 기반 기본 대화 처리
    """
    state["current_node"] = "chat"
    user_message = state.get("user_input", "")
    if not user_message:
        return state

    try:
        intent = _classify_intent_with_llm(user_message)
        state["routing_decision"] = intent
        chat_response = _generate_chat_response(state, user_message, intent)
        state["result"] = chat_response

        conversation_history = state.get("conversation_history", [])
        conversation_history.append({"user": user_message, "assistant": chat_response})
        state["conversation_history"] = conversation_history

        print(f"Chat Node - 의도 분류: {intent}")
    except Exception as e:
        intent = "chat"
        state["routing_decision"] = intent
        error_message = _rule_based_reply(intent)
        state["result"] = error_message
        state["error"] = str(e)

        conversation_history = state.get("conversation_history", [])
        conversation_history.append({"user": user_message, "assistant": error_message})
        state["conversation_history"] = conversation_history

    return state

def is_mentioned_park(text: str) -> bool:
    """
    텍스트에서 롯데월드 언급 여부 확인
    """
    if PARK_NAME in text:
        return True
    text_lower = text.lower()
    return any(alias.lower() in text_lower for alias in PARK_SYNONYMS)
