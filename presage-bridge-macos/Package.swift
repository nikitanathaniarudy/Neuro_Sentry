// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "presage-bridge-macos",
    platforms: [.macOS(.v12)],
    dependencies: [
        .package(url: "https://github.com/hummingbird-project/hummingbird.git", from: "1.9.0"),
        .package(url: "https://github.com/hummingbird-project/hummingbird-websocket.git", from: "1.0.0")
    ],
    targets: [
        .executableTarget(
            name: "presage-bridge-macos",
            dependencies: [
                .product(name: "Hummingbird", package: "hummingbird"),
                .product(name: "HummingbirdWebSocket", package: "hummingbird-websocket"),
            ],
            swiftSettings: [
                // Enable better optimizations when building in Release configuration. Despite the use of
                // the `.unsafeFlags` construct required by SwiftPM, this flag is recommended for Release
                // builds. See <https://github.com/swift-server/guides#building-for-production> for details.
                .unsafeFlags(["-cross-module-optimization"], .when(configuration: .release))
            ]
        )
    ]
)
