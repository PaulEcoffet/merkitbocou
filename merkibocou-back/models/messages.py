from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(
        Text(5000),
        nullable=False
    )
    user_id = Column(
        String(50),  # Limite la longueur à 50 caractères
        nullable=False
    )
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    # Relations
    project = relationship("Project", back_populates="messages")
