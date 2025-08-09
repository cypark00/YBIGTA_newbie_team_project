"""
세션 상태 구조 정의
LangGraph에서 사용할 상태 클래스와 메시지 타입 정의
"""
from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal


class AppState(TypedDict):
    """
    애플리케이션 전체 상태를 관리하는 클래스
    LangGraph의 모든 노드에서 공유되는 상태 정보
    """
    # 대화 메시지 기록
    messages: List[Dict[str, Any]]
    
    # 사용자 의도 힌트 (chat_node에서 설정)
    intent_hint: Optional[Literal["chat", "subject_info", "review_rag"]]
    
    # 후보 대상 리스트 (현재는 롯데월드로 고정)
    candidate_targets: List[str]
    
    # 현재 처리 대상 (단일 도메인)
    target: Optional[str]
    
    # 현재 처리 중인 노드
    current_node: Optional[str]
    
    # RAG 검색 결과 (rag_review_node에서 사용)
    retrieved_docs: Optional[List[Dict[str, Any]]]
    
    # Subject 정보 (subject_info_node에서 사용)
    subject_data: Optional[Dict[str, Any]]
    
    # 세션 메타데이터
    session_id: Optional[str]
    
    # 에러 정보
    error: Optional[str]


def create_initial_state() -> AppState:
    """초기 상태 생성"""
    return AppState(
        messages=[],
        intent_hint=None,
        candidate_targets=["롯데월드"],
        target="롯데월드",
        current_node="chat",
        retrieved_docs=None,
        subject_data=None,
        session_id=None,
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