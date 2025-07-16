from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:

    def __init__(self, userRepoitory: UserRepository) -> None:
        self.repo = userRepoitory


    def login(self, user_login: UserLogin) -> User:
        """
        사용자 로그인 처리
        
        Parameters:
        user_login (UserLogin): 로그인 요청 정보 (email, password)
        
        Returns:
        User: 로그인 성공 시 사용자 정보
        
        Raises:
        ValueError: 사용자 정보가 없거나 비밀번호가 일치하지 않는 경우
        """

        user = self.repo.get_user_by_email(user_login.email)
        if not user:
            raise ValueError("User not Found.")
        if user.password != user_login.password:
            raise ValueError("Invalid ID/PW")
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
        """
        사용자 비밀번호 업데이트
        
        Parameters:
        user_update (UserUpdate): 비밀번호 업데이트 요청 정보 (email, new_password)
        
        Returns:
        User: 업데이트된 사용자 정보
        
        Raises:
        ValueError: 사용자가 존재하지 않는 경우
        """

        updated_user = None
        user = self.repo.get_user_by_email(user_update.email)
        if user is None:
            raise ValueError("User not found.")
        user.password = user_update.new_password
        updated_user = self.repo.update_user(user)
        return updated_user
    
    
    


        