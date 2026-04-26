import { useEffect, useState } from "react";

import { fetchDashboardItems } from "./api";
import { ExpandedItemPanel } from "./components/ExpandedItemPanel";
import { ItemStatusBar } from "./components/ItemStatusBar";
import type { InventoryItem, RestockStatus } from "./types";

const paymentUrl =
  import.meta.env.VITE_PAYMENT_URL ?? "http://localhost:8501";
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
        const backendItems = await fetchDashboardItems();
        if (isActive) {
          setItems(sortItemsByPriority(backendItems));
        }
      } catch (loadError) {
        if (isActive) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load dashboard items.",
          );
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
  const totalRequiredQuantity = items.reduce(
    (sum, item) => sum + item.requiredQuantity,
    0,
  );

  return (
    <div className="dashboard-shell">
      <div className="app-shell">
        <header className="hero">
          <h1 className="hero__title">MRO Pilot</h1>

          <div className="hero__summary" aria-label="Inventory summary">
            <div className="summary-card summary-card--critical">
              <span>Urgent items</span>
              <strong>{statusCounts.critical}</strong>
              <small>Immediate shortage risk</small>
            </div>
            <div className="summary-card summary-card--warning">
              <span>Restock soon</span>
              <strong>{statusCounts.warning}</strong>
              <small>Needs procurement review</small>
            </div>
            <div className="summary-card summary-card--healthy">
              <span>Healthy stock</span>
              <strong>{statusCounts.healthy}</strong>
              <small>No action required</small>
            </div>
            <div className="summary-card">
              <span>Required quantity</span>
              <strong>{totalRequiredQuantity}</strong>
              <small>Total recommended order volume</small>
            </div>
          </div>
        </header>

        <main className="content-section">
          <div className="content-section__header">
            <div>
              <h2>Items to review</h2>
              <p>Sorted by urgency and restocking pressure.</p>
            </div>
          </div>

          <div className="inventory-stack">
            {isLoading ? <p className="status-message">Loading dashboard items...</p> : null}
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
          </div>
        </main>
      </div>
    </div>
  );
}
