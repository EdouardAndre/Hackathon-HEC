"""Seed suppliers from data/supplier_dataset.xlsx into the database."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import openpyxl

from app.core.database import SessionLocal
from app.repositories.models.supplier import Supplier

XLSX_PATH = Path(__file__).parent / "data" / "supplier_dataset.xlsx"


def load_rows() -> list[dict]:
    wb = openpyxl.load_workbook(XLSX_PATH)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    return [dict(zip(headers, row)) for row in rows[1:]]


def deduplicate_name(name: str, seen: dict[str, int]) -> str:
    seen[name] += 1
    count = seen[name]
    return name if count == 1 else f"{name} ({count})"


def main() -> None:
    rows = load_rows()
    seen: dict[str, int] = defaultdict(int)

    suppliers = []
    for row in rows:
        name = deduplicate_name(row["name"], seen)
        suppliers.append(
            Supplier(
                name=name,
                lead_time_days=round(row["delivery_time"]),
                available_quantity=int(row["quantity"]),
                current_unit_price=round(float(row["price"]), 2),
                reliability_score=float(row["reliability"]),
            )
        )

    with SessionLocal() as session:
        existing = session.query(Supplier).count()
        if existing:
            print(f"{existing} suppliers already in DB — skipping seed.")
            return

        session.add_all(suppliers)
        session.commit()
        print(f"Inserted {len(suppliers)} suppliers.")


if __name__ == "__main__":
    main()
