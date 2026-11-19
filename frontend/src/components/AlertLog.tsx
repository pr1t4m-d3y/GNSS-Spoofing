"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { motion } from "framer-motion";
import { AlertCircle, Clock, FileText, Radar, Zap, Upload, RefreshCw } from "lucide-react";
import type { LogEntry } from "@/types";

interface AlertLogProps {
  logs: LogEntry[];
  maxItems?: number;
  onViewAll?: () => void;
}

const TYPE_ICONS: Record<string, any> = {
  scan: Radar,
  report: FileText,
  injection: Zap,
  batch: Upload,
  alert: AlertCircle,
  reset: RefreshCw,
};

export default function AlertLog({ logs, maxItems = 5, onViewAll }: AlertLogProps) {
  const displayLogs = logs.slice(0, maxItems);

  return (
    <div className="flex flex-col gap-4">
       <div className="flex justify-between items-center px-2">
          <h3 className="text-gray-500 dark:text-white/60 font-bold uppercase tracking-widest text-xs">Log</h3>
          <span 
            className="text-xs font-bold text-indigo-600 dark:text-accent-secondary cursor-pointer hover:underline tracking-tight"
            onClick={onViewAll}
          >
            View All
          </span>
       </div>
       
       <div className="flex flex-col gap-3 max-h-[350px] overflow-y-auto pr-2 scrollbar-hide">
          {displayLogs.length === 0 ? (
            <div className="flex items-center gap-4 p-4 rounded-3xl bg-white dark:bg-white/5 border border-transparent dark:border-white/5 shadow-soft dark:shadow-none animate-float">
               <div className="w-12 h-12 rounded-2xl bg-gray-100 dark:bg-dark-bg flex items-center justify-center text-gray-400">
                  <Clock size={20} />
               </div>
               <div>
                  <h4 className="font-bold text-sm text-indigo-950 dark:text-white">Awaiting Streams</h4>
                  <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-widest">System idle</p>
               </div>
            </div>
          ) : (
            displayLogs.map((log, i) => {
              const Icon = TYPE_ICONS[log.type] || FileText;
              const isSpoofed = log.severity === "critical" || log.severity === "warning";
              
              return (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0, scale: 0.95, x: -10 }}
                  animate={{ opacity: 1, scale: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className={`flex items-center justify-between p-4 rounded-3xl border shadow-soft dark:shadow-none transition-all cursor-pointer group ${
                    isSpoofed 
                      ? "bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900/20" 
                      : log.type === "report" 
                        ? "bg-indigo-50 dark:bg-indigo-900/10 border-indigo-200 dark:border-indigo-900/20"
                        : "bg-white dark:bg-white/5 border-transparent dark:border-white/5"
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform ${
                      isSpoofed 
                        ? "bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400" 
                        : log.type === "report" 
                          ? "bg-indigo-100 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400"
                          : "bg-emerald-50 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                    }`}>
                      <Icon size={24} />
                    </div>
                    <div>
                      <h4 className="font-bold text-sm text-indigo-950 dark:text-white">{log.message}</h4>
                      <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-widest leading-none">
                        {log.type} • {typeof log.anomalyScore === "number" ? `${(log.anomalyScore * 100).toFixed(1)}% Risk` : log.severity}
                      </p>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                     <p className={`font-bold text-xs transition-colors ${
                       isSpoofed ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'
                     }`}>
                       {isSpoofed ? 'RISK' : 'OK'}
                     </p>
                     <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-tight opacity-50">
                       {log.timestamp}
                     </p>
                  </div>
                </motion.div>
              );
            })
          )}
       </div>
    </div>
  );
}
