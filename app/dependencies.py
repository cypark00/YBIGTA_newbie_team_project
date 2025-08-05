from fastapi import Depends
from app.user.user_repository import UserRepository
from app.user.user_service import UserService
from database.mysql_connection import SessionLocal
from sqlalchemy.orm import Session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_repository(db: Session = Depends(get_db)):  # 이렇게 변경
    return UserRepository(db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)
