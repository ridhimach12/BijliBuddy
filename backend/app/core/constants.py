"""Domain constants: Delhi localities, service categories, Indian phone validation, safety rules."""

import re
from typing import Dict, List, TypedDict


class LocalityInfo(TypedDict):
    name: str
    zone: str
    latitude: float
    longitude: float
    pincode: str


DELHI_LOCALITIES: List[LocalityInfo] = [
    {"name": "Connaught Place", "zone": "Central Delhi", "latitude": 28.6315, "longitude": 77.2167, "pincode": "110001"},
    {"name": "Karol Bagh", "zone": "Central Delhi", "latitude": 28.6514, "longitude": 77.1907, "pincode": "110005"},
    {"name": "Saket", "zone": "South Delhi", "latitude": 28.5245, "longitude": 77.2066, "pincode": "110017"},
    {"name": "Hauz Khas", "zone": "South Delhi", "latitude": 28.5494, "longitude": 77.2001, "pincode": "110016"},
    {"name": "Lajpat Nagar", "zone": "South Delhi", "latitude": 28.5677, "longitude": 77.2433, "pincode": "110024"},
    {"name": "Greater Kailash", "zone": "South Delhi", "latitude": 28.5482, "longitude": 77.2348, "pincode": "110048"},
    {"name": "Malviya Nagar", "zone": "South Delhi", "latitude": 28.5298, "longitude": 77.2102, "pincode": "110017"},
    {"name": "Vasant Kunj", "zone": "South Delhi", "latitude": 28.5293, "longitude": 77.1520, "pincode": "110070"},
    {"name": "Dwarka", "zone": "Dwarka/NCR", "latitude": 28.5921, "longitude": 77.0460, "pincode": "110075"},
    {"name": "Janakpuri", "zone": "West Delhi", "latitude": 28.6219, "longitude": 77.0878, "pincode": "110058"},
    {"name": "Rajouri Garden", "zone": "West Delhi", "latitude": 28.6423, "longitude": 77.1160, "pincode": "110027"},
    {"name": "Rohini", "zone": "North Delhi", "latitude": 28.7041, "longitude": 77.1025, "pincode": "110085"},
    {"name": "Pitampura", "zone": "North Delhi", "latitude": 28.6980, "longitude": 77.1310, "pincode": "110034"},
    {"name": "Civil Lines", "zone": "North Delhi", "latitude": 28.6768, "longitude": 77.2248, "pincode": "110054"},
    {"name": "Mayur Vihar", "zone": "East Delhi", "latitude": 28.6095, "longitude": 77.2940, "pincode": "110091"},
    {"name": "Preet Vihar", "zone": "East Delhi", "latitude": 28.6388, "longitude": 77.2945, "pincode": "110092"},
]

LOCALITY_MAP: Dict[str, LocalityInfo] = {item["name"]: item for item in DELHI_LOCALITIES}

SERVICE_CATEGORIES_CONFIG = [
    {
        "name": "Wiring",
        "slug": "wiring",
        "description": "Internal house wiring, short-circuit fault tracing, earthing, concealed cable laying, and rewiring.",
        "base_price_inr": 450,
        "estimated_duration_mins": 75,
        "safety_level": "high",
        "icon_name": "Cable",
        "suggested_service_type": "Electrical Wiring Inspection & Fault Tracing",
    },
    {
        "name": "Switchboard",
        "slug": "switchboard",
        "description": "Modular switch/socket replacement, regulator repair, burnt switchboard replacement, and power sockets.",
        "base_price_inr": 250,
        "estimated_duration_mins": 40,
        "safety_level": "medium",
        "icon_name": "ToggleRight",
        "suggested_service_type": "Switchboard & Socket Repair / Replacement",
    },
    {
        "name": "Fan installation/repair",
        "slug": "fan-installation-repair",
        "description": "Ceiling, exhaust, and wall fan installation, capacitor replacement, wobbling, and humming repair.",
        "base_price_inr": 300,
        "estimated_duration_mins": 45,
        "safety_level": "low",
        "icon_name": "Fan",
        "suggested_service_type": "Ceiling / Exhaust Fan Servicing & Mounting",
    },
    {
        "name": "Lighting",
        "slug": "lighting",
        "description": "LED tube lights, panel lights, chandelier mounting, false-ceiling fixtures, and balcony lighting.",
        "base_price_inr": 220,
        "estimated_duration_mins": 35,
        "safety_level": "low",
        "icon_name": "Lightbulb",
        "suggested_service_type": "Indoor / Outdoor Light Fixture Installation & Repair",
    },
    {
        "name": "MCB/circuit breaker",
        "slug": "mcb-circuit-breaker",
        "description": "Frequent MCB tripping, RCCB/ELCB protection, distribution box upgrades, and phase load balancing.",
        "base_price_inr": 400,
        "estimated_duration_mins": 60,
        "safety_level": "high",
        "icon_name": "ShieldAlert",
        "suggested_service_type": "MCB / Distribution Board Diagnostics & Replacement",
    },
    {
        "name": "Inverter",
        "slug": "inverter",
        "description": "Home inverter & battery setup, changeover wiring, backup failure diagnosis, and fuse replacement.",
        "base_price_inr": 500,
        "estimated_duration_mins": 70,
        "safety_level": "high",
        "icon_name": "BatteryCharging",
        "suggested_service_type": "Inverter & Battery Backup Wiring Service",
    },
    {
        "name": "Electrical appliance connection",
        "slug": "electrical-appliance-connection",
        "description": "AC stabilizer/16A power point, geyser point, microwave/chimney socket, and heavy appliance wiring.",
        "base_price_inr": 350,
        "estimated_duration_mins": 50,
        "safety_level": "medium",
        "icon_name": "PlugZap",
        "suggested_service_type": "Heavy Appliance 16A/25A Dedicated Point Setup",
    },
    {
        "name": "General electrical maintenance",
        "slug": "general-electrical-maintenance",
        "description": "Home electrical safety audit, voltage fluctuation check, doorbell installation, and earthing testing.",
        "base_price_inr": 300,
        "estimated_duration_mins": 55,
        "safety_level": "medium",
        "icon_name": "Wrench",
        "suggested_service_type": "General Home Electrical Inspection & Maintenance",
    },
]

CATEGORY_NAMES: List[str] = [c["name"] for c in SERVICE_CATEGORIES_CONFIG]
CATEGORY_BY_NAME: Dict[str, dict] = {c["name"]: c for c in SERVICE_CATEGORIES_CONFIG}

INDIAN_PHONE_REGEX = re.compile(r"^(?:\+91[\-\s]?)?[6-9]\d{9}$")


def normalize_indian_phone(phone: str) -> str:
    """Validate and normalize an Indian mobile number to +91XXXXXXXXXX."""
    cleaned = re.sub(r"[\s\-]", "", phone.strip())
    if not INDIAN_PHONE_REGEX.match(cleaned):
        raise ValueError(
            "Invalid Indian mobile number. Expected 10 digits starting with 6-9 (optional +91 prefix)."
        )
    if cleaned.startswith("+91"):
        return cleaned
    if cleaned.startswith("91") and len(cleaned) == 12:
        return f"+{cleaned}"
    return f"+91{cleaned}"


EMERGENCY_HELPLINES = {
    "national_emergency": "112",
    "fire_service": "101",
    "bses_rajdhani": "19123",
    "bses_yamuna": "19122",
    "tata_power_ddl": "19124",
}

TIME_SLOTS = ["Morning (6AM-12PM)", "Afternoon (12PM-5PM)", "Evening (5PM-9PM)", "Night (9PM-6AM)"]
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
