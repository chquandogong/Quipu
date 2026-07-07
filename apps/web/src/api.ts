import type { FleetOverview } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export async function fetchFleetOverview(): Promise<FleetOverview> {
  const response = await fetch(`${API_BASE_URL}/api/fleet/overview`);
  if (!response.ok) {
    throw new Error(`Fleet overview request failed with ${response.status}`);
  }
  return response.json() as Promise<FleetOverview>;
}
