from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:
    def __init__(self, userRepoitory: UserRepository) -> None:
        self.repo = userRepoitory

    def login(self, user_login: UserLogin) -> User:
        # 이메일로 사용자를 조회하기
        user = self.repo.get_user_by_email(user_login.email)
        # 사용자가 존재하지 않으면 오류 발생
        if not user:
            raise ValueError("User not Found.")
        # 비밀번호가 일치하지 않으면 오류 발생
        if user.password != user_login.password:
            raise ValueError("Invalid ID/PW")
        # 이메일과 비밀번호가 모두 일치하면 사용자 정보 반환
        return user
        
    def register_user(self, new_user: User) -> User:
        ## TODO
        new_user = None
        return new_user

    def delete_user(self, email: str) -> User:
        ## TODO        
    def delete_user(self, email: str) -> User:
        ## TODO
        '''
        사용자 삭제
        Parameters:
            email: 삭제할 사용자의 이메일 주소
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

    def update_user_pwd(self, user_update: UserUpdate) -> User:
        # 반환할 사용자 객체를 초기화
        updated_user = None
        # 이메일로 사용자를 조회하기
        user = self.repo.get_user_by_email(user_update.email)
        # 사용자가 존재하지 않으면 오류 발생
        if user is None:
            raise ValueError("User not found.")
        # 비밀번호를 새 비밀번호로 업데이트
        user.password = user_update.new_password
        # 변경된 정보를 저장하고 저장된 사용자 객체 반환
        updated_user = self.repo.update_user(user)
        # 업데이트된 사용자 객체 반환
        return updated_user
        
