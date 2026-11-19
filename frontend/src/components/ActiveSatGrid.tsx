"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Satellite, X } from "lucide-react";
import { useState } from "react";
import type { SatelliteStat } from "@/types";

const MAX_VISIBLE = 7;

export default function ActiveSatGrid({ satellites }: { satellites: SatelliteStat[] }) {
  const [selectedPRN, setSelectedPRN] = useState<number | null>(null);
  const visible = satellites.slice(0, MAX_VISIBLE);
  const selected = satellites.find((s) => s.prn === selectedPRN) ?? null;

  return (
    <div className="flex flex-col gap-4 relative">
      <div className="flex items-center gap-2">
        <Satellite size={14} className="text-indigo-600 dark:text-accent-secondary" />
        <h3 className="text-gray-500 dark:text-white/60 font-bold uppercase tracking-widest text-xs">
          Satellites in view
        </h3>
      </div>

      {visible.length === 0 ? (
        <p className="text-xs font-bold text-gray-400 dark:text-white/30">No telemetry analysed yet.</p>
      ) : (
        <div className="flex flex-wrap gap-4 items-center">
          {visible.map((sat, i) => (
            <motion.div
              key={sat.prn}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: i * 0.1 }}
              className="flex flex-col items-center gap-1 group cursor-pointer"
              onClick={() => setSelectedPRN((prev) => (prev === sat.prn ? null : sat.prn))}
            >
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center shadow-sm border transition-all ${
                  selectedPRN === sat.prn
                    ? "bg-indigo-950 dark:bg-accent-primary text-white border-indigo-500 shadow-lg scale-110"
                    : sat.spoofedSamples > 0
                      ? "bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-900/30"
                      : "bg-gradient-to-tr from-indigo-100 to-indigo-50 dark:from-white/5 dark:to-white/10 border-white/50 dark:border-white/5 group-hover:shadow-md"
                }`}
              >
                <span
                  className={`font-bold text-xs ${
                    selectedPRN === sat.prn ? "text-white" : "text-indigo-900 dark:text-white"
                  }`}
                >
                  {sat.prn}
                </span>
              </div>
              <span className="text-[10px] font-bold text-gray-400 dark:text-white/20 uppercase tracking-tighter">
                PRN
              </span>
            </motion.div>
          ))}
          {satellites.length > MAX_VISIBLE && (
            <span className="text-xs font-bold text-gray-400">+{satellites.length - MAX_VISIBLE} more</span>
          )}
        </div>
      )}

      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full left-0 right-0 mt-2 z-50"
          >
            <div className="bg-white dark:bg-dark-card rounded-2xl p-4 shadow-xl dark:shadow-none border border-indigo-100 dark:border-white/10">
              <div className="flex justify-between items-center mb-3">
                <span className="font-bold text-sm text-indigo-950 dark:text-white">PRN {selected.prn}</span>
                <button
                  onClick={() => setSelectedPRN(null)}
                  className="w-6 h-6 rounded-full bg-gray-100 dark:bg-white/5 flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors"
                >
                  <X size={12} />
                </button>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <Cell label="Samples" value={String(selected.samples)} />
                <Cell label="Flagged" value={String(selected.spoofedSamples)} />
                <Cell label="Mean CN0" value={`${selected.meanCn0.toFixed(1)} dB-Hz`} />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Cell({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-indigo-50 dark:bg-white/5 rounded-xl p-2.5 text-center">
      <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest mb-0.5">{label}</p>
      <p className="text-sm font-black text-indigo-950 dark:text-white">{value}</p>
    </div>
  );
}
