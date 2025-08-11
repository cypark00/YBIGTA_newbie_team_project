import streamlit as st
import os
from dotenv import load_dotenv
from st_app.graph.router import compiled
from st_app.rag.llm import get_upstage_llm
from st_app.utils.state import State, create_initial_state
from datetime import datetime

# 환경변수 로드
load_dotenv()

# LLM 초기화
try:
    llm = get_upstage_llm(model="solar-pro2", temperature=0.2)
except Exception as e:
    st.error(f"LLM 초기화 실패: {e}")
    st.stop()

# 페이지 설정
st.set_page_config(page_title="롯데월드 챗봇", page_icon="🎢", layout="wide")

# CSS 스타일 (채팅 버블)
st.markdown("""
<style>
.user-bubble {
    background-color: #DCF8C6;
    padding: 10px 15px;
    border-radius: 15px;
    margin: 5px 0;
    max-width: 75%;
    float: right;
    clear: both;
}
.bot-bubble {
    background-color: #E8F4FD;
    padding: 10px 15px;
    border-radius: 15px;
    margin: 5px 0;
    max-width: 75%;
    float: left;
    clear: both;
}
.timestamp {
    font-size: 0.7rem;
    color: #888;
}
</style>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.title("🎢 롯데월드 챗봇")
    st.markdown("📍 위치, 티켓, 운영시간 등 기본정보 \n💬 일반 대화\n📝 리뷰/후기")
    st.markdown("---")
    if st.button("🔄 대화 초기화"):
        st.session_state.clear()
        st.rerun()
    if st.session_state.get("chat_history"):
        chat_text = "\n".join(
            f"[{msg['node']}] 사용자: {msg['user']}\n챗봇: {msg['assistant']}\n"
            for msg in st.session_state.chat_history
        )
        st.download_button("💾 대화 저장", chat_text, file_name="lotteworld_chat.txt")

# 상태 초기화
if "state" not in st.session_state:
    st.session_state.state = create_initial_state()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"user": None, "assistant": "안녕하세요! 🎡 롯데월드 챗봇이에요.\n무엇이든 물어보세요!", "node": "chat"}
    ]

# 채팅 입력
user_input = st.chat_input("질문을 입력하세요...")

if user_input:
    current_state = st.session_state.state.copy()
    current_state["user_input"] = user_input
    with st.spinner("🤔 생각 중..."):
        result_state = compiled.invoke(current_state)
    st.session_state.state = result_state
    assistant_response = result_state.get("result", "죄송합니다. 응답을 생성할 수 없습니다.")
    st.session_state.chat_history.append({
        "user": user_input,
        "assistant": assistant_response,
        "node": result_state.get("current_node", "unknown"),
        "time": datetime.now().strftime("%H:%M")
    })
    st.rerun()

# 채팅 출력
for msg in st.session_state.chat_history:
    if msg["user"]:  # 사용자 메시지
        st.markdown(f'<div class="user-bubble">{msg["user"]}</div>', unsafe_allow_html=True)
    # 챗봇 메시지
    st.markdown(f'<div class="bot-bubble">{msg["assistant"]}</div>', unsafe_allow_html=True)