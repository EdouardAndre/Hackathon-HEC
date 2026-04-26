import { useEffect, useState } from "react";

import type { InventoryItem, SupplierOption } from "../types";
import { AlternativeOptionsPopover } from "./AlternativeOptionsPopover";

type ExpandedItemPanelProps = {
  item: InventoryItem;
  paymentUrl: string;
};

function estimateOrderQuantity(item: InventoryItem): number {
  return Math.max(item.reorderPoint * 2 - item.currentQuantity, item.reorderPoint);
}

export function ExpandedItemPanel({ item, paymentUrl }: ExpandedItemPanelProps) {
  const [selectedOption, setSelectedOption] = useState<SupplierOption>(item.bestOption);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);

  const orderQuantity = estimateOrderQuantity(item);

  useEffect(() => {
    if (!isPopoverOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsPopoverOpen(false);
      }
    }

    window.addEventListener("keydown", handleEscape);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleEscape);
    };
  }, [isPopoverOpen]);

  function handleConfirm() {
    const checkoutUrl = new URL(paymentUrl);
    checkoutUrl.searchParams.set("item", item.name);
    checkoutUrl.searchParams.set("supplier", selectedOption.supplierName);
    checkoutUrl.searchParams.set("quantity", String(orderQuantity));
    window.location.href = checkoutUrl.toString();
  }

  return (
    <>
      <section className="expanded-panel">
        <div className="expanded-panel__summary">
          <div>
            <p className="eyebrow">Recommended supplier</p>
            <h3>{selectedOption.supplierName}</h3>
            <p className="muted-copy">
              Best current fit based on price, lead time, reliability, and available stock.
            </p>
          </div>
          <div className="expanded-panel__pill">
            Reorder {orderQuantity} units
          </div>
        </div>

        <dl className="detail-grid">
          <div>
            <dt>Unit price</dt>
            <dd>${selectedOption.unitPrice.toFixed(2)}</dd>
          </div>
          <div>
            <dt>Lead time</dt>
            <dd>{selectedOption.leadTimeDays} days</dd>
          </div>
          <div>
            <dt>Reliability</dt>
            <dd>{Math.round(selectedOption.reliabilityScore * 100)}%</dd>
          </div>
          <div>
            <dt>Available now</dt>
            <dd>{selectedOption.availableQuantity}</dd>
          </div>
        </dl>

        <div className="expanded-panel__actions">
          <button
            className="secondary-button"
            onClick={() => setIsPopoverOpen(true)}
            type="button"
          >
            Show alternatives
          </button>
          <button className="primary-button" onClick={handleConfirm} type="button">
            Confirm and continue to payment
          </button>
        </div>
      </section>

      <AlternativeOptionsPopover
        isOpen={isPopoverOpen}
        itemName={item.name}
        onClose={() => setIsPopoverOpen(false)}
        onSelect={(option) => {
          setSelectedOption(option);
          setIsPopoverOpen(false);
        }}
        options={item.alternatives}
      />
    </>
  );
}
