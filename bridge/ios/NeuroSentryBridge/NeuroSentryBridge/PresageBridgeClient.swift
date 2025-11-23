import Foundation
import Combine
import SmartSpectraSwiftSDK

// Set this to your Mac LAN IP (e.g., "ws://192.168.1.20:8000/presage_stream")
private let BACKEND_WS = "ws://172.20.10.2:8000/presage_stream"

struct PresagePacket: Codable {
    let type: String
    let timestamp: String
    let heart_rate: Double?
    let breathing_rate: Double?
    let quality: Double?
    let blood_pressure: [String: Double]?
    let face_points: [[Double]]
}

final class PresageBridgeClient: ObservableObject {
    private let sdk = SmartSpectraSwiftSDK.shared
    private let vitals = SmartSpectraVitalsProcessor.shared
    private var cancellables: Set<AnyCancellable> = []
    private var webSocket: URLSessionWebSocketTask?
    @Published var isRunning = false
    private var didLogFirstPacket = false

    init(apiKey: String) {
        sdk.setApiKey(apiKey)
        sdk.setSmartSpectraMode(.continuous)
    }

    func startVitals() {
        guard !isRunning else { return }
        isRunning = true
        didLogFirstPacket = false
        connectWebSocket()

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
            self.vitals.startProcessing()
            self.vitals.startRecording()
            self.observeMetrics()
            self.sendControl(type: "session_start")
            print("[PresageBridge] session_start sent")
        }
    }

    func stopVitals() {
        guard isRunning else { return }
        isRunning = false
        vitals.stopProcessing()
        vitals.stopRecording()
        sendControl(type: "session_end")
        cancellables.removeAll()
        webSocket?.cancel(with: .goingAway, reason: "stop".data(using: .utf8))
        webSocket = nil
        print("[PresageBridge] session_end sent and WS closed")
    }

    private func connectWebSocket() {
        webSocket?.cancel()
        guard let url = URL(string: BACKEND_WS) else {
            print("[PresageBridge] BACKEND_WS invalid. Set your Mac LAN IP.")
            return
        }
        webSocket = URLSession(configuration: .default).webSocketTask(with: url)
        webSocket?.resume()
        listen()
        print("[PresageBridge] ws connected -> \(url)")
    }

    private func listen() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .failure(let error):
                print("[PresageBridge] ws error: \(error.localizedDescription)")
            case .success:
                self?.listen()
            }
        }
    }

    private func observeMetrics() {
        sdk.$metricsBuffer
            .compactMap { $0 }
            .sink { [weak self] metrics in
                self?.handleMetrics(metrics: metrics)
            }
            .store(in: &cancellables)
    }

    private func handleMetrics(metrics: Presage_Physiology_MetricsBuffer) {
        let hrValue = metrics.pulse.rate.last?.value
        let brValue = metrics.breathing.rate.last?.value
        let qualityValue = metrics.pulse.rate.last?.confidence

        var points: [[Double]] = []
        if let lastLandmarks = sdk.edgeMetrics?.face.landmarks.last?.value {
            points = lastLandmarks.map { [Double($0.x), Double($0.y)] }
        }

        // Blood pressure may not be provided by SDK; pass nil if unavailable.
        let bp: [String: Double]? = nil

        let packet = PresagePacket(
            type: "vitals",
            timestamp: ISO8601DateFormatter().string(from: Date()),
            heart_rate: hrValue.map(Double.init),
            breathing_rate: brValue.map(Double.init),
            quality: qualityValue.map(Double.init),
            blood_pressure: bp,
            face_points: points
        )
        sendPacket(packet)
    }

    private func sendPacket(_ packet: PresagePacket) {
        guard let ws = webSocket else { return }
        do {
            let data = try JSONEncoder().encode(packet)
            if let jsonString = String(data: data, encoding: .utf8) {
                ws.send(.string(jsonString)) { error in
                    if let error = error { print("[PresageBridge] send error: \(error.localizedDescription)") }
                }
                if !didLogFirstPacket {
                    print("[PresageBridge] first packet JSON -> \(jsonString)")
                    didLogFirstPacket = true
                }
                print("[PresageBridge] sent vitals packet (HR: \(packet.heart_rate ?? -1))")
            }
        } catch {
            print("[PresageBridge] encode error: \(error.localizedDescription)")
        }
    }

    private func sendControl(type: String) {
        guard let ws = webSocket else { return }
        let payload: [String: Any] = ["type": type, "timestamp": ISO8601DateFormatter().string(from: Date())]
        guard let data = try? JSONSerialization.data(withJSONObject: payload, options: []),
              let json = String(data: data, encoding: .utf8) else { return }
        ws.send(.string(json)) { error in
            if let error = error { print("[PresageBridge] control send error: \(error.localizedDescription)") }
        }
    }
}
