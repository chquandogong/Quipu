import { useEffect, useMemo, useState } from 'react';

import { fetchFleetOverview } from './api';
import type { DeviceSnapshot, FleetOverview, RiskLevel } from './types';
import './styles.css';

const riskLabels: Record<RiskLevel, string> = {
  healthy: 'Healthy',
  warning: 'Warning',
  critical: 'Critical',
  stale: 'Stale',
};

function metricValue(device: DeviceSnapshot, name: string): string {
  const metric = device.latest_metrics[name];
  if (!metric) return 'Unavailable';
  if (metric.unit === 'celsius') return `${metric.value.toFixed(1)}C`;
  if (metric.unit === 'percent') return `${metric.value.toFixed(1)}%`;
  return `${metric.value}`;
}

function riskClass(level: RiskLevel): string {
  return `risk risk-${level}`;
}

export default function App() {
  const [overview, setOverview] = useState<FleetOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchFleetOverview()
      .then((data) => {
        if (active) {
          setOverview(data);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unknown API error');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const topFindings = useMemo(() => {
    return overview?.devices.flatMap((device) =>
      device.findings.map((finding) => ({
        device: device.device.hostname,
        ...finding,
      })),
    ) ?? [];
  }, [overview]);

  if (loading) {
    return (
      <main className="page">
        <p className="status">Loading fleet health...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <h1>Quipu</h1>
        <p className="error">{error}</p>
      </main>
    );
  }

  if (!overview) {
    return (
      <main className="page">
        <h1>Quipu</h1>
        <p className="status">No fleet data available.</p>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">Team workstation health</p>
          <h1>Quipu</h1>
        </div>
        <p className="generated">Generated {new Date(overview.generated_at).toLocaleString()}</p>
      </header>

      <section className="summary" aria-label="Fleet summary">
        <div><span>{overview.summary.total}</span><strong>Total</strong></div>
        <div><span>{overview.summary.critical}</span><strong>Critical</strong></div>
        <div><span>{overview.summary.warning}</span><strong>Warnings</strong></div>
        <div><span>{overview.summary.stale}</span><strong>Stale</strong></div>
      </section>

      <section className="layout">
        <div className="panel">
          <div className="panel-head">
            <h2>Fleet</h2>
            <span>{overview.devices.length} devices</span>
          </div>
          <div className="device-list">
            {overview.devices.map((device) => (
              <article className="device-row" key={device.device.device_id}>
                <div>
                  <div className="device-title">
                    <strong>{device.device.hostname}</strong>
                    <span className={riskClass(device.risk_level)}>{riskLabels[device.risk_level]}</span>
                  </div>
                  <p>{device.device.model ?? 'Unknown model'} / {device.device.kernel_version ?? 'Unknown kernel'}</p>
                </div>
                <dl>
                  <div><dt>CPU</dt><dd>{metricValue(device, 'cpu.package_temp_c')}</dd></div>
                  <div><dt>Load</dt><dd>{metricValue(device, 'cpu.load_1m')}</dd></div>
                  <div><dt>NVMe</dt><dd>{metricValue(device, 'nvme.temp_c')}</dd></div>
                </dl>
              </article>
            ))}
          </div>
        </div>

        <aside className="panel">
          <div className="panel-head">
            <h2>Evidence</h2>
            <span>{topFindings.length} findings</span>
          </div>
          <div className="finding-list">
            {topFindings.length === 0 ? (
              <p className="status">No active findings.</p>
            ) : (
              topFindings.map((finding, index) => (
                <article className="finding" key={`${finding.device}-${finding.title}-${index}`}>
                  <span>{finding.device} / {finding.category} / {finding.confidence}</span>
                  <strong>{finding.title}</strong>
                  <p>{finding.evidence}</p>
                </article>
              ))
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}
