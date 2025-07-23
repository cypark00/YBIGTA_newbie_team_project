from review_analysis.crawling.base_crawler import BaseCrawler
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import csv
import time
from typing import List, Tuple


class KakaoMapCrawler(BaseCrawler):
    def __init__(self, output_dir: str): 
        super().__init__(output_dir)
        self.base_url = 'https://place.map.kakao.com/27560699#comment'
        self.reviews : List[Tuple[str,str,str]] = []
        self.driver = None

    def start_browser(self): 
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.base_url)
        time.sleep(3)
    
    def scrape_reviews(self):
        if self.driver is None:
            self.start_browser()
        print("크롤링 시작")

        scroll_count = 0
        seen_reviews = set()
        collected = 0 
    


        while collected < 500:
                time.sleep(1.5)
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                review_items = soup.select("ul.list_review > li")
                print(f"[스크롤 {scroll_count}] 현재 review_items 수: {len(review_items)}")
                
                if not review_items:
                    print("리뷰 항목 없음. 페이지 구조 확인 필요.")
                    break

                for item in review_items:
                    try: 
                        stars = item.select("span.figure_star.on")
                        rating = str(len(stars))
                        
                        date_tag = item.select_one("span.txt_date")
                        content_tag = item.select_one("p.desc_review")

                        if not (rating and date_tag and content_tag): 
                            continue

                        review = (rating, date_tag.text.strip(), content_tag.text.strip())
                        if review not in seen_reviews:
                            self.reviews.append(review)
                            seen_reviews.add(review)
                            collected += 1
                            print(f"{len(self.reviews)}번째 리뷰 수집됨")


                        if collected >= 500:
                            break

                    except Exception as e:
                        print(f"리뷰 파싱 중 오류 발생: {e}")
                        continue

                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                scroll_count += 1
                time.sleep(2.5)


        self.driver.quit()
        print(f"총 수집된 리뷰 수: {len(self.reviews)}개")

                

    def save_to_database(self): 
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "reviews_kakaomap.csv")

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["rating", "date", "content"])
            writer.writerows(self.reviews)

        print(f"저장 완료: {output_path}")
        



                                    
