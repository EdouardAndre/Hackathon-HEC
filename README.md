# Hackathon HEC

Inventory forecasting and supplier-selection demo for a fintech / ops hackathon.

This repo contains:
- a `FastAPI` backend that serves forecast-driven dashboard data, supplier recommendations, and order endpoints
- a `React + TypeScript + Vite` frontend that displays inventory risk, recommended suppliers, alternatives, and checkout flow

## What We Built

The app is a lightweight inventory control dashboard for a single-operator workflow:
- the backend uses the demand forecasting dataset to build dashboard items
- the dashboard endpoint enriches those items with forecast output and ranked supplier options
- the frontend shows items sorted by urgency and lets the user inspect the optimal supplier, compare alternatives, and continue to payment


## Repo Structure

```text
frontend/
  src/
    components/
    api.ts
    App.tsx
    styles.css
backend/
  app/
    core/
    presentation/
      routes/
      schemas/
    repositories/
    services/
    main.py
  data/
    supplier_dataset.xlsx
  alembic/
  requirements.txt
demand-forecasting-kernels-only/
  train.csv
```

## How To Run

### 1. Frontend

```bash
cd /Users/eda/Documents/Hackathon_HEC/Hackathon-HEC/frontend
npm install
npm run dev
```

Frontend URL:
- `http://localhost:5173`

### 2. Backend

```bash
cd /Users/eda/Documents/Hackathon_HEC/Hackathon-HEC/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend URLs:
- API root: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### 3. Payment App

The frontend confirm action redirects to the standalone Streamlit payment flow in `Black_swan`.

```bash
cd /Users/eda/Documents/Hackathon_HEC/Hackathon-HEC/Black_swan
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Payment app URL:
- `http://127.0.0.1:8501`

## Runtime Notes

### Dashboard-only usage

If you only want the frontend dashboard and its backend data feed:
- you do **not** need PostgreSQL for `GET /api/v1/dashboard/items`
- that endpoint uses:
  - `demand-forecasting-kernels-only/train.csv`
  - `backend/data/supplier_dataset.xlsx`
  - the forecasting service

### PostgreSQL-backed usage

You still need PostgreSQL if you want to use:
- `GET /api/v1/suppliers`
- `POST /api/v1/suppliers`
- `GET /api/v1/inventory/current`
- `POST /api/v1/inventory`
- `POST /api/v1/recommendations/suppliers`
- `POST /api/v1/orders/drafts`
- `POST /api/v1/orders/{order_id}/confirm`
- `GET /api/v1/orders/{order_id}`

If you plan to use those endpoints, update `backend/.env` with a valid `DATABASE_URL` and run migrations:

```bash
cd /Users/eda/Documents/Hackathon_HEC/Hackathon-HEC/backend
source .venv/bin/activate
alembic upgrade head
```

## Main Endpoints

### Health

- `GET /health`

Example response:

```json
{
  "status": "ok"
}
```

### Dashboard Items

- `GET /api/v1/dashboard/items`

Example response shape:

```json
{
  "items": [
    {
      "id": "store-8-item-1",
      "name": "Thermal Receipt Paper",
      "sku": "BOB-POS-ROLL-57",
      "unit_label": "rolls",
      "store_id": 8,
      "item_id": 1,
      "current_quantity": 96,
      "reorder_point": 168,
      "status": "warning",
      "expected_shortage_date": "2018-01-03",
      "required_quantity": 241,
      "forecast_source": "chronos",
      "best_option": {
        "supplier_name": "Prime Direct",
        "unit_price": 282.51,
        "lead_time_days": 2,
        "reliability_score": 0.6254,
        "available_quantity": 745
      },
      "alternatives": [
        {
          "supplier_name": "Apex Partners",
          "unit_price": 246.05,
          "lead_time_days": 25,
          "reliability_score": 0.6535,
          "available_quantity": 891
        }
      ]
    }
  ]
}
```

### Forecast Quantity

- `POST /api/v1/forecasting/predict`

Example request:

```json
{
  "store_id": 1,
  "item_id": 1,
  "current_stock": 80,
  "prediction_days": 14
}
```

Example response:

```json
{
  "required_quantity": 609
}
```

## Frontend Behavior

The frontend:
- fetches dashboard items from `GET /api/v1/dashboard/items`
- sorts items by priority: `critical`, then `warning`, then `healthy`
- shows the optimal supplier inside the expanded row
- opens supplier alternatives in a popover
- redirects to the configured payment URL when the user confirms a supplier


## Tests

Backend:

```bash
cd /Users/eda/Documents/Hackathon_HEC/Hackathon-HEC/backend
pytest
```

Frontend build:

```bash
cd /Users/eda/Documents/Hackathon_HEC/Hackathon-HEC/frontend
npm run build
```
