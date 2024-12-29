import logging
from typing import List, Annotated

from fastapi import FastAPI, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_jwt import JwtAccessBearer

import models.projects
from config import settings

from crud import crud
from database import AsyncSessionLocal, engine, Base
from schemas.schemas import DeveloperCreate, DeveloperResponse, DeveloperUpdatePreference, ProjectSummaryResponse, \
    ProjectResponse, ProjectDetailsResponse, MessageCreate, ProjectCreate, MessageOut, ThankYouClickCreate, ThankYouOut, \
    DeveloperLogin
from services.mailing import send_summary_mail_to_all

app = FastAPI()

auth = JwtAccessBearer(secret_key=settings.jwt_secret_key)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def startup_event():
    await init_db()


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/dashboard.html")

# ---- ROUTES ----


# DEVELOPERS
@app.post("/developers/", response_model=DeveloperResponse)
async def register_developer(developer: DeveloperCreate, db: AsyncSession = Depends(get_db)):
    """
    Route pour enregistrer un nouveau développeur.
    """
    existing_dev = await crud.get_developer_by_username(db, developer.username)
    if existing_dev:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un développeur avec ce nom existe déjà."
        )

    return await crud.create_developer(db, developer)


@app.post("/developers/login/")
async def login_developer(developer: DeveloperLogin, db: AsyncSession = Depends(get_db)):
    """
    Route pour connecter un développeur et générer un JWT.
    """
    dev = await crud.authenticate_developer(db, developer.username, developer.password)
    if not dev:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect."
        )

    token = auth.create_access_token({"sub": developer.username, "id": dev.id})
    return {"access_token": token, "token_type": "bearer"}


# PROJECTS
@app.post("/projects/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate, db: AsyncSession = Depends(get_db), user=Depends(auth)
):
    """
    Route pour créer un nouveau projet.
    """
    developer_id = user["id"]
    existing_project = await crud.get_project_by_name_and_developer(db, project.name, developer_id)
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un projet avec ce nom existe déjà. Veuillez en choisir un autre."
        )

    return await crud.create_project(db, developer_id, project)


@app.get("/projects/", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), user=Depends(auth)):
    """
    Route pour lister tous les projets d'un développeur.
    """
    developer_id = user["id"]
    return await crud.get_projects_by_developer(db, developer_id)


@app.get("/projects/{project_id}/stats/")
async def project_stats(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(auth)
) -> ProjectSummaryResponse:
    """
    Route pour récupérer les statistiques d'un projet.
    """
    developer_id = user["id"]
    project: models.projects.Project = await crud.verify_project_ownership(db, project_id, developer_id)

    total_clicks = await crud.get_total_clicks_for_project(db, project.id)
    messages = await crud.get_messages_for_project(db, project.id)

    return ProjectSummaryResponse(
        project_name=project.name,
        dev_id=project.developer_id,
        total_clicks=total_clicks,
        messages=messages,
    )


@app.get("/projects/summary/", response_model=List[ProjectSummaryResponse])
async def project_summary(db: AsyncSession = Depends(get_db), user=Depends(auth)) -> List[ProjectSummaryResponse]:
    """
    Retourne le résumé de tous les projets d'un développeur :
    - Total de clics
    - Dernier message envoyé
    """
    developer_id = user["id"]
    # Récupère tous les projets du développeur
    projects = await crud.get_projects_by_developer(db, developer_id)

    summaries: list[ProjectSummaryResponse] = []
    for project in projects:
        total_clicks = await crud.get_total_clicks_for_project(db, project.id)
        last_message = await crud.get_last_message_for_project(db, project.id)
        logging.warning(f"{total_clicks}, {last_message}")
        summaries.append(ProjectSummaryResponse(
            id=project.id,
            name=project.name,
            dev_id=project.developer_id,
            total_clicks=total_clicks,
            last_message=last_message
        ))
    return summaries


@app.get("/projects/{project_id}/details/", response_model=ProjectDetailsResponse)
async def project_details(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(auth)
):
    """
    Retourne les détails d'un projet :
    - 10 dernières sessions de clics (avec user_id et timestamp)
    - 10 derniers messages (avec contenu, user_id et timestamp)
    """
    developer_id = user["id"]

    # Vérifie que le développeur est propriétaire du projet
    project = await crud.verify_project_ownership(db, project_id, developer_id)

    # Récupère les 10 dernières sessions de clics
    recent_clicks: list[ThankYouOut] = await crud.get_recent_clicks_for_project(db, project.id, limit=10)

    # Récupère les 10 derniers messages
    recent_messages = await crud.get_recent_messages_for_project(db, project.id, limit=10)

    return ProjectDetailsResponse(
        id=project.id,
        name=project.name,
        dev_id=project.developer_id,
        recent_clicks=recent_clicks,
        recent_messages=recent_messages
    )


# THANK YOU
@app.post("/thank-you/")
async def thank_you(click: ThankYouClickCreate, db: AsyncSession = Depends(get_db)):
    """
    Route pour enregistrer un clic sur un projet.
    """
    try:
        return await crud.create_thank_you_click(db=db, click=click)
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"Le projet {click.project_name} n'existe pas.")


# MESSAGES
@app.post("/send-message/")
async def send_message(message: MessageCreate, db: AsyncSession = Depends(get_db)):
    """
    Route pour envoyer un message à un projet.
    """
    try:
        return await crud.create_message(db=db, message=message)
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"Le projet {message.project_name} n'existe pas.")


#### CRON OPERATION

@app.get("/triggerwebcron")
async def trigger_cron(secret: Annotated[str, Query()], background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    if secret != settings.cron_secret_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Hophophop c’est interdit ici pour toi")
    else:
        background_tasks.add_task(send_summary_mail_to_all, db)
    return True