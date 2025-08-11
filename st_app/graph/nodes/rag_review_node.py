# st_app/graph/nodes/rag_review_node.py
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import os

from langchain.schema import Document  # 문서 타입 힌트용

# 공용 레이어
from st_app.rag.embedder import load_faiss_index
from st_app.rag.prompt import get_rag_review_prompt

# 상태/헬퍼
from st_app.utils.state import State
from st_app.rag.llm import get_upstage_llm

# --------- 모듈 전역 캐시 ---------
_VS = None         # FAISS vector store


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
        if _VS is None:
            raise RuntimeError("FAISS 인덱스를 로드할 수 없습니다.")
    return _VS


def _short_src(md: Dict[str, Any]) -> str:
    """
    근거 표기에 들어갈 간략 소스 문자열 생성
    """
    try:
        rating = md.get("rating")
        date = md.get("date", "") or ""
        platform = md.get("platform", "unknown") or "unknown"
        rate_s = f"|rating={rating}" if rating is not None else ""
        platform_s = f"|{platform}" if platform and platform != "unknown" else ""
        return f"review|{date}{rate_s}{platform_s}"
    except Exception as e:
        print(f"Error in _short_src: {e}, metadata: {md}")
        return "review|unknown"


def _format_context(docs_with_scores: List[Tuple[Document, float]]) -> str:
    """
    모델에 제공할 컨텍스트 문자열 생성
    - 각 청크와 메타를 함께 전달 (모델이 출력에서 근거 인용을 구성하기 쉬움)
    - 유사도 점수도 포함
    """
    if not docs_with_scores:
        return ""
    parts = []
    for i, (doc, score) in enumerate(docs_with_scores):
        parts.append(
            f"[Review {i+1}]\n"
            f"{doc.page_content}\n"
            f"(source: {_short_src(doc.metadata)}, similarity: {score:.3f})"
        )
    return "\n\n".join(parts)


def _to_document_hits(docs_with_scores: List[Tuple[Document, float]]) -> List[Dict[str, Any]]:
    """
    상태에 저장할 RAG 결과(진단/출처용)
    """
    results: List[Dict[str, Any]] = []
    for doc, score in docs_with_scores:
        try:
            md = doc.metadata or {}
            results.append({
                "chunk": doc.page_content,
                "date": md.get("date", ""),
                "rating": md.get("rating"),
                "platform": md.get("platform", "unknown"),
                "place": md.get("place", "롯데월드"),
                "source_row": md.get("source_row"),
                "chunk_index": md.get("chunk_index"),
                "score": float(score)  # 유사도 점수 추가
            })
        except Exception as e:
            print(f"Error processing document hit: {e}, metadata: {doc.metadata}")
            # 에러가 있어도 기본 정보는 포함
            results.append({
                "chunk": doc.page_content,
                "date": "",
                "rating": None,
                "platform": "unknown",
                "place": "롯데월드",
                "source_row": None,
                "chunk_index": None,
                "score": float(score)
            })
    return results


def _filter_by_threshold(docs_with_scores: List[Tuple[Document, float]], threshold: float = 0.6) -> List[Tuple[Document, float]]:
    """
    유사도 임계값으로 필터링
    """
    return [(doc, score) for doc, score in docs_with_scores if score >= threshold]


def rag_review_node(state: State) -> State:
    """
    FAISS 기반 리뷰 RAG 응답 노드 (커스텀 FAISS 사용)
    입력:
      - state.user_input
      - state.conversation_history
    출력:
      - state.result (응답)
      - state.retrieved_reviews (검색된 리뷰들)
      - state.review_query, state.current_node="rag_review"
    에러:
      - state.error 에 간단한 사유 저장
    """
    try:
        # 1) 쿼리 확보
        question = state.get("user_input", "").strip()
        if not question:
            state["result"] = "질문이 비어 있어요. 어떤 점이 궁금한가요?"
            state["current_node"] = "rag_review"
            return state

        state["review_query"] = question

        # 2) FAISS 벡터 저장소 준비
        vs = _ensure_vs()

        # 3) 검색 수행 - similarity_search_with_score 사용하여 점수도 함께 가져오기
        docs_with_scores: List[Tuple[Document, float]] = vs.similarity_search_with_score(question, k=10)
        
        if not docs_with_scores:
            state["result"] = "관련된 리뷰를 찾을 수 없어요. 다른 질문을 해보시겠어요?"
            state["current_node"] = "rag_review"
            state["retrieved_reviews"] = []
            return state

        # 4) 유사도 임계값으로 필터링 (선택사항)
        # 너무 관련성이 낮은 문서는 제외
        filtered_docs = _filter_by_threshold(docs_with_scores, threshold=0.4)
        
        # 필터링 후에도 최소 3개는 유지
        if len(filtered_docs) < 3 and len(docs_with_scores) >= 3:
            filtered_docs = docs_with_scores[:3]
        elif not filtered_docs and docs_with_scores:
            filtered_docs = docs_with_scores[:1]  # 최소 1개는 유지
        
        # 최종적으로 상위 5개만 사용
        final_docs = filtered_docs[:5]

        # 5) 컨텍스트/근거 메타 구성
        context = _format_context(final_docs)
        state["retrieved_reviews"] = _to_document_hits(final_docs)
        state["rag_context"] = context

        # 6) 검색 품질 정보 추가
        avg_score = sum(score for _, score in final_docs) / len(final_docs)
        max_score = max(score for _, score in final_docs)
        min_score = min(score for _, score in final_docs)
        state["search_quality"] = {
            "total_found": len(docs_with_scores),
            "filtered_count": len(filtered_docs),
            "used_count": len(final_docs),
            "avg_similarity": avg_score,
            "max_similarity": max_score,
            "min_similarity": min_score
        }

        # 7) 프롬프트 생성 및 LLM 호출
        llm = get_upstage_llm(temperature=0.2)
        prompt_text = get_rag_review_prompt(context=context, question=question)
        result = llm.invoke(prompt_text)
        answer: str = result.content

        # 8) 검색 품질에 따른 신뢰도 표시 추가 (선택사항)
        confidence_note = ""
        if avg_score < 0.5:
            confidence_note = "\n\n💡 *검색된 리뷰와의 관련성이 다소 낮을 수 있습니다. 더 구체적인 질문을 해보시겠어요?*"
        elif avg_score > 0.7:
            confidence_note = "\n\n✨ *매우 관련성이 높은 리뷰들을 찾았습니다!*"

        # 9) 응답 저장 및 현재 노드 표시
        state["result"] = answer + confidence_note
        state["current_node"] = "rag_review"
        state["error"] = None
        
        # 대화 기록 업데이트
        conversation_history = state.get("conversation_history", [])
        conversation_history.append({
            "user": question,
            "assistant": answer
        })
        state["conversation_history"] = conversation_history
        
        return state

    except Exception as e:
        # 에러시 사용자에게도 짧게 안내하고, 에러 저장
        err_msg = f"리뷰 검색 중 오류가 발생했어요: {str(e)}"
        state["result"] = err_msg
        state["error"] = str(e)
        state["current_node"] = "rag_review"
        
        # 대화 기록 업데이트
        conversation_history = state.get("conversation_history", [])
        conversation_history.append({
            "user": state.get("user_input", ""),
            "assistant": err_msg
        })
        state["conversation_history"] = conversation_history
        
        return state