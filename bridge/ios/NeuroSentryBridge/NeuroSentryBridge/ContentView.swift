import SwiftUI
import SmartSpectraSwiftSDK

struct ContentView: View {
    // Paste your Presage API key here for the demo
    private let apiKey: String = "Fl5OoJHmDO5pfK89lw7UT5wWP414U8HB4ZvzoFNF"

    @StateObject private var bridge: PresageBridgeClient

    init() {
        let key = apiKey
        _bridge = StateObject(wrappedValue: PresageBridgeClient(apiKey: key))
    }

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
