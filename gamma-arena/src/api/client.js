/**
 * Gamma Arena API Client
 * Targets: Port 3012 (Hardened Phase 1.6 Contract)
 */

const BASE_URL = 'http://localhost:3012';

export const apiClient = {
  async getStatus() {
    const res = await fetch(`${BASE_URL}/api/status`);
    if (!res.ok) throw new Error('Status unavailable');
    return res.json();
  },

  async getProgression() {
    const res = await fetch(`${BASE_URL}/api/progression`);
    if (!res.ok) throw new Error('Progression unavailable');
    return res.json();
  },

  async getAgents() {
    const res = await fetch(`${BASE_URL}/api/agents`);
    if (!res.ok) throw new Error('Agents unavailable');
    return res.json();
  },

  async getPersistence() {
    const res = await fetch(`${BASE_URL}/api/persistence`);
    if (!res.ok) throw new Error('Persistence unavailable');
    return res.json();
  },

  async getHealth() {
    const res = await fetch(`${BASE_URL}/api/health`);
    if (!res.ok) throw new Error('Health unavailable');
    return res.json();
  },

  async getLogs(lines = 100) {
    const res = await fetch(`${BASE_URL}/api/logs/raw?lines=${lines}`);
    if (!res.ok) throw new Error('Logs unavailable');
    return res.json();
  },

  subscribeToEvents(onMessage, onError) {
    const eventSource = new EventSource(`${BASE_URL}/api/events/stream`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (err) {
        console.error('SSE Parse Error:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE Connection Error:', err);
      if (onError) onError(err);
      eventSource.close();
      // Reconnect logic would go here
    };

    return () => eventSource.close();
  }
};
