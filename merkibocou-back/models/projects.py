from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(100),  # Limite la longueur à 100 caractères
        unique=False,
        index=True,
        nullable=False
    )
    developer_id = Column(Integer, ForeignKey("developers.id"), nullable=False, index=True)

    # Relations
    developer = relationship("Developer", back_populates="projects")
    thank_you_clicks = relationship("ThankYouClick", back_populates="project")
    messages = relationship("Message", back_populates="project")

    __table_args__ = (
        UniqueConstraint('name', 'developer_id', name='unique_project_name_per_developer'),
    )
