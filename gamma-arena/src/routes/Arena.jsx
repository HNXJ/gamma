import React, { useState, useEffect } from 'react'
import { apiClient } from '../api/client'
import { Milestone, Trophy, Network } from 'lucide-react'

export default function Arena() {
  const [progression, setProgression] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await apiClient.getProgression()
        setProgression(data)
      } catch (err) {
        console.error('Arena Fetch Error:', err)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  const level = progression?.largest_pass_network_neuron_count || 10
  const totalSegments = 100
  const activeSegments = Math.min(Math.floor(level / 10), totalSegments)

  return (
    <div className="p-8 space-y-8 max-w-7xl">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-white underline decoration-amber-500/30 underline-offset-8">Scientific Arena</h1>
        <p className="text-gray-400">Progression Ladder & PASS Network Growth</p>
      </header>

      {/* Progression Bar */}
      <div className="bg-[#141414] border border-white/5 rounded-xl p-8 space-y-6">
        <div className="flex justify-between items-end">
          <div className="space-y-1">
            <span className="text-xs uppercase tracking-widest text-gray-500">Current Level</span>
            <div className="text-4xl font-bold font-mono text-amber-500">{level}<span className="text-sm text-gray-600 ml-2 uppercase font-sans tracking-tighter">Neurons</span></div>
          </div>
          <div className="text-right space-y-1">
            <span className="text-xs uppercase tracking-widest text-gray-500">Truth Class</span>
            <div className={`text-xs font-bold uppercase font-mono px-2 py-0.5 rounded ${progression?.truth_class === 'GROUNDED' ? 'bg-green-500/10 text-green-500' : 'bg-gray-500/10 text-gray-400'}`}>
              {progression?.truth_class || 'DEGRADED'}
            </div>
          </div>
        </div>

        <div className="h-6 w-full flex space-x-0.5">
          {Array.from({ length: totalSegments }).map((_, i) => {
            const isPassed = i < activeSegments
            const isCurrent = i === activeSegments
            return (
              <div 
                key={i} 
                className={`flex-1 rounded-sm transition-all duration-500 ${
                  isPassed ? 'bg-amber-500' : 
                  isCurrent ? 'bg-amber-500 animate-pulse' : 
                  'bg-white/5'
                }`}
              />
            )
          })}
        </div>
        
        <div className="flex justify-between text-[10px] uppercase tracking-widest text-gray-500 font-mono">
          <span>10 N</span>
          <span>100 N</span>
          <span>250 N</span>
          <span>500 N</span>
          <span>1000 N</span>
        </div>
      </div>

      {/* Milestone Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#141414] border border-white/5 rounded-xl p-6 space-y-4">
          <div className="flex items-center space-x-2 text-amber-500">
            <Milestone size={18} />
            <h3 className="font-bold uppercase tracking-tight text-sm">Next Unlock</h3>
          </div>
          <div className="text-xl font-bold">40 Neuron VIP</div>
          <p className="text-xs text-gray-500 leading-relaxed">
            Contextual Disinhibition & SST/PV Balance Control activation threshold.
          </p>
        </div>

        <div className="bg-[#141414] border border-white/5 rounded-xl p-6 space-y-4">
          <div className="flex items-center space-x-2 text-blue-500">
            <Network size={18} />
            <h3 className="font-bold uppercase tracking-tight text-sm">PASS Network</h3>
          </div>
          <div className="text-xl font-bold">{level}-Node PASS</div>
          <p className="text-xs text-gray-500 leading-relaxed">
            Largest interconnected neuronal assembly verified in live scientific research.
          </p>
        </div>

        <div className="bg-[#141414] border border-white/5 rounded-xl p-6 space-y-4 opacity-50 grayscale">
          <div className="flex items-center space-x-2 text-gray-500">
            <Trophy size={18} />
            <h3 className="font-bold uppercase tracking-tight text-sm">Target Milestone</h3>
          </div>
          <div className="text-xl font-bold">100 Neuron L4</div>
          <p className="text-xs text-gray-500 leading-relaxed">
            Apical/Basal Dendrites + Laminar Predictive Routing.
          </p>
        </div>
      </div>
    </div>
  )
}
