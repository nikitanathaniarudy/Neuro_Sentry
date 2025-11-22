import SwiftUI
import SmartSpectraSwiftSDK

struct ContentView: View {
    // Paste your Presage API key here for the demo
    private let apiKey: String = "YOUR_PRESAGE_API_KEY"
    @StateObject private var bridge = PresageBridgeClient(apiKey: "YOUR_PRESAGE_API_KEY")

    var body: some View {
        SmartSpectraView()
            .ignoresSafeArea()
            .onAppear {
                bridge.startVitals()
            }
            .onDisappear {
                bridge.stopVitals()
            }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
