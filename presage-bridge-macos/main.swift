import Hummingbird
import HummingbirdWebSocket
import Foundation

// --- 1. Data Structures ---
struct PresagePacket: Codable {
    let hr: Int
    let rr: Int
    let mesh: [Point3D]
    let confidence: Double
    let timestamp: UInt64
    let asymmetry: Double
    let stroke_risk: Int
    let bell_palsy_risk: Int
}

struct Point3D: Codable {
    let x: Double
    let y: Double
    let z: Double
}

// --- 2. Data Simulation Logic ---
func generateMockPresageData() -> PresagePacket {
    let mesh = (0..<478).map { _ in
        Point3D(x: Double.random(in: 0.3...0.7),
                y: Double.random(in: 0.2...0.8),
                z: Double.random(in: -0.05...0.05))
    }
    
    let leftCheilion = mesh[61]
    let rightCheilion = mesh[291]
    let asymmetry = abs(leftCheilion.y - rightCheilion.y) * 10

    return PresagePacket(
        hr: Int.random(in: 60...110),
        rr: Int.random(in: 12...22),
        mesh: mesh,
        confidence: Double.random(in: 0.85...0.99),
        timestamp: UInt64(Date().timeIntervalSince1970 * 1000),
        asymmetry: asymmetry,
        stroke_risk: Int.random(in: 5...95),
        bell_palsy_risk: Int.random(in: 5...60)
    )
}

// --- 3. Application Setup ---
// Create the application
let app = HBApplication(configuration: .init(address: .hostname("localhost", port: 8081)))

// Add WebSocket upgrade
app.ws.add(path: "/") { _, ws in
    print("INFO: Web client connected.")
    
    let scheduled = ws.channel.eventLoop.scheduleRepeatedTask(
        initialDelay: .seconds(1),
        delay: .milliseconds(100)
    ) { _ in
        let packet = generateMockPresageData()
        let encoder = JSONEncoder()
        do {
            let data = try encoder.encode(packet)
            if let jsonString = String(data: data, encoding: .utf8) {
                ws.write(.text(jsonString))
            }
        } catch {
            print("ERROR: Failed to encode JSON: \(error)")
        }
    }
    
    ws.onClose { _ in
        print("INFO: Web client disconnected.")
        scheduled.cancel()
    }
}

// Start the server
do {
    try app.start()
    app.wait()
} catch {
    print("ERROR: Failed to start server: \(error)")
    app.stop()
}
