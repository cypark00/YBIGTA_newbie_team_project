from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:
    def __init__(self, userRepoitory: UserRepository) -> None:
        self.repo = userRepoitory

    def login(self, user_login: UserLogin) -> User:
        ## TODO #로그인 기능 구현 
        user = None
        return user
        
    def register_user(self, new_user: User) -> User:
        """
        새로운 사용자 등록 
        Parameters: 
        new_user: 등록할 사용자 정보 (email, password, username)
        
        Returns: 
        User: 등록된 사용자 정보 

        Raises: 
        ValueError: 이미 해당 이메일의 사용자가 존재하는 경우 
        """
        existing_user = self.repo.get_user_by_email(new_user.email)
        if existing_user: 
            raise ValueError("User already Exists")
        
        self.repo.save_user(new_user)
        return new_user
    

    def delete_user(self, email: str) -> User:
        ## TODO        
        deleted_user = None
        return deleted_user

    def update_user_pwd(self, user_update: UserUpdate) -> User:
        ## TODO
        updated_user = None
        return updated_user
        