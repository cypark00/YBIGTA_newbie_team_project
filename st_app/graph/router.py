import json
from langgraph.graph import StateGraph, START, END
from st_app.utils.state import State
from st_app.rag.llm import get_upstage_llm
from st_app.rag.prompt import get_intent_classification_prompt
from st_app.graph.nodes.chat_node import chat_node
from st_app.graph.nodes.subject_info_node import subject_info_node
from st_app.graph.nodes.rag_review_node import rag_review_node

def direct_router(state: State) -> str:
    """LLM 기반 라우팅 함수"""
    text = (state.get("user_input") or "").strip()
    
    if not text:
        return "chat"
    
    try:
        # LLM 기반 라우팅 시도
        llm = get_upstage_llm(temperature=0.1)
        prompt = get_intent_classification_prompt(text)
        response = llm.invoke([{"role": "user", "content": prompt}])
        
        # JSON 파싱 시도
        try:
            import json
            result = json.loads(response.content)
            intent = result.get("intent", "chat")
            return intent
        except:
            # JSON 파싱 실패 시 키워드 기반 폴백
            pass
    except Exception as e:
        print(f"LLM 라우팅 실패, 키워드 기반으로 폴백: {e}")
    
    # 키워드 기반 폴백 라우팅
    t = text.lower()
    if any(k in t for k in ["후기","리뷰","평가","추천","어때","만족","재밌","별로","좋아","나빠","요약"]):
        return "rag_review"
    if any(k in t for k in ["위치","주소","가격","요금","티켓","운영시간","시간","어트랙션","시설","교통"]):
        return "subject_info"
    return "chat"

graph = StateGraph(State)
graph.add_node("chat", chat_node)
graph.add_node("subject_info", subject_info_node)
graph.add_node("rag_review", rag_review_node)

graph.add_conditional_edges(START, direct_router, {
    "chat": "chat",
    "subject_info": "subject_info",
    "rag_review": "rag_review",
})
graph.add_edge("chat", END)
graph.add_edge("subject_info", END)
graph.add_edge("rag_review", END)

compiled = graph.compile()