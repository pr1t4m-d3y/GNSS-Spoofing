"use client";

import { motion } from "framer-motion";
import { Activity, ShieldAlert, ShieldCheck } from "lucide-react";

export default function AnalysisEngine({ isProcessing, isSpoofed }: { isProcessing: boolean, isSpoofed: boolean }) {
  const color = isSpoofed ? "#ff003c" : "#00f3ff";
  
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 relative overflow-hidden">
      
      {/* Background concentric circles */}
      <div className="absolute inset-0 flex items-center justify-center opacity-20 pointer-events-none">
        <motion.div 
           className="w-48 h-48 sm:w-64 sm:h-64 rounded-full border-2 border-dashed"
           style={{ borderColor: color }}
           animate={{ rotate: 360 }}
           transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        />
        <motion.div 
           className="absolute w-32 h-32 sm:w-48 sm:h-48 rounded-full border border-solid"
           style={{ borderColor: color }}
           animate={{ scale: isProcessing ? [1, 1.2, 1] : 1, opacity: isProcessing ? [0.5, 1, 0.5] : 0.5 }}
           transition={{ duration: 1.5, repeat: Infinity }}
        />
      </div>

      <div className="z-10 text-center flex flex-col items-center">
         {isSpoofed ? (
           <ShieldAlert className="w-20 h-20 text-signal-red mb-6 animate-pulse neon-red-glow" />
         ) : isProcessing ? (
           <Activity className="w-20 h-20 text-neon-cyan mb-6 animate-[spin_3s_linear_infinite] neon-text" />
         ) : (
           <ShieldCheck className="w-20 h-20 text-signal-green mb-6 drop-shadow-[0_0_10px_#00ff66]" />
         )}
         
         <h2 className={`text-2xl font-mono mb-2 uppercase tracking-widest ${isSpoofed ? 'text-signal-red neon-red-glow' : 'neon-text'}`}>
           Isolation Forest Core
         </h2>
         <div className="bg-midnight-dark/80 px-4 py-2 rounded-full border border-midnight-border mt-4">
            <span className="text-xs font-mono tracking-wider text-gray-300">
              {isProcessing ? "ANALYZING SIGNAL FEATURES..." : isSpoofed ? "ANOMALY ISOLATED" : "AWAITING TELEMETRY"}
            </span>
         </div>

         {/* Scanning line */}
         {isProcessing && (
           <motion.div 
             className="absolute left-0 right-0 h-1 bg-neon-cyan shadow-[0_0_15px_#00f3ff]"
             initial={{ top: "0%" }}
             animate={{ top: "100%" }}
             transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
           />
         )}
      </div>
    </div>
  );
}
