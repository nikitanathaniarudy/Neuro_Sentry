import asyncio
import websockets
import json
import random
from datetime import datetime, timezone

async def send_presage_packets():
    uri = "ws://localhost:8000/presage_stream"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            while True:
                # Generate dummy PresagePacket data
                heart_rate = random.uniform(60.0, 100.0)
                breathing_rate = random.uniform(12.0, 20.0)
                quality = random.uniform(0.5, 1.0)

                # Generate dummy face_points (e.g., 5 points, each [x, y])
                face_points = []
                for _ in range(5):
                    face_points.append([random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)])

                # Dummy regions data
                regions = {
                    "forehead": random.uniform(0.0, 1.0),
                    "cheeks": random.uniform(0.0, 1.0)
                }
                
                packet = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "heart_rate": round(heart_rate, 2),
                    "breathing_rate": round(breathing_rate, 2),
                    "quality": round(quality, 2),
                    "face_points": face_points,
                    "regions": regions,
                    "is_simulated": True # Indicate that this packet is from the simulator
                }
                
                await websocket.send(json.dumps(packet))
                # print(f"Sent: {packet}")
                await asyncio.sleep(random.uniform(0.2, 0.5)) # Send at 2-5 Hz

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed by backend: {e}. Is the backend running at {uri} and accepting valid packets?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("Starting Presage Simulator. Ensure backend is running at ws://localhost:8000/presage_stream")
    asyncio.run(send_presage_packets())
