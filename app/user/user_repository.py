from typing import Optional
from app.user.user_schema import User
from database.mysql_connection import SessionLocal
from sqlalchemy import text
from sqlalchemy.orm import Session

class UserRepository:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session


    def get_user_by_email(self, email: str) -> Optional[User]:
        # users 테이블에서 email로 조회
        query = text("SELECT * FROM users WHERE email = :email")
        result = self.db.execute(query, {"email": email}).fetchone()
        if result:
            return User(email=result[0], password=result[1], username=result[2])
        return None


    def save_user(self, user: User) -> User:
        # 이미 존재하면 update, 없으면 insert
        exist = self.get_user_by_email(user.email)
        if exist:
            query = text("""
                UPDATE users SET password=:password, username=:username WHERE email=:email
            """)
        else:
            query = text("""
                INSERT INTO users (email, password, username) VALUES (:email, :password, :username)
            """)
        self.db.execute(query, user.dict())
        self.db.commit()
        return user


    def delete_user(self, user: User) -> User:
        query = text("DELETE FROM users WHERE email = :email")
        self.db.execute(query, {"email": user.email})
        self.db.commit()
        return user

