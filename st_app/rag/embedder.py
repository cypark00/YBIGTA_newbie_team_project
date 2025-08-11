"""
FAISS 인덱스 생성 및 임베딩 관련 기능
"""
import os
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import faiss
from langchain.schema import Document

def load_review_data() -> List[Dict[str, Any]]:
    """리뷰 데이터 로드"""
    reviews = []
    
    # CSV 파일들 로드
    csv_files = [
        "database/preprocessed_reviews_kakaomap.csv",
        "database/preprocessed_reviews_myrealtrip.csv", 
        "database/preprocessed_reviews_tripdotcom.csv"
    ]
    
    for file_path in csv_files:
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                platform = file_path.split('_')[2].split('.')[0]  # kakaomap, myrealtrip, tripdotcom
                
                for _, row in df.iterrows():
                    review = {
                        "content": str(row.get('content', '')),
                        "rating": row.get('rating'),
                        "date": str(row.get('date', '')),
                        "platform": platform,
                        "subject": "롯데월드",
                        "place": "롯데월드"
                    }
                    reviews.append(review)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return reviews

def create_documents_from_reviews(reviews: List[Dict[str, Any]]) -> List[Document]:
    """리뷰 데이터를 LangChain Document로 변환"""
    documents = []
    
    for review in reviews:
        content = review.get('content', '')
        if content and len(content.strip()) > 10:  # 의미있는 내용만 포함
            doc = Document(
                page_content=content,
                metadata={
                    "platform": review.get('platform', ''),
                    "subject": review.get('subject', ''),
                    "place": review.get('place', ''),
                    "date": review.get('date', ''),
                    "rating": review.get('rating'),
                    "url": review.get('url', '')
                }
            )
            documents.append(doc)
    
    return documents

def create_embeddings(texts: List[str]) -> np.ndarray:
    """Upstage API를 사용한 임베딩 생성 -> np.ndarray(float32)로 반환"""
    try:
        from langchain_upstage import UpstageEmbeddings
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv("UPSTAGE_API_KEY")
        if not api_key:
            raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")

        # ✅ 최신 모델명 (환경변수로 오버라이드 가능)
        model_name = os.getenv("UPSTAGE_EMBED_MODEL", "solar-embedding-1-large")

        emb = UpstageEmbeddings(model=model_name, api_key=api_key)

        # 간단 헬스체크(첫 문장만 시도해봄; 실패 시 즉시 명확한 에러)
        _ = emb.embed_documents([texts[0] if texts else "healthcheck"])

        # 실제 임베딩
        vecs: List[List[float]] = emb.embed_documents(texts)
        arr = np.array(vecs, dtype="float32")  # ✅ numpy 변환
        return arr

    except Exception as e:
        print(f"[Upstage Embedding Error] {e}")
        print("임베딩 생성에 실패했습니다. (모델명 또는 입력 형식을 확인하세요)")
        raise

def build_faiss_index(documents: List[Document], index_path: str = "st_app/db/faiss_index") -> None:
    """FAISS 인덱스 생성 및 저장"""
    if not documents:
        print("No documents to index")
        return
    
    # 디렉토리 생성
    os.makedirs(index_path, exist_ok=True)
    
    # 텍스트 추출
    texts = [doc.page_content for doc in documents]
    
    # 임베딩 생성
    print("Creating embeddings using Upstage API...")
    embeddings = create_embeddings(texts)
    
    # FAISS 인덱스 생성
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner Product for cosine similarity
    
    # 정규화 (cosine similarity를 위해)
    faiss.normalize_L2(embeddings)
    
    # 인덱스에 벡터 추가
    index.add(embeddings.astype('float32'))
    
    # 인덱스 저장
    faiss.write_index(index, os.path.join(index_path, "index.faiss"))
    
    # 메타데이터 저장 (리뷰 내용 포함)
    metadata = []
    for doc in documents:
        metadata.append({
            "content": doc.page_content,  # 리뷰 내용 포함
            "platform": doc.metadata.get('platform', ''),
            "subject": doc.metadata.get('subject', ''),
            "place": doc.metadata.get('place', ''),
            "date": doc.metadata.get('date', ''),
            "rating": doc.metadata.get('rating'),
            "url": doc.metadata.get('url', '')
        })
    
    with open(os.path.join(index_path, "meta.json"), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"FAISS index saved to {index_path}")
    print(f"Indexed {len(documents)} documents")

def load_faiss_index(index_path: str = "st_app/db/faiss_index"):
    """FAISS 인덱스 로드"""
    try:
        index_file = os.path.join(index_path, "index.faiss")
        meta_file = os.path.join(index_path, "meta.json")
        
        if not os.path.exists(index_file) or not os.path.exists(meta_file):
            print("FAISS index not found. Creating new index...")
            create_faiss_index()
        
        # 인덱스 로드
        index = faiss.read_index(index_file)
        
        # 메타데이터 로드
        with open(meta_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return {"index": index, "metadata": metadata}
        
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return None

def create_faiss_index():
    """FAISS 인덱스 생성 메인 함수"""
    print("Loading review data...")
    reviews = load_review_data()
    
    print("Creating documents...")
    documents = create_documents_from_reviews(reviews)
    
    print("Building FAISS index...")
    build_faiss_index(documents)
    
    print("FAISS index creation completed!")

# 기존 LangChain 호환성을 위한 함수들
def _get_embedding_model(model_name: Optional[str] = None):
    """
    Upstage 임베딩을 우선 사용하고, 키가 없거나 실패하면 멀티링구얼 SBERT로 폴백.
    - 환경변수:
        UPSTAGE_API_KEY
        UPSTAGE_EMBED_MODEL (기본: "solar-embedding-1-large")
    """
    upstage_key = os.getenv("UPSTAGE_API_KEY")
    if upstage_key:
        try:
            from langchain_upstage import UpstageEmbeddings
            # 더 안전한 모델명 사용
            up_model = os.getenv("UPSTAGE_EMBED_MODEL", "solar-embedding-1-large")
            return UpstageEmbeddings(model=up_model, api_key=upstage_key)
        except Exception as e:
            print(f"[embedder] Upstage 임베딩 사용 실패 → 폴백합니다: {e}")

    # 폴백: 한국어&다국어 무난한 소형 모델
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=model_name or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

if __name__ == "__main__":
    create_faiss_index()