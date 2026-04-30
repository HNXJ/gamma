async function refreshDashboard() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) return;
        const data = await response.json();
        
        // Update Header with null safety
        document.getElementById('sys-status-text').innerText = data.system?.status || "DEGRADED";
        document.getElementById('vram-val').innerText = data.system?.vram || "N/A";
        document.getElementById('uptime-val').innerText = data.system?.uptime || "00:00:00";
        document.getElementById('boot-epoch').innerText = data.system?.boot_epoch || "UNAVAILABLE";
        
        const heart = document.getElementById('heartbeat-proof');
        if (heart) {
            heart.innerText = `SEC_${Math.floor(Date.now()/1000) % 60}_OK`;
            heart.style.opacity = heart.style.opacity === "1" ? "0.7" : "1";
        }

        // Update Research with null safety
        const passNet = document.getElementById('pass-network');
        if (passNet) {
            const passVal = data.research?.pass_network;
            passNet.innerText = passVal ? passVal.split(' ')[0] : "NULL";
        }
        
        const activePatch = document.getElementById('active-patch');
        if (activePatch) activePatch.innerText = data.research?.active_patch || "v0.0.0";
        
        const omissions = document.getElementById('omissions-count');
        if (omissions) omissions.innerText = (data.research?.omissions ?? 0).toString().padStart(2, '0');

        // Render Session Matrix (G01-G04)
        const matrix = document.getElementById('session-matrix');
        if (matrix && data.sessions) {
            matrix.innerHTML = '';
            data.sessions.slice(0, 4).forEach(s => {
                const card = document.createElement('div');
                card.className = 'card glass';
                const isDegraded = s.status === 'IDLE';
                
                card.innerHTML = `
                    <div class="card-title">
                        ${s.id} <span style="font-size: 10px; color: var(--accent);">${s.status || 'IDLE'}</span>
                    </div>
                    <div style="font-size: 18px; font-weight: 600;">${s.topic || 'Standby'}</div>
                    <div style="font-family: var(--mono); font-size: 11px; color: var(--text-dim);">
                        Round: ${s.round ?? 0} | Last: ${s.last_active ? (s.last_active.includes('T') ? s.last_active.split('T')[1].split('.')[0] : s.last_active) : 'NEVER'}
                    </div>
                    <div class="card-footer">
                        <span class="truth-badge ${isDegraded ? 'truth-degraded' : 'truth-grounded'}">
                            ${isDegraded ? 'DEGRADED' : 'GROUNDED'}
                        </span>
                        <span>council://v1/${s.id}</span>
                        <span>${new Date().toLocaleTimeString()}</span>
                    </div>
                `;
                matrix.appendChild(card);
            });
        }

    } catch (err) {
        console.error("Dashboard refresh failed:", err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setInterval(refreshDashboard, 1000);
    refreshDashboard();
    console.log("Gamma Operator Console Initialized");
});
