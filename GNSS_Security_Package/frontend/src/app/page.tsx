"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useState, useCallback } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";

// Components
import Sidebar from "@/components/Sidebar";
import ThemeToggle from "@/components/ThemeToggle";
import MainSummary from "@/components/MainSummary";
import SatelliteCard from "@/components/SatelliteCard";
import ActiveSatGrid from "@/components/ActiveSatGrid";
import AlertLog from "@/components/AlertLog";
import FluidChart from "@/components/FluidChart";
import ModernInput from "@/components/ModernInput";

// Views
import SatellitesView from "@/components/views/SatellitesView";
import AlertsView from "@/components/views/AlertsView";
import LogsView from "@/components/views/LogsView";
import SettingsView from "@/components/views/SettingsView";

// Types
import type { LogEntry, SignalPoint, AppSettings } from "@/types";

// ── Helper: generate unique IDs ──
let logIdCounter = 0;
function nextLogId() {
  logIdCounter++;
  return `log-${Date.now()}-${logIdCounter}`;
}

function getTimestamp() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function Home() {
  // ── Global State ──
  const [activeView, setActiveView] = useState("home");
  const [prediction, setPrediction] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [signalSeries, setSignalSeries] = useState<SignalPoint[]>([]);
  const [settings, setSettings] = useState<AppSettings>({
    sensitivity: 50,
    theme: "light",
    notificationsEnabled: true,
  });

  // ── Add Log Entry Helper ──
  const addLog = useCallback((entry: Omit<LogEntry, "id" | "timestamp">) => {
    setLogs((prev) => [{ ...entry, id: nextLogId(), timestamp: getTimestamp() }, ...prev]);
  }, []);

  // ── Append Signal Points ──
  const appendSignalPoints = useCallback((points: SignalPoint[]) => {
    setSignalSeries((prev) => [...prev, ...points]);
  }, []);

  // ── File Upload ──
  const handleFileUpload = async (file: File) => {
    setIsProcessing(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post("http://localhost:8000/predict/file", formData);
      setPrediction(res.data);

      // Generate signal points from timeline
      const timeline = res.data?.timeline || [];
      const newPoints: SignalPoint[] = timeline.map((item: any, i: number) => ({
        index: signalSeries.length + i,
        score: Math.abs((item.anomaly_score || 0) * 100),
        is_spoofed: item.is_spoofed || false,
      }));
      appendSignalPoints(newPoints);

      // Log the batch upload
      const spoofedCount = timeline.filter((t: any) => t.is_spoofed).length;
      const avgScore = res.data?.summary?.average_anomaly_score || 0;
      addLog({
        type: "batch",
        severity: spoofedCount > 0 ? "critical" : "info",
        message: `Batch Upload: ${file.name} (${timeline.length} signals)`,
        details: `${spoofedCount} spoofed signals detected`,
        isSpoofed: spoofedCount > 0,
        anomalyScore: avgScore,
      });

      // Auto-generate alert for spoofed batches
      if (spoofedCount > 0) {
        addLog({
          type: "alert",
          severity: "critical",
          message: `⚠ Spoofing Detected in ${file.name}`,
          details: `${spoofedCount}/${timeline.length} signals flagged as anomalous`,
          isSpoofed: true,
          anomalyScore: avgScore,
        });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
      addLog({
        type: "alert",
        severity: "warning",
        message: `Upload Failed: ${file.name}`,
        details: err.response?.data?.detail || err.message,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // ── Manual Signal Injection ──
  const handleManualInject = async (data: any) => {
    setIsProcessing(true);
    setError(null);
    try {
      const payload = { data: [data] };
      const res = await axios.post("http://localhost:8000/predict", payload);
      setPrediction(res.data);

      // Extract result
      const result = res.data?.predictions?.[0];
      const isSpoofed = result?.is_spoofed || false;
      const anomalyScore = result?.anomaly_score || 0;

      // Append to signal series
      appendSignalPoints([{
        index: signalSeries.length,
        score: Math.abs(anomalyScore * 100),
        is_spoofed: isSpoofed,
      }]);

      // Auto-log the injection
      addLog({
        type: "injection",
        severity: isSpoofed ? "critical" : "info",
        message: `Manual Signal Injection — ${isSpoofed ? "Risk Detected" : "Safe"}`,
        details: `PRN ${data.PRN} | Doppler ${data.Carrier_Doppler_hz}Hz | CN0 ${data.CN0}dB`,
        isSpoofed,
        anomalyScore,
        prn: data.PRN,
      });

      // Auto-alert for spoofed injections
      if (isSpoofed) {
        addLog({
          type: "alert",
          severity: "critical",
          message: `⚠ Spoofing Risk: Manual Injection PRN ${data.PRN}`,
          details: `Anomaly score: ${(anomalyScore * 100).toFixed(1)}%`,
          isSpoofed: true,
          anomalyScore,
          prn: data.PRN,
        });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  // ── Reset ──
  const handleReset = async () => {
    setIsProcessing(true);
    try {
      await axios.post("http://localhost:8000/reset");
      setPrediction(null);
      setError(null);
      setSignalSeries([]);
      addLog({
        type: "reset",
        severity: "info",
        message: "System Reset — All data cleared",
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  // ── Scan ──
  const handleScan = async () => {
    setIsProcessing(true);
    setError(null);
    addLog({
      type: "scan",
      severity: "info",
      message: "System Scan Initiated",
    });
    try {
      await axios.get("http://localhost:8000/scan");
      await new Promise((resolve) => setTimeout(resolve, 2000));
      addLog({
        type: "scan",
        severity: "info",
        message: "System Scan Complete — All subsystems operational",
      });
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      addLog({
        type: "scan",
        severity: "info",
        message: "System Scan Complete",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // ── Report ──
  const handleReport = () => {
    addLog({
      type: "report",
      severity: "info",
      message: "Manual Security Report Generated",
      details: `Signal series: ${signalSeries.length} packets analyzed`,
    });
  };

  // ── Settings ──
  const handleUpdateSettings = (newSettings: AppSettings) => {
    setSettings(newSettings);
    addLog({
      type: "report",
      severity: "info",
      message: "Settings Updated",
      details: `Sensitivity: ${newSettings.sensitivity}% | Theme: ${newSettings.theme} | Notifications: ${newSettings.notificationsEnabled ? "On" : "Off"}`,
    });
  };

  // ── Navigation ──
  const navigateTo = (viewId: string) => setActiveView(viewId);

  // ── Computed ──
  const activeSats = prediction?.summary?.active_satellites || [];
  const sampleSat = prediction?.features?.[0] || { PRN: 12, Carrier_Doppler_hz: 1500, CN0: 45 };

  // ── Render Views ──
  const renderView = () => {
    switch (activeView) {
      case "satellites":
        return <SatellitesView />;
      case "alerts":
        return <AlertsView logs={logs} />;
      case "logs":
        return <LogsView logs={logs} />;
      case "settings":
        return <SettingsView settings={settings} onUpdateSettings={handleUpdateSettings} />;
      default:
        return renderHome();
    }
  };

  const renderHome = () => (
    <>
      {/* Header Bar */}
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-indigo-950 dark:text-white tracking-tight">Security Command</h1>
          <p className="text-sm font-bold text-gray-400 dark:text-white/20 uppercase tracking-widest mt-1">v2.4 Active Monitoring</p>
        </div>
        <div className="flex items-center gap-4">
          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-xs font-bold rounded-2xl border border-red-200 dark:border-red-900/40"
            >
              {error}
            </motion.div>
          )}
          <ThemeToggle />
          <div className="flex items-center gap-3 bg-white dark:bg-dark-card p-2 pr-4 rounded-2xl shadow-soft dark:shadow-none border border-transparent dark:border-white/5 cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-white/5 flex items-center justify-center text-indigo-600 dark:text-accent-secondary">
              S
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-black text-indigo-950 dark:text-white">Security Ops</p>
              <p className="text-[10px] font-bold text-gray-400">Officer 402</p>
            </div>
          </div>
        </div>
      </header>

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 min-w-0">
        {/* Left Column */}
        <div className="xl:col-span-6 flex flex-col gap-6 min-w-0">
          <MainSummary
            prediction={prediction}
            isProcessing={isProcessing}
            onReset={handleReset}
            onScan={handleScan}
            onReport={handleReport}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bento-card p-6 flex flex-col justify-center gap-4">
              <ActiveSatGrid satellites={activeSats} />
            </div>
            <div className="bento-card p-6 flex flex-col justify-center">
              <div className="flex justify-between items-center mb-4">
                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Signal Health</p>
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              </div>
              <p className="text-3xl font-black text-indigo-950 dark:text-white tracking-tighter">
                {signalSeries.length > 0
                  ? `${(100 - (signalSeries.slice(-10).reduce((a, b) => a + b.score, 0) / Math.max(signalSeries.slice(-10).length, 1))).toFixed(1)}`
                  : "99.2"}
                <span className="text-sm font-bold text-gray-400 ml-1">%</span>
              </p>
              <p className="text-[10px] font-bold text-emerald-500 uppercase tracking-tight mt-2 flex items-center gap-1">
                {signalSeries.length} packets <span className="text-gray-400 dark:text-white/20">analyzed</span>
              </p>
            </div>
          </div>

          <AlertLog
            logs={logs}
            maxItems={5}
            onViewAll={() => navigateTo("logs")}
          />
        </div>

        {/* Right Column */}
        <div className="xl:col-span-6 flex flex-col gap-6 min-w-0">
          {/* Satellite Cards */}
          <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide perspective-1000">
            <SatelliteCard prn={sampleSat.PRN} snr={sampleSat.CN0} isSpoofed={prediction?.predictions?.[0]?.is_spoofed || false} />
            <SatelliteCard prn={28} snr={42.5} isSpoofed={false} delay={0.1} />
            <SatelliteCard prn={14} snr={38.2} isSpoofed={false} delay={0.2} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
            <FluidChart signalSeries={signalSeries} />
            <ModernInput
              onFileUpload={handleFileUpload}
              onManualInject={handleManualInject}
              isProcessing={isProcessing}
            />
          </div>
        </div>
      </div>
    </>
  );

  return (
    <div className="flex h-screen w-full bg-main-bg dark:bg-dark-bg p-4 gap-4 overflow-hidden font-sans transition-colors duration-300">
      {/* Sidebar */}
      <aside className="w-72 h-full hidden lg:block">
        <Sidebar activeView={activeView} onNavigate={navigateTo} />
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-y-auto pr-2 custom-scrollbar">
        <div className="max-w-[1400px] mx-auto flex flex-col gap-6 py-4">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeView}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col gap-6"
            >
              {renderView()}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
