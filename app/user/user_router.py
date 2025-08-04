from fastapi import APIRouter, HTTPException, Depends, status
from typing import Any
from app.user.user_schema import User, UserLogin, UserUpdate, UserDeleteRequest
from app.user.user_service import UserService
from app.dependencies import get_user_service
from app.responses.base_response import BaseResponse

user = APIRouter(prefix="/api/user")


@user.post("/login", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def login_user(user_login: UserLogin, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    try:
        user = service.login(user_login)
        return BaseResponse(status="success", data=user, message="Login Success.") 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

#라우팅 연결 
@user.post("/register", response_model=BaseResponse[User], status_code=status.HTTP_201_CREATED)
def register_user(user: User, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    새로운 사용자 등록 
    
    Parameters: 
    - user : 클라이언트가 보낸 사용자 정보 
    - service : 

    Returns: 
    - BaseRespons : 등록된 사용자 정보를 포함한 응답 

    Raises: 
    - HTTPException 400 : 이메일이 이미 존재할 경우 
    """
    try: 
        new_user = service.register_user(user)
        return BaseResponse(
            status = "success",
            data=new_user, 
            message = "User registeration success."
        )
    except ValueError as e: 
        raise HTTPException(status_code=400, detail=str(e))
    


@user.delete("/delete", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def delete_user(user_delete_request: UserDeleteRequest, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    
    try:
        deleted_user = service.delete_user(user_delete_request.email)
        return BaseResponse(        
            status="success",
            message="User Deletion Success",
            data=deleted_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@user.put("/update-password", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def update_user_password(user_update: UserUpdate, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    사용자 비밀번호 변경 API
    
    Parameters:
    user_update (UserUpdate): 비밀번호 업데이트 요청 정보 (email, new_password)
    service (UserService): 사용자 서비스 의존성 주입
    
    Returns:
    BaseResponse[User]: 비밀번호가 성공적으로 업데이트된 사용자 정보와 성공 메시지
    
    Raises:
    HTTPException: 사용자 정보가 없거나 비밀번호 업데이트에 실패한 경우 (status code 404)
    """
    try:
        updated_user = service.update_user_pwd(user_update)
        return BaseResponse(status="success", data=updated_user, message="User password updated successfully.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
