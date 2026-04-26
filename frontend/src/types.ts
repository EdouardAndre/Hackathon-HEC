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
  unitLabel: string;
  storeId: number;
  itemId: number;
  currentQuantity: number;
  reorderPoint: number;
  status: RestockStatus;
  expectedShortageDate: string | null;
  requiredQuantity: number;
  forecastSource: string;
  bestOption: SupplierOption;
  alternatives: SupplierOption[];
};

export type DashboardResponse = {
  items: Array<{
    id: string;
    name: string;
    sku: string;
    unit_label: string;
    store_id: number;
    item_id: number;
    current_quantity: number;
    reorder_point: number;
    status: RestockStatus;
    expected_shortage_date: string | null;
    required_quantity: number;
    forecast_source: string;
    best_option: {
      supplier_name: string;
      unit_price: number;
      lead_time_days: number;
      reliability_score: number;
      available_quantity: number;
    } | null;
    alternatives: Array<{
      supplier_name: string;
      unit_price: number;
      lead_time_days: number;
      reliability_score: number;
      available_quantity: number;
    }>;
  }>;
};
