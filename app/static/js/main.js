// OpsBeacon Client-side JavaScript
document.addEventListener("DOMContentLoaded", () => {
    const incidentForm = document.getElementById("incident-form");
    const btnLoad = document.getElementById("btn-load");
    const btnError = document.getElementById("btn-error");
    const btnRefresh = document.getElementById("btn-refresh");
    const consoleOutput = document.getElementById("console-output");

    function logConsole(msg) {
        const time = new Date().toLocaleTimeString();
        consoleOutput.innerHTML = `[${time}] ${msg}<br>` + consoleOutput.innerHTML;
    }

    // Refresh Incident Table
    async function loadIncidents() {
        try {
            const res = await fetch("/api/incidents");
            const data = await res.json();
            const countBadge = document.getElementById("incident-count");
            countBadge.innerText = `${data.length} Total`;

            const tbody = document.getElementById("incidents-body");
            if (data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-secondary">No incidents logged yet. Create one or simulate an event!</td></tr>`;
                return;
            }

            tbody.innerHTML = data.map(inc => `
                <tr id="row-${inc.id}">
                    <td class="ps-3 fw-bold text-secondary">#${inc.id}</td>
                    <td class="fw-semibold">${escapeHtml(inc.title)}</td>
                    <td><code>${escapeHtml(inc.service_name)}</code></td>
                    <td>
                        <span class="badge ${getSeverityBadge(inc.severity)}">${inc.severity}</span>
                    </td>
                    <td>
                        <span class="badge ${inc.status === 'RESOLVED' ? 'bg-success-subtle text-success border border-success' : 'bg-warning-subtle text-warning border border-warning'}">
                            ${inc.status}
                        </span>
                    </td>
                    <td class="text-secondary small">${inc.created_at}</td>
                    <td class="text-end pe-3">
                        ${inc.status !== 'RESOLVED' ? `<button class="btn btn-sm btn-outline-success" onclick="resolveIncident(${inc.id})">Resolve</button>` : `<i class="bi bi-check2-circle text-success"></i>`}
                    </td>
                </tr>
            `).join("");
        } catch (err) {
            logConsole(`Error fetching incidents: ${err.message}`);
        }
    }

    function getSeverityBadge(severity) {
        switch(severity) {
            case "CRITICAL": return "bg-danger";
            case "HIGH": return "bg-warning text-dark";
            case "MEDIUM": return "bg-primary";
            default: return "bg-secondary";
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.innerText = text;
        return div.innerHTML;
    }

    // Handle Form Submit
    if (incidentForm) {
        incidentForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const title = document.getElementById("incident-title").value.trim();
            const service_name = document.getElementById("incident-service").value;
            const severity = document.getElementById("incident-severity").value;

            try {
                const res = await fetch("/api/incidents", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title, service_name, severity })
                });

                if (res.ok) {
                    const created = await res.json();
                    logConsole(`Created incident #${created.id} [${created.severity}]: ${created.title}`);
                    document.getElementById("incident-title").value = "";
                    loadIncidents();
                } else {
                    const err = await res.json();
                    logConsole(`Failed to create incident: ${err.error}`);
                }
            } catch (err) {
                logConsole(`Network error: ${err.message}`);
            }
        });
    }

    // Simulate Load
    if (btnLoad) {
        btnLoad.addEventListener("click", async () => {
            logConsole("Sending simulated latency load batch...");
            try {
                const promises = [1, 2, 3].map(() => fetch("/api/simulate-load").then(r => r.json()));
                const results = await Promise.all(promises);
                results.forEach(r => logConsole(`Latency test: response took ${r.latency_seconds}s`));
            } catch (e) {
                logConsole(`Simulation error: ${e.message}`);
            }
        });
    }

    // Simulate 500 Error
    if (btnError) {
        btnError.addEventListener("click", async () => {
            try {
                const res = await fetch("/api/simulate-error");
                const data = await res.json();
                logConsole(`Triggered expected 500 Error: ${data.error} (Prometheus metric counter updated)`);
            } catch (e) {
                logConsole(`Trigger error: ${e.message}`);
            }
        });
    }

    if (btnRefresh) {
        btnRefresh.addEventListener("click", () => {
            loadIncidents();
            logConsole("Refreshed incident list.");
        });
    }

    // Initial fetch
    loadIncidents();
});

// Global function for Resolve button
window.resolveIncident = async function(id) {
    try {
        const res = await fetch(`/api/incidents/${id}/resolve`, { method: "POST" });
        if (res.ok) {
            const countBadge = document.getElementById("incident-count");
            // Reload table
            const fetchRes = await fetch("/api/incidents");
            const data = await fetchRes.json();
            document.dispatchEvent(new Event("DOMContentLoaded"));
        }
    } catch (e) {
        console.error(e);
    }
};
