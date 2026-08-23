import secrets
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .config import API_USERNAME, API_PASSWORD, SWAGGER_USERNAME, SWAGGER_PASSWORD

security_api = HTTPBasic(auto_error=False)
security_swagger = HTTPBasic()

UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Basic"}

def verify_api_credentials(credentials: HTTPBasicCredentials = Depends(security_api)):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide Basic Auth credentials.",
        )
    correct_user = secrets.compare_digest(credentials.username.encode("utf-8"), API_USERNAME.encode("utf-8")) if API_USERNAME else False
    correct_pass = secrets.compare_digest(credentials.password.encode("utf-8"), API_PASSWORD.encode("utf-8")) if API_PASSWORD else False
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API credentials",
        )
    return credentials.username

def verify_swagger_credentials(credentials: HTTPBasicCredentials = Depends(security_swagger)):
    correct_user = secrets.compare_digest(credentials.username.encode("utf-8"), SWAGGER_USERNAME.encode("utf-8")) if SWAGGER_USERNAME else False
    correct_pass = secrets.compare_digest(credentials.password.encode("utf-8"), SWAGGER_PASSWORD.encode("utf-8")) if SWAGGER_PASSWORD else False
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Swagger credentials",
            headers=UNAUTHORIZED_HEADERS,
        )
    return credentials.username