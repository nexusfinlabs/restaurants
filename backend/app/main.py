import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_email import router as email_router
from app.api.routes_menu import router as menu_router
from app.api.routes_reservations import router as reservations_router
from app.api.routes_webhooks import router as webhooks_router
from app.api.routes_whatsapp_live import router as wa_live_router
from app.config import settings

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / 'static'


async def _email_poller() -> None:
    """Background task: poll IMAP every N seconds for new emails."""
    from app.api.dependencies import get_email_service

    interval = settings.email_poll_interval
    if not settings.imap_email:
        logger.info('IMAP email not configured — email poller disabled')
        return

    logger.info('Email poller started (interval=%ds, inbox=%s)', interval, settings.imap_email)

    while True:
        try:
            service = get_email_service()
            count = service.poll_and_process()
            if count:
                logger.info('Email poller processed %d emails', count)
        except Exception:
            logger.exception('Email poller error')

        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Startup / shutdown hooks."""
    task = asyncio.create_task(_email_poller())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title=settings.app_name, version='0.2.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])


@app.get('/health')
def health():
    return {
        'status': 'ok',
        'environment': settings.environment,
        'email_polling': bool(settings.imap_email),
    }


app.include_router(webhooks_router)
app.include_router(reservations_router)
app.include_router(menu_router)
app.include_router(email_router)
app.include_router(wa_live_router)

# ── Serve the Nómada frontend ──────────────────────────────────────
if STATIC_DIR.exists():
    app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')

    @app.get('/')
    def serve_index():
        return FileResponse(str(STATIC_DIR / 'index.html'))

