import { useState } from "react";

import { ExpandedItemPanel } from "./components/ExpandedItemPanel";
import { ItemStatusBar } from "./components/ItemStatusBar";
import { inventoryItems } from "./data/inventory";
import type { InventoryItem, RestockStatus } from "./types";

const paymentUrl =
  import.meta.env.VITE_PAYMENT_URL ?? "https://example.com/payment";

const statusPriority: Record<RestockStatus, number> = {
  critical: 0,
  warning: 1,
  healthy: 2,
};

function countByStatus(status: "healthy" | "warning" | "critical"): number {
  return inventoryItems.filter((item) => item.status === status).length;
}

function sortItemsByPriority(items: InventoryItem[]): InventoryItem[] {
  return [...items].sort((left, right) => {
    const statusDifference = statusPriority[left.status] - statusPriority[right.status];
    if (statusDifference !== 0) {
      return statusDifference;
    }

    return left.currentQuantity - right.currentQuantity;
  });
}

export default function App() {
  const [expandedItemId, setExpandedItemId] = useState<string | null>(null);
  const sortedItems = sortItemsByPriority(inventoryItems);

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero__copy">
          <h1>BOB</h1>
        </div>

        <div className="hero__summary" aria-label="Inventory summary">
          <div className="summary-card summary-card--healthy">
            <span>Healthy</span>
            <strong>{countByStatus("healthy")}</strong>
          </div>
          <div className="summary-card summary-card--warning">
            <span>Restock Soon</span>
            <strong>{countByStatus("warning")}</strong>
          </div>
          <div className="summary-card summary-card--critical">
            <span>Urgent</span>
            <strong>{countByStatus("critical")}</strong>
          </div>
        </div>
      </header>

      <main className="inventory-stack">
        {sortedItems.map((item) => {
          const isExpanded = expandedItemId === item.id;

          return (
            <section className="inventory-row" key={item.id}>
              <ItemStatusBar
                isExpanded={isExpanded}
                item={item}
                onToggle={(itemId) =>
                  setExpandedItemId((current) => (current === itemId ? null : itemId))
                }
              />
              <div
                aria-hidden={!isExpanded}
                className={`inventory-row__panel ${
                  isExpanded ? "inventory-row__panel--open" : ""
                }`}
              >
                <div className="inventory-row__panel-inner">
                  <ExpandedItemPanel item={item} paymentUrl={paymentUrl} />
                </div>
              </div>
            </section>
          );
        })}
      </main>
    </div>
  );
}
