import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Simulate binary responses
X = np.random.randint(0, 2, size=(150, 40))
y = np.random.randint(0, 2, size=150)

# Train model
clf = RandomForestClassifier()
clf.fit(X, y)

# Save model locally (compatible with your environment)
with open("data/modelo_entrenado.pkl", "wb") as f:
    pickle.dump(clf, f)

print("✅ Model saved and ready.")
