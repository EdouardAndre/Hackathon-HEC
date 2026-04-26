import type { DashboardResponse, InventoryItem } from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}.`);
  }
  return (await response.json()) as T;
}

export async function fetchDashboardItems(): Promise<InventoryItem[]> {
  const payload = await request<DashboardResponse>("/dashboard/items");

  return payload.items
    .filter((item) => item.best_option !== null)
    .map((item) => ({
      id: item.id,
      name: item.name,
      sku: item.sku,
      unitLabel: item.unit_label,
      storeId: item.store_id,
      itemId: item.item_id,
      currentQuantity: item.current_quantity,
      reorderPoint: item.reorder_point,
      status: item.status,
      expectedShortageDate: item.expected_shortage_date,
      requiredQuantity: item.required_quantity,
      forecastSource: item.forecast_source,
      bestOption: {
        supplierName: item.best_option!.supplier_name,
        unitPrice: item.best_option!.unit_price,
        leadTimeDays: item.best_option!.lead_time_days,
        reliabilityScore: item.best_option!.reliability_score,
        availableQuantity: item.best_option!.available_quantity,
      },
      alternatives: item.alternatives.map((option) => ({
        supplierName: option.supplier_name,
        unitPrice: option.unit_price,
        leadTimeDays: option.lead_time_days,
        reliabilityScore: option.reliability_score,
        availableQuantity: option.available_quantity,
      })),
    }));
}
