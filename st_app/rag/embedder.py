from __future__ import annotations
import os, json, glob
import pandas as pd
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import FAISS

# 임베딩: Upstage 우선, 없으면 sentence-transformers
def _get_embedding_model(model_name: Optional[str] = None):
    upstage_key = os.getenv("UPSTAGE_API_KEY")
    if upstage_key:
        try:
            from langchain_upstage import UpstageEmbeddings  # pip install langchain-upstage
            return UpstageEmbeddings(model="solar-embedding-1")
        except Exception:
            pass
    # fallback
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=model_name or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def _read_reviews(paths: List[str]) -> pd.DataFrame:
    dfs = []
    for p in paths:
        if p.endswith(".csv"):
            dfs.append(pd.read_csv(p))
        elif p.endswith(".jsonl"):
            dfs.append(pd.read_json(p, lines=True))
    if not dfs:
        raise FileNotFoundError("No review files found. Use CSV or JSONL.")
    df = pd.concat(dfs, ignore_index=True)
    # 최소 컬럼 보정
    needed = ["text"]
    for c in needed:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")
    # 메타 기본값
    for c in ["subject","rating","date","url","review_id"]:
        if c not in df.columns:
            df[c] = None
    return df

def _to_documents(df: pd.DataFrame) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=120)  # 한국어 문장 길이 고려
    docs: List[Document] = []
    for _, row in df.iterrows():
        base_meta = {
            "subject": row.get("subject"),
            "rating": row.get("rating"),
            "date": row.get("date"),
            "url": row.get("url"),
            "review_id": row.get("review_id"),
        }
        text = str(row["text"]).strip()
        if not text:
            continue
        for chunk in splitter.split_text(text):
            docs.append(Document(page_content=chunk, metadata=base_meta))
    return docs

def build_faiss_index(input_glob: str, out_dir: str):
    paths = glob.glob(input_glob)
    df = _read_reviews(paths)
    docs = _to_documents(df)
    embeddings = _get_embedding_model()
    vs = FAISS.from_documents(docs, embeddings)
    os.makedirs(out_dir, exist_ok=True)
    vs.save_local(out_dir)
    # 메타(모델 정보 등) 저장
    meta = {"embedding": embeddings.__class__.__name__, "files": paths}
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def load_faiss_index(dir_path: str):
    embeddings = _get_embedding_model()
    return FAISS.load_local(dir_path, embeddings, allow_dangerous_deserialization=True)

if __name__ == "__main__":
    # 예시: python -m st_app.rag.embedder "database/reviews*.csv" "st_app/db/faiss_index"
    import sys
    in_glob = sys.argv[1] if len(sys.argv) > 1 else "database/reviews.csv"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "st_app/db/faiss_index"
    build_faiss_index(in_glob, out_dir)
    print(f"Saved FAISS to: {out_dir}")
