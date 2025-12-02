"""
Airport code to city name lookup
Common IATA codes for major airports
"""

# Dictionary of IATA airport codes to city/airport names
# Focus on major European and world airports
AIRPORTS = {
    # UK
    'LHR': 'London Heathrow',
    'LGW': 'London Gatwick',
    'STN': 'London Stansted',
    'LTN': 'London Luton',
    'LCY': 'London City',
    'SEN': 'Southend',
    'MAN': 'Manchester',
    'BHX': 'Birmingham',
    'EDI': 'Edinburgh',
    'GLA': 'Glasgow',
    'BRS': 'Bristol',
    'LPL': 'Liverpool',
    'NCL': 'Newcastle',
    'EMA': 'East Midlands',
    'LBA': 'Leeds Bradford',
    'ABZ': 'Aberdeen',
    'BFS': 'Belfast',
    'BHD': 'Belfast City',
    'CWL': 'Cardiff',
    'EXT': 'Exeter',
    'SOU': 'Southampton',
    'NWI': 'Norwich',
    'INV': 'Inverness',
    'JER': 'Jersey',
    'GCI': 'Guernsey',
    'IOM': 'Isle of Man',

    # Ireland
    'DUB': 'Dublin',
    'SNN': 'Shannon',
    'ORK': 'Cork',
    'KIR': 'Kerry',

    # France
    'CDG': 'Paris CDG',
    'ORY': 'Paris Orly',
    'NCE': 'Nice',
    'LYS': 'Lyon',
    'MRS': 'Marseille',
    'TLS': 'Toulouse',
    'BOD': 'Bordeaux',
    'NTE': 'Nantes',
    'SXB': 'Strasbourg',

    # Germany
    'FRA': 'Frankfurt',
    'MUC': 'Munich',
    'DUS': 'Dusseldorf',
    'TXL': 'Berlin Tegel',
    'BER': 'Berlin',
    'HAM': 'Hamburg',
    'CGN': 'Cologne',
    'STR': 'Stuttgart',
    'HAJ': 'Hanover',
    'NUE': 'Nuremberg',
    'LEJ': 'Leipzig',
    'DRS': 'Dresden',

    # Netherlands
    'AMS': 'Amsterdam',
    'RTM': 'Rotterdam',
    'EIN': 'Eindhoven',

    # Belgium
    'BRU': 'Brussels',
    'CRL': 'Charleroi',
    'ANR': 'Antwerp',

    # Spain
    'MAD': 'Madrid',
    'BCN': 'Barcelona',
    'PMI': 'Palma',
    'AGP': 'Malaga',
    'ALC': 'Alicante',
    'VLC': 'Valencia',
    'SVQ': 'Seville',
    'BIO': 'Bilbao',
    'TFS': 'Tenerife South',
    'TFN': 'Tenerife North',
    'LPA': 'Gran Canaria',
    'ACE': 'Lanzarote',
    'FUE': 'Fuerteventura',
    'IBZ': 'Ibiza',
    'MAH': 'Menorca',

    # Portugal
    'LIS': 'Lisbon',
    'OPO': 'Porto',
    'FAO': 'Faro',
    'FNC': 'Madeira',

    # Italy
    'FCO': 'Rome Fiumicino',
    'CIA': 'Rome Ciampino',
    'MXP': 'Milan Malpensa',
    'LIN': 'Milan Linate',
    'BGY': 'Milan Bergamo',
    'VCE': 'Venice',
    'NAP': 'Naples',
    'BLQ': 'Bologna',
    'FLR': 'Florence',
    'PSA': 'Pisa',
    'TRN': 'Turin',
    'CTA': 'Catania',
    'PMO': 'Palermo',

    # Switzerland
    'ZRH': 'Zurich',
    'GVA': 'Geneva',
    'BSL': 'Basel',

    # Austria
    'VIE': 'Vienna',
    'SZG': 'Salzburg',
    'INN': 'Innsbruck',

    # Scandinavia
    'CPH': 'Copenhagen',
    'ARN': 'Stockholm',
    'GOT': 'Gothenburg',
    'OSL': 'Oslo',
    'BGO': 'Bergen',
    'TRD': 'Trondheim',
    'HEL': 'Helsinki',
    'RVN': 'Rovaniemi',
    'KEF': 'Reykjavik',

    # Eastern Europe
    'PRG': 'Prague',
    'WAW': 'Warsaw',
    'KRK': 'Krakow',
    'BUD': 'Budapest',
    'OTP': 'Bucharest',
    'SOF': 'Sofia',
    'ZAG': 'Zagreb',
    'LJU': 'Ljubljana',
    'BEG': 'Belgrade',

    # Greece & Cyprus
    'ATH': 'Athens',
    'SKG': 'Thessaloniki',
    'HER': 'Heraklion',
    'RHO': 'Rhodes',
    'CFU': 'Corfu',
    'JMK': 'Mykonos',
    'JTR': 'Santorini',
    'LCA': 'Larnaca',
    'PFO': 'Paphos',

    # Turkey
    'IST': 'Istanbul',
    'SAW': 'Istanbul Sabiha',
    'ESB': 'Ankara',
    'AYT': 'Antalya',
    'ADB': 'Izmir',
    'DLM': 'Dalaman',
    'BJV': 'Bodrum',

    # Middle East
    'DXB': 'Dubai',
    'AUH': 'Abu Dhabi',
    'DOH': 'Doha',
    'BAH': 'Bahrain',
    'KWI': 'Kuwait',
    'MCT': 'Muscat',
    'AMM': 'Amman',
    'BEY': 'Beirut',
    'TLV': 'Tel Aviv',
    'RUH': 'Riyadh',
    'JED': 'Jeddah',

    # North America
    'JFK': 'New York JFK',
    'EWR': 'Newark',
    'LGA': 'New York LaGuardia',
    'LAX': 'Los Angeles',
    'SFO': 'San Francisco',
    'ORD': 'Chicago',
    'ATL': 'Atlanta',
    'DFW': 'Dallas',
    'DEN': 'Denver',
    'SEA': 'Seattle',
    'MIA': 'Miami',
    'BOS': 'Boston',
    'IAD': 'Washington Dulles',
    'DCA': 'Washington Reagan',
    'PHX': 'Phoenix',
    'IAH': 'Houston',
    'LAS': 'Las Vegas',
    'MSP': 'Minneapolis',
    'DTW': 'Detroit',
    'PHL': 'Philadelphia',
    'CLT': 'Charlotte',
    'YYZ': 'Toronto',
    'YVR': 'Vancouver',
    'YUL': 'Montreal',
    'YYC': 'Calgary',
    'MEX': 'Mexico City',
    'CUN': 'Cancun',

    # South America
    'GRU': 'Sao Paulo',
    'GIG': 'Rio de Janeiro',
    'EZE': 'Buenos Aires',
    'SCL': 'Santiago',
    'BOG': 'Bogota',
    'LIM': 'Lima',

    # Asia
    'HND': 'Tokyo Haneda',
    'NRT': 'Tokyo Narita',
    'PEK': 'Beijing',
    'PKX': 'Beijing Daxing',
    'PVG': 'Shanghai Pudong',
    'SHA': 'Shanghai Hongqiao',
    'HKG': 'Hong Kong',
    'ICN': 'Seoul Incheon',
    'SIN': 'Singapore',
    'BKK': 'Bangkok',
    'KUL': 'Kuala Lumpur',
    'CGK': 'Jakarta',
    'DEL': 'Delhi',
    'BOM': 'Mumbai',
    'MAA': 'Chennai',
    'BLR': 'Bangalore',
    'MNL': 'Manila',
    'TPE': 'Taipei',
    'HAN': 'Hanoi',
    'SGN': 'Ho Chi Minh',

    # Africa
    'JNB': 'Johannesburg',
    'CPT': 'Cape Town',
    'CAI': 'Cairo',
    'CMN': 'Casablanca',
    'ADD': 'Addis Ababa',
    'NBO': 'Nairobi',
    'LOS': 'Lagos',
    'ACC': 'Accra',

    # Oceania
    'SYD': 'Sydney',
    'MEL': 'Melbourne',
    'BNE': 'Brisbane',
    'PER': 'Perth',
    'AKL': 'Auckland',
    'WLG': 'Wellington',
    'CHC': 'Christchurch',
}


def get_airport_city(code: str) -> str:
    """
    Get the city/airport name for an IATA airport code.
    Returns the original code if not found.
    """
    if not code or code == '???':
        return ''
    return AIRPORTS.get(code.upper(), '')


def get_airport_display(code: str) -> tuple[str, str]:
    """
    Get both the code and city name for display.
    Returns (code, city_name) tuple.
    City name will be empty string if not found.
    """
    city = get_airport_city(code)
    return (code, city)
