import type { FleetOverview, InvestigationDetail, InvestigationQueue } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export async function fetchFleetOverview(): Promise<FleetOverview> {
  const response = await fetch(`${API_BASE_URL}/api/fleet/overview`);
  if (!response.ok) {
    throw new Error(`Fleet overview request failed with ${response.status}`);
  }
  return response.json() as Promise<FleetOverview>;
}

export async function fetchInvestigationQueue(): Promise<InvestigationQueue> {
  const response = await fetch(`${API_BASE_URL}/api/investigations/queue`);
  if (!response.ok) {
    throw new Error(`Investigation queue request failed with ${response.status}`);
  }
  return response.json() as Promise<InvestigationQueue>;
}

export async function fetchInvestigationDetail(itemId: string): Promise<InvestigationDetail> {
  const response = await fetch(`${API_BASE_URL}/api/investigations/${encodeURIComponent(itemId)}`);
  if (!response.ok) {
    throw new Error(`Investigation detail request failed with ${response.status}`);
  }
  return response.json() as Promise<InvestigationDetail>;
}
