import React, { useState, useEffect } from 'react'
import { apiClient } from '../api/client'
import { Database, RotateCcw, Save, ShieldAlert } from 'lucide-react'

export default function Persistence() {
  const [persistence, setPersistence] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await apiClient.getPersistence()
        setPersistence(data)
      } catch (err) {
        console.error('Persistence Fetch Error:', err)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-8 space-y-8 max-w-7xl">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-white">Persistence Registry</h1>
        <p className="text-gray-400">Arena World-State & Recovery Manifests</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Persistence Card */}
        <div className="lg:col-span-2 bg-[#141414] border border-white/5 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
            <div className="flex items-center space-x-3 text-amber-500">
              <Database size={20} />
              <h2 className="font-bold uppercase tracking-tight text-sm">Active World State</h2>
            </div>
            <div className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${persistence?.freshness === 'GROUNDED' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
              {persistence?.freshness || 'DEGRADED'}
            </div>
          </div>
          
          <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-12">
            <div className="space-y-6">
              <div>
                <h4 className="text-xs text-gray-500 uppercase tracking-widest mb-2 flex items-center space-x-2">
                  <RotateCcw size={12} />
                  <span>Boot Type</span>
                </h4>
                <div className="text-2xl font-bold font-mono tracking-tighter">
                  {persistence?.boot_type || '---'}
                </div>
              </div>
              <div>
                <h4 className="text-xs text-gray-500 uppercase tracking-widest mb-2 flex items-center space-x-2">
                  <Save size={12} />
                  <span>Resume Count</span>
                </h4>
                <div className="text-2xl font-bold font-mono tracking-tighter text-amber-500">
                  {persistence?.resume_count ?? '---'}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <h4 className="text-xs text-gray-500 uppercase tracking-widest mb-2">Last Checkpoint</h4>
                <div className="text-2xl font-bold font-mono tracking-tighter">
                  {persistence?.last_checkpoint || 'NEVER'}
                </div>
              </div>
              <div className="pt-4 border-t border-white/5">
                <p className="text-[10px] text-gray-500 leading-relaxed uppercase">
                  World manifest is written atomically to <code>local/game001/arena_runtime_state.json</code>.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Advisory Panel */}
        <div className="bg-red-500/[0.03] border border-red-500/10 rounded-xl p-8 space-y-6">
          <div className="flex items-center space-x-3 text-red-500">
            <ShieldAlert size={24} />
            <h2 className="font-bold uppercase tracking-tight text-sm">Integrity Shield</h2>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            Automatic checkpointing is active every 300 seconds. In the event of a crash, the Arena will attempt a namespaced resume using the latest grounded manifest.
          </p>
          <div className="space-y-4">
            <div className="flex items-center space-x-2 text-[10px] uppercase font-bold text-gray-500">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
              <span>Atomic Writes: OK</span>
            </div>
            <div className="flex items-center space-x-2 text-[10px] uppercase font-bold text-gray-500">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
              <span>Namespace: game001</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
