from fastapi import APIRouter
from app.schemas.request import InputData
from app.models.predictor import load_model, predict_risk

router = APIRouter()
model = load_model()

@router.post("/predict")
def predict(data: InputData):
    result = predict_risk(model, data)
    return {"estimated_risk": f"{result*100:.2f}%"}
