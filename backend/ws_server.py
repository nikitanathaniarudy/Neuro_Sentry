from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import List

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# In-memory store for connected clients
connected_clients: List[WebSocket] = []

@app.websocket("/ws/presage")
async def presage_ws(websocket: WebSocket):
    """
    This endpoint handles the WebSocket connection from the native Presage bridge.
    It receives data from the bridge and forwards it to all connected web clients.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # For each connected web client, send the data
            for client in connected_clients:
                await client.send_text(data)
    except WebSocketDisconnect:
        print("Native bridge disconnected")

@app.websocket("/ws/data")
async def data_ws(websocket: WebSocket):
    """
    This endpoint handles the WebSocket connection from the web UI.
    It adds the client to the list of connected clients and keeps the connection open.
    """
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("Web client disconnected")
        connected_clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
