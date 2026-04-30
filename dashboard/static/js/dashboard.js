document.addEventListener('DOMContentLoaded', () => {
    const logContainer = document.getElementById('log-container');
    const fields = {
        'epoch-count': 'epoch',
        'system-status': 'status',
        'z-val': 'z',
        'w-val': 'w',
        'x-val': 'x',
        'y-val': 'y',
        'loss-val': 'loss'
    };

    const previousValues = {};

    function updateValue(id, newValue, decimals = 3) {
        const element = document.getElementById(id);
        const formattedValue = typeof newValue === 'number' ? newValue.toFixed(decimals) : newValue;
        
        if (previousValues[id] !== formattedValue) {
            element.innerText = formattedValue;
            element.classList.remove('value-change');
            void element.offsetWidth; // Trigger reflow
            element.classList.add('value-change');
            previousValues[id] = formattedValue;
        }
    }

    function addLogLine(msg) {
        const line = document.createElement('div');
        line.className = 'log-line';
        
        const now = new Date();
        const timestamp = now.toTimeString().split(' ')[0];
        
        line.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${msg}`;
        logContainer.appendChild(line);
        
        // Keep only last 100 lines
        while (logContainer.children.length > 100) {
            logContainer.removeChild(logContainer.firstChild);
        }
        
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    // Initialize EventSource
    const evtSource = new EventSource("/stream");

    evtSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // Update all metrics
        updateValue('epoch-count', data.epoch, 0);
        updateValue('system-status', data.status);
        updateValue('z-val', data.z);
        updateValue('w-val', data.w);
        updateValue('x-val', data.x);
        updateValue('y-val', data.y);
        updateValue('loss-val', data.loss);

        // Update logs if they changed
        if (data.logs && data.logs.length > 0) {
            // In the provided script, 'logs' is a list of all current logs.
            // We only want to add the NEW ones.
            const lastLog = data.logs[data.logs.length - 1];
            if (previousValues['lastLog'] !== lastLog) {
                addLogLine(lastLog);
                previousValues['lastLog'] = lastLog;
            }
        }
    };

    evtSource.onerror = function() {
        updateValue('system-status', 'RECONNECTING...');
    };

    // Initial dummy data for visual testing if needed
    console.log("Gamma Dashboard Initialized");
});
