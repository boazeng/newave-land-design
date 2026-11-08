from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from services import auth_service

router = APIRouter()


class GoogleLogin(BaseModel):
    credential: str


def _is_https(request: Request) -> bool:
    proto = request.headers.get('x-forwarded-proto') or request.url.scheme
    return proto == 'https'


@router.get('/config')
def config():
    return {'google_client_id': auth_service.client_id()}


@router.post('/google')
def login_google(body: GoogleLogin, request: Request, response: Response):
    try:
        user = auth_service.verify_google_credential(body.credential)
    except auth_service.AuthError as e:
        raise HTTPException(status_code=403, detail=str(e))
    response.set_cookie(
        auth_service.COOKIE_NAME,
        auth_service.make_session(user),
        max_age=auth_service.SESSION_MAX_AGE,
        httponly=True,
        secure=_is_https(request),
        samesite='lax',
        path='/',
    )
    return user


@router.get('/me')
def me(request: Request):
    user = auth_service.read_session(request.cookies.get(auth_service.COOKIE_NAME))
    if not user:
        raise HTTPException(status_code=401, detail='לא מחובר')
    return user


@router.post('/logout')
def logout(response: Response):
    response.delete_cookie(auth_service.COOKIE_NAME, path='/')
    return {'ok': True}
