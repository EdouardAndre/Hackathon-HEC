import type { InventoryItem, RestockStatus } from "../types";

type ItemStatusBarProps = {
  item: InventoryItem;
  isExpanded: boolean;
  onToggle: (itemId: string) => void;
};

const statusCopy: Record<RestockStatus, string> = {
  healthy: "Stock is healthy",
  warning: "Restock soon",
  critical: "Restock urgently",
};

export function ItemStatusBar({ item, isExpanded, onToggle }: ItemStatusBarProps) {
  return (
    <button
      aria-expanded={isExpanded}
      className={`item-bar item-bar--${item.status} ${
        isExpanded ? "item-bar--expanded" : ""
      }`}
      onClick={() => onToggle(item.id)}
      type="button"
    >
      <div className="item-bar__identity">
        <span className="item-bar__name">{item.name}</span>
        <span className="item-bar__sku">{item.sku}</span>
      </div>
      <div className="item-bar__meta">
        <span>{item.currentQuantity} units</span>
        <span>{statusCopy[item.status]}</span>
      </div>
    </button>
  );
}
