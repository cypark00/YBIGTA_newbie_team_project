import os
import time
import csv
import re
import random
from selenium import webdriver
from selenium.webdriver.common.by import By        
from selenium.webdriver.chrome.options import Options       
from selenium.webdriver.chrome.service import Service       
from selenium.common.exceptions import NoSuchElementException  
from webdriver_manager.chrome import ChromeDriverManager
from review_analysis.crawling.base_crawler import BaseCrawler


class KlookCrawler(BaseCrawler):
    def __init__(self, output_dir: str): 
        super().__init__(output_dir)
        self.base_url = 'https://www.klook.com/ko/activity/45338-lotte-world-ticket-seoul/?utm_campaign=kr_sem_nb_activity-10-13-south-korea-seoul_ao_ko-kr_aid_landing_45338_sem_B&utm_source=naver&utm_medium=cpc&utm_content=45338&utm_term=%EB%A1%AF%EB%8D%B0%EC%9B%94%EB%93%9C&n_media=27758&n_query=%EB%A1%AF%EB%8D%B0%EC%9B%94%EB%93%9C&n_rank=3&n_ad_group=grp-a001-01-000000016632292&n_ad=nad-a001-01-000000396363269&n_keyword_id=nkw-a001-01-000007187936480&n_keyword=%EB%A1%AF%EB%8D%B0%EC%9B%94%EB%93%9C&n_campaign_type=1&n_ad_group_type=1&n_match=1&NaPm=ct%3Dmd77l849%7Cci%3DER623cc531-62f3-11f0-b046-8abc338c5865%7Ctr%3Dsa%7Chk%3D69aaf2e9283e4a7b806dc2a59c652838a52d8fce%7Cnacn%3DwkTLBkQdYLSP'
        self.reviews = [] 

    def start_browser(self): 
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_argument("user-agent=Mozilla/5.0")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.implicitly_wait(3)

        self.driver.get(self.base_url)
        time.sleep(3) 

    def scrape_reviews(self):
        self.start_browser()
        print("크롤링 시작")

        try: 
            sort_button = self.driver.find_element(By.CSS_SELECTOR, "span.review-filter_sort-btn-text")
            sort_button.click() 
            time.sleep(1)
            latest_option = self.driver.find_element(By.XPATH, "//li[contains(text(), '최신순')]") 
            latest_option.click()
            time.sleep(2) 
            print("최신순 정렬 완료")
            
        except Exception as e:
            print("최신순 정렬 실패")

        while len(self.reviews) < 500: 
            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.review-card.review-detail__card")

            for card in cards[len(self.reviews):]:
                try: 
                    rating = card.find_element(By.CSS_SELECTOR, "span.user-rating__rating ").text.strip() 
                    date = card.find_element(By.CSS_SELECTOR, "div.user-info__rating-time").text.strip()
                    content = card.find_element(By.CSS_SELECTOR, "div.review-card__review-content").text.strip()

                    if rating and date and content: 
                        self.reviews.append({
                            "rating": rating, 
                            "date": date, 
                            "content": content
                        })
                    if len(self.reviews) >= 500: 
                        break 

                except Exception: 
                    continue

            try: 
                next_button = self.driver.find_element(By.CSS_SELECTOR, "span.klk-pagination-next-btn")
                self.driver.execute_script("arguments[0].click();", next_button)
            except NoSuchElementException:
                print("더 이상 다음 페이지 없음")
                break 
            except Exception as e: 
                print("다음 페이지 이동 실패", e)
                break 

        self.driver.quit()
        print(f"총 수집 리뷰 수: {len(self.reviews)}")



    def save_to_database(self): 
        os.makedirs(self.output_dir, exist_ok=True)
        save_path = os.path.join(self.output_dir, "reviews_klook.csv")

        with open(save_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames = ["rating", "date", "content"])
            writer.writeheader()
            writer.writerows(self.reviews)

        print(f"저장 완료: {save_path}")



                                    
