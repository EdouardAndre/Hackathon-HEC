import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Step 1 — Load dataset
# -----------------------------
df = pd.read_csv("demand-forecasting-kernels-only/train.csv")

# -----------------------------
# Step 2 — Convert date
# -----------------------------
df["date"] = pd.to_datetime(df["date"])

# -----------------------------
# Step 3 — Filter ONE item + ONE store
# -----------------------------
df = df[(df["store"] == 1) & (df["item"] == 1)]

# -----------------------------
# Step 4 — Keep only date + quantity
# -----------------------------
df = df[["date", "sales"]]
df.columns = ["date", "quantity"]

# -----------------------------
# Step 5 — Sort
# -----------------------------
df = df.sort_values("date").reset_index(drop=True)

# -----------------------------
# Step 6 — Check
# -----------------------------
print(df.head())
print(df.shape)



# -----------------------------
# Plot time series
# -----------------------------
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Chronos T5 Forecasting

import torch
import numpy as np
from chronos import ChronosPipeline

# Charger le modèle pré-entraîné
pipeline = ChronosPipeline.from_pretrained(
    "amazon/chronos-t5-small",  # ou "medium" / "large" selon tes ressources
    device_map="cpu",           # "cuda" si tu as un GPU
    torch_dtype=torch.float32,
)

# Données historiques issues du DataFrame chargé plus haut
historique = torch.tensor(df["quantity"].values, dtype=torch.float32).unsqueeze(0)

# Prévision sur les 7 prochains jours
forecast = pipeline.predict(
    inputs=historique,
    prediction_length=7,
    num_samples=100  # pour avoir des intervalles de confiance
)

# Résultats
low, median, high = np.quantile(forecast.numpy(), [0.1, 0.5, 0.9], axis=1)
print("Prévision médiane :", median[0])
print("Intervalle bas    :", low[0])
print("Intervalle haut   :", high[0])

# Visualisation de la prévision
last_dates = df["date"].values
future_dates = pd.date_range(start=df["date"].iloc[-1] + pd.Timedelta(days=1), periods=7)

# Ancre : dernier point historique pour raccorder les deux courbes
anchor_date = [df["date"].iloc[-1]]
anchor_value = df["quantity"].values[-1]
median_connected = np.concatenate([[anchor_value], median[0]])
low_connected = np.concatenate([[anchor_value], low[0]])
high_connected = np.concatenate([[anchor_value], high[0]])
dates_connected = np.concatenate([anchor_date, future_dates])

axes[0].plot(last_dates[-90:], df["quantity"].values[-90:])
axes[0].set_title("Demand over Time (Store 1, Item 1)")
axes[0].set_xlabel("Date")
axes[0].set_ylabel("Quantity")
axes[0].tick_params(axis="x", rotation=45)

axes[1].plot(last_dates[-90:], df["quantity"].values[-90:], label="Historique")
axes[1].plot(dates_connected, median_connected, label="Prévision médiane", color="orange")
axes[1].fill_between(dates_connected, low_connected, high_connected, alpha=0.3, color="orange", label="Intervalle 10-90%")
axes[1].set_title("Prévision Chronos (Store 1, Item 1)")
axes[1].set_xlabel("Date")
axes[1].set_ylabel("Quantité")
axes[1].legend()
axes[1].tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.show()