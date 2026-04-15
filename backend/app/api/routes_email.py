from fastapi import APIRouter

from app.api.dependencies import get_email_service

router = APIRouter(prefix='/email', tags=['email'])


@router.post('/poll')
def poll_emails():
    """Manually trigger an email poll cycle. Returns count of emails processed."""
    count = get_email_service().poll_and_process()
    return {'processed': count}
