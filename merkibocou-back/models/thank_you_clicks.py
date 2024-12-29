from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base


class ThankYouClick(Base):
    __tablename__ = "thank_you_clicks"

    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer, default=0, nullable=False)
    user_id = Column(
        String(50),  # Limite la longueur à 50 caractères
        index=True,
        nullable=False
    )
    timestamp = Column(DateTime, server_default=func.now())
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Relations
    project = relationship("Project", back_populates="thank_you_clicks")
    