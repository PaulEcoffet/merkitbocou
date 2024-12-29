from typing import Annotated, List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# ---- FACTORISATION DES VALIDATIONS ----

# Contraintes communes
PROJECT_NAME_REGEX = r"^[a-zA-Z0-9_-]+$"
USER_ID_REGEX = r"^[a-zA-Z0-9_-]+$"

# Définition des types annotés réutilisables
ProjectName = Annotated[
    str,
    Field(
        min_length=3,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Nom du projet (lettres, chiffres, tirets, underscores uniquement, 3-100 caractères)."
    )
]

UserName = Annotated[
    str,
    Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Identifiant utilisateur (lettres, chiffres, tirets, underscores uniquement, 3-50 caractères)."
    )
]


# ---- THANK YOU CLICKS ----

class ThankYouClickCreate(BaseModel):
    """
    Schéma pour créer un clic "merci" associé à un projet.
    """
    project_name: ProjectName = Field(
        alias="projectName",
        description="Nom du projet (lettres, chiffres, tirets, underscores uniquement, max 100 caractères).",
    )
    dev_id: int = Field(
        alias="devId", description="id of the developper",
        ge=0,
    )
    user_id: UserName = Field(
        alias="userId",
        description="Identifiant utilisateur (lettres, chiffres, tirets, underscores uniquement, 3-50 caractères).",
    )
    count: int = Field(
        alias="clicks",
        gt=0,
        description="Nombre de clics (doit être un entier positif)."
    )

    class Config:
        populate_by_name = True


# ---- MESSAGES ----

class MessageCreate(BaseModel):
    """
    Schéma pour envoyer un message associé à un projet.
    """
    project_name: ProjectName = Field(
        alias="projectName",
        description="Nom du projet (lettres, chiffres, tirets, underscores uniquement, max 100 caractères)."
    )
    dev_id: int = Field(
        alias="devId", description="id of the developper",
        ge=0,
    )
    user_id: UserName = Field(
        alias="userId",
        description="Identifiant utilisateur (lettres, chiffres, tirets, underscores uniquement, 3-50 caractères)."
    )
    content: str = Field(
        alias="message",
        max_length=5000,
        description="Le message ne doit pas dépasser 5000 caractères."
    )

    class Config:
        populate_by_name = True


# ---- DEVELOPERS ----

class DeveloperCreate(BaseModel):
    """
    Schéma pour créer un compte développeur.
    """
    username: UserName = Field(
        description="Nom d'utilisateur (lettres, chiffres, tirets, underscores uniquement, 3-50 caractères)."
    )
    password: str = Field(
        min_length=8,
        description="Mot de passe (doit contenir au moins 8 caractères)."
    )
    email: EmailStr = Field(description="email de l'utilisateur.")


class DeveloperLogin(BaseModel):
    """
    Schéma pour créer un compte développeur.
    """
    username: UserName = Field(
        description="Nom d'utilisateur (lettres, chiffres, tirets, underscores uniquement, 3-50 caractères)."
    )
    password: str = Field(
        min_length=8,
        description="Mot de passe (doit contenir au moins 8 caractères)."
    )


class DeveloperResponse(BaseModel):
    """
    Réponse pour les informations d'un développeur.
    """
    id: int
    username: UserName

    class Config:
        from_attributes = True

class DeveloperUpdatePreference(BaseModel):
    instant_messages: Optional[bool] = Field(None, alias="instantMessages")
    instant_thank_you: Optional[bool] = Field(None, alias="instantThankYou")
    summary_frequency: Optional[Literal["weekly", "daily", "none"]] = Field(None, alias="summaryFrequency")  # ! "none" = pas de summary, None: pas d’update des pref

class Config:
        populate_by_name = True


# ---- PROJECTS ----

class ProjectCreate(BaseModel):
    """
    Schéma pour créer un projet.
    """
    name: ProjectName = Field(
        description="Nom du projet (lettres, chiffres, tirets, underscores uniquement, max 100 caractères)."
    )


class ProjectResponse(BaseModel):
    """
    Réponse pour les informations d'un projet.
    """
    id: int
    name: ProjectName
    dev_id: int

    class Config:
        from_attributes = True


class ProjectSummaryResponse(BaseModel):
    id: int
    name: str
    dev_id: int
    total_clicks: int = Field(serialization_alias="totalClicks")
    last_message: dict|None = Field(serialization_alias="lastMessage", default_factory=dict)  # Dictionnaire contenant le contenu, user_id et timestamp du dernier message


class MessageOut(BaseModel):
    user_id: UserName = Field(serialization_alias="userId")
    content: str = Field(serialization_alias="message")
    timestamp: datetime


class ThankYouOut(BaseModel):
    user_id: UserName = Field(serialization_alias="userId")
    count: int = Field(serialization_alias="clicks")
    timestamp: datetime


class ProjectDetailsResponse(BaseModel):
    id: int
    name: str
    dev_id: int
    recent_clicks: List[ThankYouOut] = Field(serialization_alias="recentClicks", default_factory=list)  # Liste des sessions de clics avec count, user_id et timestamp
    recent_messages: List[MessageOut] = Field(serialization_alias="recentMessages", default_factory=list)  # Liste des messages avec contenu, user_id et timestamp

    class Config:
        from_attributes = True


class ProjectMailSummary(BaseModel):
    id: int
    name: str
    recent_clicks: List[ThankYouOut]
    recent_messages: List[MessageOut]


class DeveloperMailSummaryResponse(BaseModel):
    username: str
    email: str
    projects: List[ProjectMailSummary]