
from __future__ import annotations
from typing import List, Dict, Any, Optional
import hashlib

from langchain_community.vectorstores import FAISS
from langchain.schema import Document


# ── 내부 유틸 ──────────────────────────────────────────────────────────────────
META_KEYS = ("platform", "subject", "place", "date", "rating", "url")

def _ensure_meta_fields(d: Document) -> None:
    """문서 메타에 필요한 키들이 없으면 None으로 채워 일관성 유지."""
    if d.metadata is None:
        d.metadata = {}
    for k in META_KEYS:
        d.metadata.setdefault(k, None)

def _short_src(md: Dict[str, Any]) -> str:
    """프롬프트 인용에 쓰일 간략 소스 문자열."""
    platform = md.get("platform") or "review"
    subj = md.get("subject") or md.get("place") or ""
    date = md.get("date") or ""
    rating = md.get("rating")
    rate_s = f"|rating={rating}" if rating is not None else ""
    return f"{platform}|{subj}|{date}{rate_s}"

def _dedup_by_text(docs: List[Document]) -> List[Document]:
    """동일/거의 동일한 청크가 많을 때 간단히 중복 제거(문자열 해시 기반)."""
    seen, out = set(), []
    for d in docs:
        key = hashlib.md5(d.page_content.strip().encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out


# ── 공개 API ───────────────────────────────────────────────────────────────────
def make_retriever(
    vs: FAISS,
    mode: str = "mmr",
    k: int = 5,
    fetch_k: int = 25,
):
    """
    FAISS → LangChain retriever 생성.
    - mode="mmr" : 다양성(near-duplicate 억제), 권장
    - mode="similarity" : 단순 상위 k
    """
    if mode == "mmr":
        return vs.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": fetch_k}
        )
    return vs.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )


def format_docs(docs: List[Document]) -> str:
    """
    프롬프트에 넣을 컨텍스트 문자열 생성.
    rag_review_node의 응답 가이드에 맞춰 한 청크당 메타 포함.
    """
    if not docs:
        return ""

    # 메타 보정 + 경량 중복 제거
    for d in docs:
        _ensure_meta_fields(d)
    docs = _dedup_by_text(docs)

    parts = []
    for d in docs:
        parts.append(
            "[Chunk]\n"
            f"{d.page_content}\n"
            f"(meta: source={_short_src(d.metadata)})"
        )
    return "\n\n".join(parts)


def docs_to_hits(docs: List[Document]) -> List[Dict[str, Any]]:
    """
    상태(AppState['retrieved_docs'])에 저장할 수 있는 경량 메타로 변환.
    (score는 기본 retriever에선 제공되지 않으므로 None)
    """
    results: List[Dict[str, Any]] = []
    for d in docs:
        _ensure_meta_fields(d)
        md = d.metadata or {}
        results.append({
            "chunk": d.page_content,
            "platform": md.get("platform"),
            "subject": md.get("subject"),
            "place": md.get("place"),
            "date": md.get("date"),
            "rating": md.get("rating"),
            "url": md.get("url"),
            "score": md.get("score"),  # 직접 계산/주입하는 경우만 사용됨
        })
    return results

