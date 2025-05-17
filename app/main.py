from fastapi import FastAPI
from app.routes.predict import router as predict_router

app = FastAPI(title="Neurodevelopmental Disorders Risk Calculator")
app.include_router(predict_router)
