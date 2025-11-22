// swift-tools-version: 5.10
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "Neuro_Sentry",
    platforms: [
        .macOS(.v13) 
    ],
    dependencies: [
        .package(url: "https://github.com/hummingbird-project/hummingbird.git", from: "1.0.0"),
        .package(url: "https://github.com/hummingbird-project/hummingbird-websocket.git", from: "1.0.0")
    ],
    targets: [
        .executableTarget(
            name: "Neuro_Sentry",
            dependencies: [
                .product(name: "Hummingbird", package: "hummingbird"),
                .product(name: "HummingbirdWebSocket", package: "hummingbird-websocket")
            ],
            path: "Sources"
        ),
    ]
)
