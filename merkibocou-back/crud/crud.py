import logging
from datetime import timedelta
import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound, IntegrityError
from passlib.hash import bcrypt

from models.projects import Project
from models.messages import Message
from models.developers import Developer
from models.thank_you_clicks import ThankYouClick
from schemas import schemas
from schemas.schemas import ThankYouOut, MessageOut, ProjectMailSummary, DeveloperMailSummaryResponse, ProjectResponse, \
    DeveloperDetailedResponse


# ---- DEVELOPERS ----

async def create_developer(db: AsyncSession, developer: schemas.DeveloperCreate):
    """
    Crée un nouveau développeur avec un mot de passe hashé.
    """
    hashed_password = bcrypt.hash(developer.password)
    dev = Developer(username=developer.username, hashed_password=hashed_password, email=developer.email)
    db.add(dev)
    await db.commit()
    await db.refresh(dev)
    return dev


async def authenticate_developer(db: AsyncSession, username: str, password: str):
    """
    Authentifie un développeur en vérifiant son mot de passe.
    """
    result = await db.execute(select(Developer).filter(Developer.username == username))
    dev = result.scalars().first()
    if dev and bcrypt.verify(password, dev.hashed_password):
        return dev
    return None


async def get_developer_by_username(db: AsyncSession, username: str):
    """
    Récupère un développeur par son nom d'utilisateur.
    """
    result = await db.execute(select(Developer).filter(Developer.username == username))
    return result.scalars().first()

async def get_developer_by_id(db: AsyncSession, id: int) -> DeveloperDetailedResponse:
    """
    Récupère un développeur par son nom d'utilisateur.
    """
    result = await db.execute(select(Developer).filter(Developer.id == id))
    dev: Developer = result.scalars().first()
    return DeveloperDetailedResponse(id=dev.id, username=dev.username, email=dev.email,
                                     instant_messages=dev.instant_messages, instant_thank_you=dev.instant_thank_you,
                                     summary_frequency=dev.summary_frequency, last_summary_sent=dev.last_summary_sent)


# ---- PROJECTS ----

async def create_project(db: AsyncSession, developer_id: int, project: schemas.ProjectCreate):
    """
    Crée un nouveau projet pour un développeur.
    """
    new_project = Project(name=project.name, developer_id=developer_id)
    db.add(new_project)
    try:
        await db.commit()
        await db.refresh(new_project)
        return ProjectResponse(id=new_project.id, name=new_project.name, dev_id=new_project.developer_id)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un projet avec ce nom existe déjà pour ce développeur."
        )


async def get_project_by_id(db: AsyncSession, project_id: int):
    """
    Récupère un projet par son ID.
    """
    result = await db.execute(select(Project).filter(Project.id == project_id))
    return result.scalars().first()


async def get_project_by_name_and_developer(db: AsyncSession, project_name: str, developer_id: int):
    """
    Récupère un projet par son nom et son développeur.
    """
    result = await db.execute(
        select(Project).filter(
            Project.name == project_name,
            Project.developer_id == developer_id
        )
    )
    return result.scalars().first()


async def get_projects_by_developer(db: AsyncSession, developer_id: int):
    """
    Récupère tous les projets d'un développeur donné.
    """
    result = await db.execute(select(Project).filter(Project.developer_id == developer_id))
    return result.scalars().all()


# ---- THANK YOU CLICKS ----

async def create_thank_you_click(db: AsyncSession, click: schemas.ThankYouClickCreate):
    """
    Enregistre un clic "merci" pour un projet donné.
    """
    project = await get_project_by_name_and_developer(db, click.project_name, click.dev_id)
    if not project:
        raise NoResultFound(f"Le projet '{click.project_name}' est introuvable.")
    thank_you_click = ThankYouClick(
        count=click.count,
        user_id=click.user_id,
        project_id=project.id,
    )
    db.add(thank_you_click)
    await db.commit()
    await db.refresh(thank_you_click)
    return thank_you_click


# ---- MESSAGES ----

async def create_message(db: AsyncSession, message: schemas.MessageCreate):
    """
    Enregistre un message pour un projet donné.
    """
    project = await get_project_by_name_and_developer(db, message.project_name, message.dev_id)
    if not project:
        raise NoResultFound(f"Le projet '{message.project_name}' de {message.dev_id} est introuvable.")
    msg = Message(
        content=message.content,
        user_id=message.user_id,
        project_id=project.id,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


# ---- STATISTICS ----

async def get_total_clicks_for_project(db: AsyncSession, project_id: int):
    """
    Récupère le nombre total de clics pour un projet donné.
    """
    result = await db.execute(
        select(ThankYouClick.count).filter(ThankYouClick.project_id == project_id)
    )
    return sum(result.scalars().all())


async def get_messages_for_project(db: AsyncSession, project_id: int):
    """
    Récupère tous les messages pour un projet donné.
    """
    result = await db.execute(
        select(Message.content).filter(Message.project_id == project_id)
    )
    return result.scalars().all()


async def verify_project_ownership(db: AsyncSession, project_id: int, developer_id: int):
    """
    Vérifie qu'un développeur est le propriétaire d'un projet.
    """
    project = await get_project_by_id(db, project_id)
    if not project or project.developer_id != developer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à accéder à ce projet."
        )
    return project


async def get_last_message_for_project(db: AsyncSession, project_id: int):
    """
    Récupère le dernier message pour un projet donné.
    """
    result = await db.execute(
        select(Message).filter(Message.project_id == project_id).order_by(
            Message.timestamp.desc()
        ).limit(1)
    )
    message = result.scalars().first()
    if message:
        return {"content": message.content, "user_id": message.user_id, "timestamp": message.timestamp}
    return None


async def get_recent_clicks_for_project(db: AsyncSession, project_id: int, limit: int = 10) -> list[ThankYouOut]:
    """
    Récupère les dernières sessions de clics pour un projet donné.
    """
    result = await db.execute(
        select(ThankYouClick).filter(ThankYouClick.project_id == project_id).order_by(
            ThankYouClick.timestamp.desc()
        ).limit(limit)
    )
    return [
        ThankYouOut(count=click.count, user_id=click.user_id, timestamp=click.timestamp)
        for click in result.scalars().all()
    ]


async def get_recent_messages_for_project(db: AsyncSession, project_id: int, limit: int = 10) -> list[MessageOut]:
    """
    Récupère les derniers messages pour un projet donné.
    """
    result = await db.execute(
        select(Message).filter(Message.project_id == project_id).order_by(
            Message.timestamp.desc()
        ).limit(limit)
    )
    return [
        MessageOut(content=message.content, user_id=message.user_id, timestamp=message.timestamp)
        for message in result.scalars().all()
    ]


async def get_messages_not_yet_summarized_grouped_by_project(session: AsyncSession):
    now = datetime.datetime.now(datetime.UTC)
    daily_limit = now - timedelta(hours=23, minutes=31)
    two_weeks_ago = now - timedelta(weeks=2)
    weekly_limit = now - timedelta(days=6, hours=23, minutes=31)

    stmt = (
        select(
            Developer.id.label("developer_id"),
            Developer.username.label("developer_username"),
            Developer.email.label("developer_email"),
            Project.id.label("project_id"),
            Project.name.label("project_name"),
            Message.id.label("message_id"),
            Message.user_id.label("message_user_id"),
            Message.content.label("message_content"),
            Message.timestamp.label("message_date")
        )
        .join(
            Project,
            and_(
                Developer.id == Project.developer_id,
                Developer.summary_frequency != "none"  # Exclure ceux avec "none"
            )
        )
        .join(
            Message,
            and_(
                Project.id == Message.project_id,
                Message.timestamp > two_weeks_ago  # Exclure les messages vieux de plus de deux semaines
            )
        )
        # .filter(
        #     case(
        #         (Developer.summary_frequency == "daily", Developer.last_summary_sent < daily_limit),
        #         (Developer.summary_frequency == "weekly", Developer.last_summary_sent < weekly_limit),
        #     )
        # )
        .filter(Message.timestamp > Developer.last_summary_sent)
        .order_by(Developer.id, Project.id, desc(Message.timestamp))
    )
    result = await session.execute(stmt)
    rows = result.fetchall()
    grouped_data = {}
    for row in rows:
        dev_id = row.developer_id
        project_id = row.project_id
        if dev_id not in grouped_data:
            grouped_data[dev_id] = {
                "developer_username": row.developer_username,
                "developer_email": row.developer_email,
                "projects": {}
            }
        if project_id not in grouped_data[dev_id]["projects"]:
            grouped_data[dev_id]["projects"][project_id] = {
                "project_name": row.project_name,
                "messages": []
            }
        grouped_data[dev_id]["projects"][project_id]["messages"].append({
            "user_id": row.message_user_id,
            "content": row.message_content,
            "date": row.message_date
        })
    return grouped_data


async def get_thank_you_clicks_not_yet_summarized_grouped_by_project(session: AsyncSession):
    now = datetime.datetime.now(datetime.UTC)
    daily_limit = now - timedelta(hours=23, minutes=31)
    two_weeks_ago = now - timedelta(weeks=2)
    weekly_limit = now - timedelta(days=6, hours=23, minutes=31)

    stmt = (
        select(
            Developer.id.label("developer_id"),
            Developer.username.label("developer_username"),
            Developer.email.label("developer_email"),
            Project.id.label("project_id"),
            Project.name.label("project_name"),
            ThankYouClick.id.label("thank_you_id"),
            ThankYouClick.user_id.label("thank_you_user_id"),
            ThankYouClick.count.label("thank_you_count"),
            ThankYouClick.timestamp.label("thank_you_date")
        )
        .join(
            Project,
            and_(
                Developer.id == Project.developer_id,
                Developer.summary_frequency != "none"  # Exclure ceux avec "none"
            )
        )
        .join(
            ThankYouClick,
            and_(
                Project.id == ThankYouClick.project_id,
                ThankYouClick.timestamp > two_weeks_ago  # Exclure les messages vieux de plus de deux semaines
            )
        )
        # .filter(
        #     case(
        #         (Developer.summary_frequency == "daily", Developer.last_summary_sent < daily_limit),
        #         (Developer.summary_frequency == "weekly", Developer.last_summary_sent < weekly_limit),
        #     )
        # )
        .filter(ThankYouClick.timestamp > Developer.last_summary_sent)
        .order_by(Developer.id, Project.id, desc(ThankYouClick.timestamp))
    )
    result = await session.execute(stmt)
    rows = result.fetchall()

    grouped_data = {}
    for row in rows:
        dev_id = row.developer_id
        project_id = row.project_id
        if dev_id not in grouped_data:
            grouped_data[dev_id] = {
                "developer_username": row.developer_username,
                "developer_email": row.developer_email,
                "projects": {}
            }
        if project_id not in grouped_data[dev_id]["projects"]:
            grouped_data[dev_id]["projects"][project_id] = {
                "project_name": row.project_name,
                "thank_you_clicks": []
            }
        grouped_data[dev_id]["projects"][project_id]["thank_you_clicks"].append({
            "user_id": row.thank_you_user_id,
            "count": row.thank_you_count,
            "date": row.thank_you_date
        })
    return grouped_data

async def get_developer_summary_mails_to_send(db: AsyncSession):
    messages_data = await get_messages_not_yet_summarized_grouped_by_project(db)
    thank_you_data = await get_thank_you_clicks_not_yet_summarized_grouped_by_project(db)

    # Étape 2 : Construire les DeveloperMailSummaryResponse
    mails_to_send_data = []
    for dev_id, dev_data in messages_data.items():
        projects = []

        for project_id, project_data in dev_data["projects"].items():
            # Construire un résumé de projet avec messages et clics
            recent_clicks = (
                thank_you_data.get(dev_id, {}).get("projects", {}).get(project_id, {}).get("thank_you_clicks", [])
            )
            projects.append(ProjectMailSummary(
                id=project_id,
                name=project_data["project_name"],
                recent_messages=[
                    MessageOut(
                        user_id=msg["user_id"],
                        content=msg["content"],
                        timestamp=msg["date"],
                    )
                    for msg in project_data["messages"]
                ],
                recent_clicks=[
                    ThankYouOut(
                        user_id=click["user_id"],
                        count=click["count"],
                        timestamp=click["date"],
                    )
                    for click in recent_clicks
                ],
            ))

        mails_to_send_data.append(DeveloperMailSummaryResponse(
            username=dev_data["developer_username"],
            email=dev_data["developer_email"],
            projects=projects
        ))
    return mails_to_send_data
