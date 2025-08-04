from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

import os
from dotenv import load_dotenv

load_dotenv()

user = os.environ["DB_USER"]
passwd = os.environ["DB_PASSWORD"]
host = os.environ["DB_HOST"]
port = os.environ["DB_PORT"]
db = os.environ["DB_NAME"]

DB_URL = f'mysql+pymysql://{user}:{passwd}@{host}:{port}/{db}?charset=utf8'

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
