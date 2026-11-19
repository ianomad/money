import { manifest } from "./freshness_data.js";
import { COMPONENT_TYPES, COMPONENT_STATUSES } from "./schema.js";

const STALE_AFTER_DAYS = 45;

const UNAVAILABLE = [
  {
    id: "runtime_health",
    kind: "health",
    status: "unavailable",
    label: "Runtime health",
    provenance: "No health adapter is configured.",
    reason: "This deployment has no probe for site, worker, or bot health.",
  },
  {
    id: "job_results",
    kind: "job_results",
    status: "unavailable",
    label: "Job results",
    provenance: "No job-result adapter is configured.",
    reason: "GitHub Actions history is not queried. The deploy workflow has no status feed here.",
  },
  {
    id: "evaluations",
    kind: "evaluation",
    status: "unavailable",
    label: "Evaluations",
    provenance: "No evaluation adapter is configured.",
    reason: "No evaluation runner is connected.",
  },
  {
    id: "usage",
    kind: "usage",
    status: "unavailable",
    label: "Usage",
    provenance: "No analytics query adapter is configured.",
    reason: "Public pages may load analytics in the browser. This dashboard has no analytics query API and does not invent traffic numbers.",
  },
];

function point(entry) {
  return { ...entry, series: [], value: null };
}

export function datasetManifest() {
  return manifest;
}

export function buildMetrics({ now, storage, counts = null, files = null }) {
  const sources = [];
  const datasetFiles = files || manifest.files;
  if (!storage) {
    sources.push(point({
      id: "registry",
      kind: "registry",
      status: "disconnected",
      label: "Admin registry",
      provenance: "D1 binding ADMIN_DB",
      reason: "The admin database is not bound, so registry counts are unavailable.",
      observedAt: now,
    }));
  } else {
    const byType = Object.fromEntries(COMPONENT_TYPES.map((type) => [type, counts.byType[type] || 0]));
    const byStatus = Object.fromEntries(COMPONENT_STATUSES.map((status) => [status, counts.byStatus[status] || 0]));
    sources.push(point({
      id: "registry",
      kind: "registry",
      status: "ok",
      label: "Admin registry",
      provenance: "ADMIN_DB component, rule, and audit tables",
      observedAt: now,
      counts: {
        components: counts.components,
        rules: counts.rules,
        byType,
        byStatus,
        lastAuditAt: counts.lastAuditAt,
      },
    }));
  }

  const nowMs = Date.parse(now);
  for (const file of datasetFiles) {
    const checkedMs = Date.parse(file.checkedAt);
    const ageDays = Number.isFinite(checkedMs) && Number.isFinite(nowMs)
      ? Math.floor((nowMs - checkedMs) / 86400000)
      : null;
    let status = "unavailable";
    let reason;
    if (ageDays == null) reason = "The bundled timestamp could not be read.";
    else if (ageDays < -2) {
      status = "unavailable";
      reason = "The bundled timestamp is in the future.";
    } else if (ageDays > STALE_AFTER_DAYS) status = "stale";
    else status = "ok";
    sources.push(point({
      id: "dataset:" + file.id,
      kind: "dataset_freshness",
      status,
      label: file.label,
      provenance: file.file + " field " + file.timeField + ", bundled with this deployment",
      checkedAt: file.checkedAt,
      ageDays,
      staleAfterDays: STALE_AFTER_DAYS,
      observedAt: manifest.builtAt,
      reason,
    }));
  }

  for (const adapter of UNAVAILABLE) sources.push(point({ ...adapter, observedAt: now }));

  return {
    schemaVersion: 1,
    generatedAt: now,
    note: "Point-in-time readings only. No historical chart is stored or invented.",
    manifestNote: manifest.note,
    sources,
  };
}
