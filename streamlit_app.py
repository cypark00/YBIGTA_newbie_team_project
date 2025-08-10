import streamlit as st
from typing_extensions import TypedDict
from langchain_upstage import ChatUpstage
import os
from dotenv import load_dotenv
from st_app.graph.router import compiled

# 환경변수 로드
load_dotenv()
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

# LLM 초기화
llm = ChatUpstage(model="solar-pro2")  # 실제 모델 이름 변경 가능 (예: gemini-pro)

# Streamlit 페이지 기본 설정
st.set_page_config(page_title="RAG Agent Chatbot", page_icon="🤖")

st.title("💬 RAG Agent 챗봇")
st.write("아래 입력창에 문장을 입력하면 LangGraph를 통해 응답합니다.")

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 사용자 입력
user_input = st.text_input("문장을 입력하세요:")

# 버튼 클릭 시 실행
if st.button("보내기"):
    if user_input.strip():
        # LangGraph 실행
        result = compiled.invoke({
            "user_input": user_input,
            "decision": "",
            "result": ""
        })

        # 대화 기록 저장
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": str(result)})

# 채팅 기록 출력
if st.session_state.chat_history:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"**🙋‍♂️ 사용자:** {msg['content']}")
        else:
            st.markdown(f"**🤖 챗봇:** {msg['content']}")