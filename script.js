// --- DOM References ---
const startBtn = document.getElementById('start-scan-btn');
const recordBtn = document.getElementById('record-audio-btn');
const promptDisplay = document.getElementById('current-prompt');
const scanView = document.getElementById('scan-view');
const dashboard = document.getElementById('dashboard');

const hrValue = document.getElementById('hr-value');
const rrValue = document.getElementById('rr-value');
const riskScore = document.getElementById('risk-score');
const triageLevel = document.getElementById('triage-level');
const rationaleBox = document.getElementById('rationale-box');
const riskPanel = document.getElementById('risk-panel');

// --- Global State ---
let ws = null;
let currentStep = 0;
let mediaRecorder = null;
let audioChunks = [];
const PROMPT_FLOW = [
    { text: "Starting Neuro-Sentry Scan... Please position yourself in the camera frame.", duration: 3000 },
    { text: "CALIBRATION: Maintain a neutral facial expression for 3 seconds.", duration: 3000 },
    { text: "FACIAL ASYMMETRY TEST: Please smile widely, showing your teeth, for 3 seconds.", duration: 3000 },
    { text: "SPEECH ASSESSMENT: Please clearly say 'The quick brown fox jumps over the lazy dog'", duration: 5000, audio: true },
    { text: "ARM STRENGTH TEST: Please describe if you notice any arm weakness or numbness.", duration: 4000, audio: true },
    { text: "ANALYZING DATA... Running Cincinnati Stroke Scale assessment.", duration: 6000 },
];

// --- WebSocket Connection Handler ---
function connectWebSocket() {
    // For demo purposes, we'll simulate WebSocket behavior
    // In production, replace with actual WebSocket URL
    console.log("🔗 Connecting to Neuro-Sentry analysis engine...");
    
    // Simulate WebSocket connection
    ws = {
        send: (data) => console.log("📤 Sent:", data),
        close: () => console.log("🔌 WebSocket closed")
    };
    
    // Simulate successful connection
    setTimeout(() => {
        console.log("✅ WebSocket connected to Presage bridge.");
        startPromptFlow();
    }, 1000);
}

// --- Mock Data Generator for Demo ---
function generateMockPresageData() {
    const baseHR = 65 + Math.floor(Math.random() * 40); // 65-105 bpm
    const baseRR = 12 + Math.floor(Math.random() * 10); // 12-22 breaths/min
    
    return {
        hr: baseHR,
        rr: baseRR,
        facial_asym_score: (Math.random() * 0.5).toFixed(3),
        hrv: (25 + Math.random() * 30).toFixed(1),
        status: currentStep < PROMPT_FLOW.length - 1 ? 'COLLECTING' : 'FINISHED'
    };
}

// --- Live Data Handler ---
function handleLivePresageData(data) {
    // Update Vitals Display
    hrValue.textContent = data.hr || '--';
    rrValue.textContent = data.rr || '--';
    
    // Simulate risk calculation based on vitals
    const risk = calculateMockRisk(data);
    
    // Update risk display during collection
    if (data.status === 'COLLECTING') {
        riskScore.textContent = Math.min(risk, 45); // Cap at 45% during collection
        riskScore.style.color = risk < 30 ? '#ffc107' : '#ff9800';
    }
    
    // Handle asymmetry visualization
    const asymmetryScore = data.facial_asym_score || 0;
    updateAsymmetryDisplay(asymmetryScore);
}

// --- Mock Risk Calculation (Cincinnati Stroke Scale based) ---
function calculateMockRisk(data) {
    let risk = 0;
    
    // Heart Rate variability (lower HRV = higher risk)
    if (data.hr > 100) risk += 25;
    if (data.hrv < 30) risk += 20;
    
    // Respiration rate (higher RR = potential sepsis/stress)
    if (data.rr > 20) risk += 15;
    
    // Facial asymmetry
    if (data.facial_asym_score > 0.2) risk += 30;
    
    return Math.min(risk, 100);
}

// --- Asymmetry Visualization ---
function updateAsymmetryDisplay(score) {
    const canvas = document.getElementById('face-overlay');
    const ctx = canvas.getContext('2d');
    const video = document.getElementById('webcam-feed');
    
    if (video.videoWidth) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw facial grid overlay
        ctx.strokeStyle = score > 0.2 ? '#f73859' : '#87ceeb';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 3]);
        
        // Simple facial landmark simulation
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 3;
        
        // Draw asymmetric indicators if score is high
        if (score > 0.2) {
            ctx.fillStyle = 'rgba(247, 56, 89, 0.3)';
            ctx.beginPath();
            ctx.arc(centerX - 50, centerY + 20, 30, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.strokeRect(centerX - 80, centerY - 40, 160, 200);
    }
}

// --- Audio Recording Handler ---
function startAudioRecording() {
    recordBtn.textContent = "🎤 Recording...";
    recordBtn.disabled = true;
    
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                console.log("🎙️ Audio recorded:", audioBlob);
                
                // In real implementation, send to backend for analysis
                // ws.send(JSON.stringify({ type: 'audio', data: audioBlob }));
                
                // Stop all audio tracks
                stream.getTracks().forEach(track => track.stop());
                
                // Move to next step
                currentStep++;
                runNextPrompt();
            };
            
            mediaRecorder.start();
            
            // Stop recording after 5 seconds
            setTimeout(() => {
                if (mediaRecorder.state === "recording") {
                    mediaRecorder.stop();
                }
            }, 5000);
        })
        .catch(err => {
            console.error("❌ Audio recording failed:", err);
            // Fallback: continue without audio
            currentStep++;
            runNextPrompt();
        });
}

// --- Prompt Flow State Machine ---
function startPromptFlow() {
    startBtn.style.display = 'none';
    runNextPrompt();
}

function runNextPrompt() {
    if (currentStep >= PROMPT_FLOW.length) {
        promptDisplay.textContent = "Data collection complete. Running fusion analysis...";
        
        // Simulate final analysis
        setTimeout(() => {
            const finalData = {
                status: 'FINISHED',
                overall_risk_probability: 65 + Math.floor(Math.random() * 35),
                triage_level: 'HIGH',
                short_rationale: "Facial asymmetry detected with unilateral smile weakness. Elevated heart rate (102 bpm) and speech articulation abnormalities noted. Recommended: Immediate neurological consultation and CT scan."
            };
            renderFinalResults(finalData);
        }, 3000);
        return;
    }

    const step = PROMPT_FLOW[currentStep];
    promptDisplay.textContent = step.text;

    // Simulate data collection during each step
    const mockData = generateMockPresageData();
    handleLivePresageData(mockData);

    if (step.audio) {
        recordBtn.style.display = 'inline-block';
        recordBtn.textContent = "🎤 START RECORDING";
        recordBtn.disabled = false;
        recordBtn.onclick = startAudioRecording;
    } else {
        recordBtn.style.display = 'none';
        
        // Auto-advance for non-audio steps
        setTimeout(() => {
            currentStep++;
            runNextPrompt();
        }, step.duration);
    }
}

// --- Final Results Renderer ---
function renderFinalResults(data) {
    scanView.classList.add('hidden');
    dashboard.classList.remove('hidden');
    
    const score = Math.round(data.overall_risk_probability);
    riskScore.textContent = score;
    triageLevel.textContent = `Triage Level: ${data.triage_level}`;
    rationaleBox.textContent = data.short_rationale;

    // Visual alert for high risk
    if (score >= 70) {
        riskPanel.classList.add('alert-high');
        triageLevel.innerHTML = '🚨 <strong>URGENT: CODE STROKE ADVISED</strong>';
    } else if (score >= 50) {
        triageLevel.innerHTML = '⚠️ <strong>MODERATE RISK: NEURO CONSULT RECOMMENDED</strong>';
    } else {
        triageLevel.innerHTML = '✅ <strong>LOW RISK: ROUTINE ASSESSMENT</strong>';
    }
}

// --- Initializer ---
startBtn.addEventListener('click', () => {
    console.log("🚀 Starting Neuro-Sentry Scan...");
    
    // Get webcam access
    navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480 } 
    })
    .then(stream => {
        const video = document.getElementById('webcam-feed');
        video.srcObject = stream;
        
        // Start WebSocket connection
        connectWebSocket();
    })
    .catch(err => {
        console.error("❌ Webcam access denied:", err);
        // Continue without webcam for demo purposes
        connectWebSocket();
    });
});

// Initialize with a safe state
recordBtn.style.display = 'none';
