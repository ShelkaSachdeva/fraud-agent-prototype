const form = document.querySelector("#investigation-form");
const transactionInput = document.querySelector("#transaction-id");
const startButton = document.querySelector("#start-button");
const overallStatus = document.querySelector("#overall-status");
const resultsPanel = document.querySelector("#results-panel");
const auditLog = document.querySelector("#audit-log");
const clearLogButton = document.querySelector("#clear-log");

let eventSource = null;

const agentCards = {
    orchestrator: document.querySelector(
        '[data-agent="orchestrator"]'
    ),
    fraud: document.querySelector('[data-agent="fraud"]'),
    kyc: document.querySelector('[data-agent="kyc"]'),
    compliance: document.querySelector(
        '[data-agent="compliance"]'
    ),
};

function setPill(element, status) {
    const normalized = status.toLowerCase();
    element.textContent = status;
    element.className = element.className
        .replace(/\b(waiting|running|completed|failed)\b/g, "")
        .trim();
    element.classList.add(normalized);
}

function updateAgent(agent, status, message) {
    const card = agentCards[agent];
    if (!card) {
        return;
    }

    card.classList.remove("active", "done", "error");

    if (status === "RUNNING") {
        card.classList.add("active");
    } else if (status === "COMPLETED") {
        card.classList.add("done");
    } else if (status === "FAILED") {
        card.classList.add("error");
    }

    const statusElement = card.querySelector(".agent-status");
    const activity = card.querySelector(".activity");

    setPill(statusElement, status);

    if (message) {
        activity.textContent = message;
    }
}

function addLog(source, message) {
    const emptyEntry = auditLog.querySelector(".muted");
    if (emptyEntry) {
        emptyEntry.remove();
    }

    const entry = document.createElement("div");
    entry.className = "log-entry";

    const time = new Date().toLocaleTimeString();

    entry.innerHTML = `
        <span class="time">${escapeHtml(time)}</span>
        <span class="source">${escapeHtml(source)}</span>
        <span>${escapeHtml(message)}</span>
    `;

    auditLog.appendChild(entry);
    auditLog.scrollTop = auditLog.scrollHeight;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function resetUi() {
    ["orchestrator", "fraud", "kyc", "compliance"].forEach(
        (agent) => {
            updateAgent(
                agent,
                "WAITING",
                "Waiting for the orchestrator."
            );
        }
    );

    agentCards.orchestrator.querySelector(
        ".activity"
    ).textContent = "Waiting for an investigation request.";

    resultsPanel.classList.add("hidden");
    document.querySelector("#fraud-result").innerHTML =
        "No result yet.";
    document.querySelector("#kyc-result").innerHTML =
        "No result yet.";
    document.querySelector("#compliance-result").innerHTML =
        "No result yet.";

    setPill(overallStatus, "WAITING");
}

function renderFraud(output) {
    const result = output?.fraud_result;
    if (!result) {
        return;
    }

    const signals = (result.fraud_signals || [])
        .map((signal) => `<li>${escapeHtml(signal)}</li>`)
        .join("");

    document.querySelector("#fraud-result").innerHTML = `
        <div class="metric">
            <span>Risk score</span>
            <strong>${escapeHtml(result.risk_score)}</strong>
        </div>
        <div class="metric">
            <span>Risk level</span>
            <strong>${escapeHtml(result.risk_level)}</strong>
        </div>
        <p><strong>Signals</strong></p>
        <ul class="signal-list">${signals}</ul>
    `;

    resultsPanel.classList.remove("hidden");
}

function renderKyc(output) {
    const result = output?.kyc_result;
    if (!result) {
        return;
    }

    const rows = Object.entries(result)
        .map(([key, value]) => `
            <div class="metric">
                <span>${escapeHtml(
                    key.replaceAll("_", " ")
                )}</span>
                <strong>${escapeHtml(value)}</strong>
            </div>
        `)
        .join("");

    document.querySelector("#kyc-result").innerHTML = rows;
    resultsPanel.classList.remove("hidden");
}

function renderCompliance(output) {
    const result = output?.compliance_result;
    if (!result) {
        return;
    }

    const rows = Object.entries(result)
        .map(([key, value]) => `
            <div class="metric">
                <span>${escapeHtml(
                    key.replaceAll("_", " ")
                )}</span>
                <strong>${escapeHtml(
                    typeof value === "object"
                        ? JSON.stringify(value)
                        : value
                )}</strong>
            </div>
        `)
        .join("");

    document.querySelector(
        "#compliance-result"
    ).innerHTML = `
        ${rows}
        <p>
            <strong>Human review required before any consequential
            action.</strong>
        </p>
    `;

    resultsPanel.classList.remove("hidden");
}

function closeStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}

form.addEventListener("submit", (event) => {
    event.preventDefault();

    closeStream();
    resetUi();

    const transactionId = transactionInput.value.trim();

    if (!transactionId) {
        return;
    }

    startButton.disabled = true;
    startButton.textContent = "Investigation Running...";
    setPill(overallStatus, "RUNNING");

    addLog(
        "USER",
        `Submitted transaction ${transactionId} for investigation.`
    );

    eventSource = new EventSource(
        `/api/investigations/stream/${encodeURIComponent(
            transactionId
        )}`
    );

    eventSource.addEventListener("orchestrator", (event) => {
        const data = JSON.parse(event.data);

        updateAgent(
            "orchestrator",
            data.status,
            data.message
        );

        addLog("ORCHESTRATOR", data.message);
    });

    eventSource.addEventListener("fraud_started", (event) => {
        const data = JSON.parse(event.data);

        updateAgent("orchestrator", "COMPLETED",
            "Investigation plan created. Fraud analysis delegated."
        );
        updateAgent("fraud", data.status, data.message);
        addLog("FRAUD AGENT", data.message);
    });

    eventSource.addEventListener("fraud_completed", (event) => {
        const data = JSON.parse(event.data);

        updateAgent(
            "fraud",
            data.status,
            data.status === "COMPLETED"
                ? "Fraud score and behavioral signals returned."
                : "Fraud analysis failed."
        );

        renderFraud(data.output);
        addLog(
            "FRAUD AGENT",
            data.status === "COMPLETED"
                ? "Returned trusted fraud assessment."
                : "Failed to return a fraud assessment."
        );
    });

    eventSource.addEventListener("kyc_started", (event) => {
        const data = JSON.parse(event.data);

        updateAgent("kyc", data.status, data.message);
        addLog("KYC AGENT", data.message);
    });

    eventSource.addEventListener("kyc_completed", (event) => {
        const data = JSON.parse(event.data);

        updateAgent(
            "kyc",
            data.status,
            data.status === "COMPLETED"
                ? "Identity, sanctions, and customer risk returned."
                : "KYC review failed."
        );

        renderKyc(data.output);
        addLog(
            "KYC AGENT",
            data.status === "COMPLETED"
                ? "Returned trusted KYC assessment."
                : "Failed to return a KYC assessment."
        );
    });

    eventSource.addEventListener(
        "compliance_started",
        (event) => {
            const data = JSON.parse(event.data);

            updateAgent(
                "compliance",
                data.status,
                data.message
            );
            addLog("COMPLIANCE AGENT", data.message);
        }
    );

    eventSource.addEventListener(
        "compliance_completed",
        (event) => {
            const data = JSON.parse(event.data);

            updateAgent(
                "compliance",
                data.status,
                data.status === "COMPLETED"
                    ? "Compliance recommendation returned."
                    : "Compliance review failed."
            );

            renderCompliance(data.output);
            addLog(
                "COMPLIANCE AGENT",
                data.status === "COMPLETED"
                    ? "Returned governed compliance recommendation."
                    : "Failed to return a recommendation."
            );
        }
    );

    eventSource.addEventListener(
        "investigation_completed",
        (event) => {
            const data = JSON.parse(event.data);

            setPill(overallStatus, "COMPLETED");
            addLog(
                "ORCHESTRATOR",
                `Investigation ${data.transaction_id} completed.`
            );

            startButton.disabled = false;
            startButton.textContent =
                "Start Autonomous Investigation";

            closeStream();
        }
    );

    eventSource.addEventListener(
        "investigation_failed",
        (event) => {
            const data = JSON.parse(event.data);

            setPill(overallStatus, "FAILED");
            addLog(
                "ORCHESTRATOR",
                data.error || "Investigation failed."
            );

            startButton.disabled = false;
            startButton.textContent =
                "Start Autonomous Investigation";

            closeStream();
        }
    );

    eventSource.onerror = () => {
        if (overallStatus.textContent !== "COMPLETED") {
            addLog(
                "SYSTEM",
                "The live connection ended."
            );
        }

        startButton.disabled = false;
        startButton.textContent =
            "Start Autonomous Investigation";
    };
});

clearLogButton.addEventListener("click", () => {
    auditLog.innerHTML = `
        <div class="log-entry muted">
            Activity log cleared.
        </div>
    `;
});

resetUi();
