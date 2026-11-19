/* eslint-disable @typescript-eslint/no-explicit-any */
import type { SatelliteStat } from "@/types";

// All browser requests go through the same-origin proxy in src/app/api, which adds the API key.
export const API_BASE = "/api";

export function newSessionId(): string {
  const raw =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return raw.replace(/[^A-Za-z0-9_-]/g, "").slice(0, 64);
}

// FastAPI returns `detail` as a string for most errors and as a list of objects for validation errors.
export function errorMessage(err: any): string {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item: any) => `${(item.loc ?? []).slice(1).join(".")}: ${item.msg}`)
      .join("; ");
  }
  return err?.message ?? "Request failed";
}

// Build per-satellite stats from either a batch summary or a manual-injection response.
export function deriveSatellites(prediction: any): SatelliteStat[] {
  const fromSummary = prediction?.summary?.satellites;
  if (Array.isArray(fromSummary)) {
    return fromSummary.map((s: any) => ({
      prn: s.prn,
      samples: s.samples,
      spoofedSamples: s.spoofed_samples,
      meanScore: s.mean_anomaly_score,
      meanCn0: s.mean_cn0,
    }));
  }
  const features = prediction?.features;
  const predictions = prediction?.predictions;
  if (Array.isArray(features) && Array.isArray(predictions)) {
    return features
      .map((row: any, i: number) => ({
        prn: row.PRN,
        samples: 1,
        spoofedSamples: predictions[i]?.is_spoofed ? 1 : 0,
        meanScore: predictions[i]?.anomaly_score ?? 0,
        meanCn0: row.CN0,
      }))
      .filter((s: SatelliteStat) => typeof s.prn === "number" && s.prn > 0);
  }
  return [];
}
