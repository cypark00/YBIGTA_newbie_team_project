"""
LLM 설정 및 호출 관련 함수들
Upstage API를 활용한 LLM 인스턴스 생성 및 관리
"""
from typing import Optional, List, Dict, Any
import os
from langchain_upstage import ChatUpstage
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_upstage_llm(
    model: str = "solar-pro",
    temperature: float = 0.1,
    max_tokens: Optional[int] = None
) -> ChatUpstage:
    """
    Upstage LLM 인스턴스 생성
    
    Args:
        model: 사용할 모델명 (기본: solar-pro)
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

class MockLLM:
    """API 키가 없을 때 사용할 모의 LLM"""
    def __init__(self, temperature=0.1):
        self.temperature = temperature
    
    def invoke(self, messages):
        if isinstance(messages, str):
            content = messages
        else:
            # LangChain 메시지 형식에서 마지막 사용자 메시지 추출
            content = ""
            for msg in messages:
                if hasattr(msg, 'content'):
                    content = msg.content
                elif isinstance(msg, dict) and 'content' in msg:
                    content = msg['content']
                elif isinstance(msg, str):
                    content = msg
        
        # 간단한 키워드 기반 응답
        if "안녕" in content or "hello" in content.lower():
            response = "안녕하세요! 롯데월드에 대해 궁금한 게 있으신가요?"
        elif "가격" in content or "티켓" in content or "요금" in content:
            response = "롯데월드 티켓 가격은 성인 61,000원, 청소년 54,000원, 어린이 47,000원입니다."
        elif "위치" in content or "주소" in content or "어디" in content:
            response = "롯데월드는 서울 송파구 올림픽로 240에 위치해 있습니다."
        elif "시간" in content or "운영" in content or "오픈" in content:
            response = "롯데월드는 매일 10:00~21:00에 운영됩니다."
        elif "후기" in content or "리뷰" in content or "평가" in content or "평" in content:
            response = """롯데월드 후기를 분석해드리겠습니다.

**요약:**
롯데월드는 전반적으로 긍정적인 평가를 받고 있으며, 특히 가족 단위 방문객들에게 인기가 높습니다.

**긍정 포인트:**
• 다양한 어트랙션과 시설로 하루 종일 즐길 수 있음
• 실내/실외 공간이 있어 날씨에 관계없이 이용 가능
• 깔끔하고 안전한 시설 관리

**주의 포인트:**
• 주말과 공휴일에는 매우 혼잡함
• 일부 인기 어트랙션은 대기시간이 길 수 있음

**팁:**
• 평일 방문을 권장하며, 오픈 시간에 맞춰 방문하면 대기시간을 줄일 수 있습니다.

**근거:**
• "롯데월드는 정말 재미있어요! 아이들이 너무 좋아했어요." (source=kakaomap|롯데월드|2023-01-15|rating=5)
• "시설이 깔끔하고 안전해서 좋았습니다." (source=myrealtrip|롯데월드|2023-02-20|rating=4)
• "주말에 갔는데 너무 복잡했어요. 평일에 가는 걸 추천해요." (source=tripdotcom|롯데월드|2023-03-10|rating=3)"""
        else:
            response = "롯데월드에 대해 더 구체적으로 질문해 주시면 도움을 드릴게요!"
        
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        return MockResponse(response)

def get_chat_llm(
    model_upstage: str = "solar-pro",
    temperature: float = 0.2
):
    """
    공용 팩토리: Upstage가 있으면 Upstage, 없으면 모의 LLM으로 폴백.
    RAG 체인(LCEL)에 바로 연결 가능.
    """
    try:
        return get_upstage_llm(model=model_upstage, temperature=temperature)
    except Exception:
        # API 키가 없으면 모의 LLM 사용
        return MockLLM(temperature=temperature)
