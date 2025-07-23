import pandas as pd 
import numpy as np 
import json 
from sklearn.metrics.pairwise import cosine_similarity


data_files = [
    "database/preprocessed_reviews_kakaomap.csv",
    "database/preprocessed_reviews_myrealtrip.csv",
    "database/preprocessed_reviews_tripdotcom.csv"
]

#데이터프레임 병합 
dfs = []
for file in data_files:
    df = pd.read_csv(file)
    df["embedding"] = df["embedding"].apply(json.loads)
    dfs.append(df) 

df_all = pd.concat(dfs, ignore_index=True)

#그룹 나누기 
short_df = df_all[df_all["text_length"] <= 20] 
long_df = df_all[df_all["text_length"] >= 60] 

#평균 임베딩 
short_mean = np.mean(short_df["embedding"].tolist(), axis=0).reshape(1,-1)
long_mean = np.mean(long_df["embedding"].tolist(), axis=0).reshape(1,-1)

#Cosine Smilarity 
similarity = cosine_similarity(short_mean, long_mean)[0][0]

print("====== 텍스트 길이 기반 유사도 분석 ======")
print(f"짧은 리뷰 수 (≤20자): {len(short_df)}개")
print(f"긴 리뷰 수 (≥60자): {len(long_df)}개")
print(f"Cosine Similarity: {similarity:.4f}")

if similarity > 0.9:
    print("짧은 리뷰와 긴 리뷰는 분위기가 매우 유사합니다.")
elif similarity > 0.7:
    print("짧은 리뷰와 긴 리뷰는 분위기 차이가 일부 존재합니다.")
else:
    print("짧은 리뷰와 긴 리뷰는 서로 다른 분위기를 가질 가능성이 높습니다.")