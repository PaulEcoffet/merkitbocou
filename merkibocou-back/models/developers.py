from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from database import Base


class Developer(Base):
    __tablename__ = "developers"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(
        String(50),  # Limite la longueur à 50 caractères
        unique=True,
        index=True,
        nullable=False
    )
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    instant_messages = Column(Boolean, default=True)  # Messages envoyés immédiatement
    instant_thank_you = Column(Boolean, default=False)  # Merci envoyés toutes les 5 min
    summary_frequency = Column(
        String(20),  # "daily", "weekly", "none"
        default="daily"
    )
    last_summary_sent = Column(DateTime, nullable=False, default=func.now(), index=True)  # Date du dernier résumé envoyé

    # Relations
    projects = relationship("Project", back_populates="developer")