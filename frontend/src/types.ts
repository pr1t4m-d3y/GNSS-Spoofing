/* eslint-disable @typescript-eslint/no-explicit-any */

// ── Unified Log Entry ──
export interface LogEntry {
  id: string;
  type: "scan" | "report" | "injection" | "batch" | "alert" | "reset";
  severity: "info" | "warning" | "critical";
  message: string;
  timestamp: string;
  details?: string;
  isSpoofed?: boolean;
  anomalyScore?: number;
  prn?: number;
}

// ── Signal Series Data Point ──
export interface SignalPoint {
  index: number;
  score: number;
  is_spoofed: boolean;
}

// ── Per-satellite statistics derived from analysed telemetry ──
export interface SatelliteStat {
  prn: number;
  samples: number;
  spoofedSamples: number;
  meanScore: number; // 0..1 anomaly score
  meanCn0: number; // dB-Hz
}
