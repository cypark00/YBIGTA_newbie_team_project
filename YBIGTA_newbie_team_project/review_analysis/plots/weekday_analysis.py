import pandas as pd 

files = [
    ("KakaoMap", "database/preprocessed_reviews_kakaomap.csv"),
    ("MyRealTrip", "database/preprocessed_reviews_myrealtrip.csv"),
    ("Trip.com", "database/preprocessed_reviews_tripdotcom.csv")
]

dfs = [] 

#site 정보 추가 
df_list = []
for site, path in files:
    df = pd.read_csv(path)
    df["site"] = site
    df_list.append(df)

all_df = pd.concat(df_list, ignore_index=True)

#요일별로 리뷰 수, 평균 별점, 평균 텍스트 길이 계산 
weekday_summary = all_df.groupby("weekday").agg(
    review_count=("content", "count"),
    avg_rating=("rating", "mean"),
    avg_length=("text_length", "mean")
).reset_index()

#요일 순서 정렬 
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_summary["weekday"] = pd.Categorical(weekday_summary["weekday"], categories=weekday_order, ordered=True)
weekday_summary = weekday_summary.sort_values("weekday")

print(weekday_summary)