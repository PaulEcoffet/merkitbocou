from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List

from crud.crud import get_developer_summary_mails_to_send
from schemas.schemas import DeveloperMailSummaryResponse

conf = ConnectionConfig(
    MAIL_USERNAME = "username",
    MAIL_PASSWORD = "**********",
    MAIL_FROM = "test@email.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "mail server",
    MAIL_FROM_NAME="Desired Name",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    SUPPRESS_SEND = 1
)


async def send_summary_mail_to_all(db: AsyncSession):
    from jinja2 import Environment, FileSystemLoader

    # Initialiser l'environnement avec un dossier de templates
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('mail.html.j2')
    mails_to_send_data: list[DeveloperMailSummaryResponse] = await get_developer_summary_mails_to_send(db)
    fm = FastMail(conf)

    for mail_data in mails_to_send_data:
        print(mail_data.dict())
        print(template.render(mail_data.dict()))
    #await fm.send_message(message)
