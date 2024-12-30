from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List

from crud.crud import get_developer_by_id, get_developer_summary_mails_to_send, get_project_by_name_and_developer
from schemas.schemas import DeveloperDetailedResponse, DeveloperMailSummaryResponse, MessageCreate, ThankYouClickCreate
from jinja2 import Environment, FileSystemLoader
from config import settings 

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=settings.mail_validate_certs,
)


# Initialiser l'environnement avec un dossier de templates
env = Environment(loader=FileSystemLoader('templates'))


async def mail_message_to_dev(message: MessageCreate, dev: DeveloperDetailedResponse):
    template = env.get_template("instant_message.html.j2")
    rendered_html = template.render({'username': dev.username, 'project': message.project_name, 'message': message.model_dump()})
    fm = FastMail(conf)
    mail = MessageSchema(
        subject=f"Nouveau message pour {message.project_name} avec Merkit Bocou",
        recipients=[dev.email],
        body=rendered_html,
        subtype=MessageType.html
    )
    await fm.send_message(mail)


async def send_instant_thank_you_notification(db: AsyncSession, click: ThankYouClickCreate):
    """
    Envoie un email instantané de remerciement si activé par le développeur.
    """
    dev: DeveloperDetailedResponse = await get_developer_by_id(db, click.dev_id)
    if dev.instant_thank_you:
        # Récupérer le projet
        project = await get_project_by_name_and_developer(db, click.project_name, click.dev_id)

        # Construire le contenu du mail
        template = env.get_template("instant_thank_you.html.j2")
        rendered_html = template.render({
            "username": dev.username,
            "project_name": project.name,
            "thank_you": click.model_dump()
        })

        # Préparer et envoyer le mail
        fm = FastMail(conf)
        mail = MessageSchema(
            subject=f"Merci reçu pour {project.name} avec Merkit Bocou",
            recipients=[dev.email],
            body=rendered_html,
            subtype=MessageType.html
        )
        await fm.send_message(mail)


async def send_summary_mail_to_all(db: AsyncSession):
    template = env.get_template('summary_mail.html.j2')
    mails_to_send_data: list[DeveloperMailSummaryResponse] = await get_developer_summary_mails_to_send(db)
    fm = FastMail(conf)

    for mail_data in mails_to_send_data:
        rendered_html = template.render(mail_data.model_dump())
        
        # Créer le message
        message = MessageSchema(
            subject="Résumé MerkitBocou",
            recipients=[mail_data.email],  # Utiliser l'email du développeur
            body=rendered_html,
            subtype=MessageType.html  # Indique qu'on envoie un email HTML
        )
        # Envoyer le message
        await fm.send_message(message)

