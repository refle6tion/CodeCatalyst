const startBtn = document.getElementById('startBtn');
const streamOutput = document.getElementById('stream-output');
const statusDiv = document.getElementById('status');
const analysisSection = document.getElementById('analysis-section');
const analysisResult = document.getElementById('analysis-result');

let eventSource = null;

startBtn.addEventListener('click', startAnalysis);

function startAnalysis() {
    // Reset UI
    startBtn.disabled = true;
    startBtn.textContent = 'Running...';
    streamOutput.innerHTML = '';
    analysisSection.classList.add('hidden');
    analysisResult.textContent = '';
    statusDiv.textContent = 'Connecting...';

    // Close existing connection if any
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource('/api/stream?count=150');

    eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
            finishStream();
            return;
        }

        try {
            const data = JSON.parse(event.data);
            addLogItem(data);
            streamOutput.scrollTop = streamOutput.scrollHeight;
            statusDiv.textContent = `Streaming... (${streamOutput.children.length} signals)`;
        } catch (e) {
            console.error('Parse error:', e);
        }
    };

    eventSource.onerror = () => {
        eventSource.close();
        statusDiv.textContent = 'Connection error';
        startBtn.disabled = false;
        startBtn.textContent = 'Retry';
    };
}

function addLogItem(data) {
    const item = document.createElement('div');
    item.className = 'log-item';

    const statusClass = data.status === 'SUCCESS' ? 'status-success' : 'status-fail';
    const amount = typeof data.amount === 'number' ? data.amount.toFixed(2) : data.amount;

    item.innerHTML = `
        <span class="${statusClass}">${data.status}</span>
        <span>${data.currency}</span>
        <span>${amount}</span>
        <span>${data.latency_ms}ms</span>
    `;

    streamOutput.appendChild(item);
}

async function finishStream() {
    eventSource.close();
    statusDiv.textContent = 'Analyzing with AI...';

    try {
        const res = await fetch('/api/analyze', { method: 'POST' });
        const data = await res.json();

        analysisSection.classList.remove('hidden');

        if (data.error) {
            analysisResult.innerHTML = `<p style="color: var(--error)">Error: ${escapeHtml(data.error)}</p>`;
        } else {
            analysisResult.innerHTML = formatResult(data.result);
        }

        statusDiv.textContent = 'Complete';
        analysisSection.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        analysisResult.innerHTML = `<p style="color: var(--error)">Failed: ${escapeHtml(err.message)}</p>`;
        statusDiv.textContent = 'Error';
    } finally {
        startBtn.disabled = false;
        startBtn.textContent = 'Start Analysis';
    }
}

function formatResult(text) {
    let content = text;

    // Try to parse as JSON first
    try {
        const parsed = JSON.parse(text);
        // Extract content from common JSON structures
        content = parsed.content || parsed.text || parsed.output || parsed.message || JSON.stringify(parsed);
    } catch (e) {
        // Not JSON, use as-is
    }

    // Convert escaped newlines to real newlines
    content = content
        .replace(/\\n/g, '\n')
        .replace(/\\t/g, '  ');

    // Parse markdown to HTML
    return marked.parse(content);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
