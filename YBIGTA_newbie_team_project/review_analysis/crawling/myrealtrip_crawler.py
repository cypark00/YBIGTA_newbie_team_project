from base_crawler import BaseCrawler
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
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.base_url = 'https://www.myrealtrip.com/offers/70816'
        self.driver = None
        
    def start_browser(self):
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
                
        reviews = []

        # 리뷰 더보기 버튼 여러 번 클릭
        for i in range(100):
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, "button.mrt-button.css-i2nbjs")
                button.click()
                time.sleep(1)
            except Exception as e:
                print(f"{i}번째 클릭 실패: {e}")
                break  # 더 이상 클릭할 버튼이 없으면 종료

        # 현재 페이지의 HTML 소스 파싱
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

        return reviews
            
    def save_to_database(self):
        reviews = self.scrape_reviews()
        output_path = os.path.join(self.output_dir, "reviews_myrealtrip.csv")
        pd.DataFrame(reviews).to_csv(output_path, index=False)        
        
