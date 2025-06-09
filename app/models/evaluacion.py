"""
SQLAlchemy model for storing user evaluations in the database.
Fixed version with proper column handling.
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
    
    # User demographics - Using Spanish names as primary
    sexo = Column(String(10), nullable=False, comment="User's sex (M/F)")
    edad = Column(Integer, nullable=False, comment="User's age")
    
    # SCQ questionnaire responses (40 boolean values)
    # Using JSON for SQLite compatibility
    respuestas = Column(JSON, nullable=False, comment="40 SCQ questionnaire responses as boolean array")
    
    # Risk estimation result
    riesgo_estimado = Column(Float, nullable=False, comment="Estimated risk probability (0.0 to 1.0)")
    
    # Consent and metadata
    acepto_consentimiento = Column(Boolean, nullable=False, default=False, comment="User consent acceptance")
    
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Evaluation timestamp")

    def __init__(self, **kwargs):
        """
        Initialize with support for both English and Spanish field names.
        """
        # Map English field names to Spanish if provided
        field_mapping = {
            'sex': 'sexo',
            'age': 'edad', 
            'responses': 'respuestas',
            'estimated_risk': 'riesgo_estimado',
            'consent_accepted': 'acepto_consentimiento'
        }
        
        # Convert English fields to Spanish
        mapped_kwargs = {}
        for key, value in kwargs.items():
            if key in field_mapping:
                mapped_kwargs[field_mapping[key]] = value
            else:
                mapped_kwargs[key] = value
        
        # Call parent constructor
        super().__init__(**mapped_kwargs)
    
    # Properties for English aliases
    @property
    def sex(self):
        return self.sexo
    
    @sex.setter
    def sex(self, value):
        self.sexo = value
    
    @property
    def age(self):
        return self.edad
    
    @age.setter
    def age(self, value):
        self.edad = value
    
    @property
    def responses(self):
        return self.respuestas
    
    @responses.setter
    def responses(self, value):
        self.respuestas = value
    
    @property
    def estimated_risk(self):
        return self.riesgo_estimado
    
    @estimated_risk.setter
    def estimated_risk(self, value):
        self.riesgo_estimado = value
    
    @property
    def consent_accepted(self):
        return self.acepto_consentimiento
    
    @consent_accepted.setter
    def consent_accepted(self, value):
        self.acepto_consentimiento = value
    
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
            "fecha": self.fecha.isoformat() if self.fecha else None,
            # English aliases for compatibility
            "sex": self.sexo,
            "age": self.edad,
            "responses": self.respuestas,
            "estimated_risk": self.riesgo_estimado,
            "consent_accepted": self.acepto_consentimiento
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Create an Evaluacion instance from a dictionary.
        Supports both English and Spanish field names.
        """
        return cls(
            sexo=data.get("sexo") or data.get("sex"),
            edad=data.get("edad") or data.get("age"),
            respuestas=data.get("respuestas") or data.get("responses"),
            riesgo_estimado=data.get("riesgo_estimado") or data.get("estimated_risk"),
            acepto_consentimiento=data.get("acepto_consentimiento", data.get("consent_accepted", False))
        )