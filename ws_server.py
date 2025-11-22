import asyncio
import json
import random
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI()

# Allow your frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/data")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    try:
        while True:
            # --- Dummy vitals ---
            hr = random.randint(60, 100)  # Heart rate
            rr = random.randint(12, 20)   # Respiration rate

            # --- Dummy face mesh: 478 points in [0,1] range ---
            mesh = [{"x": random.random(), "y": random.random()} for _ in range(478)]

            # Send as JSON
            payload = json.dumps({"hr": hr, "rr": rr, "mesh": mesh})
            await websocket.send_text(payload)

            await asyncio.sleep(0.1)  # 10 FPS
    except Exception as e:
        print("Client disconnected:", e)