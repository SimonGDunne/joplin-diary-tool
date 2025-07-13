import Foundation
import CoreLocation
import Cocoa

@main
class LocationApp: NSObject, NSApplicationDelegate, CLLocationManagerDelegate {
    private let locationManager = CLLocationManager()
    private let app = NSApplication.shared
    private var completion: ((String?) -> Void)?
    
    override init() {
        super.init()
        app.delegate = self
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyKilometer
    }
    
    static func main() {
        let app = LocationApp()
        app.run()
    }
    
    func run() {
        // Set up the app to run headless
        app.setActivationPolicy(.prohibited) // Don't show in dock
        
        getCurrentLocation { [weak self] result in
            if let location = result {
                print(location)
                exit(0)
            } else {
                fputs("Unable to determine location\n", stderr)
                exit(1)
            }
        }
        
        // Run the app with a timeout
        DispatchQueue.main.asyncAfter(deadline: .now() + 15) {
            fputs("Location request timed out\n", stderr)
            exit(1)
        }
        
        app.run()
    }
    
    func getCurrentLocation(completion: @escaping (String?) -> Void) {
        self.completion = completion
        
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
        let geocoder = CLGeocoder()
        geocoder.reverseGeocodeLocation(location) { [weak self] placemarks, error in
            if let error = error {
                // If reverse geocoding fails, provide coordinates
                let lat = String(format: "%.4f", location.coordinate.latitude)
                let lng = String(format: "%.4f", location.coordinate.longitude)
                self?.completion?("Coordinates: \(lat), \(lng)")
                return
            }
            
            guard let placemark = placemarks?.first else {
                self?.completion?(nil)
                return
            }
            
            // Build location string
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
    
    // MARK: - NSApplicationDelegate
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // App is ready
    }
}