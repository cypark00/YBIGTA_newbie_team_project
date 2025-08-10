from streamlit_app import llm
from st_app.utils.state import State
from langgraph.graph import StateGraph, START, END

from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node

def router(state: State) -> State:
    """LLM이 사용자 입력을 분석하여 적절한 노드로 라우팅 결정"""
    
    # 대화 히스토리가 있다면 포함
    conversation_history = state.get('conversation_history', [])
    history_context = ""
    if conversation_history:
        recent_history = conversation_history[-3:]  # 최근 3번의 대화만 참고
        history_context = "\n".join([f"사용자: {h.get('user', '')} / 시스템: {h.get('assistant', '')}" for h in recent_history])
        history_context = f"\n최근 대화 내역:\n{history_context}\n"
    
    prompt = f"""
당신은 사용자 요청을 분석하여 가장 적절한 처리 방식을 결정하는 라우터입니다.

{history_context}
현재 사용자 입력: {state['user_input']}

다음 3가지 처리 방식 중 가장 적절한 것을 선택해주세요:

1. **chat**: 일반적인 대화, 인사, 감정 표현, 단순 질문, 잡담 등
   - 예시: "안녕하세요", "고마워요", "어떻게 지내세요", "날씨가 좋네요"

2. **subject_info**: 특정 장소, 시설, 제품 등에 대한 객관적 정보나 기본 데이터가 필요한 경우
   - 예시: "롯데월드 위치 어디야", "운영시간 알려줘", "입장료 얼마야", "어떤 어트랙션 있어"
   - 기본적인 팩트, 운영정보, 시설정보, 가격정보 등

3. **rag_review**: 실제 이용자들의 경험담, 평가, 후기, 추천 여부 등 주관적 의견이 필요한 경우
   - 예시: "롯데월드 어때?", "가볼만해?", "리뷰 알려줘", "추천해?", "재미있어?"
   - 평점, 후기, 만족도, 장단점, 개인적 경험 등

사용자의 의도를 파악하여 위 3가지 중 하나만 선택해주세요.
단순히 키워드 매칭이 아닌, 사용자가 정말로 원하는 것이 무엇인지 맥락을 고려해서 판단해주세요.

답변은 다음 중 하나만 출력하세요: chat, subject_info, rag_review
"""
    
    try:
        result = llm.invoke(prompt)
        decision = result.content.strip().lower()
        
        # 유효한 결정인지 확인
        valid_decisions = ["chat", "subject_info", "rag_review"]
        if decision not in valid_decisions:
            # LLM이 예상과 다른 답변을 했을 경우 기본값 설정
            decision = "chat"
            
        return {**state, "routing_decision": decision}
        
    except Exception as e:
        # 오류 발생 시 기본적으로 chat으로 라우팅
        print(f"Router error: {e}")
        return {**state, "routing_decision": "chat", "router_error": str(e)}



# 그래프 구성
graph = StateGraph(State)

# 노드 추가
graph.add_node("chat", chat_node) 
graph.add_node("router", router)
graph.add_node("subject_info", subject_info_node)
graph.add_node("rag_review", rag_review_node)

# 시작점에서 chat_node로 (기본 대화)
graph.add_edge(START, "chat")

# chat_node에서 router로 (입력 분석)
graph.add_edge("chat", "router")

# LLM 기반 조건부 분기 함수
def llm_branching_logic(state: State) -> str:
    """LLM의 라우팅 결정에 따른 분기 - 단순하게 결정사항 반영"""
    decision = state.get("routing_decision", "chat")
    
    # LLM이 결정한 대로 분기
    valid_decisions = ["chat", "subject_info", "rag_review"]
    if decision in valid_decisions:
        return decision
    else:
        # 예외 상황시 chat으로 기본 분기
        return "chat"

# 라우터에서 LLM 기반 조건부 분기
graph.add_conditional_edges(
    "router",
    llm_branching_logic,
    {
        "chat": "chat",
        "subject_info": "subject_info", 
        "rag_review": "rag_review"
    }
)

# 전문 노드들이 처리 후 다시 chat_node로 복귀
graph.add_edge("subject_info", "chat")
graph.add_edge("rag_review", "chat")

# 그래프 컴파일
compiled = graph.compile()