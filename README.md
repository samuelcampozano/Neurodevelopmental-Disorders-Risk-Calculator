# Neurodevelopmental Disorders Risk Calculator

This project is a professional-grade backend service developed using **FastAPI**, designed to predict the risk level of neurodevelopmental disorders based on responses to the SCQ (Social Communication Questionnaire).

## 👨‍⚕️ Purpose

This API receives binary responses to 40 SCQ questions and returns a probability score estimating the risk level.

## 🛠️ Technologies Used

- **FastAPI** (web framework)
- **scikit-learn** (machine learning)
- **pydantic** (data validation)
- **uvicorn** (ASGI server)
- **numpy** (data manipulation)

## ▶️ How to Run

```bash
git clone https://github.com/your_username/Neurodevelopmental-Disorders-Risk-Calculator.git
cd Neurodevelopmental-Disorders-Risk-Calculator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
./run.sh
```

## 🔁 Sample Request

**POST /predict**

```json
{
  "responses": [1, 0, 1, 1, 0, ..., 1]  # 40 binary values
}
```

## 🧪 Testing

Unit test can be added in the `tests/` folder to validate the endpoint behavior.

---

Developed by **Samuel Campozano Lopez** as a part of a real-world ML project deployment.
