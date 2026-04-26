# Hackathon HEC

FastAPI backend scaffold plus a React landing page prototype for inventory forecasting, supplier comparison, and purchase-order flow exploration.

## Structure

```text
frontend/
  src/
backend/
  alembic/
    versions/
  app/
    api/
      routes/
    core/
    integrations/
      ap2/
    models/
    repositories/
    schemas/
    services/
    main.py
  tests/
  .env.example
  alembic.ini
  requirements.txt
```

## Quick Start

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The landing page runs at `http://localhost:5173` and currently uses fake static inventory and supplier data.

### Backend

1. Create a virtual environment and install dependencies.
2. Copy `backend/.env.example` to `backend/.env`.
3. Update the PostgreSQL connection string.
4. Run migrations.
5. Start the API server.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Example Endpoints

### Health

- `GET /health`

Response:

```json
{
  "status": "ok"
}
```

### Suppliers

- `POST /api/v1/suppliers`
- `GET /api/v1/suppliers`

Create request:

```json
{
  "name": "Supplier A",
  "lead_time_days": 5,
  "available_quantity": 800,
  "current_unit_price": 12.5,
  "reliability_score": 0.94
}
```

Create response:

```json
{
  "id": 1,
  "name": "Supplier A",
  "lead_time_days": 5,
  "available_quantity": 800,
  "current_unit_price": 12.5,
  "reliability_score": 0.94,
  "created_at": "2026-04-26T00:00:00Z"
}
```

### Inventory Snapshot

- `POST /api/v1/inventory`
- `GET /api/v1/inventory/current`

Request:

```json
{
  "stock_level": 240
}
```

Response:

```json
{
  "id": 1,
  "stock_level": 240,
  "recorded_at": "2026-04-26T00:00:00Z"
}
```

### Forecast Placeholder

- `POST /api/v1/forecasting/manual`

Request:

```json
{
  "expected_shortage_date": "2026-05-03",
  "required_quantity": 300
}
```

Response:

```json
{
  "expected_shortage_date": "2026-05-03",
  "required_quantity": 300,
  "source": "manual"
}
```

### Supplier Recommendations

- `POST /api/v1/recommendations/suppliers`

Request:

```json
{
  "expected_shortage_date": "2026-05-03",
  "required_quantity": 300
}
```

Response:

```json
{
  "forecast": {
    "expected_shortage_date": "2026-05-03",
    "required_quantity": 300,
    "source": "manual"
  },
  "recommendations": [
    {
      "supplier_id": 1,
      "supplier_name": "Supplier A",
      "can_fulfill": true,
      "recommended_quantity": 300,
      "lead_time_days": 5,
      "available_quantity": 800,
      "current_unit_price": 12.5,
      "reliability_score": 0.94,
      "score": 0.9027
    }
  ]
}
```

### Orders

- `POST /api/v1/orders/drafts`
- `POST /api/v1/orders/{order_id}/confirm`
- `GET /api/v1/orders/{order_id}`

Draft request:

```json
{
  "supplier_id": 1,
  "quantity": 300,
  "expected_shortage_date": "2026-05-03"
}
```

Draft response:

```json
{
  "id": 1,
  "supplier_id": 1,
  "quantity": 300,
  "unit_price": 12.5,
  "status": "draft",
  "expected_shortage_date": "2026-05-03",
  "ap2_reference": null,
  "created_at": "2026-04-26T00:00:00Z",
  "updated_at": "2026-04-26T00:00:00Z"
}
```

Confirm response:

```json
{
  "id": 1,
  "supplier_id": 1,
  "quantity": 300,
  "unit_price": 12.5,
  "status": "confirmed",
  "expected_shortage_date": "2026-05-03",
  "ap2_reference": "AP2-MOCK-1",
  "created_at": "2026-04-26T00:00:00Z",
  "updated_at": "2026-04-26T00:05:00Z"
}
```

## Notes

- Authentication is intentionally left as a TODO for hackathon speed.
- Forecasting currently uses a manual placeholder service that can be replaced later.
- AP2 confirmation currently uses a mock integration module.

## Tests

```bash
cd backend
pytest
```
