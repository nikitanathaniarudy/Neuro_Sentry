
// --- DOM References ---
const startBtn = document.getElementById('start-scan-btn');
const recordBtn = document.getElementById('record-audio-btn');
const promptDisplay = document.getElementById('current-prompt');
const scanView = document.getElementById('scan-view');
const dashboard = document.getElementById('dashboard');
const logsContainer = document.getElementById('logs');

const hrValue = document.getElementById('hr-value');
const rrValue = document.getElementById('rr-value');
const riskScoreDisplay = document.getElementById('risk-score');
const triageLevelDisplay = document.getElementById('triage-level');
const rationaleBox = document.getElementById('rationale-box');
const riskPanel = document.getElementById('risk-panel');
const video = document.getElementById('webcam-feed');
const canvas = document.getElementById('face-overlay');
const ctx = canvas.getContext('2d');

// --- Global State ---
let ws = null;
let currentStep = 0;
let mediaRecorder = null;
let audioChunks = [];
let baselineHR = 70;
let baselineRR = 16;

const PROMPT_FLOW = [
    { text: "Please position your face in the center of the camera frame.", duration: 4000 },
    { text: "Calibrating baseline vital signs. Please remain still.", duration: 5000, action: 'calibrate' },
    { text: "TEST 1: Keep a neutral expression.", duration: 4000 },
    { text: "TEST 2: Now, please give a wide smile, showing your teeth.", duration: 4000 },
    { text: "TEST 3: Raise both eyebrows for a few seconds.", duration: 4000 },
    { text: "TEST 4: Prepare to speak. You will be prompted to say a short phrase.", duration: 3000, audio: true, prep: true },
    { text: "Please say: 'The sky is blue in Cincinnati.'", duration: 5000, audio: true },
    { text: "Finalizing analysis... Compiling neurological indicators.", duration: 7000 },
];

// --- Logging ---
function log(message, type = 'info') {
    const logEntry = document.createElement('p');
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logEntry.className = `log-${type}`;
    logsContainer.appendChild(logEntry);
    logsContainer.scrollTop = logsContainer.scrollHeight;
    console.log(message);
}

// --- WebSocket Connection ---
function connectWebSocket() {
    log("🔗 Connecting to data stream...");
    ws = new WebSocket("ws://localhost:8000/ws/data");

    ws.onopen = () => {
        log("✅ Data stream connected.", 'success');
        startPromptFlow();
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleLivePresageData(data);
        } catch (e) {
            log(`Received non-JSON message: ${event.data}`, 'error');
        }
    };

    ws.onclose = () => {
        log("🔌 Data stream closed.", 'error');
    };

    ws.onerror = (error) => {
        log("❌ WebSocket error. Is the backend server running?", 'error');
        console.error("WebSocket Error:", error);
    };
}


// --- Data Handling & Analysis ---
function handleLivePresageData(data) {
    if (!data.mesh || !data.hr || !data.rr) {
        return;
    }

    // Update Vitals Display
    hrValue.textContent = data.hr;
    rrValue.textContent = data.rr;

    // Calculate Asymmetry
    const asymmetry = calculateAsymmetry(data.mesh);
    
    // Update face overlay
    drawFaceMesh(data.mesh, asymmetry);

    // TODO: Send to a more advanced fusion engine
    updateRiskScore(data, asymmetry);
}

function calculateAsymmetry(mesh) {
    // These indices are examples, refer to the actual MediaPipe face mesh documentation
    const leftCheilion = mesh[61]; 
    const rightCheilion = mesh[291];
    
    if(!leftCheilion || !rightCheilion) return 0;

    // A simple 2D asymmetry score for demonstration
    const asymmetry = Math.abs(leftCheilion.y - rightCheilion.y);
    return asymmetry;
}

function updateRiskScore(data, asymmetry) {
    // This is a simplified risk calculation for the demo
    let risk = 0;
    const hrAnomaly = data.hr - baselineHR;
    const rrAnomaly = data.rr - baselineRR;

    if (hrAnomaly > 20) risk += 25; // High HR jump
    if (rrAnomaly > 6) risk += 15; // High RR jump
    if (asymmetry > 0.05) risk += 40; // Significant asymmetry
    
    riskScoreDisplay.textContent = `${Math.min(100, Math.round(risk))}%`;
}


// --- UI Drawing ---
function drawFaceMesh(mesh, asymmetry) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw all mesh points
    ctx.fillStyle = "rgba(100, 200, 255, 0.5)";
    for (const point of mesh) {
        ctx.beginPath();
        ctx.arc(point.x * canvas.width, point.y * canvas.height, 1, 0, 2 * Math.PI);
        ctx.fill();
    }
    
    // Highlight asymmetry
    if (asymmetry > 0.05) {
        const leftCheilion = mesh[61];
        const rightCheilion = mesh[291];
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(leftCheilion.x * canvas.width, leftCheilion.y * canvas.height);
        ctx.lineTo(rightCheilion.x * canvas.width, rightCheilion.y * canvas.height);
        ctx.stroke();
    }
}


// --- Audio Recording ---
function startAudioRecording() {
    // (Existing audio recording logic remains the same)
}

// --- Main Prompt Flow ---
function startPromptFlow() {
    startBtn.style.display = 'none';
    log("🚀 Starting neurological scan protocol...");
    runNextPrompt();
}

function runNextPrompt() {
    if (currentStep >= PROMPT_FLOW.length) {
        log("🏁 Data collection complete. Final result displayed.");
        // In a real scenario, the final result would come from a fusion engine
        // For now, the risk score is continuously updated.
        return;
    }

    const step = PROMPT_FLOW[currentStep];
    promptDisplay.innerHTML = step.text;
    log(`[Step ${currentStep + 1}/${PROMPT_FLOW.length}] ${step.text}`);
    
    if (step.action === 'calibrate') {
        // In a real scenario, we would average the HR/RR over the duration
        // For this demo, we'll just log it.
        log("Calibrating baseline vitals...");
    }

    if (step.audio) {
        recordBtn.style.display = 'block';
        if(step.prep) {
             recordBtn.disabled = true;
             recordBtn.textContent = "PREPARE TO RECORD";
        } else {
             recordBtn.disabled = false;
             recordBtn.textContent = "🎤 START RECORDING";
             recordBtn.onclick = startAudioRecording;
        }
    } else {
        recordBtn.style.display = 'none';
    }

    if (!step.audio || step.prep) {
        setTimeout(() => {
            currentStep++;
            runNextPrompt();
        }, step.duration);
    }
}

// --- Initializer ---
function initializeKiosk() {
    recordBtn.style.display = 'none';
    logsContainer.innerHTML = '';
    
    video.addEventListener('play', () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
    });

    startBtn.addEventListener('click', async () => {
        log("Requesting camera access...");
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
            video.srcObject = stream;
            await video.play();
            log("✅ Camera access granted.", 'success');
            // Now that the camera is ready, connect to the WebSocket
            connectWebSocket();
        } catch (err) {
            log(`❌ Camera error: ${err.name} - ${err.message}`, 'error');
            promptDisplay.textContent = "Camera access is required to perform the scan.";
        }
    });
}

initializeKiosk();
