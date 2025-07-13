#!/usr/bin/env swift

import Foundation
import CoreLocation

// Simple test to check if CoreLocation is accessible
let manager = CLLocationManager()
print("Authorization status: \(manager.authorizationStatus.rawValue)")

switch manager.authorizationStatus {
case .notDetermined:
    print("Permission not determined - would need to request")
case .denied:
    print("Permission denied")
case .restricted:
    print("Permission restricted")
case .authorizedWhenInUse:
    print("Permission granted (when in use)")
case .authorizedAlways:
    print("Permission granted (always)")
@unknown default:
    print("Unknown status")
}

print("Location services enabled: \(CLLocationManager.locationServicesEnabled())")
print("Test completed")