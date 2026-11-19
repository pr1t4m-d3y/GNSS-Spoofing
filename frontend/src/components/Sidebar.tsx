"use client";

import { motion } from "framer-motion";
import { Home, Satellite, Bell, Terminal, ShieldCheck } from "lucide-react";

const menuItems = [
  { icon: Home, label: "Home", id: "home" },
  { icon: Satellite, label: "Satellites", id: "satellites" },
  { icon: Bell, label: "Alerts", id: "alerts" },
  { icon: Terminal, label: "Logs", id: "logs" },
];

interface SidebarProps {
  activeView: string;
  onNavigate: (viewId: string) => void;
}

export default function Sidebar({ activeView, onNavigate }: SidebarProps) {
  return (
    <div className="sidebar-container flex flex-col h-full shadow-soft dark:shadow-none">
      <div className="flex items-center gap-3 px-2 mb-10">
        <div className="w-10 h-10 bg-white dark:bg-dark-bg rounded-xl flex items-center justify-center shadow-sm">
          <ShieldCheck className="text-accent-primary w-6 h-6" />
        </div>
        <span className="font-bold text-xl tracking-tight text-indigo-900 dark:text-white">GNSS Guard</span>
      </div>

      <nav className="flex-1 space-y-2">
        {menuItems.map((item) => (
          <motion.button
            key={item.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-4 px-4 py-3 rounded-2xl transition-all duration-200 ${
              activeView === item.id
                ? "bg-indigo-950 dark:bg-accent-primary text-white shadow-lg"
                : "text-indigo-900/60 dark:text-white/60 hover:bg-white/50 dark:hover:bg-white/5"
            }`}
          >
            <item.icon size={20} />
            <span className="font-medium">{item.label}</span>
            {activeView === item.id && (
              <motion.div
                layoutId="active-pill"
                className="ml-auto w-1.5 h-1.5 rounded-full bg-white"
              />
            )}
          </motion.button>
        ))}
      </nav>

    </div>
  );
}
