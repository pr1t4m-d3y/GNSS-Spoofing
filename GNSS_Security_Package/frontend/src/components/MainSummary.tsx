"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { motion } from "framer-motion";
import { Radar, FileText, Layers, RefreshCw, ShieldCheck, AlertTriangle } from "lucide-react";

interface MainSummaryProps {
  prediction: any;
  isProcessing: boolean;
  onReset: () => void;
  onScan: () => void;
  onReport: () => void;
}

export default function MainSummary({ prediction, isProcessing, onReset, onScan, onReport }: MainSummaryProps) {
  const isSpoofed = prediction?.summary?.spoofed_samples > 0 || (prediction?.predictions && prediction.predictions[0]?.is_spoofed);
  const score = prediction?.summary ? prediction.summary.average_anomaly_score * 100 : (prediction?.predictions?.[0]?.anomaly_score * 100) || 0;
  
  // Health score is 100 - anomaly score
  const healthScore = Math.max(0, 100 - score).toFixed(1);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bento-card p-8 min-h-[220px] flex flex-col justify-between relative overflow-hidden ${
        isSpoofed 
          ? "bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900/30" 
          : "bg-indigo-50 dark:bg-indigo-900/10 border-indigo-100 dark:border-indigo-900/20"
      }`}
    >
      {/* Decorative Background Icon */}
      <div className="absolute -right-10 -bottom-10 opacity-[0.03] dark:opacity-[0.05]">
        <ShieldCheck size={280} />
      </div>

      <div className="flex justify-between items-start relative z-10">
        <div>
          <p className="text-gray-500 dark:text-white/60 font-medium mb-1">System Security Health</p>
          <div className="flex items-baseline gap-2">
            <h2 className={`text-5xl font-bold tracking-tight dark:text-white ${isSpoofed ? 'text-red-600' : 'text-indigo-950'}`}>
              {prediction ? `${healthScore}%` : '---%'}
            </h2>
          </div>
        </div>
        <div className={`p-4 rounded-3xl ${isSpoofed ? 'bg-red-500 text-white shadow-red-200 shadow-xl' : 'bg-indigo-950 dark:bg-accent-primary text-white shadow-indigo-200 shadow-xl'}`}>
           {isSpoofed ? <AlertTriangle size={32} className="animate-pulse" /> : <ShieldCheck size={32} />}
        </div>
      </div>

      <div className="flex gap-4 mt-8 relative z-10">
        <ActionButton icon={Radar} label="Scan" primary onClick={onScan} spin={isProcessing} />
        <ActionButton icon={FileText} label="Report" onClick={onReport} />
        <ActionButton icon={Layers} label="History" />
        <ActionButton icon={RefreshCw} label="Reset" spin={isProcessing} onClick={onReset} />
      </div>
    </motion.div>
  );
}

function ActionButton({ icon: Icon, label, primary = false, spin = false, onClick }: { icon: any, label: string, primary?: boolean, spin?: boolean, onClick?: () => void }) {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={`flex flex-col items-center gap-2 group`}
      onClick={onClick}
    >
      <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
        primary 
          ? "bg-indigo-950 dark:bg-accent-primary text-white shadow-lg" 
          : "bg-white dark:bg-dark-bg text-indigo-950 dark:text-white shadow-md group-hover:bg-indigo-50 dark:group-hover:bg-white/5"
      }`}>
        <Icon size={20} className={spin ? "animate-spin" : ""} />
      </div>
      <span className="text-xs font-semibold text-gray-500 dark:text-white/40 uppercase tracking-tighter">{label}</span>
    </motion.button>
  );
}
