from review_analysis.preprocessing.base_processor import BaseDataProcessor

class ExampleProcessor(BaseDataProcessor):
    def __init__(self, input_path: str, output_path: str):
        super().__init__(input_path, output_path)

    def preprocess(self):
        pass
    
    def feature_engineering(self):
        #날짜 -> 요일 파생 변수 생성 
        import pandas as pd
        self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")
        self.df["weekday"] = self.df["date"].dt.day_name()

        #텍스트 길이 파생 변수 생성 
        self.df["text_length"] = self.df["content"].astype(str).apply(len)




    def save_to_database(self):
        pass
