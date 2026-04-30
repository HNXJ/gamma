import React, { useState, useEffect, useRef } from 'react'
import { apiClient } from '../api/client'
import { FileText, Terminal, Activity, Info } from 'lucide-react'

const EventItem = ({ event }) => {
  const isCouncil = event.type === 'COUNCIL_CHAT'
  const data = isCouncil ? event.data : event
  
  return (
    <div className="flex space-x-4 p-4 border-b border-white/5 hover:bg-white/[0.02] transition-colors group">
      <div className="text-[10px] font-mono text-gray-600 pt-1 shrink-0">
        {data.time?.split(' ')[1] || '---'}
      </div>
      <div className="space-y-1 overflow-hidden">
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-bold uppercase tracking-widest text-amber-500">[{data.agent || 'SYSTEM'}]</span>
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">INFO</span>
        </div>
        <div className="text-sm text-gray-300 font-mono leading-relaxed break-words">
          {data.msg}
        </div>
      </div>
    </div>
  )
}

export default function Logs() {
  const [events, setEvents] = useState([])
  const [rawLogs, setRawLogs] = useState('')
  const [activeTab, setActiveTab] = useState('events')
  const scrollRef = useRef(null)

  useEffect(() => {
    // Initial events from status if needed, but here we just subscribe
    const unsubscribe = apiClient.subscribeToEvents((newEvent) => {
      setEvents(prev => [...prev.slice(-49), newEvent])
    })

    const fetchRaw = async () => {
      try {
        const data = await apiClient.getLogs(50)
        setRawLogs(data.content)
      } catch (err) {
        console.error('Raw Log Fetch Error:', err)
      }
    }

    if (activeTab === 'raw') fetchRaw()
    
    return () => unsubscribe()
  }, [activeTab])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [events, rawLogs])

  return (
    <div className="h-screen flex flex-col">
      <header className="p-8 pb-4 space-y-4">
        <div className="flex justify-between items-center">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight text-white">Provenance Stream</h1>
            <p className="text-gray-400 text-sm">Real-time Scientific Event Rail</p>
          </div>
          <div className="flex bg-[#141414] p-1 rounded-lg border border-white/5">
            <button 
              onClick={() => setActiveTab('events')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md text-xs font-bold transition-all ${activeTab === 'events' ? 'bg-amber-500 text-black' : 'text-gray-500 hover:text-white'}`}
            >
              <Activity size={14} />
              <span>Event Rail</span>
            </button>
            <button 
              onClick={() => setActiveTab('raw')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md text-xs font-bold transition-all ${activeTab === 'raw' ? 'bg-amber-500 text-black' : 'text-gray-500 hover:text-white'}`}
            >
              <FileText size={14} />
              <span>Raw Tails</span>
            </button>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-hidden px-8 pb-8">
        <div className="h-full bg-[#0d0d0d] border border-white/5 rounded-xl flex flex-col">
          <div className="p-3 border-b border-white/5 flex items-center justify-between bg-white/[0.01]">
            <div className="flex items-center space-x-2 text-gray-500">
              <Terminal size={14} />
              <span className="text-[10px] font-bold uppercase tracking-widest">{activeTab === 'events' ? 'Council Dialogue' : 'System Proof'}</span>
            </div>
            <div className="flex space-x-2">
              <div className="w-2 h-2 rounded-full bg-green-500/50 animate-pulse" />
              <span className="text-[8px] font-bold text-gray-600 uppercase tracking-tighter">Live Stream Active</span>
            </div>
          </div>

          <div 
            ref={scrollRef}
            className="flex-1 overflow-auto p-4 font-mono text-xs scrollbar-thin scrollbar-thumb-white/10"
          >
            {activeTab === 'events' ? (
              events.length > 0 ? (
                events.map((ev, i) => <EventItem key={i} event={ev} />)
              ) : (
                <div className="h-full flex items-center justify-center text-gray-600 uppercase tracking-widest text-[10px]">
                  Waiting for council events...
                </div>
              )
            ) : (
              <pre className="text-gray-400 whitespace-pre-wrap leading-relaxed">
                {rawLogs || 'Loading raw provenance logs...'}
              </pre>
            )}
          </div>

          <div className="p-4 border-t border-white/5 bg-white/[0.01] flex items-start space-x-3">
            <Info size={14} className="text-amber-500 shrink-0 mt-0.5" />
            <p className="text-[9px] text-gray-500 uppercase leading-relaxed tracking-tight">
              Evidence grounding: All events are sourced directly from <code>{activeTab === 'events' ? 'SSE Stream' : 'Log Tail'}</code>. 
              Mutation and write-access are restricted in this console layer.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
