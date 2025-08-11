
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


"""
RAG Review Node - 리뷰 데이터 기반 답변
"""
import os
import json
import numpy as np
import faiss
from typing import Dict, Any, List
from st_app.utils.state import AppState
from st_app.rag.llm import get_chat_llm
from st_app.rag.prompt import RAG_REVIEW_SYSTEM_PROMPT

def load_faiss_index(index_path: str = "st_app/db/faiss_index"):
    """FAISS 인덱스 로드"""
    try:
        index_file = os.path.join(index_path, "index.faiss")
        meta_file = os.path.join(index_path, "meta.json")
        
        if not os.path.exists(index_file) or not os.path.exists(meta_file):
            print("FAISS index not found!")
            return None
        
        # 인덱스 로드
        index = faiss.read_index(index_file)
        
        # 메타데이터 로드
        with open(meta_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return {"index": index, "metadata": metadata}
        
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return None

def search_similar_reviews(question: str, faiss_data: Dict, top_k: int = 5) -> List[Dict]:
    """질문과 유사한 리뷰 검색"""
    try:
        from st_app.rag.embedder import _get_embedding_model
        
        # 임베딩 모델 로드
        embedding_model = _get_embedding_model()
        
        # 질문 임베딩 생성
        question_embedding = embedding_model.embed_documents([question])
        question_vector = np.array(question_embedding, dtype='float32')
        
        # 정규화 (cosine similarity를 위해)
        faiss.normalize_L2(question_vector)
        
        # FAISS 검색
        index = faiss_data["index"]
        metadata = faiss_data["metadata"]
        
        # 유사도 검색
        similarities, indices = index.search(question_vector, top_k)
        
        # 결과 반환
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(metadata):
                result = metadata[idx].copy()
                result['similarity'] = float(similarities[0][i])
                results.append(result)
        
        return results
        
    except Exception as e:
        print(f"Search error: {e}")
        return []

def rag_review_node(state: AppState) -> Dict[str, Any]:
    """RAG Review Node - 리뷰 데이터 기반 답변"""
    try:
        # 사용자 입력 가져오기
        user_input = state.get('user_input', '')
        messages = state.get('messages', [])
        
        # 질문 결정 (user_input 우선, 없으면 마지막 메시지)
        if user_input:
            question = user_input
        elif messages:
            question = messages[-1].get('content', '')
        else:
            question = ''
        
        if not question:
            return {
                'current_node': 'chat',
                'messages': messages + [{'role': 'assistant', 'content': '질문을 입력해주세요.'}]
            }
        
        # FAISS 인덱스 로드
        faiss_data = load_faiss_index()
        if not faiss_data:
            return {
                'current_node': 'chat',
                'messages': messages + [{'role': 'assistant', 'content': '리뷰 데이터를 로드할 수 없습니다.'}]
            }
        
        # 유사한 리뷰 검색 (더 많은 리뷰 검색)
        similar_reviews = search_similar_reviews(question, faiss_data, top_k=8)
        
        if not similar_reviews:
            return {
                'current_node': 'chat',
                'messages': messages + [{'role': 'assistant', 'content': '관련된 리뷰를 찾을 수 없습니다.'}]
            }
        
        # 컨텍스트 구성 (더 자세한 정보 포함)
        context_parts = []
        for i, review in enumerate(similar_reviews, 1):
            content = review.get('content', '')
            platform = review.get('platform', '')
            rating = review.get('rating', '')
            date = review.get('date', '')
            similarity = review.get('similarity', 0)
            
            context_part = f"[리뷰 {i}] {content}\n- 출처: {platform}\n- 평점: {rating}점\n- 날짜: {date}\n- 관련도: {similarity:.3f}"
            context_parts.append(context_part)
        
        context = "\n\n".join(context_parts)
        
        # LLM 호출
        llm = get_chat_llm()
        
        # 프롬프트 구성
        system_prompt = RAG_REVIEW_SYSTEM_PROMPT.replace("{context}", context).replace("{question}", question)
        
        # 메시지 구성
        chat_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        # LLM 응답 생성
        response = llm.invoke(chat_messages)
        
        # 응답 추출
        if hasattr(response, 'content'):
            answer = response.content
        else:
            answer = str(response)
        
        # 상태 업데이트
        updated_messages = messages + [
            {'role': 'user', 'content': question},
            {'role': 'assistant', 'content': answer}
        ]
        
        return {
            'current_node': 'chat',
            'messages': updated_messages
        }
        
    except Exception as e:
        print(f"RAG Review Node Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'current_node': 'chat',
            'messages': messages + [{'role': 'assistant', 'content': f'오류가 발생했습니다: {str(e)}'}]
        }

