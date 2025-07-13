#!/usr/bin/env swift

import Foundation
import CoreLocation

class LocationManager: NSObject, CLLocationManagerDelegate {
    private let locationManager = CLLocationManager()
    private let geocoder = CLGeocoder()
    private var completion: ((String?) -> Void)?
    
    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyKilometer // Lower accuracy for privacy/battery
    }
    
    func getCurrentLocation(completion: @escaping (String?) -> Void) {
        self.completion = completion
        
        // Check authorization status
        let authStatus = locationManager.authorizationStatus
        
        switch authStatus {
        case .notDetermined:
            locationManager.requestWhenInUseAuthorization()
        case .authorizedWhenInUse, .authorizedAlways:
            requestLocation()
        case .denied, .restricted:
            completion(nil)
        @unknown default:
            completion(nil)
        }
    }
    
    private func requestLocation() {
        locationManager.requestLocation()
    }
    
    // MARK: - CLLocationManagerDelegate
    
    func locationManager(_ manager: CLLocationManager, didChangeAuthorization status: CLAuthorizationStatus) {
        switch status {
        case .authorizedWhenInUse, .authorizedAlways:
            requestLocation()
        case .denied, .restricted:
            completion?(nil)
        default:
            break
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.first else {
            completion?(nil)
            return
        }
        
        // Reverse geocode to get human-readable location
        geocoder.reverseGeocodeLocation(location) { [weak self] placemarks, error in
            if let error = error {
                // If reverse geocoding fails, fall back to coordinates
                let lat = String(format: "%.4f", location.coordinate.latitude)
                let lng = String(format: "%.4f", location.coordinate.longitude)
                self?.completion?("Coordinates: \(lat), \(lng)")
                return
            }
            
            guard let placemark = placemarks?.first else {
                self?.completion?(nil)
                return
            }
            
            // Try to build a meaningful location string
            var locationComponents: [String] = []
            
            // Add locality (town/city) - most important
            if let locality = placemark.locality {
                locationComponents.append(locality)
            }
            
            // Add subLocality if available (neighborhood/area)
            if let subLocality = placemark.subLocality {
                locationComponents.append(subLocality)
            }
            
            // Add administrative area (county/state) if we don't have locality
            if locationComponents.isEmpty, let adminArea = placemark.administrativeArea {
                locationComponents.append(adminArea)
            }
            
            let locationString = locationComponents.joined(separator: ", ")
            self?.completion?(locationString.isEmpty ? nil : locationString)
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        completion?(nil)
    }
}

// Main execution
let locationManager = LocationManager()
let semaphore = DispatchSemaphore(value: 0)
var result: String?

locationManager.getCurrentLocation { location in
    result = location
    semaphore.signal()
}

// Wait for location with timeout
let timeoutResult = semaphore.wait(timeout: .now() + 10)

if timeoutResult == .timedOut {
    print("Location request timed out", to: &standardError)
    exit(1)
}

if let location = result {
    print(location)
    exit(0)
} else {
    print("Unable to determine location", to: &standardError)
    exit(1)
}

// Helper for stderr output
var standardError = FileHandle.standardError

extension FileHandle: TextOutputStream {
    public func write(_ string: String) {
        let data = Data(string.utf8)
        self.write(data)
    }
}