"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { motion } from "framer-motion";
import { AlertCircle, FileText, Radar, RefreshCw, Zap, Upload, Terminal } from "lucide-react";
import type { LogEntry } from "@/types";

interface LogsViewProps {
  logs: LogEntry[];
}

const TYPE_CONFIG: Record<string, { icon: any; color: string; bg: string }> = {
  scan:      { icon: Radar,      color: "text-blue-600 dark:text-blue-400",    bg: "bg-blue-50 dark:bg-blue-500/10" },
  report:    { icon: FileText,   color: "text-indigo-600 dark:text-indigo-400", bg: "bg-indigo-50 dark:bg-indigo-500/10" },
  injection: { icon: Zap,        color: "text-purple-600 dark:text-purple-400", bg: "bg-purple-50 dark:bg-purple-500/10" },
  batch:     { icon: Upload,     color: "text-cyan-600 dark:text-cyan-400",    bg: "bg-cyan-50 dark:bg-cyan-500/10" },
  alert:     { icon: AlertCircle, color: "text-red-600 dark:text-red-400",     bg: "bg-red-50 dark:bg-red-500/10" },
  reset:     { icon: RefreshCw,  color: "text-gray-600 dark:text-gray-400",    bg: "bg-gray-50 dark:bg-white/5" },
};

const SEVERITY_DOT: Record<string, string> = {
  info: "bg-emerald-500",
  warning: "bg-yellow-500",
  critical: "bg-red-500 animate-pulse",
};

export default function LogsView({ logs }: LogsViewProps) {
  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-indigo-950 dark:text-white tracking-tight">System Logs</h1>
          <p className="text-sm font-bold text-gray-400 dark:text-white/20 uppercase tracking-widest mt-1">
            {logs.length} Transaction{logs.length !== 1 ? "s" : ""} Recorded
          </p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-indigo-50 dark:bg-white/5 rounded-2xl">
          <Terminal size={14} className="text-indigo-600 dark:text-accent-secondary" />
          <span className="text-xs font-bold text-indigo-600 dark:text-accent-secondary uppercase tracking-wider">Live</span>
        </div>
      </div>

      {/* Log Table */}
      <div className="bento-card overflow-hidden">
        {/* Column Header */}
        <div className="grid grid-cols-12 gap-4 px-5 py-3 bg-gray-50 dark:bg-white/[0.02] border-b border-gray-100 dark:border-white/5">
          <div className="col-span-1">
            <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Sev</p>
          </div>
          <div className="col-span-2">
            <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Type</p>
          </div>
          <div className="col-span-5">
            <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Message</p>
          </div>
          <div className="col-span-2">
            <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Score</p>
          </div>
          <div className="col-span-2 text-right">
            <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Time</p>
          </div>
        </div>

        {/* Rows */}
        <div className="max-h-[600px] overflow-y-auto scrollbar-hide">
          {logs.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-sm text-gray-400 dark:text-white/40 font-semibold">No transactions recorded yet.</p>
            </div>
          ) : (
            logs.map((log, i) => {
              const config = TYPE_CONFIG[log.type] || TYPE_CONFIG.report;
              const Icon = config.icon;
              return (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.02 }}
                  className="grid grid-cols-12 gap-4 px-5 py-3.5 border-b border-gray-50 dark:border-white/[0.03] hover:bg-indigo-50/30 dark:hover:bg-white/[0.02] transition-colors"
                >
                  {/* Severity Dot */}
                  <div className="col-span-1 flex items-center">
                    <div className={`w-2.5 h-2.5 rounded-full ${SEVERITY_DOT[log.severity]}`} />
                  </div>
                  {/* Type Badge */}
                  <div className="col-span-2 flex items-center">
                    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg ${config.bg}`}>
                      <Icon size={12} className={config.color} />
                      <span className={`text-[10px] font-bold uppercase tracking-wider ${config.color}`}>{log.type}</span>
                    </div>
                  </div>
                  {/* Message */}
                  <div className="col-span-5 flex items-center">
                    <p className="text-sm font-semibold text-indigo-950 dark:text-white truncate">{log.message}</p>
                  </div>
                  {/* Score */}
                  <div className="col-span-2 flex items-center">
                    {typeof log.anomalyScore === "number" ? (
                      <span className={`text-sm font-bold ${
                        log.anomalyScore > 0.6 ? "text-red-600 dark:text-red-400" : 
                        log.anomalyScore > 0.3 ? "text-yellow-600 dark:text-yellow-400" : 
                        "text-emerald-600 dark:text-emerald-400"
                      }`}>
                        {(log.anomalyScore * 100).toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-xs text-gray-300 dark:text-white/20">—</span>
                    )}
                  </div>
                  {/* Timestamp */}
                  <div className="col-span-2 flex items-center justify-end">
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tight">{log.timestamp}</span>
                  </div>
                </motion.div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
