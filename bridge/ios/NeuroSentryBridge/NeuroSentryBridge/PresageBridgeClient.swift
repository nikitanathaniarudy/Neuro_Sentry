import Foundation
import Combine
import SmartSpectraSwiftSDK

struct PresagePacket: Codable {
    let timestamp: Int64
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

    init(backendHost: String, apiKey: String) {
        self.backendURL = URL(string: backendHost) ?? URL(string: "ws://localhost:8000/presage_stream")!
        sdk.setApiKey(apiKey)
        sdk.setSmartSpectraMode(.continuous)
    }

    func startVitals() {
        vitals.startProcessing()
        vitals.startRecording()
        observeMetrics()
        connectWebSocket()
    }

    func stopVitals() {
        vitals.stopProcessing()
        vitals.stopRecording()
        webSocket?.cancel(with: .goingAway, reason: "app_background".data(using: .utf8))
        cancellables.removeAll()
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
            timestamp: Int64(Date().timeIntervalSince1970 * 1000),
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
