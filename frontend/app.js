const BACKEND_URL = "http://127.0.0.1:8000";

// 1. Check API heartbeat connection status on page initialization
async function evaluateHeartbeatSignal() {
    const indicator = document.getElementById('connectionStatus');
    try {
        const response = await fetch(`${BACKEND_URL}/`);
        const statusReport = await response.json();
        if (statusReport.status === "online" && statusReport.database_connected) {
            indicator.className = "status-pill status-online";
            indicator.innerText = "⚡ API Matrix Engine & PostgreSQL Online";
        }
    } catch {
        indicator.className = "status-pill status-offline";
        indicator.innerText = "🛑 Connection Interrupted: Check Local Server Port 8000";
    }
}

// 2. Capture, format metrics, and pass data structures to FastAPI endpoint
document.getElementById('failsafeForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const runtimeMessage = document.getElementById('runtimeMessage');
    const runtimeText = document.getElementById('runtimeText');
    const analyticsPayload = document.getElementById('analyticsPayload');
    const trackContainer = document.getElementById('dynamicSubjectTracksContainer');

    // Trigger visual processing loading state animations
    runtimeMessage.className = "state-container processing";
    runtimeText.innerText = "Querying calculations across active subject matrix modules...";
    analyticsPayload.classList.add('hidden');
    trackContainer.innerHTML = "";

    // Build values dynamically following your system's precise Pydantic schemas
    const mG1 = document.getElementById('mG1').value;
    const mG2 = document.getElementById('mG2').value;
    const pG1 = document.getElementById('pG1').value;
    const pG2 = document.getElementById('pG2').value;

    const payload = {
        student_id: document.getElementById('studentId').value,
        math_performance: (mG1 || mG2) ? {
            failures: parseInt(document.getElementById('mFailures').value) || 0,
            absences: parseInt(document.getElementById('mAbsences').value) || 0,
            G1: parseInt(mG1) || 0,
            G2: parseInt(mG2) || 0,
            studytime: parseInt(document.getElementById('mStudytime').value)
        } : null,
        portuguese_performance: (pG1 || pG2) ? {
            failures: parseInt(document.getElementById('pFailures').value) || 0,
            absences: parseInt(document.getElementById('pAbsences').value) || 0,
            G1: parseInt(pG1) || 0,
            G2: parseInt(pG2) || 0,
            studytime: parseInt(document.getElementById('pStudytime').value)
        } : null
    };

    try {
        const response = await fetch(`${BACKEND_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errDetails = await response.json();
            throw new Error(errDetails.detail || "API Endpoint processing fault.");
        }

        const data = await response.json();

        // Bind global structural data layouts directly from final_response_data format
        const globalSummary = data.unified_academic_summary;
        document.getElementById('compositeRiskVal').innerText = globalSummary.composite_risk_average;
        
        const badge = document.getElementById('globalTierBadge');
        badge.innerText = globalSummary.global_standing_classification;
        
        // Dynamic badge color code logic using tier checks
        const tierStr = globalSummary.global_standing_classification;
        if (tierStr.includes("Emergency")) badge.className = "global-tier-badge critical-alert";
        else if (tierStr.includes("Watchlist")) badge.className = "global-tier-badge monitoring-alert";
        else badge.className = "global-tier-badge standard-alert";

        document.getElementById('protocolCopy').innerText = globalSummary.actionable_intervention_protocol;

        // Render inner arrays from matching subject maps
        Object.keys(data.individual_subject_diagnostics).forEach(trackKey => {
            const trackData = data.individual_subject_diagnostics[trackKey];
            const diagnosticInfo = trackData.diagnostic; // Unpacks get_subject_insights mapping model
            
            let colorClass = "stable-border";
            if (diagnosticInfo.risk_tier.includes("High")) colorClass = "high-border";
            else if (diagnosticInfo.risk_tier.includes("Moderate")) colorClass = "mod-border";

            const elementCard = document.createElement('div');
            elementCard.className = `subject-diagnostic-widget ${colorClass}`;
            elementCard.innerHTML = `
                <div class="widget-top">
                    <h4>${trackKey.toUpperCase()} METRIC MATRIX</h4>
                    <span class="mini-pill">${diagnosticInfo.risk_tier}</span>
                </div>
                <p class="risk-idx-txt">Calculated Core Risk Index: <strong>${trackData.calculated_risk_index}</strong></p>
                <div class="diagnostic-desc-block">
                    <p><strong>Status Profile:</strong> ${diagnosticInfo.status}</p>
                    <p class="action-highlight"><strong>Intervention Map:</strong> ${diagnosticInfo.intervention}</p>
                </div>
            `;
            trackContainer.appendChild(elementCard);
        });

        // Toggle visibility to render graphs
        runtimeMessage.classList.add('hidden');
        analyticsPayload.classList.remove('hidden');

    } catch (err) {
        runtimeMessage.className = "state-container application-error";
        runtimeText.innerText = `Data Pipeline Execution Failure: ${err.message}`;
    }
});

// Run API link configuration 
evaluateHeartbeatSignal();