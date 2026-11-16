"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useState, useCallback } from "react";
import { UploadCloud, Zap, Sliders } from "lucide-react";

export default function SidebarInput({ 
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
    Carrier_Doppler_hz: 1500,
    Pseudorange_m: 22000000,
    CN0: 45,
    Carrier_phase: 115000000,
    TOW: 350000,
    RX_time: 350000.073,
    EC: 100, LC: 98, PC: 102,
    PIP: 50, PQP: 2, TCD: 0.1
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
    <div className="glass-panel p-6 h-full flex flex-col gap-6 overflow-hidden relative">
      <div className="flex justify-between items-center border-b border-midnight-border pb-4">
        <h2 className="text-xl font-mono neon-text uppercase tracking-widest flex items-center gap-2">
           <Zap className="w-5 h-5 text-neon-cyan" />
           Telemetry Input
        </h2>
      </div>

      <div className="flex rounded-md bg-midnight-dark/50 p-1 border border-midnight-border">
        <button 
          className={`flex-1 py-2 text-xs font-mono uppercase tracking-wider rounded transition-colors ${activeTab === 'file' ? 'bg-neon-cyan/20 text-neon-cyan' : 'text-gray-400 hover:text-gray-200'}`}
          onClick={() => setActiveTab('file')}
        >
          Batch Upload
        </button>
        <button 
          className={`flex-1 py-2 text-xs font-mono uppercase tracking-wider rounded transition-colors ${activeTab === 'manual' ? 'bg-neon-cyan/20 text-neon-cyan' : 'text-gray-400 hover:text-gray-200'}`}
          onClick={() => setActiveTab('manual')}
        >
          Manual Inject
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-hide pr-2 flex flex-col gap-4">
        {activeTab === 'file' ? (
          <div 
             className={`flex-1 border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 transition-all ${isProcessing ? 'border-neon-cyan/50 bg-neon-cyan/5' : 'border-midnight-border hover:border-neon-cyan hover:bg-neon-cyan/5'} cursor-pointer h-full min-h-[250px]`}
             onDragOver={onDragOver}
             onDrop={onDrop}
             onClick={() => document.getElementById("file-upload")?.click()}
          >
            <input id="file-upload" type="file" accept=".csv,.json" className="hidden" onChange={handleFileSelect} />
            <UploadCloud className={`w-16 h-16 mb-4 ${isProcessing ? 'text-neon-cyan animate-bounce' : 'text-gray-500'}`} />
            <p className="text-sm text-gray-300 font-mono text-center">Drag & drop signal log<br/>CSV or JSON</p>
            <p className="text-xs text-gray-500 mt-2">or click to browse</p>
          </div>
        ) : (
          <div className="flex flex-col gap-6 pt-2">
             <div className="flex flex-col gap-2">
                 <div className="flex justify-between text-xs font-mono text-gray-300">
                     <span>Carrier Doppler (Hz)</span>
                     <span className="text-neon-cyan bg-midnight-dark px-2 rounded border border-midnight-border">{manualData.Carrier_Doppler_hz}</span>
                 </div>
                 <input type="range" min="-5000" max="5000" step="10" 
                        value={manualData.Carrier_Doppler_hz}
                        onChange={(e) => handleSliderChange('Carrier_Doppler_hz', parseFloat(e.target.value))}
                        className="w-full h-1 bg-midnight-border rounded-lg appearance-none cursor-pointer" />
             </div>
             
             <div className="flex flex-col gap-2">
                 <div className="flex justify-between text-xs font-mono text-gray-300">
                     <span>Pseudorange (m)</span>
                     <span className="text-neon-cyan bg-midnight-dark px-2 rounded border border-midnight-border">{manualData.Pseudorange_m}</span>
                 </div>
                 <input type="range" min="20000000" max="25000000" step="1000" 
                        value={manualData.Pseudorange_m}
                        onChange={(e) => handleSliderChange('Pseudorange_m', parseFloat(e.target.value))}
                        className="w-full h-1 bg-midnight-border rounded-lg appearance-none cursor-pointer" />
             </div>

             <div className="flex flex-col gap-2">
                 <div className="flex justify-between text-xs font-mono text-gray-300">
                     <span>CN0 Ratio (dB-Hz)</span>
                     <span className="text-neon-cyan bg-midnight-dark px-2 rounded border border-midnight-border">{manualData.CN0}</span>
                 </div>
                 <input type="range" min="20" max="55" step="1" 
                        value={manualData.CN0}
                        onChange={(e) => handleSliderChange('CN0', parseFloat(e.target.value))}
                        className="w-full h-1 bg-midnight-border rounded-lg appearance-none cursor-pointer" />
             </div>

             <button 
                onClick={() => onManualInject(manualData)}
                disabled={isProcessing}
                className="mt-6 w-full py-3 bg-neon-cyan/10 hover:bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/50 hover:border-neon-cyan rounded-lg font-mono uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(0,243,255,0.1)] hover:shadow-[0_0_20px_rgba(0,243,255,0.3)] flex items-center justify-center gap-2 disabled:opacity-50"
             >
                <Sliders className="w-4 h-4" />
                {isProcessing ? "Injecting..." : "Inject Signal"}
             </button>
          </div>
        )}
      </div>
    </div>
  );
}
