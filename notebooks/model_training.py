"""
Smart Home Energy Efficiency — Random Forest Classification
Dataset : ENB2012 (UCI Energy Efficiency)
Target  : Cooling Load → 3 classes (Low / Medium / High energy)
Model   : RandomForestClassifier with hyperparameter tuning via GridSearchCV
"""

import os
import urllib.request
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")          # non-interactive backend (safe for scripts)
import matplotlib.pyplot as plt

from sklearn.ensemble          import RandomForestClassifier
from sklearn.model_selection   import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing     import StandardScaler, LabelEncoder
from sklearn.metrics           import (
    accuracy_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay
)

# ── 1. Dataset ────────────────────────────────────────────────────────────────
DATA_PATH = "data/raw/ENB2012_data.xlsx"
DATA_URL  = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "00242/ENB2012_data.xlsx"
)

os.makedirs("data/raw",      exist_ok=True)
os.makedirs("backend/models", exist_ok=True)
os.makedirs("data/outputs",   exist_ok=True)

if not os.path.exists(DATA_PATH):
    print("Downloading ENB2012 dataset from UCI...")
    urllib.request.urlretrieve(DATA_URL, DATA_PATH)
    print(f"  Saved to {DATA_PATH}")
else:
    print(f"Dataset found: {DATA_PATH}")

# ── 2. Load & clean ───────────────────────────────────────────────────────────
df = pd.read_excel(DATA_PATH)
df.dropna(how="all", inplace=True)
df = df.loc[:, df.notna().any()]

print(f"\nDataset shape : {df.shape}")
print(f"Columns       : {list(df.columns)}")

# Rename columns for clarity (ENB2012 standard names)
feature_names = [
    "Relative_Compactness", "Surface_Area", "Wall_Area", "Roof_Area",
    "Overall_Height", "Orientation", "Glazing_Area", "Glazing_Area_Distribution"
]
target_col = df.columns[-1]   # Cooling Load (Y2)

X = df.iloc[:, :8].copy()
X.columns = feature_names

# ── 3. Target engineering — 3-class classification ───────────────────────────
# Bin Cooling Load into Low / Medium / High using equal-frequency (quantile) bins
# so each class has roughly equal samples → avoids class imbalance
y_raw = df[target_col]
y, bin_edges = pd.qcut(y_raw, q=3, labels=[0, 1, 2], retbins=True)
y = y.astype(int)

label_map = {0: "Low Energy", 1: "Medium Energy", 2: "High Energy"}
print(f"\nClass distribution:")
for cls, name in label_map.items():
    print(f"  Class {cls} ({name}): {(y == cls).sum()} samples")
print(f"Bin edges (Cooling Load): {bin_edges.round(2)}")

# ── 4. Train / test split ─────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain size : {len(X_train)}  |  Test size : {len(X_test)}")

# ── 5. Feature scaling ────────────────────────────────────────────────────────
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

# ── 6. Baseline Random Forest ─────────────────────────────────────────────────
print("\n--- Baseline Random Forest ---")
rf_base = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
rf_base.fit(X_train_sc, y_train)
base_acc = accuracy_score(y_test, rf_base.predict(X_test_sc))
print(f"Baseline test accuracy : {base_acc:.4f}")

# ── 7. Hyperparameter tuning (GridSearchCV) ───────────────────────────────────
print("\n--- GridSearchCV tuning (this may take ~30s) ---")
param_grid = {
    "n_estimators":      [100, 200],
    "max_depth":         [None, 10, 20],
    "min_samples_split": [2, 5],
    "max_features":      ["sqrt", "log2"],
}
grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42, n_jobs=-1),
    param_grid,
    cv=5,
    scoring="accuracy",
    n_jobs=-1,
    verbose=0,
)
grid_search.fit(X_train_sc, y_train)
best_params = grid_search.best_params_
print(f"Best params  : {best_params}")
print(f"Best CV acc  : {grid_search.best_score_:.4f}")

# ── 8. Final model ────────────────────────────────────────────────────────────
model = grid_search.best_estimator_
y_pred = model.predict(X_test_sc)

test_acc = accuracy_score(y_test, y_pred)
print(f"\nFinal test accuracy : {test_acc:.4f}")

# 5-fold cross-validation on full dataset
cv_scores = cross_val_score(model, scaler.transform(X), y, cv=5, scoring="accuracy")
print(f"5-fold CV accuracy  : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# ── 9. Classification report ──────────────────────────────────────────────────
print("\n--- Classification Report ---")
print(classification_report(
    y_test, y_pred,
    target_names=["Low Energy", "Medium Energy", "High Energy"]
))

# ── 10. Feature importance ────────────────────────────────────────────────────
importances = pd.Series(model.feature_importances_, index=feature_names)
importances_sorted = importances.sort_values(ascending=False)
print("--- Feature Importances ---")
for feat, imp in importances_sorted.items():
    bar = "#" * int(imp * 40)
    print(f"  {feat:<35} {imp:.4f}  {bar}")

# ── 11. Save plots ────────────────────────────────────────────────────────────
# Confusion matrix
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Random Forest — Energy Efficiency Classification", fontsize=13)

cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(cm, display_labels=["Low", "Medium", "High"])
disp.plot(ax=axes[0], colorbar=False, cmap="Blues")
axes[0].set_title("Confusion Matrix")

# Feature importance bar chart
axes[1].barh(importances_sorted.index, importances_sorted.values, color="#2dd4bf")
axes[1].set_xlabel("Importance")
axes[1].set_title("Feature Importances")
axes[1].invert_yaxis()

plt.tight_layout()
plot_path = "data/outputs/rf_results.png"
plt.savefig(plot_path, dpi=120, bbox_inches="tight")
plt.close()
print(f"\nPlot saved to {plot_path}")

# ── 12. Save model artifacts ──────────────────────────────────────────────────
joblib.dump(model,      "backend/models/model.pkl")
joblib.dump(scaler,     "backend/models/scaler.pkl")
joblib.dump(bin_edges,  "backend/models/bin_edges.pkl")
joblib.dump(label_map,  "backend/models/label_map.pkl")

print("\nArtifacts saved:")
print("  backend/models/model.pkl")
print("  backend/models/scaler.pkl")
print("  backend/models/bin_edges.pkl")
print("  backend/models/label_map.pkl")
print(f"\nDone. Test accuracy = {test_acc:.4f}")
