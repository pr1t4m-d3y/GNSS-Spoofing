"use client";

import { motion } from "framer-motion";
import { Signal, Satellite, ShieldCheck, AlertCircle } from "lucide-react";

export default function SatelliteCard({ prn, snr, isSpoofed, delay = 0 }: { prn: number, snr: number, isSpoofed: boolean, delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      className={`relative min-w-[300px] min-h-[200px] flex-shrink-0 rounded-[32px] p-6 overflow-hidden flex flex-col justify-between shadow-soft dark:shadow-none border border-transparent dark:border-white/5 ${
        isSpoofed 
          ? "bg-gradient-to-br from-red-600 to-red-900 text-white shadow-red-300 dark:shadow-red-900/40" 
          : "bg-indigo-950 dark:bg-accent-primary text-white shadow-indigo-100 dark:shadow-indigo-900/40"
      }`}
    >
      {/* Decorative Wave Design */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl" />
      <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full -ml-12 -mb-12 blur-3xl" />

      <div className="flex justify-between items-start relative z-10">
         <div className="flex flex-col">
            <span className="text-white/60 text-xs font-semibold uppercase tracking-widest mb-1">Signal Source</span>
            <div className="flex items-center gap-2">
               <Satellite size={18} className="text-white/80" />
               <span className="text-xl font-bold">GPS-PRN {prn}</span>
            </div>
         </div>
         {isSpoofed ? <AlertCircle size={24} className="animate-pulse text-red-200" /> : <ShieldCheck size={24} className="text-emerald-400 font-bold" />}
      </div>

      <div className="mt-4 relative z-10">
         <span className="text-white/60 text-xs font-semibold uppercase tracking-widest block mb-1">Carrier-to-Noise Ratio</span>
         <div className="flex items-center gap-2">
            <span className="text-3xl font-bold tracking-tighter">{snr.toFixed(1)} dB-Hz</span>
            <Signal size={20} className={snr > 40 ? 'text-emerald-400' : 'text-yellow-400'} />
         </div>
      </div>

      <div className="flex justify-between items-end relative z-10 pt-2 border-t border-white/10 mt-auto">
         <div className="flex flex-col">
            <span className="text-white/40 text-[10px] uppercase font-bold tracking-tighter">Status</span>
            <span className="text-xs font-bold">{isSpoofed ? 'COMPROMISED' : 'AUTHORIZED'}</span>
         </div>
         <div className="flex flex-col text-right">
            <span className="text-white/40 text-[10px] uppercase font-bold tracking-tighter">Validation</span>
            <span className="text-xs font-bold">SHA-256 Sig</span>
         </div>
      </div>
    </motion.div>
  );
}
