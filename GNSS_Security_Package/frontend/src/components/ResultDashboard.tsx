"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useMemo } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, CheckCircle, Database, Shield } from "lucide-react";

export default function ResultDashboard({ prediction, error, isProcessing }: { prediction: any, error: string | null, isProcessing: boolean }) {
  
  const isSpoofed = prediction?.summary?.spoofed_samples > 0 || (prediction?.predictions && prediction.predictions[0]?.is_spoofed);
  
  const timelineData = useMemo(() => {
    if (!prediction?.timeline && !prediction?.features) return [];
    
    // Convert to recharts format
    const source = prediction.timeline || prediction.features;
    return source.map((item: any, i: number) => ({
      index: i,
      score: item.anomaly_score * 100, // percentage
      doppler: item.Carrier_Doppler_hz,
      is_spoofed: item.is_spoofed ? 100 : 0
    }));
  }, [prediction]);

  if (error) {
    return (
      <div className="glass-panel p-6 h-full flex flex-col gap-4 border-signal-red">
         <h2 className="text-xl font-mono text-signal-red uppercase tracking-widest flex items-center gap-2">
           <AlertTriangle /> Error
         </h2>
         <p className="text-sm text-red-400 font-mono">{error}</p>
      </div>
    );
  }

  if (!prediction && !isProcessing) {
    return (
      <div className="glass-panel p-6 h-full flex flex-col justify-center items-center text-gray-500 gap-4">
         <Database className="w-12 h-12" />
         <p className="font-mono text-sm">Awaiting telemetry datastream...</p>
      </div>
    );
  }

  const score = prediction?.summary ? prediction.summary.average_anomaly_score * 100 : (prediction?.predictions?.[0]?.anomaly_score * 100) || 0;

  return (
    <div className={`glass-panel p-6 h-full flex flex-col gap-6 overflow-hidden transition-opacity duration-300 ${isProcessing ? 'opacity-50' : 'opacity-100'}`}>
      <div className="flex justify-between items-center border-b border-midnight-border pb-4">
        <h2 className={`text-xl font-mono uppercase tracking-widest flex items-center gap-2 ${isSpoofed ? 'text-signal-red drop-shadow-[0_0_8px_rgba(255,0,60,0.8)]' : 'text-signal-green drop-shadow-[0_0_8px_rgba(0,255,102,0.8)]'}`}>
           <Shield className="w-6 h-6" />
           Threat Analysis
        </h2>
      </div>

      <div className="flex-1 flex flex-col gap-6 overflow-y-auto scrollbar-hide pr-2">
         {/* Verdict Banner */}
         <div className={`p-4 rounded-xl border flex items-center justify-between ${isSpoofed ? 'bg-signal-red/10 border-signal-red text-signal-red shadow-[inset_0_0_20px_rgba(255,0,60,0.2)]' : 'bg-signal-green/5 border-signal-green/50 text-signal-green shadow-[inset_0_0_20px_rgba(0,255,102,0.1)]'}`}>
            <div>
               <h3 className="text-xl font-mono uppercase font-bold tracking-wider">
                 {isSpoofed ? "SPOOFING DETECTED" : "SIGNAL AUTHENTIC"}
               </h3>
               <p className="text-xs font-mono opacity-80 mt-1">
                 {prediction?.summary ? `${prediction.summary.spoofed_samples} anomalous samples out of ${prediction.summary.total_samples}` : 'Single signal validation completed'}
               </p>
            </div>
            {isSpoofed ? <AlertTriangle className="w-12 h-12 animate-pulse" /> : <CheckCircle className="w-12 h-12" />}
         </div>

         {/* Stats Row */}
         <div className="grid grid-cols-2 gap-4">
            <div className="bg-midnight-dark/50 border border-midnight-border p-4 rounded-xl flex flex-col justify-center items-center">
               <span className="text-gray-400 text-xs font-mono uppercase tracking-widest mb-2">Threat Confidence</span>
               <span className={`text-4xl font-mono font-bold drop-shadow-md ${score > 60 ? 'text-signal-red' : score > 40 ? 'text-yellow-400' : 'text-signal-green'}`}>
                 {score.toFixed(1)}%
               </span>
            </div>
            {prediction?.summary ? (
              <div className="bg-midnight-dark/50 border border-midnight-border p-4 rounded-xl flex flex-col justify-center items-center">
                 <span className="text-gray-400 text-xs font-mono uppercase tracking-widest mb-2">Total Packets</span>
                 <span className="text-4xl font-mono font-bold text-neon-cyan drop-shadow-[0_0_8px_rgba(0,243,255,0.8)]">
                   {prediction.summary.total_samples}
                 </span>
              </div>
            ) : (
                <div className="bg-midnight-dark/50 border border-midnight-border p-4 rounded-xl flex flex-col justify-center items-center">
                 <span className="text-gray-400 text-xs font-mono uppercase tracking-widest mb-2">Satellite PRN</span>
                 <span className="text-4xl font-mono font-bold text-gray-200">
                   {prediction?.features?.[0]?.PRN || 'N/A'}
                 </span>
              </div>
            )}
         </div>

         {/* Chart */}
         {timelineData.length > 0 && (
           <div className="flex-1 min-h-[250px] border border-midnight-border rounded-xl p-4 bg-midnight-dark/30 flex flex-col">
              <h4 className="text-xs font-mono text-gray-400 mb-4 uppercase tracking-widest flex items-center justify-between">
                Anomaly Score Timeline
                {isSpoofed && <span className="w-2 h-2 rounded-full bg-signal-red animate-pulse"></span>}
              </h4>
              <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timelineData}>
                    <defs>
                      <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={isSpoofed ? "#ff003c" : "#00f3ff"} stopOpacity={0.4}/>
                        <stop offset="95%" stopColor={isSpoofed ? "#ff003c" : "#00f3ff"} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="index" stroke="#444" tick={{fontSize: 10, fill: '#666', fontFamily: 'monospace'}} />
                    <YAxis stroke="#444" domain={[0, 100]} tick={{fontSize: 10, fill: '#666', fontFamily: 'monospace'}} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#050510', borderColor: 'rgba(0,243,255,0.2)', color: '#fff', fontSize: '12px', fontFamily: 'monospace', borderRadius: '8px' }}
                      itemStyle={{ color: isSpoofed ? '#ff003c' : '#00f3ff' }}
                    />
                    <Area type="monotone" dataKey="score" stroke={isSpoofed ? "#ff003c" : "#00f3ff"} strokeWidth={2} fillOpacity={1} fill="url(#scoreGradient)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
           </div>
         )}
      </div>
    </div>
  );
}
