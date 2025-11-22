import SwiftUI
import SmartSpectraSwiftSDK

struct ContentView: View {
    @StateObject private var sdk = SmartSpectraSwiftSDK.shared

    // Put your key here for now (later move to a safer place)
    private let apiKey: String = "Fl5OoJHmDO5pfK89lw7UT5wWP414U8HB4ZvzoFNF"

    // Hackathon demo state
    @State private var didConfigure = false
    @State private var timer: Timer?
    @State private var secondsRemaining: Int = 30

    @State private var lastHR: Double?
    @State private var lastBR: Double?
    @State private var faceCount: Int = 0
    @State private var riskFlag: String = "—"

    var body: some View {
        ZStack(alignment: .top) {
            // Full-screen camera + Presage UI
            SmartSpectraView()
                .ignoresSafeArea()
                .onAppear {
                    configureSDKIfNeeded()
                    startHackathonLoop()
                }
                .onDisappear {
                    stopHackathonLoop()
                }

            // Simple overlay so you SEE results on-device
            VStack(alignment: .leading, spacing: 8) {
                Text("NeuroSentry Checkup (demo)")
                    .font(.headline)
                    .bold()

                if let hr = lastHR, let br = lastBR {
                    Text("HR: \(Int(hr)) BPM   |   BR: \(String(format: "%.1f", br)) RPM")
                        .font(.title3)
                        .bold()
                } else {
                    Text("Align face, hold still, good lighting…")
                        .font(.subheadline)
                }

                Text("Faces detected: \(faceCount)")
                    .font(.subheadline)

                Text("Risk flag: \(riskFlag)")
                    .font(.subheadline)
                    .bold()

                Text("Time left: \(secondsRemaining)s")
                    .font(.subheadline)
                    .opacity(0.9)

                Text("Note: demo heuristic, not a medical device")
                    .font(.caption2)
                    .opacity(0.7)
            }
            .padding(12)
            .foregroundColor(.white)
            .background(Color.black.opacity(0.5))
            .cornerRadius(12)
            .padding()
        }
    }

    // MARK: - SDK setup

    private func configureSDKIfNeeded() {
        guard !didConfigure else { return }
        didConfigure = true

        sdk.setApiKey(apiKey)

        // Config per docs
        sdk.setSmartSpectraMode(.continuous)  // live updates
        sdk.setMeasurementDuration(30.0)      // 20–120s ok
        sdk.setCameraPosition(.front)
        sdk.setRecordingDelay(3)
        sdk.showControlsInScreeningView(true)

        print("[Setup] SmartSpectra configured with API key auth.")
    }

    // MARK: - Hackathon loop (pull + log every second)

    private func startHackathonLoop() {
        secondsRemaining = 30
        pullLatestMetricsAndLog()

        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            pullLatestMetricsAndLog()
            if secondsRemaining > 0 { secondsRemaining -= 1 }
        }
    }

    private func stopHackathonLoop() {
        timer?.invalidate()
        timer = nil
    }

    private func pullLatestMetricsAndLog() {
        // Face count / status
        faceCount = detectedFaceCount()

        guard let metrics = sdk.metricsBuffer else {
            lastHR = nil
            lastBR = nil
            riskFlag = "—"
            print("[Hackathon] No metrics yet. faces=\(faceCount). Align face + lighting.")
            return
        }

        // Latest values come as Float? from protobuf
        let hrF: Float? = metrics.pulse.rate.last?.value
        let brF: Float? = metrics.breathing.rate.last?.value

        if let hrF, let brF {
            // FIX: cast Float -> Double to match state vars
            lastHR = Double(hrF)
            lastBR = Double(brF)

            riskFlag = computeRiskFlag(
                hr: lastHR!,
                br: lastBR!,
                faces: faceCount
            )

            print("[Vitals] HR=\(Int(lastHR!)) BPM | BR=\(String(format: "%.1f", lastBR!)) RPM | faces=\(faceCount) | risk=\(riskFlag)")
        } else {
            lastHR = nil
            lastBR = nil
            riskFlag = "—"
            print("[Vitals] Waiting for stable vitals… faces=\(faceCount)")
        }
    }

    // MARK: - Helpers

    private func detectedFaceCount() -> Int {
        // Many builds only expose hasFace, not multi-face count.
        // We treat "hasFace" as 1 face; otherwise 0.
        guard let edge = sdk.edgeMetrics else { return 0 }
        return edge.hasFace ? 1 : 0
    }

    private func computeRiskFlag(hr: Double, br: Double, faces: Int) -> String {
        // Simple non-medical heuristic for demo UI.
        if faces != 1 { return "CHECK FACE" }

        var score = 0
        if hr >= 110 { score += 2 }
        else if hr >= 95 { score += 1 }

        if br >= 24 { score += 2 }
        else if br >= 20 { score += 1 }

        if score >= 3 { return "HIGH" }
        if score == 2 { return "MODERATE" }
        return "LOW"
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
