"use client";

import { motion } from "framer-motion";
import { Satellite, Signal } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import type { SatelliteInfo } from "@/types";

// Hardcoded satellite data for prototype
const SATELLITES: SatelliteInfo[] = [
  { prn: 8,  snr: 42, elevation: 15, status: "Healthy", lastSeen: "Now",     history: [12, 8, 15, 10, 9, 11, 13, 8, 10, 12] },
  { prn: 12, snr: 44, elevation: 32, status: "Healthy", lastSeen: "Now",     history: [10, 12, 9, 11, 8, 10, 9, 11, 10, 8] },
  { prn: 14, snr: 38, elevation: 21, status: "Healthy", lastSeen: "Now",     history: [15, 18, 14, 20, 16, 19, 17, 22, 18, 15] },
  { prn: 21, snr: 46, elevation: 55, status: "Healthy", lastSeen: "Now",     history: [5, 6, 4, 7, 5, 6, 8, 5, 4, 6] },
  { prn: 24, snr: 40, elevation: 42, status: "Healthy", lastSeen: "Now",     history: [9, 11, 13, 10, 12, 8, 10, 14, 11, 9] },
  { prn: 28, snr: 42, elevation: 38, status: "Healthy", lastSeen: "2s ago",  history: [7, 9, 8, 10, 7, 11, 8, 9, 7, 10] },
  { prn: 31, snr: 35, elevation: 10, status: "Degraded", lastSeen: "5s ago",  history: [25, 30, 35, 28, 40, 38, 32, 45, 42, 38] },
  { prn: 3,  snr: 30, elevation: 8,  status: "Degraded", lastSeen: "12s ago", history: [30, 35, 40, 38, 45, 50, 42, 55, 48, 52] },
];

export default function SatellitesView() {
  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-indigo-950 dark:text-white tracking-tight">Satellite Constellation</h1>
          <p className="text-sm font-bold text-gray-400 dark:text-white/20 uppercase tracking-widest mt-1">{SATELLITES.length} Active Vehicles</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-bold text-emerald-500 uppercase tracking-wider">Tracking Live</span>
        </div>
      </div>

      {/* Satellite Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SATELLITES.map((sat, i) => (
          <motion.div
            key={sat.prn}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`bento-card p-5 flex flex-col gap-4 hover:shadow-lg transition-shadow cursor-pointer ${
              sat.status === "Degraded" ? "border-yellow-200 dark:border-yellow-900/30" : ""
            }`}
          >
            {/* Top: PRN + Status */}
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className={`w-11 h-11 rounded-2xl flex items-center justify-center shadow-sm ${
                  sat.status === "Healthy" 
                    ? "bg-indigo-50 dark:bg-white/5 text-indigo-600 dark:text-accent-secondary" 
                    : "bg-yellow-50 dark:bg-yellow-500/10 text-yellow-600 dark:text-yellow-400"
                }`}>
                  <Satellite size={20} />
                </div>
                <div>
                  <h3 className="font-black text-indigo-950 dark:text-white">GPS PRN {sat.prn}</h3>
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{sat.lastSeen}</p>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                sat.status === "Healthy" 
                  ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" 
                  : "bg-yellow-50 dark:bg-yellow-500/10 text-yellow-600 dark:text-yellow-400"
              }`}>
                {sat.status}
              </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-indigo-50/50 dark:bg-white/[0.03] rounded-xl p-2.5 text-center">
                <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">SNR</p>
                <p className="text-sm font-black text-indigo-950 dark:text-white mt-0.5">{sat.snr} <span className="text-[9px] text-gray-400">dB</span></p>
              </div>
              <div className="bg-indigo-50/50 dark:bg-white/[0.03] rounded-xl p-2.5 text-center">
                <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Elev</p>
                <p className="text-sm font-black text-indigo-950 dark:text-white mt-0.5">{sat.elevation}°</p>
              </div>
              <div className="bg-indigo-50/50 dark:bg-white/[0.03] rounded-xl p-2.5 text-center">
                <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Signal</p>
                <div className="flex items-center justify-center gap-1 mt-0.5">
                  <Signal size={12} className={sat.snr > 40 ? "text-emerald-500" : "text-yellow-500"} />
                  <p className={`text-sm font-black ${sat.snr > 40 ? "text-emerald-600 dark:text-emerald-400" : "text-yellow-600 dark:text-yellow-400"}`}>
                    {sat.snr > 40 ? "Strong" : "Weak"}
                  </p>
                </div>
              </div>
            </div>

            {/* Mini Health Sparkline */}
            <div className="flex items-center gap-3">
              <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap">Health History</p>
              <div className="flex-1 h-8">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={sat.history.map((v, idx) => ({ i: idx, v }))}>
                    <defs>
                      <linearGradient id={`spark-${sat.prn}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={sat.status === "Healthy" ? "#4318FF" : "#eab308"} stopOpacity={0.3}/>
                        <stop offset="100%" stopColor={sat.status === "Healthy" ? "#4318FF" : "#eab308"} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <Area type="monotone" dataKey="v" stroke={sat.status === "Healthy" ? "#4318FF" : "#eab308"} strokeWidth={1.5} fill={`url(#spark-${sat.prn})`} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
