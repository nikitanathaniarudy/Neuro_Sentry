import json
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import random
import uvicorn

app = FastAPI()

# Allow frontend JS to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/data")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Fake mesh points
            mesh = [{"x": random.random(), "y": random.random()} for _ in range(478)]
            # Fake vitals
            hr = random.randint(60, 100)
            rr = random.randint(12, 20)
            
            packet = {
                "mesh": mesh,
                "hr": hr,
                "rr": rr
            }
            
            await websocket.send_text(json.dumps(packet))
            await asyncio.sleep(0.1)  # 10Hz update rate
    except Exception as e:
        print("WebSocket disconnected:", e)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)