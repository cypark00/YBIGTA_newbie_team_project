# streamlit_app.py
import os
import streamlit as st
from dotenv import load_dotenv

from st_app.utils.state import create_initial_state, AppState
from st_app.graph.router import compiled  # 그래프 (START->router 조건분기->각 노드->END)

load_dotenv()

st.set_page_config(page_title="롯데월드 챗봇", page_icon="🎢", layout="wide")
st.title("🎢 롯데월드 챗봇")

# ── 세션 상태 초기화 ──────────────────────────────────────────────────────────
if "app_state" not in st.session_state:
    st.session_state.app_state = create_initial_state()

state: AppState = st.session_state.app_state

# ── 대화 히스토리 렌더 ──────────────────────────────────────────────────────
for m in state.get("messages", []):
    with st.chat_message("user" if m["role"]=="user" else "assistant"):
        st.write(m["content"])

# ── 입력 처리 ────────────────────────────────────────────────────────────────
user_text = st.chat_input("무엇이 궁금하세요?")
if user_text:
    # 사용자 메시지 먼저 화면에 표시
    with st.chat_message("user"):
        st.write(user_text)

    # 그래프 실행
    try:
        # 현재 상태에 user_input만 주입해서 실행
        state["user_input"] = user_text
        out = compiled.invoke(state)  # 반드시 상태(dict)가 돌아옴

        # out.messages 마지막이 assistant인지 확인 → 화면에도 출력
        msgs = out.get("messages", [])
        answer = None
        if msgs and msgs[-1].get("role") == "assistant":
            answer = msgs[-1]["content"]
        else:
            # 노드가 messages에 안 쌓았을 때 폴백
            answer = out.get("result") or "죄송해요. 응답을 생성하지 못했어요."

        with st.chat_message("assistant"):
            st.write(answer)

        # 상태 업데이트(덮어쓰기 OK: 모든 노드가 messages에 쌓도록 이미 고쳤음)
        st.session_state.app_state = out
        # 상태 업데이트 후 페이지 새로고침
        st.rerun()

    except Exception as e:
        st.error("그래프 실행 중 오류가 발생했어요.")
        with st.expander("디버그"):
            st.exception(e)

# ── 디버그 패널 ─────────────────────────────────────────────────────────────
with st.expander("디버그"):
    st.json({
        "routing_decision": state.get("routing_decision"),
        "current_node": state.get("current_node"),
        "error": state.get("error"),
        "messages_len": len(state.get("messages", [])),
    })
