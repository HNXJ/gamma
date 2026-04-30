import React, { useState, useEffect } from 'react'
import { apiClient } from '../api/client'
import { Shield, Monitor, Zap, FileSearch, UserCheck } from 'lucide-react'

const AgentCard = ({ agent }) => {
  const isActive = agent.status === 'ACTIVE'
  const isGrounded = agent.truth_class === 'GROUNDED'
  
  return (
    <div className={`bg-[#141414] border rounded-xl p-6 transition-all duration-300 ${isActive ? 'border-amber-500/30' : 'border-white/5 opacity-80'}`}>
      <div className="flex justify-between items-start mb-6">
        <div className={`p-3 rounded-lg ${isActive ? 'bg-amber-500/10 text-amber-500' : 'bg-white/5 text-gray-500'}`}>
          {agent.role === 'Monitor' && <Monitor size={24} />}
          {agent.role === 'Optimizer' && <Zap size={24} />}
          {agent.role === 'Analyst' && <FileSearch size={24} />}
          {agent.role === 'Manager' && <UserCheck size={24} />}
        </div>
        <div className="text-right">
          <div className="text-xl font-bold font-mono">{agent.id}</div>
          <div className={`text-[10px] font-bold uppercase tracking-widest ${isActive ? 'text-amber-500' : 'text-gray-600'}`}>
            {agent.status}
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <h4 className="text-xs text-gray-500 uppercase tracking-widest mb-1">Identity/Role</h4>
          <div className="font-semibold text-gray-200">{agent.role}</div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-widest mb-1">Truth Class</h4>
            <div className={`text-[10px] font-bold font-mono ${isGrounded ? 'text-green-500' : 'text-gray-600'}`}>
              {agent.truth_class}
            </div>
          </div>
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-widest mb-1">Evidence</h4>
            <div className="text-[10px] font-mono text-gray-400 truncate">
              {agent.grounded_evidence ? 'LOGGED' : 'NONE'}
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-white/5">
          <h4 className="text-xs text-gray-500 uppercase tracking-widest mb-1">Active Trace</h4>
          <div className="text-[10px] font-mono text-gray-400 truncate">
            {agent.source || '---'}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Agents() {
  const [agents, setAgents] = useState([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await apiClient.getAgents()
        setAgents(data)
      } catch (err) {
        console.error('Agents Fetch Error:', err)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-8 space-y-8 max-w-7xl">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-white">Council Roster</h1>
        <p className="text-gray-400">Grounded Agent Activity & Observability Evidence</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {agents.length > 0 ? (
          agents.map(agent => <AgentCard key={agent.id} agent={agent} />)
        ) : (
          <div className="col-span-full py-12 text-center text-gray-500 uppercase tracking-widest text-xs border border-dashed border-white/10 rounded-xl">
            Initializing Council Roster...
          </div>
        )}
      </div>
      
      <div className="bg-amber-500/5 border border-amber-500/10 p-6 rounded-xl flex items-start space-x-4">
        <Shield className="text-amber-500 shrink-0" size={20} />
        <div className="text-xs text-amber-500/80 leading-relaxed uppercase tracking-tight font-medium">
          <strong className="text-amber-500">Security Notice:</strong> Terminal-driven agent mutation is disabled in this shell. This roster provides read-only scientific grounding of active host processes only.
        </div>
      </div>
    </div>
  )
}
