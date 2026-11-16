"use client";

import { motion } from "framer-motion";
import { Gauge, Palette, Bell, BellOff, Sun, Moon, Shield, Save } from "lucide-react";
import { useState } from "react";
import type { AppSettings } from "@/types";

interface SettingsViewProps {
  settings: AppSettings;
  onUpdateSettings: (settings: AppSettings) => void;
}

export default function SettingsView({ settings, onUpdateSettings }: SettingsViewProps) {
  const [local, setLocal] = useState<AppSettings>({ ...settings });
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    onUpdateSettings(local);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-indigo-950 dark:text-white tracking-tight">Settings</h1>
          <p className="text-sm font-bold text-gray-400 dark:text-white/20 uppercase tracking-widest mt-1">System Configuration</p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSave}
          className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-bold uppercase tracking-wider text-xs transition-all ${
            saved 
              ? "bg-emerald-500 text-white shadow-lg" 
              : "bg-indigo-950 dark:bg-accent-primary text-white shadow-lg hover:shadow-indigo-500/20"
          }`}
        >
          {saved ? <Shield size={16} /> : <Save size={16} />}
          {saved ? "Saved!" : "Save Changes"}
        </motion.button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection Sensitivity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bento-card p-6 flex flex-col gap-5"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 dark:bg-white/5 flex items-center justify-center text-indigo-600 dark:text-accent-secondary">
              <Gauge size={20} />
            </div>
            <div>
              <h3 className="font-bold text-indigo-950 dark:text-white">Detection Sensitivity</h3>
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Anomaly Threshold</p>
            </div>
          </div>
          
          <div className="flex flex-col gap-3">
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Threshold</span>
              <span className="text-sm font-black text-indigo-950 dark:text-white">{local.sensitivity}%</span>
            </div>
            <input 
              type="range" 
              min={10} max={90} step={5}
              value={local.sensitivity}
              onChange={(e) => setLocal(prev => ({ ...prev, sensitivity: parseInt(e.target.value) }))}
              className="w-full h-2 bg-gray-100 dark:bg-white/5 rounded-full appearance-none cursor-pointer accent-accent-primary"
            />
            <div className="flex justify-between text-[9px] font-bold text-gray-400 uppercase tracking-widest">
              <span>Permissive</span>
              <span>Aggressive</span>
            </div>
          </div>

          <div className="bg-indigo-50/50 dark:bg-white/[0.03] rounded-xl p-3 mt-auto">
            <p className="text-[10px] text-gray-400 dark:text-white/40 leading-relaxed">
              {local.sensitivity < 30 
                ? "Low sensitivity. Fewer false positives but may miss subtle spoofing attempts." 
                : local.sensitivity > 70 
                  ? "High sensitivity. Catches subtle anomalies but may trigger more false alerts." 
                  : "Balanced sensitivity. Good trade-off between detection accuracy and false alarm rate."}
            </p>
          </div>
        </motion.div>

        {/* UI Theme */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="bento-card p-6 flex flex-col gap-5"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 dark:bg-white/5 flex items-center justify-center text-indigo-600 dark:text-accent-secondary">
              <Palette size={20} />
            </div>
            <div>
              <h3 className="font-bold text-indigo-950 dark:text-white">UI Theme</h3>
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Visual Configuration</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {(["light", "dark", "security"] as const).map((theme) => (
              <motion.button
                key={theme}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => {
                  setLocal(prev => ({ ...prev, theme }));
                  // Apply theme immediately for visual feedback
                  if (theme === "dark" || theme === "security") {
                    document.documentElement.classList.add("dark");
                  } else {
                    document.documentElement.classList.remove("dark");
                  }
                  localStorage.setItem("theme", theme);
                }}
                className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${
                  local.theme === theme 
                    ? "border-indigo-500 dark:border-accent-primary bg-indigo-50 dark:bg-white/5 shadow-md" 
                    : "border-transparent bg-gray-50 dark:bg-white/[0.02] hover:bg-indigo-50/50 dark:hover:bg-white/[0.04]"
                }`}
              >
                {theme === "light" && <Sun size={20} className="text-yellow-500" />}
                {theme === "dark" && <Moon size={20} className="text-indigo-400" />}
                {theme === "security" && <Shield size={20} className="text-emerald-500" />}
                <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500 dark:text-white/40">{theme}</span>
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Notifications */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bento-card p-6 flex flex-col gap-5 lg:col-span-2"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-2xl flex items-center justify-center ${
                local.notificationsEnabled 
                  ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" 
                  : "bg-gray-100 dark:bg-white/5 text-gray-400"
              }`}>
                {local.notificationsEnabled ? <Bell size={20} /> : <BellOff size={20} />}
              </div>
              <div>
                <h3 className="font-bold text-indigo-950 dark:text-white">Desktop Notifications</h3>
                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Spoofing Detection Alerts</p>
              </div>
            </div>

            {/* Toggle Switch */}
            <motion.button
              onClick={() => setLocal(prev => ({ ...prev, notificationsEnabled: !prev.notificationsEnabled }))}
              className={`w-14 h-8 rounded-full p-1 transition-colors duration-200 ${
                local.notificationsEnabled ? "bg-emerald-500" : "bg-gray-300 dark:bg-white/10"
              }`}
            >
              <motion.div
                animate={{ x: local.notificationsEnabled ? 22 : 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
                className="w-6 h-6 bg-white rounded-full shadow-md"
              />
            </motion.button>
          </div>

          <p className="text-xs text-gray-400 dark:text-white/40 leading-relaxed">
            When enabled, the system will display browser notifications whenever a spoofing attempt is detected. 
            This works independently of the dashboard — you&apos;ll be alerted even if the tab is in the background.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
