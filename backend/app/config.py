from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR.parent.parent / '.env'), str(BASE_DIR / '.env')),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    app_name: str = 'Restaurants Reservation API'
    environment: str = 'development'
    api_host: str = '0.0.0.0'
    api_port: int = 8090

    restaurants_db_path: str = str(BASE_DIR / 'data' / 'restaurants.db')

    ollama_base_url: str = 'http://localhost:11434'
    ollama_model: str = 'llama3.2:1b'

    google_calendar_id: str = ''
    google_credentials_path: str = ''
    google_application_credentials: str = ''

    stripe_secret_key: str = ''
    stripe_webhook_secret: str = ''
    stripe_currency: str = 'eur'

    # IMAP inbound (email polling)
    imap_server: str = 'imap.ionos.es'
    imap_email: str = ''
    imap_password: str = ''

    # Resend outbound (email replies)
    resend_api_key: str = ''
    reply_from_email: str = ''
    notification_email: str = ''

    # Restaurant identity
    restaurant_name: str = 'Nexus Lounge'

    # Email polling interval (seconds)
    email_poll_interval: int = 60


settings = Settings()
