from fastapi import APIRouter

from app.api.dependencies import get_repo, get_whatsapp_adapter
from app.models.schemas import WhatsAppInbound

router = APIRouter(prefix='/webhooks', tags=['webhooks'])


@router.post('/whatsapp/mock')
def whatsapp_mock_webhook(payload: WhatsAppInbound):
    repo = get_repo()
    repo.save_message(payload.user_id, 'user', payload.message)
    result = get_whatsapp_adapter().handle_message(payload.user_id, payload.message)
    repo.save_message(payload.user_id, 'assistant', result.get('reply', ''))
    repo.add_audit_log(None, 'whatsapp_inbound', {'user_id': payload.user_id, 'type': result.get('type')})
    return result
