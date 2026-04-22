const API_BASE_URL = window.location.origin;

const targetInput = document.getElementById("target-ip");
const scanButton = document.getElementById("scan-button");
const loadingElement = document.getElementById("loading");
const messageElement = document.getElementById("message");
const resultsCard = document.getElementById("results-card");
const hostIpElement = document.getElementById("host-ip");
const timestampElement = document.getElementById("timestamp");
const openPortsElement = document.getElementById("open-ports");
const statusBadge = document.getElementById("status-badge");
const historyDiv = document.getElementById("history");


function setLoading(isLoading) {
    loadingElement.classList.toggle("hidden", !isLoading);
    scanButton.disabled = isLoading;
    scanButton.textContent = isLoading ? "Scanning..." : "Scan";
}


function showMessage(message) {
    messageElement.textContent = message;
    messageElement.classList.remove("hidden");
}


function clearMessage() {
    messageElement.textContent = "";
    messageElement.classList.add("hidden");
}


function setStatusBadge(status) {
    const normalizedStatus = (status || "unknown").toLowerCase();

    statusBadge.textContent = normalizedStatus;
    statusBadge.classList.remove("up", "down");

    if (normalizedStatus === "up") {
        statusBadge.classList.add("up");
    } else if (normalizedStatus === "down") {
        statusBadge.classList.add("down");
    }
}


function renderPorts(openPorts) {
    openPortsElement.innerHTML = "";

    if (!Array.isArray(openPorts) || openPorts.length === 0) {
        const emptyItem = document.createElement("li");
        emptyItem.className = "empty-state";
        emptyItem.textContent = "No open ports detected in the scanned range.";
        openPortsElement.appendChild(emptyItem);
        return;
    }

    openPorts.forEach((portInfo) => {
        const listItem = document.createElement("li");

        const portNumber = document.createElement("span");
        portNumber.className = "port-number";
        portNumber.textContent = `Port ${portInfo.port}`;

        const serviceName = document.createElement("span");
        serviceName.className = "port-service";
        serviceName.textContent = portInfo.service || "unknown";

        listItem.appendChild(portNumber);
        listItem.appendChild(serviceName);
        openPortsElement.appendChild(listItem);
    });
}


function renderResults(data) {
    hostIpElement.textContent = data.host_ip || "-";
    timestampElement.textContent = data.timestamp || "-";
    setStatusBadge(data.status);
    renderPorts(data.open_ports);
    resultsCard.classList.remove("hidden");
}


async function handleScan() {
    const targetIp = targetInput.value.trim();

    clearMessage();
    resultsCard.classList.add("hidden");

    if (!targetIp) {
        showMessage("Please enter a target IP address before starting the scan.");
        return;
    }

    setLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/scan`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ target_ip: targetIp }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Scan failed. Please try again.");
        }

        renderResults(data);
        loadHistory(); // 🔥 refresh history after scan

    } catch (error) {
        showMessage(error.message || "Unable to connect to backend.");
    } finally {
        setLoading(false);
    }
}


async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE_URL}/history`);
        const data = await res.json();

        historyDiv.innerHTML = "";

        if (!Array.isArray(data) || data.length === 0) {
            historyDiv.innerHTML = "<p class='empty-state'>No scan history available.</p>";
            return;
        }

        data.forEach(item => {
            const ports = item.open_ports
                .map(p => `${p.port} (${p.service})`)
                .join(", ");

            historyDiv.innerHTML += `
                <div class="history-card">
                    <p><strong>IP:</strong> ${item.target_ip}</p>
                    <p><strong>Time:</strong> ${item.timestamp}</p>
                    <p><strong>Ports:</strong> ${ports || "None"}</p>
                </div>
            `;
        });

    } catch (error) {
        historyDiv.innerHTML = "<p class='empty-state'>Failed to load history.</p>";
    }
}


// Event Listeners
scanButton.addEventListener("click", handleScan);

targetInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        handleScan();
    }
});


// Load history on page load
window.onload = loadHistory;
