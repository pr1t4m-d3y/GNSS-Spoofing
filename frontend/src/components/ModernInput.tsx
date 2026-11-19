"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useState, useCallback } from "react";
import { UploadCloud, Zap, Sliders } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function ModernInput({ 
  onFileUpload, 
  onManualInject, 
  isProcessing 
}: { 
  onFileUpload: (file: File) => void, 
  onManualInject: (data: any) => void,
  isProcessing: boolean
}) {
  const [activeTab, setActiveTab] = useState<'manual'|'file'>('file');

  const [manualData, setManualData] = useState({
    PRN: 1,
    Carrier_Doppler_hz: 2761,
    Pseudorange_m: 505867,
    CN0: 46,
    Carrier_phase: -109573,
    TOW: 491655,
    RX_time: 491655,
    EC: 119937, LC: 119767, PC: 133558,
    PIP: -3701, PQP: 196, TCD: 2760
  });

  const handleSliderChange = (key: string, val: number) => {
    setManualData(prev => ({ ...prev, [key]: val }));
  };

  const onDragOver = useCallback((e: any) => e.preventDefault(), []);
  const onDrop = useCallback((e: any) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileUpload(e.dataTransfer.files[0]);
    }
  }, [onFileUpload]);

  const handleFileSelect = (e: any) => {
    if (e.target.files && e.target.files[0]) {
      onFileUpload(e.target.files[0]);
    }
  };

  return (
    <div className="bento-card p-6 flex flex-col gap-6 h-full min-h-[400px]">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-gray-500 dark:text-white/60 font-bold uppercase tracking-widest text-xs">Signal Injection</h3>
          <p className="text-2xl font-bold dark:text-white">Input Source</p>
        </div>
        <div className="p-3 rounded-2xl bg-indigo-50 dark:bg-white/5 text-indigo-600 dark:text-accent-secondary">
          <Sliders size={20} />
        </div>
      </div>

      <div className="flex gap-2 p-1 bg-indigo-50 dark:bg-white/5 rounded-2xl">
        <button 
          className={`flex-1 py-2.5 text-xs font-bold uppercase tracking-wider rounded-xl transition-all ${activeTab === 'file' ? 'bg-white dark:bg-accent-primary text-indigo-900 dark:text-white shadow-sm' : 'text-gray-400 dark:text-white/40 hover:text-indigo-900 dark:hover:text-white'}`}
          onClick={() => setActiveTab('file')}
        >
          Batch Files
        </button>
        <button 
          className={`flex-1 py-2.5 text-xs font-bold uppercase tracking-wider rounded-xl transition-all ${activeTab === 'manual' ? 'bg-white dark:bg-accent-primary text-indigo-900 dark:text-white shadow-sm' : 'text-gray-400 dark:text-white/40 hover:text-indigo-900 dark:hover:text-white'}`}
          onClick={() => setActiveTab('manual')}
        >
          Manual Specs
        </button>
      </div>

      <div className="flex-1 overflow-hidden relative">
        <AnimatePresence mode="wait">
          {activeTab === 'file' ? (
            <motion.div 
               key="file"
               initial={{ opacity: 0, x: -20 }}
               animate={{ opacity: 1, x: 0 }}
               exit={{ opacity: 0, x: 20 }}
               className="h-full flex flex-col"
            >
              <div 
                 className={`flex-1 min-h-[200px] border-2 border-dashed rounded-3xl flex flex-col items-center justify-center p-4 transition-all ${isProcessing ? 'border-accent-primary bg-indigo-50/50 dark:bg-accent-primary/5' : 'border-gray-200 dark:border-white/10 hover:border-accent-primary hover:bg-indigo-50 dark:hover:bg-accent-primary/5'} cursor-pointer group`}
                 onDragOver={onDragOver}
                 onDrop={onDrop}
                 onClick={() => document.getElementById("file-upload")?.click()}
              >
                <input id="file-upload" type="file" accept=".csv,.json" className="hidden" onChange={handleFileSelect} />
                <div className={`w-16 h-16 mb-4 rounded-full flex items-center justify-center transition-all ${isProcessing ? 'bg-accent-primary text-white animate-pulse' : 'bg-indigo-50 dark:bg-white/5 text-gray-400 group-hover:bg-accent-primary group-hover:text-white'}`}>
                   <UploadCloud size={28} />
                </div>
                <p className="font-bold text-indigo-950 dark:text-white text-center">Drop Telemetry Log</p>
                <p className="text-xs text-gray-400 dark:text-white/20 mt-1 font-semibold uppercase tracking-widest text-center">CSV / JSON Datasets</p>
              </div>
            </motion.div>
          ) : (
            <motion.div 
               key="manual"
               initial={{ opacity: 0, x: 20 }}
               animate={{ opacity: 1, x: 0 }}
               exit={{ opacity: 0, x: -20 }}
               className="flex flex-col gap-6 pt-2"
            >
               <ManualSlider label="Carrier Doppler" unit="Hz" min={-10000} max={10000} value={manualData.Carrier_Doppler_hz} onChange={(v) => handleSliderChange('Carrier_Doppler_hz', v)} />
               <ManualSlider label="Pseudorange" unit="m" min={-2000000} max={6000000} value={manualData.Pseudorange_m} onChange={(v) => handleSliderChange('Pseudorange_m', v)} />
               <ManualSlider label="CN0 Ratio" unit="dB-Hz" min={20} max={55} value={manualData.CN0} onChange={(v) => handleSliderChange('CN0', v)} />

               <motion.button 
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => onManualInject(manualData)}
                  disabled={isProcessing}
                  className="mt-4 w-full py-4 bg-indigo-950 dark:bg-accent-primary text-white rounded-2xl font-bold uppercase tracking-widest transition-all shadow-lg hover:shadow-indigo-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
               >
                  <Zap size={18} />
                  {isProcessing ? "Injecting..." : "Inject Signal"}
               </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function ManualSlider({ label, unit, min, max, value, onChange }: { label: string, unit: string, min: number, max: number, value: number, onChange: (v: number) => void }) {
  return (
    <div className="flex flex-col gap-3">
        <div className="flex justify-between items-end">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">{label}</span>
            <div className="flex items-center gap-2">
                <input 
                  type="number" 
                  value={value} 
                  onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
                  className="w-24 px-2 py-1 text-sm font-black text-indigo-950 dark:text-white bg-indigo-50/50 dark:bg-white/5 rounded-lg border border-indigo-100 dark:border-white/10 text-right focus:outline-none focus:ring-1 focus:ring-accent-primary"
                />
                <span className="text-[10px] text-gray-400">{unit}</span>
            </div>
        </div>
        <input 
           type="range" min={min} max={max} step={label === 'CN0 Ratio' ? 1 : 100} 
           value={value}
           onChange={(e) => onChange(parseFloat(e.target.value))}
           className="w-full h-1.5 bg-gray-100 dark:bg-white/5 rounded-full appearance-none cursor-pointer accent-accent-primary" 
        />
    </div>
  );
}
