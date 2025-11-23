import SwiftUI
import SmartSpectraSwiftSDK

struct ContentView: View {
    // Paste your Presage API key here for the demo
    private let apiKey: String = "Fl5OoJHmDO5pfK89lw7UT5wWP414U8HB4ZvzoFNF"

    @StateObject private var bridge: PresageBridgeClient
    @State private var isSessionActive = false

    init() {
        let key = apiKey
        _bridge = StateObject(wrappedValue: PresageBridgeClient(apiKey: key))
    }

    var body: some View {
        ZStack {
            SmartSpectraView()
                .ignoresSafeArea()

            VStack {
                Spacer()
                if isSessionActive {
                    Button(action: {
                        bridge.stopVitals()
                        isSessionActive = false
                    }) {
                        Text("End Session")
                            .fontWeight(.bold)
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(Color.red)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                    }
                    .padding(.horizontal, 40)
                    .padding(.bottom, 50)
                } else {
                    Text("Session Ended")
                        .fontWeight(.bold)
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color.gray)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                        .padding(.horizontal, 40)
                        .padding(.bottom, 50)
                }
            }
        }
        .onAppear {
            bridge.startVitals()
            isSessionActive = true
        }
        .onDisappear {
            if isSessionActive { bridge.stopVitals() }
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
