import { createPortal } from "react-dom";

import type { SupplierOption } from "../types";

type AlternativeOptionsPopoverProps = {
  itemName: string;
  options: SupplierOption[];
  isOpen: boolean;
  onClose: () => void;
  onSelect: (option: SupplierOption) => void;
};

export function AlternativeOptionsPopover({
  itemName,
  options,
  isOpen,
  onClose,
  onSelect,
}: AlternativeOptionsPopoverProps) {
  if (!isOpen) {
    return null;
  }

  return createPortal(
    <div
      aria-modal="true"
      className="popover-backdrop"
      onClick={onClose}
      role="dialog"
    >
      <div className="popover-card" onClick={(event) => event.stopPropagation()}>
        <div className="popover-card__header">
          <div>
            <p className="eyebrow">Alternatives</p>
            <h3>Other supplier options for {itemName}</h3>
          </div>
          <button className="ghost-button" onClick={onClose} type="button">
            Close
          </button>
        </div>

        <div className="popover-options">
          {options.map((option) => (
            <article className="option-card" key={`${itemName}-${option.supplierName}`}>
              <div>
                <h4>{option.supplierName}</h4>
                <p>
                  ${option.unitPrice.toFixed(2)} per unit · {option.leadTimeDays} day lead
                  time
                </p>
              </div>
              <dl className="option-metrics">
                <div>
                  <dt>Reliability</dt>
                  <dd>{Math.round(option.reliabilityScore * 100)}%</dd>
                </div>
                <div>
                  <dt>Available</dt>
                  <dd>{option.availableQuantity}</dd>
                </div>
              </dl>
              <button
                className="secondary-button"
                onClick={() => onSelect(option)}
                type="button"
              >
                Choose this supplier
              </button>
            </article>
          ))}
        </div>
      </div>
    </div>,
    document.body,
  );
}
