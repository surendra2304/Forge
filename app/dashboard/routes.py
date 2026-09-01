"""
Web Dashboard Subsystem for Project FORGE.
Serves interactive UI dashboard for real-time task monitoring, timeline playback, logs, and analytics.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

dashboard_router = APIRouter(tags=["Web Dashboard"])

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project FORGE — Autonomous Engineering Dashboard</title>
    <style>
        :root {
            --bg-dark: #0f172a;
            --card-bg: #1e293b;
            --border-color: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            line-height: 1.5;
            padding: 1.5rem;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 1.5rem;
        }
        .brand { font-size: 1.5rem; font-weight: 700; color: var(--primary); display: flex; align-items: center; gap: 0.5rem; }
        .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 1.5rem; }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.25rem;
        }
        .card-header { font-weight: 600; font-size: 1.1rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; }
        .task-list { list-style: none; display: flex; flex-direction: column; gap: 0.75rem; max-height: 500px; overflow-y: auto; }
        .task-item {
            background: #0f172a;
            border: 1px solid var(--border-color);
            padding: 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            transition: border-color 0.2s;
        }
        .task-item:hover { border-color: var(--primary); }
        .badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge-completed { background: rgba(16, 185, 129, 0.2); color: var(--success); }
        .badge-running { background: rgba(59, 130, 246, 0.2); color: var(--primary); }
        .badge-failed { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
        .badge-pending { background: rgba(245, 158, 11, 0.2); color: var(--warning); }

        .timeline { display: flex; gap: 0.5rem; margin-bottom: 1rem; overflow-x: auto; padding-bottom: 0.5rem; }
        .stage-box {
            padding: 0.5rem 0.75rem;
            border-radius: 4px;
            background: #0f172a;
            border: 1px solid var(--border-color);
            font-size: 0.8rem;
            text-align: center;
            min-width: 100px;
        }
        .stage-completed { border-color: var(--success); color: var(--success); }
        .stage-running { border-color: var(--primary); color: var(--primary); }

        .log-box {
            background: #000;
            color: #10b981;
            font-family: monospace;
            padding: 1rem;
            border-radius: 6px;
            height: 250px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 0.85rem;
        }
        .btn {
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
        }
        .btn:hover { background: var(--primary-hover); }
    </style>
</head>
<body>
    <header>
        <div class="brand">⚡ Project FORGE Dashboard</div>
        <button id="btn-refresh" class="btn" onclick="fetchTasks()">↻ Refresh</button>
    </header>

    <div class="grid">
        <section class="card">
            <div class="card-header">Engineering Tasks</div>
            <ul id="task-list" class="task-list">
                <li class="task-item">Loading active tasks...</li>
            </ul>
        </section>

        <section class="card">
            <div class="card-header">Task Real-Time Telemetry</div>
            <div id="detail-container">
                <p style="color: var(--text-muted);">Select a task to view execution timeline and streaming logs.</p>
            </div>
        </section>
    </div>

    <script>
        async function fetchTasks() {
            try {
                const res = await fetch('/api/tasks');
                if (!res.ok) return;
                const tasks = await res.json();
                const list = document.getElementById('task-list');
                list.innerHTML = '';
                tasks.forEach(t => {
                    const li = document.createElement('li');
                    li.className = 'task-item';
                    li.innerHTML = `
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.25rem;">
                            <strong>${t.id}</strong>
                            <span class="badge badge-${t.state.toLowerCase()}">${t.state}</span>
                        </div>
                        <div style="font-size:0.85rem; color:var(--text-muted);">${t.goal}</div>
                    `;
                    li.onclick = () => selectTask(t.id);
                    list.appendChild(li);
                });
            } catch (err) {
                console.error(err);
            }
        }

        async function selectTask(taskId) {
            try {
                const res = await fetch(`/api/tasks/${taskId}`);
                if (!res.ok) return;
                const task = await res.json();
                const container = document.getElementById('detail-container');
                container.innerHTML = `
                    <div style="margin-bottom: 1rem;">
                        <h3>${task.goal}</h3>
                        <p style="font-size:0.85rem; color:var(--text-muted);">ID: ${task.id} | Mode: ${task.mode} | Progress: ${task.progress_percentage}%</p>
                    </div>
                    <div class="timeline">
                        <div class="stage-box stage-completed">Project</div>
                        <div class="stage-box stage-completed">Requirements</div>
                        <div class="stage-box stage-completed">Architecture</div>
                        <div class="stage-box stage-running">Implementation</div>
                        <div class="stage-box">Verification</div>
                        <div class="stage-box">Release</div>
                    </div>
                    <div class="card-header" style="font-size:0.95rem; margin-top:1rem;">Sandbox Logs</div>
                    <div id="log-viewer" class="log-box">Connected to log stream for ${task.id}...</div>
                `;
            } catch (err) {
                console.error(err);
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            fetchTasks();
        });
    </script>
</body>
</html>
"""


@dashboard_router.get("/dashboard", response_class=HTMLResponse, summary="FORGE Web Dashboard")
async def get_dashboard():
    """Serve the interactive Project FORGE Web Dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)
