import { useEffect, useState } from "react";

import { fetchDashboardItems } from "./api";
import { ExpandedItemPanel } from "./components/ExpandedItemPanel";
import { ItemStatusBar } from "./components/ItemStatusBar";
import type { InventoryItem, RestockStatus } from "./types";

const paymentUrl =
  import.meta.env.VITE_PAYMENT_URL ?? "https://example.com/payment";
const statusPriority: Record<RestockStatus, number> = { critical: 0, warning: 1, healthy: 2 };

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
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    async function loadItems() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchDashboardItems();
        if (isActive) {
          setItems(sortItemsByPriority(data));
        }
      } catch (loadError) {
        if (isActive) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load items.");
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadItems();

    return () => {
      isActive = false;
    };
  }, []);

  const sortedItems = sortItemsByPriority(items);
  const statusCounts = {
    healthy: items.filter((item) => item.status === "healthy").length,
    warning: items.filter((item) => item.status === "warning").length,
    critical: items.filter((item) => item.status === "critical").length,
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero__copy">
          <h1>BOB</h1>
        </div>

        <div className="hero__summary" aria-label="Inventory summary">
          <div className="summary-card summary-card--healthy">
            <span>Healthy</span>
            <strong>{statusCounts.healthy}</strong>
          </div>
          <div className="summary-card summary-card--warning">
            <span>Restock Soon</span>
            <strong>{statusCounts.warning}</strong>
          </div>
          <div className="summary-card summary-card--critical">
            <span>Urgent</span>
            <strong>{statusCounts.critical}</strong>
          </div>
        </div>
      </header>

      <main className="inventory-stack">
        {isLoading ? <p className="status-message">Loading model-evaluated items...</p> : null}
        {error ? <p className="status-message status-message--error">{error}</p> : null}
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
