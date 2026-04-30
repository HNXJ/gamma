import React from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import { LayoutDashboard, Activity, Users, Database, FileText } from 'lucide-react'
import Overview from './routes/Overview'
import Arena from './routes/Arena'
import Agents from './routes/Agents'
import Persistence from './routes/Persistence'
import Logs from './routes/Logs'

const SidebarItem = ({ to, icon: Icon, label }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
        isActive 
          ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20' 
          : 'text-gray-400 hover:bg-white/5 hover:text-white'
      }`
    }
  >
    <Icon size={20} />
    <span className="font-medium">{label}</span>
  </NavLink>
)

export default function App() {
  return (
    <div className="flex min-h-screen bg-[#0a0a0a] text-gray-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 bg-[#0f0f0f] flex flex-col p-4 space-y-8">
        <div className="flex items-center px-4 space-x-2 text-amber-500">
          <Activity size={24} />
          <span className="text-xl font-bold tracking-tight">GAMMA ARENA</span>
        </div>
        
        <nav className="flex-1 space-y-2">
          <SidebarItem to="/" icon={LayoutDashboard} label="Overview" />
          <SidebarItem to="/arena" icon={Activity} label="Arena" />
          <SidebarItem to="/agents" icon={Users} label="Agents" />
          <SidebarItem to="/persistence" icon={Database} label="Persistence" />
          <SidebarItem to="/logs" icon={FileText} label="Logs" />
        </nav>

        <div className="px-4 py-4 border-t border-white/5 text-[10px] text-gray-500 uppercase tracking-widest">
          Operator Console v0.1.0
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-[#0a0a0a]">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/arena" element={<Arena />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/persistence" element={<Persistence />} />
          <Route path="/logs" element={<Logs />} />
        </Routes>
      </main>
    </div>
  )
}
