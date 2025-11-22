import Foundation
import Combine
import SmartSpectraSwiftSDK
import AVFoundation

// Paste your Mac LAN IP here (e.g., ws://192.168.1.23:8000/presage_stream)
private let BACKEND_WS = "ws://172.20.10.2:8000/presage_stream"

struct PresagePacket: Codable {
    let type: String
    let timestamp: String
    let heart_rate: Double?
    let breathing_rate: Double?
    let quality: Double?
    let regions: [String: Double]
    let face_points: [[Double]]
}

final class PresageBridgeClient: ObservableObject {
    private let sdk = SmartSpectraSwiftSDK.shared
    private let vitals = SmartSpectraVitalsProcessor.shared
    private var cancellables: Set<AnyCancellable> = []
    private var webSocket: URLSessionWebSocketTask?
    @Published var isRunning = false

    init(apiKey: String) {
        sdk.setApiKey(apiKey)
        sdk.setSmartSpectraMode(.continuous)
        // Force the front camera as per instructions
        sdk.setCameraPosition(.front)
    }

    func startVitals() {
        guard !isRunning else {
            print("[PresageBridge] startVitals called but already running.")
            return
        }
        print("[PresageBridge] Starting vitals...")
        isRunning = true
        connectWebSocket()
        // Delay processing to allow websocket to connect and graph to initialize
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.vitals.startProcessing()
            self.vitals.startRecording()
            self.observeMetrics()
            self.sendControl(type: "session_start")
            print("[PresageBridge] Vitals processing and recording started.")
        }
    }

    func stopVitals() {
        guard isRunning else {
            print("[PresageBridge] stopVitals called but not running.")
            return
        }
        print("[PresageBridge] Stopping vitals...")
        isRunning = false
        vitals.stopProcessing()
        vitals.stopRecording()
        sendControl(type: "session_end")
        cancellables.removeAll()
        webSocket?.cancel(with: .goingAway, reason: "stop".data(using: .utf8))
        webSocket = nil
        print("[PresageBridge] Vitals stopped.")
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
                print("[PresageBridge] ws error: \(error)")
                // Handle reconnect or other errors
            case .success(let message):
                print("[PresageBridge] ws received: \(message)")
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
        let hr = metrics.pulse.rate.last?.value
        let br = metrics.breathing.rate.last?.value
        let quality = metrics.pulse.rate.last?.confidence

        var regions: [String: Double] = [:]
        if let talking = sdk.edgeMetrics?.face.talking.last { regions["talking"] = talking.detected ? 1 : 0 }
        if let blinking = sdk.edgeMetrics?.face.blinking.last { regions["blinking"] = blinking.detected ? 1 : 0 }

        var points: [[Double]] = []
        if let lastLandmarks = sdk.edgeMetrics?.face.landmarks.last?.value {
            points = lastLandmarks.map { [Double($0.x), Double($0.y)] }
        }

        let packet = PresagePacket(
            type: "vitals",
            timestamp: ISO8601DateFormatter().string(from: Date()),
            heart_rate: hr.map(Double.init),
            breathing_rate: br.map(Double.init),
            quality: quality.map(Double.init),
            regions: regions,
            face_points: points
        )
        sendPacket(packet)
    }
    
    private func sendPacket(_ packet: PresagePacket) {
        guard let ws = webSocket else { return }
        guard let data = try? JSONEncoder().encode(packet),
              let json = String(data: data, encoding: .utf8) else {
            print("[PresageBridge] Packet encode failed")
            return
        }
        ws.send(.string(json)) { error in
            if let error = error { print("[PresageBridge] Packet send error: \(error)") }
        }
    }

    private func sendControl(type: String) {
        guard let ws = webSocket else { return }
        let payload: [String: Any] = ["type": type, "timestamp": ISO8601DateFormatter().string(from: Date())]
        guard let data = try? JSONSerialization.data(withJSONObject: payload, options: []),
              let json = String(data: data, encoding: .utf8) else { return }
        ws.send(.string(json)) { error in
            if let error = error { print("[PresageBridge] control send error: \(error)") }
        }
    }
}

