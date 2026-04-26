export type RestockStatus = "healthy" | "warning" | "critical";

export type SupplierOption = {
  supplierName: string;
  unitPrice: number;
  leadTimeDays: number;
  reliabilityScore: number;
  availableQuantity: number;
};

export type InventoryItem = {
  id: string;
  name: string;
  sku: string;
  currentQuantity: number;
  reorderPoint: number;
  status: RestockStatus;
  bestOption: SupplierOption;
  alternatives: SupplierOption[];
};
