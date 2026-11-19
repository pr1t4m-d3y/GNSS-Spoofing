"use client";

import { motion } from "framer-motion";
import { Satellite } from "lucide-react";
import type { SatelliteStat } from "@/types";

export default function SatellitesView({ satellites }: { satellites: SatelliteStat[] }) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-black text-indigo-950 dark:text-white tracking-tight">Satellites</h1>
        <p className="text-sm font-bold text-gray-400 dark:text-white/20 uppercase tracking-widest mt-1">
          {satellites.length} satellites in the last analysis
        </p>
      </div>

      {satellites.length === 0 ? (
        <div className="bento-card p-8 text-center text-sm font-bold text-gray-400 dark:text-white/30">
          Analyse a telemetry file or inject a signal to see per-satellite results.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {satellites.map((sat, i) => {
            const flagged = sat.spoofedSamples > 0;
            return (
              <motion.div
                key={sat.prn}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className={`bento-card p-5 flex flex-col gap-4 ${
                  flagged ? "border-red-200 dark:border-red-900/30" : ""
                }`}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-11 h-11 rounded-2xl flex items-center justify-center shadow-sm ${
                        flagged
                          ? "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400"
                          : "bg-indigo-50 dark:bg-white/5 text-indigo-600 dark:text-accent-secondary"
                      }`}
                    >
                      <Satellite size={20} />
                    </div>
                    <h3 className="font-black text-indigo-950 dark:text-white">PRN {sat.prn}</h3>
                  </div>
                  <span
                    className={`text-[10px] font-black uppercase tracking-wider ${
                      flagged ? "text-red-600 dark:text-red-400" : "text-emerald-500"
                    }`}
                  >
                    {flagged ? "Anomalies flagged" : "No anomalies"}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <Stat label="Samples" value={String(sat.samples)} />
                  <Stat label="Flagged" value={String(sat.spoofedSamples)} />
                  <Stat label="Mean CN0" value={`${sat.meanCn0.toFixed(1)} dB-Hz`} />
                </div>
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                  Mean anomaly score {(sat.meanScore * 100).toFixed(1)}%
                </p>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-indigo-50 dark:bg-white/5 rounded-xl p-2.5">
      <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest mb-0.5">{label}</p>
      <p className="text-sm font-black text-indigo-950 dark:text-white">{value}</p>
    </div>
  );
}
