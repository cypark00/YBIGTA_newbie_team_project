from review_analysis.crawling.base_crawler import BaseCrawler
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import time
import os

class MyRealTripCrawler(BaseCrawler):
    """
    마이리얼트립 웹사이트에서 특정 상품의 리뷰를 크롤링하는 클래스.
    
    Attributes:
        base_url (str): 크롤링 대상 마이리얼트립 상품의 URL
        driver (webdriver): Selenium 웹드라이버 인스턴스
    """

    def __init__(self, output_dir: str):
        """
        MyRealTripCrawler 클래스의 생성자.
        
        Args:
            output_dir (str): 크롤링한 리뷰 데이터를 저장할 디렉토리 경로
        """
        super().__init__(output_dir)
        self.base_url = 'https://www.myrealtrip.com/offers/70816'
        self.driver = None
        
    def start_browser(self):
        """
        Chrome 웹드라이버를 설정하고 브라우저를 시작한 후,
        크롤링 대상 URL로 이동함.
        """
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        self.driver.get(self.base_url)
        self.driver.implicitly_wait(3)
        
        try:
            self.driver.maximize_window()
        except:
            pass
    
    def scrape_reviews(self):
        """
        리뷰 페이지를 탐색하며 사용자 리뷰 데이터를 수집함.
        최대 100번 '더보기' 버튼 클릭을 시도하고, 최대 500개의 리뷰를 수집함.

        Returns:
            list of tuples: (rating, date, text) 형태의 리뷰 데이터 리스트
        """
        reviews = []

        # 리뷰 더보기 버튼 여러 번 클릭
        for i in range(100):
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, "button.mrt-button.css-i2nbjs")
                button.click()
                time.sleep(1)
            except Exception as e:
                print(f"{i}번째 클릭 실패: {e}")
                break

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        data_rows = soup.find_all('div', class_='offer-review__list--content')

        for i, row in enumerate(data_rows):
            if i >= 500:
                break

            # 별점 계산
            rating = 0
            stars = row.find('div', class_='starRating starRating--m starRating--blue starRating--')
            if stars:
                stars_ = stars.find_all('svg')
                for star in stars_:
                    path = star.find('path')
                    if path and path.get('fill') == "#51ABF3":
                        rating += 1

            # 날짜
            date_div = row.find('div', class_='offer-review__list--purpose')
            texts = list(date_div.stripped_strings)
            date = texts[-1] if texts else ""
            
            # 리뷰 내용
            text = ""
            wrapper = row.find('div', class_='offer-review__list--wrapper')
            if not wrapper:
                wrapper = row.find('div', class_='offer-review__list--photo-wrapper')
            
            if wrapper:
                msg_div = wrapper.find('div', class_='offer-review__list--message')
                if msg_div:
                    more_div = msg_div.find('div', class_='with-more')
                    if more_div:
                        text = more_div.get_text('\n', strip=True)

            reviews.append((rating, date, text))

        return pd.DataFrame(reviews, columns=['rating','date','content'])
            
    def save_to_database(self):
        """
        리뷰를 크롤링하고 지정된 디렉토리에 CSV 파일로 저장함.
        """
        reviews = self.scrape_reviews()
        output_path = os.path.join(self.output_dir, "reviews_myrealtrip.csv")
        pd.DataFrame(reviews).to_csv(output_path, encoding='utf-8-sig')