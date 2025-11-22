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

// --- Global State ---
let ws = null;
let currentStep = 0;
let mediaRecorder = null;
let audioChunks = [];
let analysisInterval = null;

const PROMPT_FLOW = [
    { text: "Please position your face in the center of the camera frame.", duration: 4000 },
    { text: "Calibrating baseline vital signs. Please remain still.", duration: 5000 },
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

// --- WebSocket Simulation ---
function connectWebSocket() {
    log("🔗 Initializing Neuro-Sentry analysis engine...");
    ws = {
        send: (data) => log(`📤 Sending data chunk...`),
        close: () => log("🔌 Connection to engine closed.")
    };
    setTimeout(() => {
        log("✅ Analysis engine connected.", 'success');
        startPromptFlow();
    }, 1500);
}

// --- Data Simulation & Display ---
function generateMockPresageData() {
    const baseHR = 70 + Math.sin(Date.now() / 2000) * 10 + Math.random() * 5;
    const baseRR = 14 + Math.sin(Date.now() / 3000) * 2 + Math.random() * 2;
    return {
        hr: Math.round(baseHR),
        rr: Math.round(baseRR),
        facial_asym_score: Math.max(0, 0.1 + Math.random() * 0.4 * (currentStep > 2 ? 1 : 0)).toFixed(3),
        vocal_biomarker_instability: (Math.random() * 0.3).toFixed(3),
    };
}

function updateLiveDashboard(data) {
    hrValue.textContent = data.hr || '--';
    rrValue.textContent = data.rr || '--';
    updateAsymmetryDisplay(data.facial_asym_score);
}

// --- Asymmetry Visualization ---
function updateAsymmetryDisplay(score) {
    const ctx = canvas.getContext('2d');
    if (video.videoWidth) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if(score > 0.15) {
            ctx.strokeStyle = `rgba(220, 53, 69, ${score * 2})`;
            ctx.lineWidth = 4;
            ctx.beginPath();
            // Simulate drawing a line on one side of the face
            const midX = canvas.width / 2;
            const midY = canvas.height / 2;
            ctx.moveTo(midX + 20, midY - 50);
            ctx.bezierCurveTo(midX + 60, midY, midX + 40, midY + 70, midX + 30, midY + 90);
            ctx.stroke();
        }
    }
}

// --- Audio Recording ---
function startAudioRecording() {
    recordBtn.textContent = "RECORDING...";
    recordBtn.classList.add('recording');
    recordBtn.disabled = true;

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                log(`🎙️ Audio captured (${(audioBlob.size / 1024).toFixed(1)} KB)`);
                stream.getTracks().forEach(track => track.stop());
                currentStep++;
                runNextPrompt();
            };
            mediaRecorder.start();
            setTimeout(() => {
                if (mediaRecorder.state === "recording") {
                    mediaRecorder.stop();
                }
            }, PROMPT_FLOW[currentStep].duration - 500);
        })
        .catch(err => {
            log("❌ Audio recording failed.", 'error');
            currentStep++;
            runNextPrompt();
        });
}

// --- Main Prompt Flow ---
function startPromptFlow() {
    startBtn.style.display = 'none';
    log("🚀 Starting neurological scan protocol...");
    analysisInterval = setInterval(() => {
        const mockData = generateMockPresageData();
        updateLiveDashboard(mockData);
        ws.send(JSON.stringify(mockData));
    }, 1000);
    runNextPrompt();
}

function runNextPrompt() {
    if (currentStep >= PROMPT_FLOW.length) {
        clearInterval(analysisInterval);
        log("🏁 Data collection complete. Running final fusion analysis...");
        setTimeout(renderFinalResults, 4000);
        return;
    }

    const step = PROMPT_FLOW[currentStep];
    promptDisplay.innerHTML = step.text;
    log(`[Step ${currentStep + 1}/${PROMPT_FLOW.length}] ${step.text}`);

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


// --- Final Results ---
function renderFinalResults() {
    const finalRisk = 30 + Math.random() * 65;
    let triage, rationale;

    if (finalRisk > 75) {
        triage = 'High';
        rationale = "Significant facial asymmetry detected (unilateral drooping). Vocal biomarkers indicate slurred speech. Combined with elevated heart rate, this strongly suggests a high probability of a cerebrovascular event. Immediate ER transport and Code Stroke protocol advised.";
    } else if (finalRisk > 40) {
        triage = 'Moderate';
        rationale = "Minor facial asymmetry noted during smile test. Speech analysis shows subtle articulation issues. Vital signs are slightly elevated. Recommend follow-up with a neurologist within 24 hours for a more comprehensive evaluation.";
    } else {
        triage = 'Low';
        rationale = "No significant facial asymmetry detected. Speech patterns are clear and within normal parameters. Vital signs are stable. Neurological event is unlikely. Standard follow-up is recommended.";
    }

    log("✅ Final analysis complete.", 'success');
    
    scanView.classList.add('hidden');
    dashboard.classList.remove('hidden');

    riskScoreDisplay.textContent = `${Math.round(finalRisk)}%`;
    triageLevelDisplay.textContent = `${triage} Risk`;
    rationaleBox.textContent = rationale;

    // Apply color coding
    const triageClass = `triage-${triage.toLowerCase()}`;
    riskScoreDisplay.classList.add(triageClass);
    triageLevelDisplay.classList.add(triageClass);
}

// --- Initializer ---
function initializeKiosk() {
    recordBtn.style.display = 'none';
    logsContainer.innerHTML = ''; // Clear logs on start
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
            connectWebSocket();
        } catch (err) {
            log(`❌ Camera error: ${err.name} - ${err.message}`, 'error');
            promptDisplay.textContent = "Camera access is required to perform the scan.";
        }
    });
}

initializeKiosk();