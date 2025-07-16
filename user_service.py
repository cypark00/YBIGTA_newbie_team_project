from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:
    def __init__(self, userRepoitory: UserRepository) -> None:
        self.repo = userRepoitory

    def delete_user(self, email: str) -> User:
        ## TODO
        '''
        사용자를 삭제
        Args:
            email (str): 삭제할 사용자의 이메일 주소
        Returns:
            User: 삭제된 사용자 객체

        Raises:
            ValueError: 해당 이메일의 사용자가 존재하지 않을 경우
        ''' 
        user = self.repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not Found")
        delete_user = self.repo.delete_user(user)
        return  delete_user