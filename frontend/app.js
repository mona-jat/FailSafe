const API_BASE_URL = "http://127.0.0.1:8000";

// --- STEP 1: INITIALIZE APPLICATION & VERIFY BACKEND CONNECTION ---
document.addEventListener("DOMContentLoaded", async () => {
    const connectionStatus = document.getElementById("connectionStatus");
    
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        if (response.ok) {
            connectionStatus.innerText = "● Core API Link Active";
            connectionStatus.className = "status-pill status-connected";
        } else {
            throw new Error("Gateway Unreachable");
        }
    } catch (error) {
        console.error("Backend offline:", error);
        connectionStatus.innerText = "● Core API Link Disconnected";
        connectionStatus.className = "status-pill status-emergency";
    }
});

// --- STEP 2: HANDLE REAL-TIME EVALUATION FORM SUBMISSION ---
document.getElementById("failsafeForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    // UI Elements for visibility toggling
    const runtimeMessage = document.getElementById("runtimeMessage");
    const analyticsPayload = document.getElementById("analyticsPayload");
    
    // Switch readout visibility to loading/calculating state
    runtimeMessage.className = "state-container loading";
    document.getElementById("runtimeText").innerText = "Executing mathematical tree estimators and persisting records...";
    analyticsPayload.classList.add("hidden");

    // Extract core student identification token
    const studentId = document.getElementById("studentId").value;

    // Capture Mathematics Feature Parameters
    const mG1 = document.getElementById("mG1").value;
    const mG2 = document.getElementById("mG2").value;
    const mFailures = document.getElementById("mFailures").value;
    const mAbsences = document.getElementById("mAbsences").value;
    const mStudytime = document.getElementById("mStudytime").value;

    // Capture Portuguese Feature Parameters
    const pG1 = document.getElementById("pG1").value;
    const pG2 = document.getElementById("pG2").value;
    const pFailures = document.getElementById("pFailures").value;
    const pAbsences = document.getElementById("pAbsences").value;
    const pStudytime = document.getElementById("pStudytime").value;

    // --- STEP 3: ASSEMBLE CONDITIONAL PAYLOAD TREE OBJECTS ---
   
    const payload = {
        student_id: studentId,
        math_performance: (mG1 || mG2) ? {
            failures: parseInt(mFailures) || 0,
            absences: parseInt(mAbsences) || 0,
            G1: parseInt(mG1) || 0,
            G2: parseInt(mG2) || 0,
            studytime: parseInt(mStudytime) || 2
        } : null,
        portuguese_performance: (pG1 || pG2) ? {
            failures: parseInt(pFailures) || 0,
            absences: parseInt(pAbsences) || 0,
            G1: parseInt(pG1) || 0,
            G2: parseInt(pG2) || 0,
            studytime: parseInt(pStudytime) || 3
        } : null
    };

    // --- STEP 4: DISPATCH ASYNC DATA FETCH REQUEST TO FASTAPI ---
    try {
        console.log("SENDING PAYLOAD TO BACKEND:", JSON.stringify(payload, null, 2));
        const response = await fetch(`${API_BASE_URL}/api/predict`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json" ,
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJmYWN1bHR5IiwiZXhwIjoxNzc5NTMwNTI0fQ.RXZ653IpOvO9u5L4Hp5uuIw7qhO3cwrDGMfz_LSnJ58"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Execution Pipeline Returned Status Code: ${response.status}`);
        }
       
        const data = await response.json();
        console.log("Backend Response Data:", data);

        
        runtimeMessage.classList.add("hidden");
        analyticsPayload.classList.remove("hidden");

        // --- STEP 5: PAINT UNIFIED GLOBAL INTERVENTION COMPOSITE RESULTS ---
        const summary = data.unified_academic_summary || {};
        const riskTierStr = summary.global_standing_classification || "Low Risk"; 
        const interventionStr = summary.actionable_intervention_protocol || "Routine Tracking: Continue normal curriculum.";
        const compositeScore = summary.composite_risk_average || "N/A";

        
        const compositeRiskElement = document.getElementById("compositeRiskVal");
        if (compositeRiskElement) {
            compositeRiskElement.innerText = compositeScore;
        }

       
        const badge = document.getElementById("globalTierBadge");
        if (badge) {
            badge.innerText = riskTierStr;
            badge.className = "global-tier-badge"; 
            
            if (riskTierStr.includes("High") || riskTierStr.includes("Emergency") || riskTierStr.includes("Critical")) {
                badge.classList.add("badge-emergency");
            } else if (riskTierStr.includes("Medium") || riskTierStr.includes("Watchlist")) {
                badge.classList.add("badge-watchlist");
            } else {
                badge.classList.add("badge-clear");
            }
        }

        const protocolElement = document.getElementById("protocolCopy");
        if (protocolElement) {
            protocolElement.innerText = interventionStr;
        }

        // --- STEP 6: DYNAMIC SUBJECT CARDS RENDERING ---
        const trackContainer = document.getElementById("dynamicSubjectTracksContainer"); 
        if (trackContainer) {
            trackContainer.innerHTML = ""; 

            const subjectDiagnostics = data.individual_subject_diagnostics || {};

            
            if (mG1 || mG2) {
                const mathData = subjectDiagnostics["mathematics"] || subjectDiagnostics["Mathematics"];
                if (mathData) {
                    renderTrackCard(trackContainer, "Mathematics", mathData, "math-card-theme");
                }
            }

            if (pG1 || pG2) {
                const porData = subjectDiagnostics["portuguese"] || subjectDiagnostics["Portuguese"];
                if (porData) {
                    renderTrackCard(trackContainer, "Portuguese", porData, "por-card-theme");
                }
            }
        }

    } catch (error) {
        console.error("Pipeline failure:", error);
        runtimeMessage.className = "state-container idle";
        
        const runtimeText = document.getElementById("runtimeText");
        if (runtimeText) {
            runtimeText.innerText = "⚠️ An error occurred processing calculations. Verify terminal server.";
        }
        
        alert("Pipeline failed to parse data response. Please check your console logs.");
    }
});

// --- STEP 7: DYNAMIC LAYOUT TEMPLATE INJECTION HELPER ---
function renderTrackCard(container, title, trackData, themeClass) {
    const score = trackData.calculated_risk_index || "N/A";
    const diag = trackData.diagnostic || {};
    const riskTier = diag.risk_tier || "Low Risk";
    const intervention = diag.intervention || "No critical steps mapped.";
    
    const badgeClass = (riskTier.toLowerCase().includes("high") || riskTier.toLowerCase().includes("emergency")) ? "badge-high" : "badge-low";

    container.innerHTML += `
        <div class="track-card ${themeClass}">
            <div class="track-card-header">
                <h4>${title.toUpperCase()} METRIC MATRIX</h4>
                <span class="status-badge ${badgeClass}">${riskTier.toUpperCase()}</span>
            </div>
            <p><strong>Calculated Core Risk Index:</strong> ${score}</p>
            <p><strong>Intervention Map:</strong> ${intervention}</p>
        </div>
    `;
}