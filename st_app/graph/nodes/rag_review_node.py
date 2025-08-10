# st_app/graph/nodes/rag_review_node.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
import os

from langchain.schema import Document  # 문서 타입 힌트용 (없어도 동작엔 지장 없음)

# 공용 레이어
from st_app.rag.embedder import load_faiss_index
from st_app.rag.retriever import make_retriever
from st_app.rag.llm import get_chat_llm
from st_app.rag.prompt import get_rag_review_prompt

# 상태/헬퍼
from st_app.utils.state import (
    AppState, add_message, get_last_user_message,
    mark_retrieval_start, mark_retrieval_end
)

# --------- 모듈 전역 캐시 ---------
_VS = None         # FAISS vector store
_RETR_MODE = None  # 마지막으로 만든 retriever의 모드
_RETR_K = None     # 마지막으로 만든 retriever의 k
_RETR = None       # retriever 캐시


def _faiss_dir() -> str:
    """
    인덱스 경로: 환경변수 RAG_FAISS_DIR 우선, 없으면 기본 경로 사용
    """
    return os.getenv("RAG_FAISS_DIR", "st_app/db/faiss_index")


def _ensure_vs():
    """
    FAISS index 로딩(1회)
    """
    global _VS
    if _VS is None:
        _VS = load_faiss_index(_faiss_dir())
    return _VS


def _ensure_retriever(mode: str = "mmr", k: int = 5):
    """
    모드/파라미터가 바뀌면 새 retriever 생성, 아니면 캐시 사용
    """
    global _RETR, _RETR_MODE, _RETR_K
    vs = _ensure_vs()
    if _RETR is None or _RETR_MODE != mode or _RETR_K != k:
        _RETR = make_retriever(vs, mode=mode, k=k)
        _RETR_MODE, _RETR_K = mode, k
    return _RETR


def _short_src(md: Dict[str, Any]) -> str:
    """
    근거 표기에 들어갈 간략 소스 문자열 생성
    """
    platform = md.get("platform") or "review"
    subj = md.get("subject") or md.get("place") or ""
    date = md.get("date") or ""
    rating = md.get("rating")
    rate_s = f"|rating={rating}" if rating is not None else ""
    return f"{platform}|{subj}|{date}{rate_s}"


def _format_context(docs: List[Document]) -> str:
    """
    모델에 제공할 컨텍스트 문자열 생성
    - 각 청크와 메타를 함께 전달 (모델이 출력에서 근거 인용을 구성하기 쉬움)
    """
    if not docs:
        return ""
    parts = []
    for d in docs:
        parts.append(
            "[Chunk]\n"
            f"{d.page_content}\n"
            f"(meta: source={_short_src(d.metadata)})"
        )
    return "\n\n".join(parts)


def _to_document_hits(docs: List[Document]) -> List[Dict[str, Any]]:
    """
    상태에 저장할 RAG 결과(진단/출처용)
    """
    results: List[Dict[str, Any]] = []
    for d in docs:
        md = d.metadata or {}
        results.append({
            "chunk": d.page_content,
            "platform": md.get("platform"),
            "subject": md.get("subject"),
            "place": md.get("place"),
            "date": md.get("date"),
            "rating": md.get("rating"),
            "url": md.get("url"),
            # langchain FAISS 기본 retriever는 score를 직접 주지 않으므로 None
            # (커스텀 스코어를 계산하는 경우 여기 채워넣기)
            "score": md.get("score")
        })
    return results


def rag_review_node(state: AppState) -> AppState:
    """
    FAISS 기반 리뷰 RAG 응답 노드
    입력:
      - state.messages (대화 로그)
      - (선택) state.user_input
      - state.retrieval_mode ("mmr"|"similarity"), state.top_k (int)
    출력:
      - state.messages (assistant 응답 추가)
      - state.retrieved_docs (근거 메타 저장)
      - state.last_query, state.retrieval_latency_ms, state.current_node="rag_review"
    에러:
      - state.error 에 간단한 사유 저장 후 chat으로 복귀
    """
    try:
        # 1) 쿼리 확보
        question = (state.get("user_input")
                    or get_last_user_message(state)
                    or "").strip()
        if not question:
            add_message(state, "assistant", "질문이 비어 있어요. 어떤 점이 궁금한가요?")
            state["current_node"] = "rag_review"
            return state

        state["last_query"] = question

        # 2) 리트리버 준비(모드/탑K는 상태에서 우선)
        mode = state.get("retrieval_mode") or "mmr"
        top_k = state.get("top_k") or 5
        retriever = _ensure_retriever(mode=mode, k=top_k)

        # 3) 검색 수행(진단 시간 기록)
        t0 = mark_retrieval_start()
        docs: List[Document] = retriever.get_relevant_documents(question)
        mark_retrieval_end(state, t0)

        # 4) 컨텍스트/근거 메타 구성
        context = _format_context(docs)
        state["retrieved_docs"] = _to_document_hits(docs)

        # 5) 프롬프트 생성 및 LLM 호출
        prompt_text = get_rag_review_prompt(context=context, question=question)
        llm = get_chat_llm()
        # LangChain ChatModel은 문자열 인풋도 받음(HumanMessage로 처리)
        answer: str = llm.invoke(prompt_text).content

        # 6) 메시지 기록 및 현재 노드 표시
        add_message(state, "assistant", answer)
        state["current_node"] = "rag_review"
        state["error"] = None
        return state

    except Exception as e:
        # 에러시 사용자에게도 짧게 안내하고, 에러 저장
        err_msg = f"리뷰 검색 중 오류가 발생했어요: {str(e)}"
        add_message(state, "assistant", err_msg)
        state["error"] = str(e)
        state["current_node"] = "rag_review"
        return state

