from st_app.rag.llm import get_upstage_llm, create_messages_from_history, get_llm_response_sync
from st_app.utils.state import State, get_conversation_history
from st_app.rag.prompt import get_router_prompt
from langgraph.graph import StateGraph, START, END
from st_app.utils.state import AppState
from st_app.rag.llm import get_upstage_llm
from st_app.rag.prompt import get_intent_classification_prompt
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node

def router(state: State) -> State:
    """LLM이 사용자 입력을 분석하여 적절한 노드로 라우팅 결정"""
    
    try:
        # llm.py의 함수들을 사용하여 LLM 초기화
        llm = get_upstage_llm(temperature=0.0)  # 라우팅은 정확성을 위해 temperature=0
        
        # state.py의 함수를 사용하여 대화 히스토리 가져오기
        conversation_history = get_conversation_history(state, last_n=3)
        
        # prompt.py의 라우터 프롬프트 사용
        system_prompt = get_router_prompt()
        
        # llm.py의 함수를 사용하여 메시지 생성
        messages = create_messages_from_history(
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            current_user_input=state['user_input']
        )
        
        # llm.py의 함수를 사용하여 LLM 응답 생성
        decision = get_llm_response_sync(llm, messages).strip().lower()
        
        print(f"Router - LLM 응답: {decision}")
        
        # 유효한 결정인지 확인
        valid_decisions = ["chat", "subject_info", "rag_review"]
        if decision not in valid_decisions:
            # LLM이 예상과 다른 답변을 했을 경우 기본값 설정
            print(f"Router - 유효하지 않은 결정 '{decision}', 기본값 'chat'으로 설정")
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

# Chat Node에서 직접 조건부 분기
def chat_branching_logic(state: State) -> str:
    """Chat Node의 라우팅 결정에 따른 분기"""
    decision = state.get("routing_decision", "chat")
    
    # chat이면 종료, 아니면 router로
    if decision == "chat":
        return END
    else:
        return "router"

# Chat Node에서 조건부 분기
graph.add_conditional_edges(
    "chat",
    chat_branching_logic,
    {
        END: END,
        "router": "router"
    }
)

# Router에서 전문 노드로 분기
def router_branching_logic(state: State) -> str:
    """Router의 라우팅 결정에 따른 분기"""
    decision = state.get("routing_decision", "chat")
    
    # 유효한 결정인지 확인
    valid_decisions = ["subject_info", "rag_review"]
    if decision in valid_decisions:
        return decision
    else:
        # 예외 상황시 종료
        return END

# Router에서 조건부 분기
graph.add_conditional_edges(
    "router",
    router_branching_logic,
    {
        "subject_info": "subject_info", 
        "rag_review": "rag_review",
        END: END
    }
)

# 전문 노드들이 처리 후 END로 종료
graph.add_edge("subject_info", END)
graph.add_edge("rag_review", END)

compiled = graph.compile()