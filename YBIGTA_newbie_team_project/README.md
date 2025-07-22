

# KakaoMap 리뷰 크롤링 

## 크롤링 대상 사이트
- KakaoMap 롯데월드 어드벤처 : https://place.map.kakao.com/27560699#comment

## 수집 데이터 개수
- 총 500개 ( 별점, 리뷰 작성일, 리뷰 내용 포함 기준) 

## 데이터 형식
- ‘rating’: 별점 (1~5점) 
- ‘date’: 리뷰 작성일 
- ‘content’: 리뷰 본문 내용 
 

## 저장 경로 
- database/reviews_kakaomap.csv`

# 실행 방법 
### 단일 크롤러 실행 
- 아래 명령어를 통해 **Kakaomap 크롤러 실행** 이 가능합니다:  
python -m review_analysis.crawling.main -o database -c KakaoMap



# Kakaomap EDA 
1. Rating distribution 
- 특징 : 대부분의 리뷰가 5점에 몰려 있음. 
- 이상치 : 범위(1~5)를 벗어난 리뷰는 0개로 확인됨 

2. Text length distribution 
- 특징 : 리뷰의 길이는 0자 ~60자 구간에 가장 많고, 전반적으로 짧은 리뷰가 많음 
- 이상치 기준: 
    - 3자 미만 : 의미 없는 짧은 리뷰로 판단
    - 약 125자 초과: IQR 기준 상위 이상치로 간주
    - 전체 리뷰 중 이상치 비율 : 약 5.20%

3. Date distribution 
- 특징 : 2023년 이후 리뷰가 많음. 데이터의 최근성이 높음. 
- 이상치 기준: 
    - 2022년 7월 이전, 오늘 날짜 이후 
    - 해당 기준은 분포 상 오래된 과거 데이터를 제거하기 위한 목적에서 설정됨. 
- 이상치 개수: 50개 
- 이상치 비율 : 10% 

# TripDotCom 리뷰 크롤링

## 크롤링 대상 사이트
- Trip.com 롯데월드 어드벤처
https://kr.trip.com/travel-guide/attraction/seoul/lotte-world-adventure-136469953/

## 수집 데이터 개수
- 총 500개 (별점, 리뷰 작성일, 리뷰 내용 포함 기준)

## 데이터 형식
- 'rating': 별점 (1~5점)
- 'date': 리뷰 작성일 (YYYY.MM.DD 형식)
- 'content': 리뷰 본문 내용

## 저장 경로
- database/reviews_tripdotcom.csv

# 실행 방법
### 단일 크롤러 실행
- 아래 명령어를 통해 **TripDotCom 크롤러 실행** 이 가능합니다.
python - m review_analysis.crawling.main -o database -c TripDotCom

# TripDotCom 리뷰 데이터 EDA
1. Rating Distribution (별점 분포)
- 특징: 5점 리뷰가 압도적으로 많아 전반적으로 긍정적인 평가가 주를 이룸.
- 이상치: 별점 범위(1~5)를 벗어난 리뷰는 존재하지 않음

2. Text Length Distribution (리뷰 길이 분포)
- 특징: 리뷰 길이가 60자 미만인 짧은 리뷰가 가장 많으며, 전체적으로 간결한 텍스트가 주를 이룸. 
- 이상치 기준: 5자 미만은 의미 없는 텍스트로 판단해 제거, 240자 초과는 Boxplot의 IQR 기준으로 상위 이상치로 간주함.
- 이상치 비율: 전체 리뷰 중 약 7.8%가 이상치로 제거됨.

3. Date Distribution (날짜 분포)
- 특징: 대부분 리뷰는 최근인 2023~2025년 사이에 작성되었으며, 최신성 높은 데이터임.
- 이상치 기준: 2022년 1월 이전 또는 오늘 날짜 이후
- 이상치 개수: 약 45개
- 이상치 비율: 약 9.0%

4. Weekday Distribution (요일별 리뷰 수)
- 특징: 주중에 리뷰가 더 많으며 주말에는 리뷰 수가 감소하는 경향이 있음.

5. 시각화 이미지 저장 경로
YBIGTA_newbie_team_project/
└── review_analysis/
    └── plots/
        ├── tripdotcom_daily_review_counts.png
        ├── tripdotcom_rating_distribution.png
        ├── tripdotcom_review_length_boxplot.png
        ├── tripdotcom_review_length_distribution.png
        └── tripdotcom_weekday_review_counts.png