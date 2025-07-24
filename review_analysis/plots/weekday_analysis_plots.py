import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns # type: ignore[import-untyped]
import os

# 시각화 저장 경로
save_dir = "."
os.makedirs(save_dir, exist_ok=True)

# CSV 경로 리스트
files = [
    ("KakaoMap", "../../database/preprocessed_reviews_kakaomap.csv"),
    ("MyRealTrip", "../../database/preprocessed_reviews_myrealtrip.csv"),
    ("Trip.com", "../../database/preprocessed_reviews_tripdotcom.csv")
]

# 데이터 로드 및 결합
df_list = []
for site, path in files:
    df = pd.read_csv(path)
    df["site"] = site
    df_list.append(df)

all_df = pd.concat(df_list, ignore_index=True)

# 요일 순서 설정
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
all_df["weekday"] = pd.Categorical(all_df["weekday"], categories=weekday_order, ordered=True)

# 1. 요일별 리뷰 수
plt.figure(figsize=(10, 6))
sns.countplot(x="weekday", data=all_df, hue="site")
plt.title("Rewvies count by weekday")
plt.xlabel("Weekday")
plt.ylabel("Review count")
plt.legend(title="Site")
plt.tight_layout()
plt.savefig(os.path.join(save_dir, "weekday_review_count.png"))
plt.close()

# 2. 요일별 평균 별점
plt.figure(figsize=(10, 6))
sns.lineplot(data=all_df, x="weekday", y="rating", hue="site", estimator="mean", errorbar=None)
plt.title("Average rating by weekday")
plt.xlabel("Weekday")
plt.ylabel("Average Rating")
plt.legend(title="Site")
plt.tight_layout()
plt.savefig(os.path.join(save_dir, "weekday_avg_rating.png"))
plt.close()

# 3. 요일별 평균 텍스트 길이
plt.figure(figsize=(10, 6))
sns.lineplot(data=all_df, x="weekday", y="text_length", hue="site", estimator="mean", errorbar=None)
plt.title("Average text length by weekday")
plt.xlabel("Weekday")
plt.ylabel("Average Text Length")
plt.legend(title="Site")
plt.tight_layout()
plt.savefig(os.path.join(save_dir, "weekday_avg_length.png"))
plt.close()