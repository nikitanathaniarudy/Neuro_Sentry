import Foundation
import Combine
import SmartSpectraSwiftSDK
import AVFoundation

// Matches backend PresagePacket schema
struct PresagePacket: Codable {
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
    private let backendURL: URL

    init(backendHost: String = "ws://localhost:8000/presage_stream", apiKey: String) {
        self.backendURL = URL(string: backendHost)!
        sdk.setApiKey(apiKey)
        sdk.setSmartSpectraMode(.continuous)
        vitals.startProcessing()
        vitals.startRecording()
        observeMetrics()
        connectWebSocket()
    }

    private func connectWebSocket() {
        webSocket?.cancel()
        webSocket = URLSession(configuration: .default).webSocketTask(with: backendURL)
        webSocket?.resume()
        listen()
        print("[PresageBridge] ws connected -> \(backendURL)")
    }

    private func listen() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .failure(let error):
                print("[PresageBridge] ws error: \(error)"); self?.retry()
            case .success:
                self?.listen()
            }
        }
    }

    private func retry() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) { [weak self] in self?.connectWebSocket() }
    }

    private func observeMetrics() {
        sdk.$metricsBuffer
            .compactMap { $0 }
            .sink { [weak self] metrics in
                self?.sendPacket(metrics: metrics)
            }
            .store(in: &cancellables)
    }

    private func sendPacket(metrics: Presage_Physiology_MetricsBuffer) {
        let hr = metrics.pulse.rate.last?.value
        let br = metrics.breathing.rate.last?.value
        let quality = metrics.pulse.rate.last?.confidence

        var regions: [String: Double] = [:]
        if let talking = sdk.edgeMetrics?.face.talking.last { regions["talking"] = talking.detected ? 1 : 0 }
        if let blinking = sdk.edgeMetrics?.face.blinking.last { regions["blinking"] = blinking.detected ? 1 : 0 }

        var points: [[Double]] = []
        if let lastLandmarks = sdk.edgeMetrics?.face.landmarks.last?.value {
            points = lastLandmarks.map { [Double($0.x) / 1280.0, Double($0.y) / 1280.0] }
        }

        let packet = PresagePacket(
            timestamp: ISO8601DateFormatter().string(from: Date()),
            heart_rate: hr.map(Double.init),
            breathing_rate: br.map(Double.init),
            quality: quality.map(Double.init),
            regions: regions,
            face_points: points
        )

        guard let data = try? JSONEncoder().encode(packet), let json = String(data: data, encoding: .utf8) else {
            print("[PresageBridge] encode failed")
            return
        }

        webSocket?.send(.string(json)) { [weak self] error in
            if let error = error {
                print("[PresageBridge] send error: \(error)"); self?.retry()
            }
        }
    }
}

// Usage example (e.g., in AppDelegate or SwiftUI App):
// let bridge = PresageBridgeClient(backendHost: "ws://your-backend:8000/presage_stream", apiKey: "YOUR_API_KEY")
