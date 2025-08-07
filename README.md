# YBIGTA 1조
YBIGTA 교육세션 1조입니다.  
'롯데월드' 리뷰 데이터를 이용하여, 크롤링, EDA 및 전처리, 분석, 시각화에 이르기까지 전 과정을 진행해보았습니다.
## 팀원 소개
- 김서정
    - 나이: 04년생
    - 전공: 인공지능학과 23
    - MBTI: ENFJ
    - 관심사: NLP에 가장 관심이 많고 최근에는 CV에 관심이 생겨 제대로 배워보려고 합니다.
- 박채연
    - 나이 : 03년생 
    - 전공: 언더우드학부 경제학과 22
    - MBTI: ISTJ
    - 관심사: 운동, 최근에는 카페를 찾아다니며 일하거나 공부하는 시간을 즐기고 있습니다. 
- 이지용
    - 나이: 01년생
    - 전공: 응용통계학과 21
    - MBTI: ISTP
    - 관심사: 운동(헬스, 축구, 농구 등등), 야구 보기, 국내 인디 음악 듣기


## 코드 실행 방법
### 의존성 설치
```
pip install -r requirements.txt
```

### Web
```
uvicorn app.main:app --reload
```
실행 후,
[http://127.0.0.1:8000/static/index.html](http://127.0.0.1:8000/static/index.html) 로 진입

### 크롤러
```
# 모든 크롤러 한번에 실행
 python -m review_analysis.crawling.main -o database -a
```
```
# 단일 크롤러 실행
 python -m review_analysis.crawling.main -o database -c {KakaoMap, MyRealTrip, TripDotCom}
```

### 전처리
```
# 모든 전처리 함수 한번에 실행
 python -m review_analysis.preprocessing.main -o database -a
```
```
# 단일 전처리 함수 실행
 python -m review_analysis.preprocessing.main -o database -c {reviews_kakaomap, reviews_myrealtrip, reviews_tripdotcom}
```


## 크롤링 
### 대상 사이트
- KakaoMap 롯데월드 어드벤처  \
https://place.map.kakao.com/27560699#comment
- MyRealTrip 롯데월드 어드벤처 종합&파크이용권  \
https://www.myrealtrip.com/offers/70816
- Trip.com 롯데월드 어드벤처 \
https://kr.trip.com/travel-guide/attraction/seoul/lotte-world-adventure-136469953/

### 수집 데이터 개수 
(별점, 리뷰 작성일, 리뷰 내용 포함 기준) 
- KakaoMap: 500개
- MyRealTrip: 625개
- TripDotCom: 500개 

### 데이터 형식
- ‘rating’: 별점 (1~5점) 
- ‘date’: 리뷰 작성일 
- ‘content’: 리뷰 본문 내용 
 

### 저장 경로
```
database/reviews_kakaomap.csv
database/reviews_myrealtrip.csv
database/reviews_tripdotcom.csv`
```



## EDA
### Kakaomap 
1. Rating distribution 
- 특징 : 대부분의 리뷰가 5점에 몰려 있음. 
- 이상치 : 범위(1~5)를 벗어난 리뷰는 0개로 확인됨

![Alt text](/review_analysis/plots/kakaomap_rating_dist.png)


2. Text length distribution 
- 특징 : 리뷰의 길이는 0자 ~60자 구간에 가장 많고, 전반적으로 짧은 리뷰가 많음 

![Alt text](/review_analysis/plots/kakaomap_text_length_dist.png)

- 이상치 기준: 
    - 3자 미만 : 의미 없는 짧은 리뷰로 판단
    - 약 125자 초과: IQR 기준 상위 이상치로 간주
    - 전체 리뷰 중 이상치 비율 : 약 5.20%

![Alt text](/review_analysis/plots/kakaomap_text_length_box.png)


3. Date distribution 
- 특징 : 2023년 이후 리뷰가 많음. 데이터의 최근성이 높음. 
- 이상치 기준: 
    - 2022년 7월 이전, 오늘 날짜 이후 
    - 해당 기준은 분포 상 오래된 과거 데이터를 제거하기 위한 목적에서 설정됨. 
- 이상치 개수: 50개 
- 이상치 비율 : 10% 

![Alt text](/review_analysis/plots/kakaomap_date_dist.png)

### MyRealTrip 
1. Rating distribution 
- 특징
    - 5점(약 90.4%)이 대부분이었고, 5점>4점>3점>1점>2점 순으로 나타났음.

- 이상치
    - 1~5점을 벗어난 리뷰는 없었음.

![Alt text](/review_analysis/plots/myrealtrip_rating_dist.png)


2.  Text length distribution

- 특징
    - 텍스트 길이는 전반적으로 짧은 편이며, 13(Q1)에서 31(Q3) 구간에 리뷰의 절반이 집중됨. 
    ![Alt text](/review_analysis/plots/myrealtrip_text_length_dist.png)
    - 낮은 평점(1점)일 때 리뷰의 평균 길이가 가장 길었음(불만이 많을수록 상세히 설명하는 경향).
    ![Alt text](/review_analysis/plots/myrealtrip_text_length_box_by_rating.png)


- 이상치:
    - 3자 미만: 유의미한 내용이 담기기 어려운 짧은 리뷰로 분류
    - 58자 초과: IQR 기반 상위 이상치로 간주할 수 있음
    - 이상치 비율: 전체 리뷰의 약 **5.20%**가 기준을 초과

![Alt text](/review_analysis/plots/myrealtrip_text_length_box.png)


3. Date distribution 
- 특징
    - 연도별: 대부분의 데이터는 2024년과 2025년에 집중되어 있으며, 2023년 데이터는 매우 소수

    - 월별: 1월\~3월에 리뷰가 가장 많고, 이후 점차 감소, 10월\~11월은 데이터가 현저히 적음

    - 요일별: 월요일에 리뷰가 집중적으로 발생함 (다른 요일 대비 뚜렷하게 높음), 그 외 요일은 비교적 고르게 분포

    - 일별: 1\~5일에 작성된 리뷰 비율이 특히 높고, 특히 3일에 집중됨, 중순(11일\~20일)에는 비교적 적은 수의 리뷰
- 이상치
    - 기준: 2022년 1월 이전 또는 오늘 날짜 이후
    - 개수: 0개

![Alt text](/review_analysis/plots/myrealtrip_date_dist.png)

### TripDotCom
1. Rating Distribution (별점 분포)
- 특징: 5점 리뷰가 압도적으로 많아 전반적으로 긍정적인 평가가 주를 이룸.
- 이상치: 별점 범위(1~5)를 벗어난 리뷰는 존재하지 않음.

![Alt text](/review_analysis/plots/tripdotcom_rating_distribution.png)

2. Text Length Distribution (리뷰 길이 분포)
- 특징: 리뷰 길이가 60자 미만인 짧은 리뷰가 가장 많으며, 전체적으로 간결한 텍스트가 주를 이룸. 

![Alt text](/review_analysis/plots/tripdotcom_review_length_distribution.png)
- 이상치 기준: 5자 미만은 의미 없는 텍스트로 판단해 제거, 240자 초과는 Boxplot의 IQR 기준으로 상위 이상치로 간주함.
- 이상치 비율: 전체 리뷰 중 약 7.8%가 이상치로 제거됨.

![Alt text](/review_analysis/plots/tripdotcom_review_length_boxplot.png)

3. Date Distribution (날짜 분포)
- 특징: 대부분 리뷰는 최근인 2023~2025년 사이에 작성되었으며, 최신성 높은 데이터임.
- 이상치 기준: 2022년 1월 이전 또는 오늘 날짜 이후
- 이상치 개수: 약 45개
- 이상치 비율: 약 9.0%

![Alt text](/review_analysis/plots/tripdotcom_daily_review_counts.png)

4. Weekday Distribution (요일별 리뷰 수)
- 특징: 주중에 리뷰가 더 많으며 주말에는 리뷰 수가 감소하는 경향이 있음.

![Alt text](/review_analysis/plots/tripdotcom_weekday_review_counts.png)


## 전처리 및 Feature Engineering
1. 결측치 처리
- rating, date, content 컬럼에서 결측값이 존재하는 행을 제거함.
- 이 과정은 리뷰 데이터의 품질을 확보하고 후속 처리 오류를 방지하기 위함.

2. 이상치 처리
- 별점 이상치 제거: rating 값이 1~5 범위를 벗어난 경우 제거
- 날짜 이상치 제거: 리뷰 날짜가 2022.01.01 이전이거나, 오늘 이후인 경우 제거
- 리뷰 길이 이상치 제거: 너무 짧은 리뷰(5자 이하)나 너무 긴 리뷰(250자-Boxplot IQR 기반 이상치)를 제거

3. 텍스트 데이터 전처리
- 리뷰 텍스트에서 특수문자를 제거하고 줄바꿈 문자(\n)와 따옴표(") 제거
- 앞뒤 공백 제거
- 동일한 텍스트의 리뷰는 중복 제거하여 유의미한 분석이 가능하도록 정제

4. 파생 변수 생성
- weekday: 날짜(date)로부터 요일을 추출하여 요일별 분석이 가능하도록 파생변수 생성
- text_length: 리뷰 텍스트의 글자 수를 측정하여 text_length 변수로 저장

5. 토큰화 & 임베딩
- klue/bert-base 토크나이저와 모델을 불러와 임베딩 생성 준비
- 리뷰 텍스트를 최대 250개 토큰으로 제한하여 토큰화 진행
- [CLS] 토큰 임베딩을 문장 표현으로 추출 후 벡터화
- 각 리뷰에 대해 임베딩을 계산해 embedding 컬럼에 저장


## 비교분석 (시계열 기반)
- 세 개의 사이트(KakaoMap, MyRealTrip, Trip.com)에서 수집한 리뷰 데이터를 기반으로 요일별 비교분석을 수행하였으며, 주요 지표로는 리뷰 수, 평균 별점, 평균 텍스트 길이를 분석하였음.

### 요일별 리뷰 수 (weekday_review_count.png)
- 주말(토요일, 일요일)에 리뷰 수가 상대적으로 많고, 평일에는 리뷰 활동이 줄어드는 경향이 나타남.
- 이는 관광 및 여가 활동이 주말에 집중되는 일반적인 사용자 행동 패턴을 반영함.

![Alt text](/review_analysis/plots/weekday_review_count.png)


### 요일별 평균 별점 (weekday_avg_rating.png)
- MyRealTrip, Trip.com 사이트의 경우 평균 별점이 요일별로 비슷하게 나타났으며, 평일보다 주말에 평균 별점이 소폭 높게 나타남.
- KakaoMap 사이트의 경우 평균 별점이 요일별 차이가 뚜렷하게 나타났으며, 주말에 평균 별점이 낮게 나타남.

![Alt text](/review_analysis/plots/weekday_avg_rating.png)


### 요일별 평균 리뷰 길이 (weekday_avg_length.png)
- KakaoMap, MyRealTrip 사이트의 경우 평균 텍스트 길이가 월요일과 토요일에 다소 길고, 화요일에 가장 짧은 경향을 보임.
- Trip.com 사이트의 경우 평균 텍스트 길이가 수요일에 가장 긴 경향을 보임.

![Alt text](/review_analysis/plots/weekday_avg_length.png)

## 비교분석 (텍스트 기반)
- 본 분석에서는 KakaoMap, MyRealTrip, TripDotcom 세 사이트에서의 콘텐츠를 기반으로 상위 키워드의 빈도수를 비교하고, 각 플랫폼의 키워드 특성을 시각적으로 분석하였음.
### 사이트별 상위 키워드 등장 횟수
- TripDotcom은 대부분의 키워드에서 높은 빈도를 보여, 콘텐츠 양이 가장 많음.
- MyRealTrip은 바로, 입장, 사용, 패스 등 실용적인 키워드 중심.
- KakaoMap은 사람, 월드, 사랑 등 감성 표현이나 장소 리뷰가 강조됨.

![Alt text](/review_analysis/plots/비교분석_topkeyword.png)


### 키워드 사용 경향 비교
- KakaoMap: 감성 중심 (추억, 처음, 진짜)과 장소 중심 키워드.
- MyRealTrip: 티켓, 이용, 할인, 구매 등 이용 및 가격 정보에 집중.
- TripDotcom: 놀이기구, 아이, 가족, 추천 등 가족 단위 방문자와 체험 중심 키워드 다수.

![Alt text](/review_analysis/plots/비교분석_wordcloud.png)

## GIT 과제 이미지 첨부
- Branch protection

![Alt text](/github/branch_protection.png)
- Push rejected

![Alt text](/github/push_rejected.png)
- Review and merged

![Alt text](/github/review_and_merged.png)

## API 실행 결과 캡처

- 회원가입 API (`/api/user/register`)
  
  ![](register.png)

- 로그인 API (`/api/user/login`)
  
  ![](login.png)

- 비밀번호 변경 API (`/api/user/update-password`)
  
  ![](update-password.png)

- 회원 삭제 API (`/api/user/delete`)
  
  ![](delete.png)

- 리뷰 전처리 API (`/api/review/preprocess/{site_name}`)
  
  ![](preprocess.png)
