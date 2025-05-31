"""
SQLAlchemy model for storing user evaluations in the database.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from app.database import Base

class Evaluacion(Base):
    """
    Model to store neurodevelopmental disorder risk evaluations.
    
    This model stores all the information from user evaluations including:
    - User demographics (age, sex)
    - SCQ questionnaire responses (40 boolean answers)
    - Risk estimation result
    - Consent and timestamp information
    """
    
    __tablename__ = "evaluaciones"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User demographics
    sexo = Column(String(10), nullable=False, comment="User's sex (M/F)")
    edad = Column(Integer, nullable=False, comment="User's age")
    
    # SCQ questionnaire responses (40 boolean values)
    # Using JSON for SQLite compatibility, can be changed to ARRAY for PostgreSQL
    respuestas = Column(JSON, nullable=False, comment="40 SCQ questionnaire responses as boolean array")
    
    # Risk estimation result
    riesgo_estimado = Column(Float, nullable=False, comment="Estimated risk probability (0.0 to 1.0)")
    
    # Consent and metadata
    acepto_consentimiento = Column(Boolean, nullable=False, default=False, comment="User consent acceptance")
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Evaluation timestamp")
    
    def __repr__(self):
        return f"<Evaluacion(id={self.id}, edad={self.edad}, sexo='{self.sexo}', riesgo={self.riesgo_estimado:.3f})>"
    
    def to_dict(self):
        """
        Convert the model instance to a dictionary for JSON serialization.
        """
        return {
            "id": self.id,
            "sexo": self.sexo,
            "edad": self.edad,
            "respuestas": self.respuestas,
            "riesgo_estimado": self.riesgo_estimado,
            "acepto_consentimiento": self.acepto_consentimiento,
            "fecha": self.fecha.isoformat() if self.fecha else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Create an Evaluacion instance from a dictionary.
        """
        return cls(
            sexo=data.get("sexo"),
            edad=data.get("edad"),
            respuestas=data.get("respuestas"),
            riesgo_estimado=data.get("riesgo_estimado"),
            acepto_consentimiento=data.get("acepto_consentimiento", False)
        )