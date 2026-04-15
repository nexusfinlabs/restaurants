from fastapi import APIRouter

from app.api.dependencies import get_llm_service
from app.models.schemas import MenuQuestionRequest, MenuQuestionResponse

router = APIRouter(prefix='/menu', tags=['menu'])


@router.post('/ask', response_model=MenuQuestionResponse)
def ask_menu(payload: MenuQuestionRequest):
    answer = get_llm_service().ask_menu(payload.question)
    return MenuQuestionResponse(answer=answer)
