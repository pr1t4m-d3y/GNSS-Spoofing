"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Plus, Satellite, X } from "lucide-react";
import { useState } from "react";

// Hardcoded PRN stats for prototype
const PRN_STATS: Record<number, { signal: number; elevation: number; status: string }> = {
  8:  { signal: 42, elevation: 15, status: "Healthy" },
  12: { signal: 44, elevation: 32, status: "Healthy" },
  14: { signal: 38, elevation: 21, status: "Healthy" },
  21: { signal: 46, elevation: 55, status: "Healthy" },
  24: { signal: 40, elevation: 42, status: "Healthy" },
  31: { signal: 35, elevation: 10, status: "Healthy" },
};

export default function ActiveSatGrid({ satellites }: { satellites: number[] }) {
  const activePRNs = satellites.length > 0 ? satellites.slice(0, 7) : [8, 12, 14, 21, 24, 31];
  const [selectedPRN, setSelectedPRN] = useState<number | null>(null);

  const handlePRNClick = (prn: number) => {
    setSelectedPRN(prev => prev === prn ? null : prn);
  };

  const stats = selectedPRN ? (PRN_STATS[selectedPRN] || { signal: 42, elevation: 15, status: "Healthy" }) : null;

  return (
    <div className="flex flex-col gap-4 relative">
      <div className="flex items-center gap-2">
        <Satellite size={14} className="text-indigo-600 dark:text-accent-secondary" />
        <h3 className="text-gray-500 dark:text-white/60 font-bold uppercase tracking-widest text-xs">Active Constellation</h3>
      </div>
      <div className="flex flex-wrap gap-4 items-center">
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className="w-12 h-12 rounded-full border-2 border-dashed border-gray-300 dark:border-white/10 flex items-center justify-center text-gray-400 dark:text-white/20"
        >
          <Plus size={20} />
        </motion.button>

        {activePRNs.map((prn, i) => (
          <motion.div
            key={prn}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: i * 0.1 }}
            className="flex flex-col items-center gap-1 group cursor-pointer"
            onClick={() => handlePRNClick(prn)}
          >
            <div className={`w-12 h-12 rounded-full flex items-center justify-center shadow-sm border transition-all ${
              selectedPRN === prn 
                ? "bg-indigo-950 dark:bg-accent-primary text-white border-indigo-500 shadow-lg scale-110" 
                : "bg-gradient-to-tr from-indigo-100 to-indigo-50 dark:from-white/5 dark:to-white/10 border-white/50 dark:border-white/5 group-hover:shadow-md"
            }`}>
               <span className={`font-bold text-xs ${selectedPRN === prn ? "text-white" : "text-indigo-900 dark:text-white"}`}>{prn}</span>
            </div>
            <span className="text-[10px] font-bold text-gray-400 dark:text-white/20 uppercase tracking-tighter">PRN</span>
          </motion.div>
        ))}
        
        {activePRNs.length > 5 && (
           <motion.div 
             className="w-12 h-12 rounded-full bg-indigo-900 dark:bg-accent-primary flex items-center justify-center text-white font-bold text-xs shadow-lg cursor-pointer hover:scale-110 transition-transform"
             onClick={() => setSelectedPRN(-1)}
             whileTap={{ scale: 0.9 }}
           >
             +{satellites.length - 6 > 0 ? satellites.length - 6 : 4}
           </motion.div>
        )}
      </div>

      {/* PRN Stats Popup */}
      <AnimatePresence>
        {selectedPRN !== null && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full left-0 right-0 mt-2 z-50"
          >
            <div className="bg-white dark:bg-dark-card rounded-2xl p-4 shadow-xl dark:shadow-none border border-indigo-100 dark:border-white/10">
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-2">
                  <Satellite size={14} className="text-indigo-600 dark:text-accent-secondary" />
                  <span className="font-bold text-sm text-indigo-950 dark:text-white">
                    {selectedPRN === -1 ? "Overflow Satellites" : `PRN ${selectedPRN}`}
                  </span>
                </div>
                <button 
                  onClick={(e) => { e.stopPropagation(); setSelectedPRN(null); }}
                  className="w-6 h-6 rounded-full bg-gray-100 dark:bg-white/5 flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors"
                >
                  <X size={12} />
                </button>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-indigo-50 dark:bg-white/5 rounded-xl p-2.5 text-center">
                  <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest mb-0.5">Signal</p>
                  <p className="text-sm font-black text-indigo-950 dark:text-white">{stats?.signal || 42} dB</p>
                </div>
                <div className="bg-indigo-50 dark:bg-white/5 rounded-xl p-2.5 text-center">
                  <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest mb-0.5">Elevation</p>
                  <p className="text-sm font-black text-indigo-950 dark:text-white">{stats?.elevation || 15}°</p>
                </div>
                <div className="bg-emerald-50 dark:bg-emerald-500/10 rounded-xl p-2.5 text-center">
                  <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest mb-0.5">Status</p>
                  <p className="text-sm font-black text-emerald-600 dark:text-emerald-400">{stats?.status || "Healthy"}</p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
