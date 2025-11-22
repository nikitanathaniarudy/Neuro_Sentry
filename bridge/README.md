# Presage Bridge (Swift → FastAPI)

This bridge is a minimal Swift layer that runs the Presage SmartSpectra SDK on an iOS device (front camera), extracts vitals and face landmarks, and streams them to the backend WebSocket `/presage_stream`. The backend already forwards each rolling window to Gemini for triage.

## Requirements
- Xcode 15+, iOS 15+ physical device (camera required)
- SmartSpectra Swift SDK dependency: `https://github.com/Presage-Security/SmartSpectra` (branch `main`)
- Presage API key from https://physiology.presagetech.com
- Backend reachable on the same network; default: `ws://<backend-host>:8000/presage_stream`

## How it works
1) `PresageBridgeClient` (Swift) configures the SDK, subscribes to `metricsBuffer` and `edgeMetrics` for vitals + face landmarks.
2) Each new metrics update is converted into the backend schema (`timestamp`, `heart_rate`, `breathing_rate`, `quality`, `regions`, `face_points`).
3) The packet is sent as JSON over a persistent `URLSessionWebSocketTask` to `/presage_stream`.
4) Backend aggregates a 2–3s rolling window, calls Gemini, and streams triage to the webpage via `/live_state`.

## Integrate in your iOS app
1) Add package dependency in Xcode: `https://github.com/Presage-Security/SmartSpectra` → branch `main`.
2) Add camera permission to `Info.plist`:
```xml
<key>NSCameraUsageDescription</key>
<string>This app needs camera access to measure vitals with SmartSpectra.</string>
```
3) Drop `PresageBridge.swift` (below) into your app target. Set your API key and backend host.
4) Run on device; confirm console logs show `ws connected` and backend logs incrementing buffer count.

## PresageBridge.swift (headless bridge)
```swift
import Foundation
import Combine
import SmartSpectraSwiftSDK
import AVFoundation

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
    private let apiKey: String

    init(backendHost: String = "ws://localhost:8000/presage_stream", apiKey: String) {
        self.backendURL = URL(string: backendHost)!
        self.apiKey = apiKey
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

        sdk.$edgeMetrics
            .sink { _ in /* landmarks handled in sendPacket via sdk.edgeMetrics */ }
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

// Usage (e.g., in AppDelegate or a SwiftUI App):
// let bridge = PresageBridgeClient(backendHost: "ws://your-backend:8000/presage_stream", apiKey: "YOUR_API_KEY")
```

## Tips
- Use the device’s local IP or host machine IP for `backendHost`; avoid `localhost` when device and backend differ.
- Keep the app in the foreground during the demo; background camera capture is restricted.
- If you need offline fallback, backend already returns a deterministic triage output when Gemini is unavailable.
