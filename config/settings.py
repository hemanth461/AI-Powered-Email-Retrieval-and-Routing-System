"""
Central application configuration.

All secrets and environment-specific values are loaded from a `.env` file
(see .env.example) using pydantic-settings. Nothing sensitive should ever
be hard-coded here.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- PostgreSQL ----
    database_url: str = "postgresql+psycopg2://triage_user:triage_pass@localhost:5432/email_triage"

    # ---- Gmail API ----
    gmail_credentials_path: str = "credentials/gmail_credentials.json"
    gmail_token_path: str = "credentials/gmail_token.json"
    gmail_monitored_account: str = "emailroutingretrieval@gmail.com"

    # ---- Department routing addresses ----
    dept_sales_email: str = "salesroutingretrieval@gmail.com"
    dept_support_email: str = "support@company.com"
    dept_billing_email: str = "billingroutingretrieval@gmail.com"
    dept_hr_email: str = "hrroutingretrieval@gmail.com"
    dept_it_email: str = "itroutingretrieval@gmail.com"
    dept_legal_email: str = "legal@company.com"
    dept_complaint_email: str = "escalations@company.com"
    dept_general_email: str = "emailroutingretrieval@gmail.com"

    # ---- Backend ----
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_base_url: str = "http://localhost:8000"

    # ---- Frontend ----
    frontend_port: int = 8501

    # ---- Polling / automation ----
    poll_interval_seconds: int = 60
    auto_routing_enabled: bool = True

    # ---- Logging ----
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
