import pickle
import numpy as np

def load_model():
    with open("data/modelo_entrenado.pkl", "rb") as f:
        return pickle.load(f)

def predict_risk(model, data):
    X = np.array(data.responses).reshape(1, -1)
    return float(model.predict_proba(X)[0][1])
