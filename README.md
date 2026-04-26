# Hackathon HEC

Inventory forecasting, supplier selection, and AI-driven AP payment agent for a fintech / ops hackathon.

This repo contains:
- a `FastAPI` backend that serves forecast-driven dashboard data, supplier recommendations, and order endpoints
- a `React + TypeScript + Vite` frontend that displays inventory risk, recommended suppliers, alternatives, and checkout flow
- a `Streamlit` payment app (`Black_swan`) that handles the full AP processing pipeline — PO creation, invoice matching, Gemini AI analysis, and Swan payment execution


## What We Built

The app covers an end-to-end MRO procurement workflow:
- the backend uses the demand forecasting dataset to build dashboard items enriched with forecast output and ranked supplier options
- the frontend shows items sorted by urgency, lets the user inspect the optimal supplier, compare alternatives, and confirm an order
- on confirmation, the frontend redirects to the Streamlit AP agent, passing item and supplier data via URL parameters
- the AP agent normalises the request, creates a PO, parses the invoice, runs a 2-way match, calls Gemini for a risk recommendation, and presents a payment draft for human approval
- approval triggers a real credit transfer via the Swan sandbox API, including SCA consent redirect


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
Black_swan/
  streamlit_app.py       # main AP agent UI
  gemini_service.py      # Gemini AI calls (request normalisation, invoice parsing, risk analysis)
  services/
    audit.py
    invoice_parser.py
    matching.py
    payment_draft.py
    po_builder.py
    swan_executor.py
  pages/
    callback.py          # Swan OAuth + SCA consent callback handler
  data/
    mock_request.json
    mock_invoice.json
  requirements.txt
demand-forecasting-kernels-only/
  train.csv
```


## How To Run

### 1. Frontend

```bash
cd frontend
npm install
npm run dev
```

URL: `http://localhost:5173`

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

URLs:
- API root: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### 3. Payment App (Black_swan)

```bash
cd Black_swan
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in credentials (see below)
streamlit run streamlit_app.py --server.port 8501
```

URL: `http://localhost:8501`

#### Required environment variables (`Black_swan/.env`)

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Gemini API key (or set `GOOGLE_CLOUD_PROJECT` for Vertex AI ADC) |
| `SWAN_CLIENT_ID` | Swan sandbox OAuth client ID |
| `SWAN_CLIENT_SECRET` | Swan sandbox OAuth client secret |
| `SWAN_REDIRECT_URI` | Must be registered in Swan Dashboard — default `http://localhost:8501/callback` |
| `SWAN_USER_ACCESS_TOKEN` | Optional — pre-filled user token; obtained automatically via the OAuth flow |


## Runtime Notes

### Dashboard-only usage

If you only want the frontend dashboard and its backend data feed:
- you do **not** need PostgreSQL for `GET /api/v1/dashboard/items`
- that endpoint uses:
  - `demand-forecasting-kernels-only/train.csv`
  - `backend/data/supplier_dataset.xlsx`
  - the forecasting service

### PostgreSQL-backed usage

You need PostgreSQL if you want to use:
- `GET /api/v1/suppliers`
- `POST /api/v1/suppliers`
- `GET /api/v1/inventory/current`
- `POST /api/v1/inventory`
- `POST /api/v1/recommendations/suppliers`
- `POST /api/v1/orders/drafts`
- `POST /api/v1/orders/{order_id}/confirm`
- `GET /api/v1/orders/{order_id}`

Update `backend/.env` with a valid `DATABASE_URL` and run migrations:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Quick start with Docker:

```bash
docker run -d --name pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres
```


## Main Endpoints

### Health

- `GET /health`

```json
{ "status": "ok" }
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

```json
{
  "store_id": 1,
  "item_id": 1,
  "current_stock": 80,
  "prediction_days": 14
}
```

Response:

```json
{ "required_quantity": 609 }
```


## Frontend Behavior

The frontend:
- fetches dashboard items from `GET /api/v1/dashboard/items`
- sorts items by priority: `critical`, then `warning`, then `healthy`
- shows the optimal supplier inside the expanded row
- opens supplier alternatives in a popover
- on supplier confirmation, redirects to the Streamlit payment app (`VITE_PAYMENT_URL`, default `http://localhost:8501`) with item, SKU, supplier, quantity, and unit price as URL query parameters


## AP Agent Pipeline (Black_swan)

On arrival from the frontend, the Streamlit app runs this pipeline:

1. **Request normalisation** — Gemini validates and structures the procurement request
2. **PO creation** — builds a purchase order from the normalised data
3. **Invoice parsing** — generates a mock invoice (exact match / price mismatch / qty mismatch scenario) and structures it via Gemini
4. **2-way matching** — compares PO vs invoice amounts, quantities, and IBAN
5. **AI risk analysis** — Gemini produces a recommendation (`proceed` / `hold` / `block`) with confidence score and risk flags
6. **Human approval** — the reviewer approves or rejects; approval triggers Swan OAuth if no token is present
7. **Payment execution** — Swan sandbox credit transfer; SCA consent redirect if required


## Tests

Backend:

```bash
cd backend
source .venv/bin/activate
pytest
```

Frontend build:

```bash
cd frontend
npm run build
```
