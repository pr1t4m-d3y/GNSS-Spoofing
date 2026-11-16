"use client";

import { motion } from "framer-motion";
import { ShieldAlert, AlertTriangle, Shield } from "lucide-react";
import type { LogEntry } from "@/types";

interface AlertsViewProps {
  logs: LogEntry[];
}

export default function AlertsView({ logs }: AlertsViewProps) {
  // Filter: only high-risk (warning/critical) entries
  const criticalLogs = logs.filter(l => l.severity === "warning" || l.severity === "critical");

  const severityConfig = {
    critical: {
      icon: ShieldAlert,
      bg: "bg-red-50 dark:bg-red-900/10",
      border: "border-red-200 dark:border-red-900/30",
      iconBg: "bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400",
      badge: "bg-red-500 text-white",
      label: "CRITICAL"
    },
    warning: {
      icon: AlertTriangle,
      bg: "bg-yellow-50 dark:bg-yellow-900/10",
      border: "border-yellow-200 dark:border-yellow-900/30",
      iconBg: "bg-yellow-100 dark:bg-yellow-500/20 text-yellow-600 dark:text-yellow-400",
      badge: "bg-yellow-500 text-white",
      label: "HIGH RISK"
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-indigo-950 dark:text-white tracking-tight">Threat Alerts</h1>
          <p className="text-sm font-bold text-gray-400 dark:text-white/20 uppercase tracking-widest mt-1">
            {criticalLogs.length} Active Threat{criticalLogs.length !== 1 ? "s" : ""}
          </p>
        </div>
        {criticalLogs.length > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 rounded-2xl">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-xs font-bold text-red-600 dark:text-red-400 uppercase tracking-wider">Threats Active</span>
          </div>
        )}
      </div>

      {/* Alert Cards */}
      <div className="flex flex-col gap-4">
        {criticalLogs.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bento-card p-12 flex flex-col items-center justify-center text-center gap-4"
          >
            <div className="w-20 h-20 rounded-full bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center">
              <Shield size={36} className="text-emerald-500" />
            </div>
            <h3 className="text-xl font-black text-indigo-950 dark:text-white">All Clear</h3>
            <p className="text-sm text-gray-400 dark:text-white/40 max-w-sm">
              No high-risk or critical alerts detected. Your GNSS constellation is secure.
            </p>
          </motion.div>
        ) : (
          criticalLogs.map((log, i) => {
            const config = severityConfig[log.severity as "critical" | "warning"];
            const Icon = config.icon;
            return (
              <motion.div
                key={log.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className={`bento-card p-5 flex items-start gap-4 ${config.bg} ${config.border} border`}
              >
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-sm flex-shrink-0 ${config.iconBg}`}>
                  <Icon size={24} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider ${config.badge}`}>
                      {config.label}
                    </span>
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{log.timestamp}</span>
                  </div>
                  <h4 className="font-bold text-sm text-indigo-950 dark:text-white truncate">{log.message}</h4>
                  {log.details && (
                    <p className="text-xs text-gray-500 dark:text-white/40 mt-1">{log.details}</p>
                  )}
                  {typeof log.anomalyScore === "number" && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="h-1.5 flex-1 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-red-500 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(log.anomalyScore * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-bold text-gray-400">{(log.anomalyScore * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}
