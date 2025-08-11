"""
FAISS 인덱스 생성 및 임베딩 관련 기능
"""
import os
import json
"""
FAISS 인덱스 생성 및 임베딩 관련 기능
"""
import os
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import faiss
from langchain.schema import Document

class FAISSVectorStore:
    """FAISS 인덱스를 래핑한 벡터 스토어 클래스"""
    
    def __init__(self, index: faiss.Index, metadata: List[Dict[str, Any]], embedder=None):
        self.index = index
        self.metadata = metadata
        self.embedder = embedder
    
    def _get_embedder(self):
        """임베딩 함수 lazy loading"""
        if self.embedder is None:
            from langchain_upstage import UpstageEmbeddings
            from dotenv import load_dotenv
            
            load_dotenv()
            api_key = os.getenv("UPSTAGE_API_KEY")
            if not api_key:
                raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")
            
            model_name = os.getenv("UPSTAGE_EMBED_MODEL", "solar-embedding-1-large")
            self.embedder = UpstageEmbeddings(model=model_name, api_key=api_key)
        
        return self.embedder
    
    def _embed_query(self, query: str) -> np.ndarray:
        """쿼리 임베딩"""
        embedder = self._get_embedder()
        embedding = embedder.embed_query(query)
        embedding_array = np.array([embedding], dtype='float32')
        faiss.normalize_L2(embedding_array)  # 코사인 유사도를 위한 정규화
        return embedding_array
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """유사도 검색 (점수 없이)"""
        docs_with_scores = self.similarity_search_with_score(query, k)
        return [doc for doc, _ in docs_with_scores]
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """유사도 검색 (점수 포함)"""
        # 쿼리 임베딩
        query_embedding = self._embed_query(query)
        
        # FAISS 검색
        scores, indices = self.index.search(query_embedding, k)
        
        # 결과 변환
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):  # 유효한 인덱스 확인
                meta = self.metadata[idx]
                
                # Document 생성
                doc = Document(
                    page_content=meta.get('content', ''),
                    metadata={
                        "platform": meta.get('platform', ''),
                        "subject": meta.get('subject', ''),
                        "place": meta.get('place', ''),
                        "date": meta.get('date', ''),
                        "rating": meta.get('rating'),
                        "url": meta.get('url', ''),
                        "source_row": idx,  # 원본 인덱스
                        "chunk_index": idx
                    }
                )
                
                # FAISS IndexFlatIP는 내적을 반환하므로, 정규화된 벡터에서는 코사인 유사도
                similarity_score = float(score)
                results.append((doc, similarity_score))
        
        return results
    
    def add_documents(self, documents: List[Document]) -> None:
        """문서 추가 (선택적 기능)"""
        # 새 문서들의 텍스트 추출
        texts = [doc.page_content for doc in documents]
        
        # 임베딩 생성
        embeddings = create_embeddings(texts)
        
        # 인덱스에 추가
        self.index.add(embeddings.astype('float32'))
        
        # 메타데이터 추가
        for doc in documents:
            meta = {
                "content": doc.page_content,
                "platform": doc.metadata.get('platform', ''),
                "subject": doc.metadata.get('subject', ''),
                "place": doc.metadata.get('place', ''),
                "date": doc.metadata.get('date', ''),
                "rating": doc.metadata.get('rating'),
                "url": doc.metadata.get('url', '')
            }
            self.metadata.append(meta)

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

def load_faiss_index(index_path: str = "st_app/db/faiss_index") -> FAISSVectorStore:
    """FAISS 인덱스 로드 - FAISSVectorStore 객체 반환"""
    try:
        index_file = os.path.join(index_path, "index.faiss")
        meta_file = os.path.join(index_path, "meta.json")
        
        if not os.path.exists(index_file) or not os.path.exists(meta_file):
            print("FAISS index not found. Creating new index...")
            create_faiss_index()
            # 재귀호출로 다시 로드
            return load_faiss_index(index_path)
        
        # 인덱스 로드
        index = faiss.read_index(index_file)
        
        # 메타데이터 로드
        with open(meta_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 메타데이터 검증
        print(f"Loaded {len(metadata)} metadata entries")
        if metadata:
            sample_meta = metadata[0]
            print(f"Sample metadata keys: {list(sample_meta.keys())}")
            print(f"Sample metadata: {sample_meta}")
            
            # 필수 키 확인
            required_keys = ['content', 'platform', 'date', 'rating']
            missing_keys = [key for key in required_keys if key not in sample_meta]
            if missing_keys:
                print(f"Warning: Missing keys in metadata: {missing_keys}")
                print("Consider regenerating the FAISS index")
        
        # FAISSVectorStore 객체 반환
        return FAISSVectorStore(index, metadata)
        
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        print("You may need to regenerate the FAISS index")
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

if __name__ == "__main__":
    create_faiss_index()
    create_faiss_index()