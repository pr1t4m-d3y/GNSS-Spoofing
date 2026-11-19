"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { motion } from "framer-motion";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { useMemo } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";
import type { SignalPoint } from "@/types";

interface FluidChartProps {
  signalSeries: SignalPoint[];
}

export default function FluidChart({ signalSeries }: FluidChartProps) {
  const { data, authPercent, droppedPercent, hasSpoofed, hasData } = useMemo(() => {
    if (signalSeries.length === 0) {
      return {
        data: [] as SignalPoint[],
        authPercent: "—",
        droppedPercent: "—",
        hasSpoofed: false,
        hasData: false,
      };
    }

    // Sliding window: show last 100 points
    const windowed = signalSeries.slice(-100);
    
    const totalItems = windowed.length;
    const spoofedCount = windowed.filter(d => d.is_spoofed).length;
    const authPct = totalItems > 0 ? ((totalItems - spoofedCount) / totalItems * 100).toFixed(1) : "100.0";
    const dropPct = totalItems > 0 ? (spoofedCount / totalItems * 100).toFixed(1) : "0.0";
    
    return { 
      data: windowed.map((p, i) => ({ ...p, index: i })), 
      authPercent: authPct, 
      droppedPercent: dropPct, 
      hasSpoofed: spoofedCount > 0,
      hasData: true,
    };
  }, [signalSeries]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bento-card p-6 h-full flex flex-col gap-4"
    >
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 relative z-10">
         <div>
            <h3 className="text-gray-500 dark:text-white/60 font-bold uppercase tracking-widest text-[10px]">Security Statistics</h3>
            <p className="text-xl font-bold dark:text-white mt-1">Signal Series</p>
         </div>
         <div className={`px-3 py-1.5 rounded-xl text-[10px] font-bold uppercase tracking-wider ${
           hasSpoofed 
             ? "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400" 
             : "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
         }`}>
           {!hasData ? "No data" : hasSpoofed ? "Anomalies Detected" : "All Clear"}
         </div>
      </div>

      <div className="flex-1 w-full min-h-[180px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="scoreGradientMain" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={hasSpoofed ? "#ef4444" : "#4318FF"} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={hasSpoofed ? "#ef4444" : "#4318FF"} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} strokeOpacity={0.1} />
            <XAxis 
               dataKey="index" 
               axisLine={false} 
               tickLine={false} 
               tick={{ fontSize: 9, fontWeight: 700, fill: '#A3AED0' }}
               label={{ value: "Signal Packet", position: "insideBottomRight", offset: -5, fontSize: 9, fill: '#A3AED0', fontWeight: 700 }}
            />
            <YAxis 
               axisLine={false} 
               tickLine={false} 
               domain={[0, 100]}
               tick={{ fontSize: 9, fontWeight: 700, fill: '#A3AED0' }} 
            />
            <Tooltip 
               cursor={{ stroke: '#4318FF', strokeWidth: 1, strokeDasharray: '4 4' }}
               contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0px 18px 40px rgba(112, 144, 176, 0.12)', backgroundColor: '#fff', color: '#1B2559', fontSize: '12px' }}
               formatter={(value: any) => [`${Number(value).toFixed(1)}%`, 'Anomaly Score']}
               labelFormatter={(label: any) => `Packet #${label}`}
            />
            <Area 
               type="monotone" 
               dataKey="score" 
               stroke={hasSpoofed ? "#ef4444" : "#4318FF"} 
               strokeWidth={2}
               fillOpacity={1} 
               fill="url(#scoreGradientMain)" 
               dot={false}
               activeDot={{ r: 4, fill: hasSpoofed ? "#ef4444" : "#4318FF", stroke: '#fff', strokeWidth: 2 }}
               isAnimationActive={true}
               animationDuration={800}
               animationEasing="ease-in-out"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-4 mt-auto">
         <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-indigo-50 dark:bg-white/5 flex items-center justify-center text-indigo-600 dark:text-accent-secondary">
               <TrendingDown size={18} />
            </div>
            <div>
               <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Auth signals</p>
               <p className="text-sm font-bold dark:text-white">{authPercent}{hasData ? "%" : ""}</p>
            </div>
         </div>
         <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              hasSpoofed 
                ? "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400" 
                : "bg-indigo-50 dark:bg-white/5 text-indigo-600 dark:text-accent-secondary"
            }`}>
               <TrendingUp size={18} />
            </div>
            <div>
               <p className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">DROPPED</p>
               <p className={`text-sm font-bold ${hasSpoofed ? 'text-red-600 dark:text-red-400' : 'dark:text-white'}`}>{droppedPercent}{hasData ? "%" : ""}</p>
            </div>
         </div>
      </div>
    </motion.div>
  );
}
