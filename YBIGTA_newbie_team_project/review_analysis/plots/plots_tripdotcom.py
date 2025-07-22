import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# 한글 폰트 오류 방지
plt.rcParams['font.family'] = 'Malgun Gothic'

# 파일 로드
df = pd.read_csv("../../database/reviews_tripdotcom.csv", encoding='utf-8')

# 리뷰 길이 변수 생성
df["review_length"] = df["content"].astype(str).apply(len)

# 날짜 변환
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["weekday"] = df["date"].dt.day_name()

## 1. 별점 분포 시각화
plt.figure(figsize=(8, 6))
sns.countplot(x="rating", data=df, palette="Set3", edgecolor='black')
plt.title("별점 분포")
plt.xlabel("별점")
plt.ylabel("리뷰 수")
plt.savefig("tripdotcom_rating_distribution.png")
plt.close()

## 2. 리뷰 길이 분포
plt.figure(figsize=(8, 6))
plt.hist(df["review_length"], bins=30, color='skyblue', edgecolor='black')
plt.title("리뷰 길이 분포")
plt.xlabel("리뷰 길이")
plt.ylabel("리뷰 수(글자 수)")
plt.savefig("tripdotcom_review_length_distribution.png")
plt.close()

plt.figure(figsize=(8, 6))
sns.boxplot(y=df["review_length"], color='skyblue')
plt.title("리뷰 길이 분포 (Box Plot)")
plt.ylabel("리뷰 길이")
plt.savefig("tripdotcom_review_length_boxplot.png")
plt.close()

## 3. 날짜별 리뷰 수
daily_counts = df["date"].value_counts().sort_index()
plt.figure(figsize=(12, 6))
plt.plot(daily_counts.index, daily_counts.values, marker='o', linestyle='-', color='blue')
plt.title("날짜별 리뷰 수")
plt.xlabel("날짜")
plt.ylabel("리뷰 수")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("tripdotcom_daily_review_counts.png")
plt.close()

## 4. 요일별 리뷰 수
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_counts = df["weekday"].value_counts().reindex(weekday_order)
plt.figure(figsize=(8, 6))
sns.barplot(x=weekday_counts.index, y=weekday_counts.values, palette="Set3", edgecolor='black')
plt.title("요일별 리뷰 수")
plt.xlabel("요일")
plt.ylabel("리뷰 수")
plt.savefig("tripdotcom_weekday_review_counts.png")
plt.close()