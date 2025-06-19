// recipient/static/recipient/js/donor-map.js

class DonorMap {
    constructor(options) {
        // Default options
        this.defaults = {
            mapElementId: 'donors-map',
            defaultLat: 40.7128,
            defaultLng: -74.0060,
            userLat: null,
            userLng: null,
            donorsData: [],
            apiKey: ''
        };

        // Merge options with defaults
        this.options = {...this.defaults, ...options};

        // Initialize
        this.map = null;
        this.userMarker = null;
        this.infoWindow = null;
        this.markers = [];
    }

    initMap() {
        console.log('Initializing Google Maps...');
        
        try {
            // Set center coordinates
            const centerLat = this.options.userLat || this.options.defaultLat;
            const centerLng = this.options.userLng || this.options.defaultLng;
            
            console.log('Map center coordinates:', centerLat, centerLng);
            
            // Check if map container exists
            const mapElement = document.getElementById(this.options.mapElementId);
            if (!mapElement) {
                console.error(`Map container #${this.options.mapElementId} not found in DOM`);
                this.showMapError('Map container not found');
                return;
            }
            
            // Initialize the map
            this.map = new google.maps.Map(mapElement, {
                center: { lat: centerLat, lng: centerLng },
                zoom: 12,
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true,
                styles: [
                    {
                        featureType: 'poi',
                        elementType: 'labels',
                        stylers: [{ visibility: 'off' }]
                    }
                ]
            });
            
            console.log('Map initialized successfully');
            
            // Initialize info window
            this.infoWindow = new google.maps.InfoWindow({
                maxWidth: 300
            });
            
            // Add user's location marker if coordinates are available
            if (this.options.userLat && this.options.userLng) {
                this.addUserMarker(this.options.userLat, this.options.userLng);
            }
            
            // Add markers for donors
            this.addDonorMarkers();
            
            // Set up other event listeners
            this.setupEventListeners();
            
        } catch (error) {
            console.error('Error initializing map:', error);
            this.showMapError('Failed to initialize map: ' + error.message);
        }
    }

    addUserMarker(lat, lng) {
        try {
            this.userMarker = new google.maps.Marker({
                position: { lat: lat, lng: lng },
                map: this.map,
                title: 'Your Location',
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 10,
                    fillColor: '#4285F4',
                    fillOpacity: 1,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 3
                },
                zIndex: 1000
            });
            
            // Add click listener for user marker
            this.userMarker.addListener('click', () => {
                this.infoWindow.setContent(`
                    <div class="map-info-window">
                        <h4>Your Location</h4>
                        <p>This is your current location</p>
                    </div>
                `);
                this.infoWindow.open(this.map, this.userMarker);
            });
            
            console.log('User marker added successfully');
        } catch (error) {
            console.error('Error adding user marker:', error);
        }
    }

    addDonorMarkers() {
        console.log('Adding donor markers...');
        
        try {
            // Clear existing markers
            this.clearMarkers();
            
            // Create bounds to fit all markers
            const bounds = new google.maps.LatLngBounds();
            if (this.userMarker) {
                bounds.extend(this.userMarker.getPosition());
            }
            
            console.log('Found', this.options.donorsData.length, 'donors to display');
            
            if (this.options.donorsData.length === 0) {
                console.warn('No donor data available');
                this.showNoDataMessage();
                return;
            }
            
            // Process each donor
            this.options.donorsData.forEach((donor, index) => {
                try {
                    // Validate coordinates
                    if (isNaN(donor.lat) || isNaN(donor.lng)) {
                        console.error('Invalid coordinates for donor:', donor.title, donor.lat, donor.lng);
                        return;
                    }
                    
                    // Create marker
                    const marker = new google.maps.Marker({
                        position: { lat: donor.lat, lng: donor.lng },
                        map: this.map,
                        title: donor.title,
                        icon: {
                            url: 'https://maps.google.com/mapfiles/ms/icons/green-dot.png',
                            scaledSize: new google.maps.Size(32, 32)
                        },
                        animation: google.maps.Animation.DROP,
                        zIndex: 100 + index
                    });
                    
                    this.markers.push(marker);
                    bounds.extend(marker.getPosition());
                    
                    // Create info window content
                    const contentString = this.createInfoWindowContent(donor);
                    
                    // Add click listener
                    marker.addListener('click', () => {
                        // Close any open info windows
                        this.infoWindow.close();
                        
                        // Set content and open
                        this.infoWindow.setContent(contentString);
                        this.infoWindow.open(this.map, marker);
                        
                        // Optional: Center map on clicked marker
                        this.map.panTo(marker.getPosition());
                    });
                    
                    // Add hover effects
                    marker.addListener('mouseover', () => {
                        marker.setIcon({
                            url: 'https://maps.google.com/mapfiles/ms/icons/yellow-dot.png',
                            scaledSize: new google.maps.Size(35, 35)
                        });
                    });
                    
                    marker.addListener('mouseout', () => {
                        marker.setIcon({
                            url: 'https://maps.google.com/mapfiles/ms/icons/green-dot.png',
                            scaledSize: new google.maps.Size(32, 32)
                        });
                    });
                    
                } catch (error) {
                    console.error('Error creating marker for donor:', donor.title, error);
                }
            });
            
            // Fit map to show all markers
            if (this.markers.length > 0) {
                this.map.fitBounds(bounds);
                
                // Prevent zooming in too far if markers are close together
                google.maps.event.addListenerOnce(this.map, 'bounds_changed', function() {
                    const zoom = this.getZoom();
                    if (zoom > 15) {
                        this.setZoom(15);
                    }
                });
            }
            
            console.log('Successfully added', this.markers.length, 'donor markers');
            
        } catch (error) {
            console.error('Error adding donor markers:', error);
            this.showMapError('Failed to load donor locations');
        }
    }

    createInfoWindowContent(donor) {
        let content = `
            <div class="map-info-window">
                <h4>${donor.title}</h4>
                <p><i class="fas fa-map-marker-alt"></i> ${donor.address}</p>
        `;
        
        if (donor.distance > 0) {
            content += `<p><i class="fas fa-route"></i> <strong>${donor.distance} miles away</strong></p>`;
        }
        
        if (donor.phone) {
            content += `<p><i class="fas fa-phone"></i> <a href="tel:${donor.phone}">${donor.phone}</a></p>`;
        }
        
        if (donor.pickupInstructions) {
            content += `<p><i class="fas fa-info-circle"></i> <strong>Pickup:</strong> ${donor.pickupInstructions}</p>`;
        }
        
        content += `
                <div style="margin-top: 10px;">
                    <a href="${donor.browseUrl}" class="btn-custom-sm" style="display: inline-block; padding: 5px 10px; background: var(--primary, #007bff); color: white; text-decoration: none; border-radius: 4px; font-size: 0.85rem;">
                        <i class="fas fa-shopping-basket"></i> View Donations
                    </a>
                </div>
            </div>
        `;
        
        return content;
    }

    clearMarkers() {
        this.markers.forEach(marker => {
            marker.setMap(null);
        });
        this.markers = [];
    }

    showMapError(message) {
        const mapElement = document.getElementById(this.options.mapElementId);
        if (mapElement) {
            mapElement.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 400px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px;">
                    <div style="text-align: center; color: #6c757d;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <h4>Map Error</h4>
                        <p>${message}</p>
                        <button onclick="location.reload()" class="btn-custom-sm">Reload Page</button>
                    </div>
                </div>
            `;
        }
    }

    showNoDataMessage() {
        const mapElement = document.getElementById(this.options.mapElementId);
        if (mapElement && (!this.map || this.markers.length === 0)) {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(255, 255, 255, 0.9);
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                z-index: 1000;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            `;
            overlay.innerHTML = `
                <i class="fas fa-map-marker-alt" style="font-size: 2rem; color: #6c757d; margin-bottom: 10px;"></i>
                <h4 style="margin: 0 0 5px 0; color: #333;">No Food Donors Found</h4>
                <p style="margin: 0; color: #666;">No food donors available in your area</p>
            `;
            mapElement.style.position = 'relative';
            mapElement.appendChild(overlay);
        }
    }

    setupEventListeners() {
        // Locate me button
        const locateMeBtn = document.getElementById('locate-me-btn');
        const locateMeBtn2 = document.getElementById('locate-me');
        
        if (locateMeBtn) {
            locateMeBtn.addEventListener('click', (e) => this.handleLocateMe(e));
        }
        if (locateMeBtn2) {
            locateMeBtn2.addEventListener('click', (e) => this.handleLocateMe(e));
        }
        
        // Refresh buttons
        const refreshBtn = document.getElementById('refresh-map-btn');
        const refreshBtn2 = document.getElementById('refresh-map');
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', (e) => this.handleRefresh(e));
        }
        if (refreshBtn2) {
            refreshBtn2.addEventListener('click', (e) => this.handleRefresh(e));
        }
    }

    handleLocateMe(event) {
        console.log('Attempting to get user location...');
        
        if (!navigator.geolocation) {
            alert('Error: Your browser doesn\'t support geolocation.');
            return;
        }
        
        // Show loading state
        const btn = event.target.closest('button');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Locating...';
        btn.disabled = true;
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                console.log('Location found:', position.coords.latitude, position.coords.longitude);
                
                const pos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                // Update user marker position
                if (this.userMarker) {
                    this.userMarker.setPosition(pos);
                } else {
                    // Create user marker if it doesn't exist
                    this.addUserMarker(pos.lat, pos.lng);
                }
                
                // Center map on user location
                if (this.map) {
                    this.map.setCenter(pos);
                    this.map.setZoom(14);
                }
                
                // Reset button
                btn.innerHTML = originalText;
                btn.disabled = false;
            },
            (error) => {
                console.error('Geolocation error:', error);
                
                let errorMessage = 'Error: Could not get your location.';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Error: Location access was denied. Please enable location permissions.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Error: Location information is unavailable.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Error: The request to get location timed out.';
                        break;
                }
                
                alert(errorMessage);
                
                // Reset button
                btn.innerHTML = originalText;
                btn.disabled = false;
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000 // 5 minutes
            }
        );
    }

    handleRefresh(event) {
        if (confirm('This will reload the map data. Continue?')) {
            console.log('Refreshing map...');
            
            // Show loading state
            const btn = event.target.closest('button');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            btn.disabled = true;
            
            // Reload the page or re-fetch data
            setTimeout(() => {
                window.location.reload();
            }, 500);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the map after Google Maps API is loaded
    window.initMap = function() {
        const donorMap = new DonorMap({
            userLat: window.userLat || null,
            userLng: window.userLng || null,
            donorsData: window.donorsData || [],
            apiKey: window.googleMapsApiKey || ''
        });
        donorMap.initMap();
    };
    
    // Fallback: Show error if map doesn't load within 10 seconds
    setTimeout(() => {
        if (typeof google === 'undefined') {
            console.error('Google Maps API failed to load');
            document.getElementById('donors-map').innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 400px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px;">
                    <div style="text-align: center; color: #6c757d;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <h4>Map Error</h4>
                        <p>Failed to load Google Maps. Please check your internet connection.</p>
                        <button onclick="location.reload()" class="btn-custom-sm">Reload Page</button>
                    </div>
                </div>
            `;
        }
    }, 10000);
});