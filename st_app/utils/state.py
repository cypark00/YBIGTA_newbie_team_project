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


class AppState(TypedDict):
    """
    애플리케이션 전체 상태를 관리하는 클래스
    LangGraph의 모든 노드에서 공유되는 상태 정보
    """
    # 대화 메시지 기록
    messages: List[Dict[str, Any]]
    
    # 사용자 입력
    user_input: Optional[str]
    
    # 사용자 의도 힌트 (chat_node에서 설정)
    intent_hint: Optional[Literal["chat", "subject_info", "review_rag"]]
    
    # 후보 대상 리스트 (현재는 롯데월드로 고정)
    candidate_targets: List[str]
    
    # 현재 처리 대상 (단일 도메인)
    target: Optional[str]
    
    # 현재 처리 중인 노드
    current_node: Optional[str]
    
    # RAG 검색 결과
    retrieved_docs: Optional[List[DocumentHit]]

    # Subject 정보
    subject_data: Optional[Dict[str, Any]]

    # RAG 진단/세팅
    last_query: Optional[str]
    retrieval_mode: Optional[Literal["similarity", "mmr"]]
    top_k: Optional[int]
    retrieval_latency_ms: Optional[float]

    # 세션/에러
    session_id: Optional[str]
    error: Optional[str]


def create_initial_state() -> AppState:
    """초기 상태 생성"""
    return AppState(
        messages=[],
        user_input=None,
        intent_hint=None,
        candidate_targets=["롯데월드"],
        target="롯데월드",
        current_node="chat",
        retrieved_docs=None,
        subject_data=None,
        last_query=None,
        retrieval_mode="mmr", # 기본 MMR 모드
        top_k=5,              # 검색할 문서 수
        retrieval_latency_ms=None,
        session_id=str(uuid4()),
        error=None
    )


def add_message(state: AppState, role: str, content: str, name: Optional[str] = None) -> AppState:
    """상태에 새로운 메시지 추가"""
    message = {
        "role": role,
        "content": content,
        "name": name
    }
    state["messages"].append(message)
    return state


def get_last_user_message(state: AppState) -> Optional[str]:
    """마지막 사용자 메시지 내용 반환"""
    messages = state.get("messages", [])
    for message in reversed(messages):
        if message["role"] == "user":
            return message["content"]
    return None


def get_conversation_history(state: AppState, last_n: int = 5) -> List[Dict[str, Any]]:
    """최근 N개의 대화 기록 반환"""
    messages = state.get("messages", [])
    return messages[-last_n:] if len(messages) > last_n else messages

# --- add to state.py ---
from time import time

def mark_retrieval_start() -> float:
    """RAG 검색 시작 시각 (ms 계산용 타임스탬프 반환)."""
    return time()

def mark_retrieval_end(state: "AppState", t0: float) -> None:
    """RAG 검색 종료 시 상태에 소요시간(ms) 기록."""
    dt_ms = (time() - t0) * 1000.0
    # 키가 없더라도 그냥 기록해 둠(있으면 덮어씀)
    state["retrieval_latency_ms"] = round(dt_ms, 2)

# --- backward-compat: 기존 팀 코드가 사용할 수 있게 별칭 제공 ---
def make_retriever_start() -> float:
    """[alias] 호환용 별칭 - mark_retrieval_start"""
    return mark_retrieval_start()

def make_retriever_end(state: "AppState", t0: float) -> None:
    """[alias] 호환용 별칭 - mark_retrieval_end"""
    return mark_retrieval_end(state, t0)
