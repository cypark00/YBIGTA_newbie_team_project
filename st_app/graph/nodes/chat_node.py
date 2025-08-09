"""
Chat Node - LLM 기반 기본 대화 처리
사용자와의 자연스러운 대화를 담당하며, 필요시 다른 노드로의 라우팅을 위한 의도 분석 수행
"""
from __future__ import annotations
import json
from typing import Literal, Optional
from st_app.utils.state import AppState, get_last_user_message, get_conversation_history, add_message
from st_app.rag.llm import get_upstage_llm, create_messages_from_history, get_llm_response_sync
from st_app.rag.prompt import get_chat_prompt, get_intent_classification_prompt

# 단일 도메인: 롯데월드
PARK_NAME = "롯데월드"
PARK_SYNONYMS = ["롯데 월드", "lotte world", "lotteworld", "Lotte World"]

# 폴백용 키워드 세트
SUBJECT_HINT = ["가격","요금","티켓","운영","운영시간","위치","입장","할인","편의시설","주소","지도"]
REVIEW_HINT = ["후기","리뷰","평가","장단점","사람 많","대기","줄","혼잡","비교","추천","만족","불만","재밌"]


def _trim_two_sentences(text: str) -> str:
    """
    응답을 2문장 이내로 제한하고 마지막에 질문으로 끝나도록 보장
    """
    # 문장 분리 (., !, ? 기준)
    text = text.strip()
    parts = []
    
    for sep in [".","!","?"]:
        text = text.replace(sep, "|||")
    
    sentences = [s.strip() for s in text.split("|||") if s.strip()]
    
    if len(sentences) <= 2:
        result = ". ".join(sentences).strip()
    else:
        result = ". ".join(sentences[:2]).strip()
    
    # 질문으로 끝나지 않으면 질문 추가
    if not result.endswith(("?", "요", "까요", "세요")):
        result += "?"
    
    return result


def _classify_intent_fallback(user_message: str) -> Literal["chat", "subject_info", "review_rag"]:
    """
    키워드 기반 폴백 의도 분류
    """
    t = user_message.lower()
    if any(w in t for w in REVIEW_HINT):  # 먼저 리뷰 성격
        return "review_rag"
    if any(w in t for w in SUBJECT_HINT):
        return "subject_info"
    return "chat"


def _classify_intent_with_llm(user_message: str) -> Literal["chat", "subject_info", "review_rag"]:
    """
    LLM을 사용하여 사용자 의도 분류 (JSON 형식으로 엄격 파싱 + 폴백)
    """
    try:
        llm = get_upstage_llm(temperature=0.0)
        
        prompt = get_intent_classification_prompt(user_message)
        messages = create_messages_from_history(
            system_prompt="",
            conversation_history=[],
            current_user_input=prompt
        )
        
        resp = get_llm_response_sync(llm, messages).strip()
        
        # JSON 파싱 시도
        intent_data = json.loads(resp)
        intent = intent_data.get("intent", "chat")
        
        # 유효한 값인지 검증
        if intent in {"chat", "subject_info", "review_rag"}:
            return intent
            
        # JSON이지만 값이 엉뚱한 경우 폴백
        return _classify_intent_fallback(user_message)
            
    except Exception as e:
        print(f"의도 분류 LLM 호출 실패, 키워드 기반으로 폴백")
        return _classify_intent_fallback(user_message)


def _rule_based_reply(intent: str) -> str:
    """
    API 실패 시 규칙 기반 폴백 응답
    """
    if intent == "subject_info":
        return "롯데월드 기본정보 중 어떤 걸 보시겠어요? 위치·티켓(요금)·운영시간·편의시설 중에서요?"
    if intent == "review_rag":
        return "후기 기준으로 정리해드릴게요. 스릴·가족·대기줄·야간 퍼레이드 중 무엇이 더 중요하신가요?"
    return "롯데월드 기준으로 도와드릴게요. 기본정보와 후기 중 어떤 관점부터 볼까요?"


def _generate_chat_response(state: AppState, user_message: str, intent: str) -> str:
    """
    LLM을 사용하여 자연스러운 대화 응답 생성 (폴백 포함)
    """
    try:
        llm = get_upstage_llm(temperature=0.6)  # 살짝 낮춰도 자연스러움 유지
        
        # 최근 대화 기록 가져오기 (최대 5개)
        history = get_conversation_history(state, last_n=5)
        
        messages = create_messages_from_history(
            system_prompt=get_chat_prompt(),
            conversation_history=history,
            current_user_input=user_message
        )
        
        response = get_llm_response_sync(llm, messages).strip()
        return _trim_two_sentences(response)  # 길이/문장수 가드
        
    except Exception as e:
        print(f"Chat 응답 LLM 호출 실패, 규칙 기반으로 폴백")
        return _rule_based_reply(intent)


def chat_node(state: AppState) -> AppState:
    """
    Chat Node - LLM 기반 기본 대화 처리
    
    기능:
    1. 사용자와 자연스러운 대화 수행 (2문장 이내 + 질문)
    2. 사용자 의도 분석 (LLM 기반, JSON 파싱)
    3. 라우팅을 위한 메타데이터 설정
    
    Args:
        state: 현재 애플리케이션 상태
        
    Returns:
        AppState: 업데이트된 상태
    """
    # 현재 노드 설정
    state["current_node"] = "chat"
    
    # 사용자 메시지 확인
    user_message = get_last_user_message(state)
    if not user_message:
        return state
    
    try:
        # LLM 기반 의도 분류 (JSON 파싱 + 폴백)
        intent = _classify_intent_with_llm(user_message)
        
        # 메타데이터 설정 (라우터가 사용할 정보)
        state["intent_hint"] = intent
        state["candidate_targets"] = ["롯데월드"]
        state["target"] = "롯데월드"  # 단일 도메인이므로 고정
        
        # LLM 기반 대화 응답 생성 (가드레일 적용 + 폴백)
        chat_response = _generate_chat_response(state, user_message, intent)
        
        # 응답을 상태에 추가
        add_message(state, "assistant", chat_response, "chat_node")
        
        print(f"Chat Node - 의도 분류: {intent}")
        
    except Exception as e:
        # 최후 폴백: 의도 분류조차 실패한 경우
        intent = "chat"
        state["intent_hint"] = intent
        state["candidate_targets"] = ["롯데월드"]
        state["target"] = "롯데월드"
        
        error_message = _rule_based_reply(intent)
        add_message(state, "assistant", error_message, "chat_node")
        state["error"] = str(e)
        
    return state


def is_mentioned_park(text: str) -> bool:
    """
    텍스트에서 롯데월드 언급 여부 확인
    """
    if PARK_NAME in text:
        return True
    text_lower = text.lower()
    return any(alias.lower() in text_lower for alias in PARK_SYNONYMS)