"""
세션 상태 구조 정의
LangGraph에서 사용할 상태 클래스와 메시지 타입 정의
"""
from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal
from uuid import uuid4
from time import time

# ---- 타입 정의 추가 ----
class Message(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str
    name: Optional[str]

class DocumentHit(TypedDict, total=False):
    # 검색된 청크와 메타
    chunk: str
    platform: Optional[str]
    subject: Optional[str]
    place: Optional[str]
    date: Optional[str]
    rating: Optional[float]
    url: Optional[str]
    score: Optional[float] 


from typing import TypedDict, List, Dict, Any, Optional

class State(TypedDict):
    # === 핵심 입출력 ===
    user_input: str                    # 사용자 입력
    result: str                        # 최종 결과/응답
    
    # === 라우팅 관련 ===
    routing_decision: Optional[str]    # router의 결정 (chat/subject_info/rag_review)
    current_node: Optional[str]        # 현재 처리 중인 노드
    
    # === 대화 히스토리 ===
    conversation_history: List[Dict[str, str]]  # 대화 기록 [{user: "", assistant: ""}]
    
    # === subject_info_node 관련 ===
    detected_category: Optional[str]   # 감지된 카테고리
    extracted_subject: Optional[str]   # 추출된 주제명
    found_subject_name: Optional[str]  # 발견된 주제명 
    info_type: Optional[str]           # 정보 유형 (subject_information/general_information)
    data_source: Optional[str]         # 데이터 소스 (json_database/llm_general)
    
    # === rag_review_node 관련 ===
    review_query: Optional[str]        # 리뷰 검색 쿼리
    retrieved_reviews: Optional[List[Dict]]  # 검색된 리뷰들
    review_summary: Optional[str]      # 리뷰 요약
    sentiment_analysis: Optional[Dict] # 감정 분석 결과
    rag_context: Optional[str]         # RAG 컨텍스트
    
    # === 오류 처리 ===
    error: Optional[str]               # 일반 에러 메시지
    router_error: Optional[str]        # 라우터 에러
    
    # === 메타데이터 (선택사항) ===
    timestamp: Optional[str]           # 처리 시간
    session_id: Optional[str]          # 세션 ID
    retrieval_latency_ms: Optional[float]  # RAG 검색 소요시간 (ms)



def create_initial_state() -> State:
    """초기 상태 생성"""
    return State(
        user_input="",
        result="",
        routing_decision=None,
        current_node="chat",
        conversation_history=[],
        detected_category=None,
        extracted_subject=None,
        found_subject_name=None,
        info_type=None,
        data_source=None,
        review_query=None,
        retrieved_reviews=None,
        review_summary=None,
        sentiment_analysis=None,
        rag_context=None,
        error=None,
        router_error=None,
        timestamp=None,
        session_id=str(uuid4()),
        retrieval_latency_ms=None
    )


def add_message(state: State, role: str, content: str, name: Optional[str] = None) -> State:
    """상태에 새로운 메시지 추가 (호환성을 위해 유지)"""
    conversation_history = state.get("conversation_history", [])
    if role == "user":
        conversation_history.append({"user": content, "assistant": ""})
    elif role == "assistant":
        if conversation_history and conversation_history[-1].get("assistant") == "":
            conversation_history[-1]["assistant"] = content
        else:
            conversation_history.append({"user": "", "assistant": content})
    state["conversation_history"] = conversation_history
    return state


def get_last_user_message(state: State) -> Optional[str]:
    """마지막 사용자 메시지 내용 반환"""
    conversation_history = state.get("conversation_history", [])
    for message in reversed(conversation_history):
        if message.get("user"):
            return message["user"]
    return state.get("user_input", "")


def get_conversation_history(state: State, last_n: int = 5) -> List[Dict[str, Any]]:
    """최근 N개의 대화 기록 반환"""
    conversation_history = state.get("conversation_history", [])
    return conversation_history[-last_n:] if len(conversation_history) > last_n else conversation_history

# --- add to state.py ---
from time import time

def mark_retrieval_start() -> float:
    """RAG 검색 시작 시각 (ms 계산용 타임스탬프 반환)."""
    return time()

def mark_retrieval_end(state: "State", t0: float) -> None:
    """RAG 검색 종료 시 상태에 소요시간(ms) 기록."""
    dt_ms = (time() - t0) * 1000.0
    # 키가 없더라도 그냥 기록해 둠(있으면 덮어씀)
    state["retrieval_latency_ms"] = round(dt_ms, 2)

# --- backward-compat: 기존 팀 코드가 사용할 수 있게 별칭 제공 ---
def make_retriever_start() -> float:
    """[alias] 호환용 별칭 - mark_retrieval_start"""
    return mark_retrieval_start()

def make_retriever_end(state: "State", t0: float) -> None:
    """[alias] 호환용 별칭 - mark_retrieval_end"""
    return mark_retrieval_end(state, t0)
