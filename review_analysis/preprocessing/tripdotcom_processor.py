from review_analysis.preprocessing.base_processor import BaseDataProcessor
import pandas as pd
import os
import re
from datetime import datetime
from transformers import BertTokenizer

class TripDotComProcessor(BaseDataProcessor):
    def __init__(self, input_path: str, output_path: str):
        super().__init__(input_path, output_path)
        self.df = pd.read_csv(input_path, encoding='utf-8')

    def preprocess(self):
        # 컬럼 남기기
        self.df = self.df[["rating", "date", "content"]]
        
        # 결측치 제거
        self.df.dropna(subset=["rating", "date", "content"], inplace=True)

        # 별점 범위 이상치 제거
        self.df = self.df[self.df["rating"].between(1, 5)]

        # 날짜 범위 이상치 제거
        today = datetime.today()
        self.df["date"] = pd.to_datetime(self.df["date"])
        self.df = self.df[(self.df["date"] >= pd.Timestamp("2022-01-01")) & (self.df["date"] <= today)]

        # 특수문자 제거
        self.df["content"] = self.df["content"].apply(
            lambda x: re.sub(r'[^\w\s]', '', x).replace('\n', '').replace('"', '')
        )

        # 리뷰 길이 제한
        self.df["review_length"] = self.df["content"].apply(len)
        self.df = self.df[(self.df["review_length"] > 5) & (self.df["review_length"] < 250)]

        # 공백 문자열 제거
        self.df["content"] = self.df["content"].str.strip()

        # 중복 리뷰 제거
        self.df.drop_duplicates(subset=["content"], inplace=True)
        
        # 리뷰 텍스트 토큰화
        tokenizer = BertTokenizer.from_pretrained('klue/bert-base')
        self.df['tokenized_content'] = self.df['content'].apply(
            lambda x: tokenizer.tokenize(x)[:250] if isinstance(x, str) else []
        )
            


    def feature_engineering(self):
        #날짜 -> 요일 파생 변수 생성 
        import pandas as pd
        self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")
        self.df["weekday"] = self.df["date"].dt.day_name()

        #텍스트 길이 파생 변수 생성 
        self.df["text_length"] = self.df["content"].astype(str).apply(len)




    def save_to_database(self):
        filename = f"preprocessed_{os.path.basename(self.input_path)}"
        output_path = os.path.join(self.output_dir, filename)
        self.df.to_csv(output_path, index=False)
        print(f"[INFO] 저장 완료: {output_path}")
