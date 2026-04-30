import React, { useState, useEffect } from 'react'
import { apiClient } from '../api/client'
import { Server, Activity, Clock, ShieldCheck } from 'lucide-react'

const StatCard = ({ label, value, icon: Icon, color = "amber" }) => (
  <div className="bg-[#141414] border border-white/5 p-6 rounded-xl space-y-4">
    <div className="flex items-center justify-between">
      <span className="text-gray-400 text-sm font-medium uppercase tracking-wider">{label}</span>
      <Icon className={`text-${color}-500`} size={20} />
    </div>
    <div className="text-3xl font-bold tracking-tight">{value || '---'}</div>
  </div>
)

export default function Overview() {
  const [status, setStatus] = useState(null)
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusData, healthData] = await Promise.all([
          apiClient.getStatus(),
          apiClient.getHealth()
        ])
        setStatus(statusData)
        setHealth(healthData)
      } catch (err) {
        console.error('Overview Fetch Error:', err)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-8 space-y-8 max-w-7xl">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-white">System Overview</h1>
        <p className="text-gray-400">Amber Arena Operational Status</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          label="System Status" 
          value={status?.system?.status} 
          icon={Server} 
          color={status?.system?.status === 'ONLINE' ? 'green' : 'gray'}
        />
        <StatCard 
          label="Heartbeat" 
          value={health?.heartbeat} 
          icon={Activity} 
          color={health?.heartbeat === 'OK' ? 'amber' : 'red'}
        />
        <StatCard 
          label="Uptime" 
          value={health?.uptime} 
          icon={Clock} 
        />
        <StatCard 
          label="Active Agents" 
          value={status?.research?.grounded_agents_active} 
          icon={ShieldCheck} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
        <div className="bg-[#141414] border border-white/5 rounded-xl p-8">
          <h2 className="text-lg font-bold mb-6 flex items-center space-x-2">
            <span>Backend Inventory</span>
            <span className="text-xs font-mono bg-white/5 px-2 py-0.5 rounded text-gray-500 uppercase tracking-tighter">Infrastructure</span>
          </h2>
          <div className="space-y-6">
            <div className="flex justify-between items-center py-3 border-b border-white/5">
              <span className="text-gray-400">Compute Slots</span>
              <span className="font-mono">{status?.system?.backend_active_slots || '---'}</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-white/5">
              <span className="text-gray-400">Zero-Idle Mandate</span>
              <span className="text-green-500 font-mono text-xs font-bold uppercase">Enforced</span>
            </div>
          </div>
        </div>

        <div className="bg-[#141414] border border-white/5 rounded-xl p-8">
          <h2 className="text-lg font-bold mb-6 flex items-center space-x-2">
            <span>Grounded Truth</span>
            <span className="text-xs font-mono bg-amber-500/10 px-2 py-0.5 rounded text-amber-500 uppercase tracking-tighter underline underline-offset-4 decoration-amber-500/50">Scientific</span>
          </h2>
          <div className="space-y-6">
            <div className="flex justify-between items-center py-3 border-b border-white/5">
              <span className="text-gray-400">Neuron Level</span>
              <span className="font-mono">{status?.research?.neuron_count || '---'}</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-white/5">
              <span className="text-gray-400">Active Patch</span>
              <span className="font-mono text-xs">{status?.research?.active_patch || '---'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
