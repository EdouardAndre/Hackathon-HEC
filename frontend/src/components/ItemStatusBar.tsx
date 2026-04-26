import type { InventoryItem, RestockStatus } from "../types";

type ItemStatusBarProps = {
  item: InventoryItem;
  isExpanded: boolean;
  onToggle: (itemId: string) => void;
};

const statusCopy: Record<RestockStatus, string> = {
  healthy: "Healthy",
  warning: "Restock soon",
  critical: "Urgent",
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
      <div className="item-bar__icon" aria-hidden="true">
        {item.name.slice(0, 2).toUpperCase()}
      </div>
      <div className="item-bar__identity">
        <span className="item-bar__name">{item.name}</span>
        <span className="item-bar__sku">{item.sku}</span>
      </div>
      <div className="item-bar__meta">
        <span>{item.currentQuantity} {item.unitLabel}</span>
        <span>{item.requiredQuantity} to order</span>
      </div>
      <span className={`item-bar__status item-bar__status--${item.status}`}>
        {statusCopy[item.status]}
      </span>
      <span className="item-bar__chevron" aria-hidden="true">
        {isExpanded ? "⌃" : "›"}
      </span>
    </button>
  );
}
