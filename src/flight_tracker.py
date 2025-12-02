"""
Lightweight FlightRadar24 API Client for tracking overhead flights
No external dependencies beyond requests
"""

import math
import requests
from dataclasses import dataclass
from typing import Optional


@dataclass
class FlightInfo:
    """Information about a tracked flight"""
    flight_number: str
    callsign: str
    aircraft_type: str
    airline: str
    origin: str
    destination: str
    altitude_ft: int
    ground_speed_kts: int
    heading: int
    latitude: float
    longitude: float
    vertical_speed: int  # feet per minute
    distance_km: float
    registration: str
    squawk: str


class FlightTracker:
    """Track flights using FlightRadar24 public data feed"""

    # FlightRadar24 data endpoint (public, no auth required)
    FR24_BASE_URL = "https://data-cloud.flightradar24.com/zones/fcgi/feed.js"

    def __init__(self, latitude: float, longitude: float, radius_km: float = 50):
        self.latitude = latitude
        self.longitude = longitude
        self.radius_km = radius_km
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
        })

    def _haversine_distance(self, lat1: float, lon1: float,
                            lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _calculate_bounds(self):
        """Calculate bounding box for flight search"""
        # Approximate degrees per km at this latitude
        km_per_degree_lat = 111.0
        km_per_degree_lon = 111.0 * math.cos(math.radians(self.latitude))

        delta_lat = self.radius_km / km_per_degree_lat
        delta_lon = self.radius_km / km_per_degree_lon

        return {
            'north': self.latitude + delta_lat,
            'south': self.latitude - delta_lat,
            'east': self.longitude + delta_lon,
            'west': self.longitude - delta_lon
        }

    def get_nearby_flights(self) -> list[FlightInfo]:
        """Get all flights within the configured radius"""
        bounds = self._calculate_bounds()

        params = {
            'bounds': f"{bounds['north']:.2f},{bounds['south']:.2f},{bounds['west']:.2f},{bounds['east']:.2f}",
            'faa': '1',
            'satellite': '1',
            'mlat': '1',
            'flarm': '1',
            'adsb': '1',
            'gnd': '0',  # Exclude ground vehicles
            'air': '1',
            'vehicles': '0',
            'estimated': '1',
            'gliders': '1',
            'stats': '0',
        }

        try:
            response = self.session.get(self.FR24_BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Error fetching flights: {e}")
            return []
        except ValueError as e:
            print(f"Error parsing flight data: {e}")
            return []

        nearby_flights = []

        for key, value in data.items():
            # Skip metadata keys
            if not isinstance(value, list) or len(value) < 14:
                continue

            try:
                # FR24 data format:
                # [0]: ICAO 24-bit address
                # [1]: latitude
                # [2]: longitude
                # [3]: heading
                # [4]: altitude (feet)
                # [5]: ground speed (knots)
                # [6]: squawk
                # [7]: radar
                # [8]: aircraft type
                # [9]: registration
                # [10]: timestamp
                # [11]: origin airport
                # [12]: destination airport
                # [13]: flight number/callsign
                # [14]: unknown
                # [15]: vertical speed
                # [16]: callsign
                # [17]: unknown
                # [18]: airline

                lat = float(value[1]) if value[1] else 0
                lon = float(value[2]) if value[2] else 0

                if lat == 0 and lon == 0:
                    continue

                distance = self._haversine_distance(
                    self.latitude, self.longitude, lat, lon
                )

                # Only include flights within radius
                if distance > self.radius_km:
                    continue

                # Extract flight info with safe defaults
                flight_number = str(value[13]) if len(value) > 13 and value[13] else ''
                callsign = str(value[16]) if len(value) > 16 and value[16] else flight_number
                aircraft_type = str(value[8]) if len(value) > 8 and value[8] else 'Unknown'
                airline = str(value[18]) if len(value) > 18 and value[18] else ''
                origin = str(value[11]) if len(value) > 11 and value[11] else '???'
                destination = str(value[12]) if len(value) > 12 and value[12] else '???'
                altitude = int(value[4]) if len(value) > 4 and value[4] else 0
                speed = int(value[5]) if len(value) > 5 and value[5] else 0
                heading = int(value[3]) if len(value) > 3 and value[3] else 0
                vertical_speed = int(value[15]) if len(value) > 15 and value[15] else 0
                registration = str(value[9]) if len(value) > 9 and value[9] else ''
                squawk = str(value[6]) if len(value) > 6 and value[6] else ''

                # Use callsign as flight number if empty
                if not flight_number:
                    flight_number = callsign or 'Unknown'

                flight_info = FlightInfo(
                    flight_number=flight_number,
                    callsign=callsign,
                    aircraft_type=aircraft_type,
                    airline=airline,
                    origin=origin,
                    destination=destination,
                    altitude_ft=altitude,
                    ground_speed_kts=speed,
                    heading=heading,
                    latitude=lat,
                    longitude=lon,
                    vertical_speed=vertical_speed,
                    distance_km=round(distance, 1),
                    registration=registration,
                    squawk=squawk
                )
                nearby_flights.append(flight_info)

            except (IndexError, TypeError, ValueError) as e:
                # Skip malformed entries
                continue

        # Sort by distance (closest first)
        nearby_flights.sort(key=lambda f: f.distance_km)
        return nearby_flights

    def get_closest_flight(self) -> Optional[FlightInfo]:
        """Get the closest flight to our position"""
        flights = self.get_nearby_flights()
        return flights[0] if flights else None

    def update_location(self, latitude: float, longitude: float):
        """Update the tracking location"""
        self.latitude = latitude
        self.longitude = longitude

    def update_radius(self, radius_km: float):
        """Update the search radius"""
        self.radius_km = radius_km
