# 🧠 NDD Risk Calculator API Documentation

## 🚀 Quick Start for Frontend Integration

### Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔐 Authentication

The API uses JWT Bearer token authentication for protected endpoints.

### Step 1: Get Access Token

```javascript
// Login to get JWT token
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    api_key: 'your-api-key-from-backend-team'
  })
});

const data = await response.json();
const token = data.access_token;

// Store token securely (e.g., in memory or sessionStorage)
sessionStorage.setItem('authToken', token);
```

### Step 2: Use Token for Protected Endpoints

```javascript
// Include token in Authorization header
const token = sessionStorage.getItem('authToken');

const response = await fetch('http://localhost:8000/api/v1/stats', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## 📡 Public Endpoints (No Auth Required)

### 1. Make Prediction
**POST** `/api/v1/predict`

```javascript
const response = await fetch('http://localhost:8000/api/v1/predict', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    responses: [true, false, true, ...], // 40 boolean values
    age: 8,
    sex: "M" // or "F"
  })
});

const result = await response.json();
// Result: {
//   probability: 0.35,
//   risk_level: "Medium",
//   confidence: 0.78,
//   interpretation: "Riesgo moderado...",
//   estimated_risk: "35.00%",
//   status: "success"
// }
```

### 2. Submit Evaluation (Save to Database)
**POST** `/api/v1/submit`

```javascript
const response = await fetch('http://localhost:8000/api/v1/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    edad: 8,
    sexo: "M",
    respuestas: [true, false, true, ...], // 40 boolean values
    acepto_consentimiento: true
  })
});

const result = await response.json();
// Result: {
//   success: true,
//   message: "Evaluación guardada exitosamente",
//   evaluation_id: 123,
//   prediction: { ... },
//   timestamp: "2024-01-15T10:30:00"
// }
```

### 3. Get Public Statistics
**GET** `/api/v1/stats/public`

```javascript
const response = await fetch('http://localhost:8000/api/v1/stats/public');
const stats = await response.json();
// Result: {
//   total_evaluations_processed: 150,
//   system_status: "operational",
//   model_version: "1.0.0",
//   last_update: "2024-01-15T10:30:00"
// }
```

## 🔒 Protected Endpoints (Auth Required)

### 1. Get All Evaluations
**GET** `/api/v1/evaluaciones`

Query Parameters:
- `limit`: Number of results (default: 100)
- `offset`: Skip results (default: 0)

```javascript
const response = await fetch('http://localhost:8000/api/v1/evaluaciones?limit=10&offset=0', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const evaluations = await response.json();
// Returns array of evaluation summaries
```

### 2. Get Evaluation Details
**GET** `/api/v1/evaluaciones/{id}`

```javascript
const response = await fetch('http://localhost:8000/api/v1/evaluaciones/123', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const evaluation = await response.json();
// Returns complete evaluation with all 40 responses
```

### 3. Get Detailed Statistics
**GET** `/api/v1/stats`

```javascript
const response = await fetch('http://localhost:8000/api/v1/stats', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const stats = await response.json();
// Result: {
//   total_evaluations: 150,
//   risk_distribution: {
//     high_risk: 15,
//     medium_risk: 45,
//     low_risk: 90
//   },
//   gender_distribution: {
//     male: 80,
//     female: 70
//   },
//   demographics: {
//     average_age: 8.5
//   }
// }
```

## 🎯 React Integration Example

### API Service Class

```javascript
// services/api.js
class NDDApiService {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    this.token = null;
  }

  async login(apiKey) {
    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey })
    });
    
    if (!response.ok) throw new Error('Login failed');
    
    const data = await response.json();
    this.token = data.access_token;
    return data;
  }

  async predict(responses, age, sex) {
    const response = await fetch(`${this.baseURL}/api/v1/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ responses, age, sex })
    });
    
    if (!response.ok) throw new Error('Prediction failed');
    return response.json();
  }

  async submitEvaluation(data) {
    const response = await fetch(`${this.baseURL}/api/v1/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) throw new Error('Submit failed');
    return response.json();
  }

  async getStats() {
    if (!this.token) throw new Error('Not authenticated');
    
    const response = await fetch(`${this.baseURL}/api/v1/stats`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    if (!response.ok) throw new Error('Failed to get stats');
    return response.json();
  }
}

export default new NDDApiService();
```

### React Hook Example

```javascript
// hooks/useNDDApi.js
import { useState } from 'react';
import api from '../services/api';

export const useNDDPrediction = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const predict = async (responses, age, sex) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await api.predict(responses, age, sex);
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { predict, loading, error, result };
};
```

## ⚠️ CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:3000` (React development)
- `http://localhost:8080` (Alternative port)

For production, update the `CORS_ORIGINS` in the backend `.env` file.

## 🐛 Error Handling

All endpoints return consistent error responses:

```javascript
// 400 Bad Request
{
  "detail": "Validation error: Expected exactly 40 responses"
}

// 401 Unauthorized
{
  "error": "Unauthorized",
  "message": "Authentication required",
  "how_to_authenticate": { ... }
}

// 500 Internal Server Error
{
  "error": "Internal Server Error",
  "message": "Error details...",
  "timestamp": "2024-01-15T10:30:00"
}
```

## 📝 Environment Variables for React

Create `.env` in your React project:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_KEY=your-api-key-from-backend
```

## 🧪 Testing the Integration

1. Start the backend: `uvicorn app.main:app --reload`
2. Check API docs: http://localhost:8000/docs
3. Test with the provided `test_auth_api.py` script
4. Integrate with your React components

## 💡 Tips

1. **Token Storage**: Store JWT tokens in memory or sessionStorage, not localStorage
2. **Token Refresh**: Tokens expire after 30 minutes, implement refresh logic
3. **Error Boundaries**: Wrap API calls in try-catch blocks
4. **Loading States**: Show loading indicators during API calls
5. **Validation**: Validate the 40 responses on frontend before sending

## 📞 Need Help?

- API Documentation: `/docs`
- Health Check: `/health`
- Backend Team: [Your contact]