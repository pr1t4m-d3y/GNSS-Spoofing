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

// ── Settings ──
export interface AppSettings {
  sensitivity: number;        // 0-100, default 50
  theme: "light" | "dark" | "security";
  notificationsEnabled: boolean;
}

// ── Satellite Info ──
export interface SatelliteInfo {
  prn: number;
  snr: number;
  elevation: number;
  status: "Healthy" | "Degraded" | "Compromised";
  lastSeen: string;
  history: number[]; // last N anomaly scores
}
