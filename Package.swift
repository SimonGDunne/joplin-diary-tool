// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "JoplinLocationHelper",
    platforms: [
        .macOS(.v11)
    ],
    products: [
        .executable(name: "JoplinLocationHelper", targets: ["JoplinLocationHelper"])
    ],
    targets: [
        .executableTarget(
            name: "JoplinLocationHelper",
            dependencies: [],
            path: "Sources"
        )
    ]
)