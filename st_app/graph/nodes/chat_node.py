
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from st_app.utils.state import AppState
from st_app.rag.llm import get_chat_llm

SYS = "당신은 롯데월드 전용 대화 어시스턴트입니다. 사용자의 질문에 자연스럽게 한국어로 대답해주세요."

prompt = ChatPromptTemplate.from_messages([
    ("system", SYS),
    MessagesPlaceholder("chat_history"),
    ("human", "{user_input}"),
])

def _to_lc(messages):
    out=[]
    for m in messages:
        if m["role"]=="user": out.append(HumanMessage(content=m["content"]))
        elif m["role"]=="assistant": out.append(AIMessage(content=m["content"]))
    return out

def chat_node(state: AppState) -> dict:
    text = (state.get("user_input") or "").strip()
    if not text:
        # 아무 변화 없음
        return {}

    llm = get_chat_llm()
    prev = list(state.get("messages", []))

    # 1) 사용자 메시지 추가
    prev.append({"role":"user","content":text})

    # 2) LLM 호출
    try:
        msgs = prompt.format_messages(
            chat_history=_to_lc(prev),
            user_input=text
        )
        ans = llm.invoke(msgs).content.strip()
    except Exception:
        ans = "잠시 문제가 생겼어요. 다시 말씀해 주실래요?"

    # 3) 어시스턴트 메시지 추가
    prev.append({"role":"assistant","content":ans})

    # state를 직접 건드리지 말고, '업데이트 딕셔너리'만 반환
    return {
        "messages": prev,
        "current_node": "chat",
        "user_input": ""  # 입력 소진
    }