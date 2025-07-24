from review_analysis.crawling.base_crawler import BaseCrawler
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
import pandas as pd
from datetime import datetime
from utils.logger import setup_logger
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

class TripDotComCrawler(BaseCrawler):
    def __init__(self, output_dir: str):
        """
        TripDotComCrawler 인스턴스를 초기화합니다.

        Args:
            output_dir (str): 출력 파일이 저장될 디렉토리 경로입니다.

        Attributes:
            logger: 크롤러 활동을 기록하는 로거 인스턴스입니다.
            base_url (str): 리뷰를 크롤링할 기본 URL입니다.
            reviews (list): 크롤링한 리뷰를 저장하는 리스트입니다.
        """
        super().__init__(output_dir)
        self.logger = setup_logger('trip_crawler.log')
        self.base_url = 'https://kr.trip.com/travel-guide/attraction/seoul/lotte-world-adventure-136469953/'
        self.reviews: list[dict] = []

    def start_browser(self):
        """
        헤드리스 Chrome 브라우저를 사용자 지정 옵션으로 초기화하고 기본 URL로 이동합니다.
        브라우저는 다음과 같은 옵션으로 구성됩니다:
            - 백그라운드 작업을 위한 헤드리스 모드
            - GPU 가속 비활성화
            - 호환성을 위한 No sandbox 모드
            - 한국어 언어 설정
            - 요청 헤더를 위한 사용자 지정 user-agent 문자열
        초기화 후 브라우저는 지정된 기본 URL로 이동하며, 페이지 로드를 위해 3초간 대기합니다.
        반환값:
            없음
        """
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--lang=ko-KR")
        # 사용자 에이전트 추가
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.base_url)
        time.sleep(3)

    def scrape_reviews(self):
        """
        Selenium WebDriver를 사용하여 Trip.com에서 리뷰를 크롤링합니다.
        사용 가능한 필터 버튼을 반복하여 각 필터에 대한 리뷰를 수집합니다.
        각 필터에 대해 페이지가 나뉜 리뷰 목록을 탐색하며, 각 리뷰의 평점, 내용, 날짜를 추출합니다.
        중복 리뷰가 수집되지 않도록 하며, 최대 리뷰 개수에 도달하면 중단합니다.
        요소 상호작용 및 파싱 중 발생하는 예외를 처리하고, 관련 경고 및 정보를 로깅합니다.
        크롤링이 완료되면 브라우저를 종료합니다.
        반환값:
            없음
        부작용:
            - self.reviews에 'rating', 'content', 'date', 'filter_index'를 포함하는 딕셔너리 추가
            - self.logger를 통해 진행 상황 및 경고 로그 기록
            - Selenium WebDriver 브라우저 시작 및 종료
        """
        max_reviews = 500
        self.start_browser()

        filter_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div.switch-item")
        collected_contents = set()

        for idx, button in enumerate(filter_buttons):
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                self.driver.execute_script("arguments[0].click();", button)
                self.logger.info(f"[필터 클릭] data-index={idx} 번째 필터 클릭")
                time.sleep(2)
            except Exception as e:
                self.logger.warning(f"[필터 클릭 실패] {e}")
                continue

            # 페이지 순회
            while True:
                review_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.TripReviewItemContainer-sc-1fopyhi-0.review-item")
                if not review_cards:
                    self.logger.warning("리뷰 요소를 찾을 수 없습니다.")
                    break

                last_review_text = review_cards[-1].text.strip()
                previous_count = len(self.reviews)

                for card in review_cards:
                    try:
                        rating = card.find_element(By.CLASS_NAME, "review_score").text.strip()
                        content = card.find_element(By.CSS_SELECTOR, "p.hover-pointer").text.strip()
                        raw_date = card.find_element(By.CSS_SELECTOR, "span.r.c2.create-time").text.strip()

                        date = raw_date
                        if "작성일" in raw_date:
                            try:
                                date_str = raw_date.replace("작성일:", "").strip()
                                date_obj = datetime.strptime(date_str, "%Y년 %m월 %d일")
                                date = date_obj.strftime("%Y.%m.%d")
                            except:
                                pass

                        if content in collected_contents:
                            continue

                        self.reviews.append({
                            "rating": rating,
                            "content": content,
                            "date": date,
                            "filter_index": idx
                        })
                        collected_contents.add(content)

                        if len(self.reviews) >= max_reviews:
                            break

                    except Exception as e:
                        self.logger.warning(f"리뷰 파싱 실패: {e}")
                        continue

                current_count = len(self.reviews)
                new_collected = current_count - previous_count
                self.logger.info(f"[페이지 수집] {new_collected}개의 리뷰를 수집했습니다. 현재 총 {current_count}개")
                
                if len(self.reviews) >= max_reviews:
                    break

                try:
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#reviews button.btn-next"))
                    )
                    if "disabled" in next_button.get_attribute("class"):
                        self.logger.info("더 이상 다음 페이지가 없습니다.")
                        break

                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", next_button)

                    WebDriverWait(self.driver, 10).until(
                        lambda d: d.find_elements(By.CSS_SELECTOR, "div.TripReviewItemContainer-sc-1fopyhi-0.review-item")[-1].text.strip() != last_review_text
                    )
                    time.sleep(1)

                except Exception as e:
                    self.logger.warning(f"다음 페이지 버튼 클릭 실패: {e}")
                    break

            if len(self.reviews) >= max_reviews:
                break

        self.driver.quit()
        self.logger.info(f"총 {len(self.reviews)}개의 리뷰를 수집했습니다.")


    def save_to_database(self):
        """
        수집된 리뷰를 지정된 출력 디렉토리에 CSV 파일로 저장합니다.

        출력 디렉토리가 존재하지 않으면 생성하고, 리뷰를 'rating', 'date', 'content' 컬럼을 가진 pandas DataFrame으로 변환한 뒤
        'reviews_tripdotcom.csv' 파일로 저장합니다. 저장된 리뷰 개수와 파일 경로를 로깅합니다.

        반환값:
            없음
        """
        os.makedirs(self.output_dir, exist_ok=True)
        df = pd.DataFrame(self.reviews)[["rating", "date", "content"]]
        save_path = os.path.join(self.output_dir, 'reviews_tripdotcom.csv')
        df.to_csv(save_path, index=False)
        self.logger.info(f"{len(self.reviews)}개의 리뷰가 저장되었습니다 → {save_path}")

