"""
LLM 설정 및 호출 관련 함수들
Upstage API를 활용한 LLM 인스턴스 생성 및 관리
"""
from typing import Optional, List, Dict, Any
import os
from langchain_upstage import ChatUpstage
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


def get_upstage_llm(
    model: str = "solar-pro2",
    temperature: float = 0.1,
    max_tokens: Optional[int] = None
) -> ChatUpstage:
    """
    Upstage LLM 인스턴스 생성
    
    Args:
        model: 사용할 모델명 (기본: solar-pro2)
        temperature: 생성 온도 (기본: 0.1)
        max_tokens: 최대 토큰 수
        
    Returns:
        ChatUpstage: 설정된 LLM 인스턴스
    """
    # Streamlit secrets 또는 환경변수에서 API 키 가져오기
    api_key = None
    
    # Streamlit secrets 시도
    try:
        import streamlit as st
        api_key = st.secrets.get("UPSTAGE_API_KEY")
    except (ImportError, AttributeError, FileNotFoundError):
        pass
    
    # 환경변수에서 시도
    if not api_key:
        api_key = os.getenv("UPSTAGE_API_KEY")
    
    if not api_key:
        raise ValueError(
            "UPSTAGE_API_KEY가 설정되지 않았습니다. "
            "Streamlit secrets 또는 환경변수에 설정해주세요."
        )
    
    kwargs = {
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
    }
    
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
        
    return ChatUpstage(**kwargs)


def create_messages_from_history(
    system_prompt: str,
    conversation_history: List[Dict[str, Any]],
    current_user_input: Optional[str] = None
) -> List[BaseMessage]:
    """
    대화 기록을 LangChain 메시지 형식으로 변환
    
    Args:
        system_prompt: 시스템 프롬프트
        conversation_history: 대화 기록
        current_user_input: 현재 사용자 입력 (옵션)
        
    Returns:
        List[BaseMessage]: LangChain 메시지 리스트
    """
    messages = [SystemMessage(content=system_prompt)]
    
    for msg in conversation_history:
        role = msg.get("role")
        content = msg.get("content", "")
        
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    
    # 현재 사용자 입력이 있으면 추가
    if current_user_input:
        messages.append(HumanMessage(content=current_user_input))
    
    return messages


async def get_llm_response(
    llm: ChatUpstage,
    messages: List[BaseMessage]
) -> str:
    """
    LLM으로부터 응답 생성
    
    Args:
        llm: ChatUpstage 인스턴스
        messages: 입력 메시지들
        
    Returns:
        str: LLM 응답 텍스트
    """
    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        return f"LLM 응답 생성 중 오류가 발생했습니다: {str(e)}"


def get_llm_response_sync(
    llm: ChatUpstage,
    messages: List[BaseMessage]
) -> str:
    """
    LLM으로부터 동기 응답 생성
    
    Args:
        llm: ChatUpstage 인스턴스
        messages: 입력 메시지들
        
    Returns:
        str: LLM 응답 텍스트
    """
    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"LLM 응답 생성 중 오류가 발생했습니다: {str(e)}"

def get_chat_llm(
    model_upstage: str = "solar-pro2",
    temperature: float = 0.2
):
    """
    공용 팩토리: Upstage가 있으면 Upstage, 없으면 OpenAI로 폴백.
    RAG 체인(LCEL)에 바로 연결 가능.
    """
    try:
        return get_upstage_llm(model=model_upstage, temperature=temperature)
    except Exception:
        # 폴백(OpenAI 등) — 없으면 주석 처리해도 됨
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
