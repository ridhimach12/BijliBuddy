"""Explicitly labeled synthetic starter dataset generators for issue classification and pricing.

IMPORTANT TRANSPARENCY NOTE:
All datasets generated here are synthetic starter datasets created for hackathon MVP training
and evaluation. They do NOT represent historical real-world customer records.
"""

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from app.core.constants import CATEGORY_NAMES

SYNTHETIC_DATASET_NOTICE = (
    "Synthetic starter dataset generated for BijliBuddy MVP demonstration and evaluation. "
    "Not real customer production data."
)

# Diverse Indian household electrical issue templates per category (8 categories)
ISSUE_TEMPLATES: Dict[str, List[str]] = {
    "Wiring": [
        "Concealed wall wiring is giving mild shock near bathroom",
        "Need internal rewiring for old copper cables in bedroom",
        "Short circuit occurred in hallway wiring and line is dead",
        "Exposed wire hanging outside balcony wall needs insulation",
        "Wire burnt inside wall conduit in kitchen area",
        "Need new concealed cable laying for study room wall",
        "Neutral wire loose causing voltage fluctuation in two rooms",
        "Rats chewed electrical wire behind wardrobe needs rewiring",
        "Earthing wire disconnected causing tingling on metal taps",
        "Living room main phase wire burnt near junction box",
        "Need fresh 2.5 sq mm copper wiring run to balcony",
        "Bedroom wall socket has no phase continuity in internal cable",
        "Old aluminium wiring sparking near wooden ceiling",
        "Loose phase wire inside junction box flickering power",
        "Need earthing pit check and new green earth wire connection",
        "Kitchen underground cable fault tripping power supply",
        "Exposed live wire sticking out of plaster after drilling",
        "Split cable joint inside roof conduit overheating",
    ],
    "Switchboard": [
        "Bedroom modular switchboard sparking when turning on switch",
        "Two plug sockets melted on living room switchboard",
        "Fan regulator knob stuck and smoking inside switch plate",
        "Need new 6-module switchboard installed near study desk",
        "Switch button broken and loose connection inside board",
        "Power socket burnt while using iron on bedroom board",
        "Switchboard making crackling sound whenever plug inserted",
        "Replace cracked 4-switch modular plate in guest room",
        "Socket pins loose plug keeps falling out of wall board",
        "Bathroom switchboard got damp and switch is jammed",
        "Kitchen switchboard one 6A switch not working",
        "Need 16A combined switch and socket installed on board",
        "Burnt smell coming from bedside switchboard panel",
        "Indicator neon light dead and switch stuck on board",
        "Replace old bakelite switchboard with modern modular board",
        "Loose backbox of wall switchboard hanging out of wall",
        "Switch sparks faintly every time pressed in dining room",
        "Regulator step dimmer not controlling speed on switchboard",
    ],
    "Fan installation/repair": [
        "Ceiling fan running very slowly needs capacitor replacement",
        "Install two new ceiling fans in master and kids bedroom",
        "Living room ceiling fan making loud humming noise and wobbling",
        "Kitchen exhaust fan stopped spinning completely",
        "Ceiling fan suddenly stopped working after voltage spike",
        "Mount a new wall fan in balcony and connect wire",
        "Ceiling fan bearing making grinding metallic sound",
        "Pedestal fan wiring cut and motor not starting",
        "Ceiling fan blades bent and shaking violently on high speed",
        "Need replacement of burnt ceiling fan condenser and check",
        "Bathroom exhaust fan jammed and emitting slight smell",
        "Uninstall old ceiling fan and fit new BLDC remote fan",
        "Ceiling fan speed does not change even on level five",
        "Fan downrod loose and vibrating dangerously on ceiling hook",
        "Install heavy duty exhaust fan in utility kitchen window",
        "Ceiling fan rotating backwards or sluggishly after repair",
        "Wall mounted fan oscillation stuck and power cord damaged",
        "Check ceiling fan motor coil and replace faulty regulator",
    ],
    "Lighting": [
        "LED tube light flickering continuously in study room",
        "Install three false ceiling LED panel lights in hall",
        "Mount dining room chandelier and connect dimmer wiring",
        "Balcony waterproof outdoor wall light not turning on",
        "Tube light driver burnt and fixture needs replacement",
        "Install mirror vanity light and LED strip in bathroom",
        "Staircase corridor light switch works intermittently",
        "False ceiling cove strip light half section dead",
        "Replace four old fluorescent tube fittings with LED battens",
        "Bedroom night lamp fixture holder melted near bulb",
        "Garden gate pillar lights stopped glowing after rain",
        "Install pendant hanging lamps above dining table",
        "LED downlight driver buzzing and blinking rapidly",
        "Kitchen under-cabinet LED strip power adapter failed",
        "Porch motion sensor floodlight not triggering at night",
        "Drawing room decorative wall sconce fitting required",
        "Bulb holder short circuited and tripped room light",
        "Replace recessed spotlight drivers in POP false ceiling",
    ],
    "MCB/circuit breaker": [
        "Main MCB trips repeatedly every ten minutes under load",
        "RCCB breaker tripping whenever water motor starts",
        "Distribution box MCB burnt and refuses to stay up",
        "Sub-meter circuit breaker smoking near main entrance",
        "Need new 32A double pole MCB installed in DB box",
        "ELCB keeps tripping randomly during afternoon hours",
        "AC room MCB heats up and trips after five minutes",
        "Upgrade old fuse cutout box to modern MCB distribution box",
        "Single phase isolator switch jammed inside main panel",
        "Main circuit breaker sparking inside metal DB enclosure",
        "Phase load unbalanced causing main breaker frequent tripping",
        "Install surge protection device and MCB in main panel",
        "Kitchen 16A MCB trips as soon as microwave turns on",
        "Broken toggle lever on 10A lighting MCB in DB board",
        "Changeover breaker inside distribution panel loose",
        "Main distribution board humming loudly before breaker trips",
        "Install separate dedicated MCB for bathroom geyser line",
        "Circuit breaker tripping instantly with loud pop noise",
    ],
    "Inverter": [
        "Inverter not charging battery during normal mains power",
        "Need fresh inverter and tubular battery wiring for 3BHK",
        "Home inverter beeping continuously with overload red light",
        "Backup power fails immediately during power cut",
        "Inverter changeover delay causes WiFi and PC to restart",
        "Battery terminal corroded and inverter wire heating up",
        "Inverter fuse blown after thunderstorm power fluctuation",
        "Connect dining room fan and two lights to inverter backup line",
        "Inverter fan making loud rattling sound inside unit",
        "Disconnect geyser and AC sockets from inverter output wiring",
        "Inverter showing low battery despite full day electricity",
        "Install double battery 24V inverter setup in utility area",
        "Inverter output socket dead while mains bypass still works",
        "Smell near inverter battery leads during backup discharge",
        "Rewire inverter phase distribution across hall and bedrooms",
        "Pure sine wave inverter tripping on single ceiling fan load",
        "Check distilled water terminals and DC fuse on inverter",
        "Need manual bypass switch installed next to inverter unit",
    ],
    "Electrical appliance connection": [
        "Install dedicated 16A AC power point with starter switch",
        "Bathroom storage geyser power socket melted needs 16A plug",
        "Microwave oven 16A socket sparking in modular kitchen",
        "Connect voltage stabilizer and split AC outdoor power cable",
        "Washing machine balcony point needs waterproof 16A socket",
        "Induction cooktop tripping socket needs heavy duty 20A point",
        "Kitchen chimney plug point installation behind upper cabinet",
        "Dishwasher power connection and proper earthing check needed",
        "Refrigerator plug socket loose and refrigerator restarting",
        "Install 25A metal clad socket for 2-ton split air conditioner",
        "Water purifier RO power socket installation near sink",
        "OTGs and mixer heavy socket burning out in kitchen",
        "Submersible water pump starter panel wiring connection",
        "Room heater 16A plug top and wall socket fused together",
        "Install smart WiFi plug module for geyser line",
        "Treadmill 16A dedicated line wiring in home gym corner",
        "TV unit concealed HDMI and multi-plug power socket setup",
        "Air cooler pump plug shorting out socket on terrace",
    ],
    "General electrical maintenance": [
        "Complete home electrical safety audit for rented flat",
        "Frequent voltage fluctuation across entire apartment",
        "Install wireless or wired electric doorbell at main door",
        "Earth leakage test needed before moving into new house",
        "Check high electricity bill and inspect faulty meter load",
        "Minor sparks and loose connections check across all rooms",
        "Pre-monsoon electrical inspection for terrace and balcony",
        "Install digital voltage and ampere meter on main board",
        "Whole flat neutral voltage showing 30V on tester check",
        "Annual electrical maintenance checkup of DB and sockets",
        "Doorbell chime buzzing continuously without anyone pressing",
        "Inspect flickering lights across hall and bedrooms together",
        "Check appliance earthing across kitchen and bathroom points",
        "Post-renovation full electrical testing and load balancing",
        "Main incoming supply phase missing in half of the house",
        "Testing wall sockets polarity and earthing continuity",
        "General troubleshooting for intermittent power drop in flat",
        "Scheduled electrical safety checkup for senior citizens home",
    ],
}

ROOMS_AND_PREFIXES = [
    "",
    "In our flat, ",
    "Urgent help needed: ",
    "Since morning, ",
    "At our Delhi residence, ",
    "Please inspect: ",
]

ROOMS_AND_SUFFIXES = [
    "",
    " in the apartment.",
    " Please send a qualified technician.",
    " Need repair today.",
    " Happened after power fluctuation.",
]


def generate_synthetic_issue_dataset(seed: int = 42) -> pd.DataFrame:
    """Generate explicitly labeled synthetic starter dataset for TF-IDF + LogisticRegression."""
    rng = np.random.default_rng(seed)
    rows: List[dict] = []

    for category in CATEGORY_NAMES:
        templates = ISSUE_TEMPLATES[category]
        for idx, base_text in enumerate(templates):
            template_id = f"{category}::{idx}"
            # Base template + 2 natural variations = 54 samples per category -> 432 total
            rows.append(
                {
                    "template_id": template_id,
                    "description": base_text,
                    "category": category,
                    "dataset_source": "synthetic_starter",
                }
            )
            prefix = ROOMS_AND_PREFIXES[(idx + 1) % len(ROOMS_AND_PREFIXES)]
            suffix = ROOMS_AND_SUFFIXES[(idx + 2) % len(ROOMS_AND_SUFFIXES)]
            varied_1 = f"{prefix}{base_text[0].lower() + base_text[1:]}{suffix}".strip()
            rows.append(
                {
                    "template_id": template_id,
                    "description": varied_1,
                    "category": category,
                    "dataset_source": "synthetic_starter",
                }
            )
            prefix2 = ROOMS_AND_PREFIXES[int(rng.integers(0, len(ROOMS_AND_PREFIXES)))]
            suffix2 = ROOMS_AND_SUFFIXES[int(rng.integers(0, len(ROOMS_AND_SUFFIXES)))]
            varied_2 = f"{prefix2}{base_text}{suffix2}".strip()
            rows.append(
                {
                    "template_id": template_id,
                    "description": varied_2,
                    "category": category,
                    "dataset_source": "synthetic_starter",
                }
            )

    df = pd.DataFrame(rows).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df


def generate_synthetic_pricing_dataset(n_samples: int = 640, seed: int = 42) -> pd.DataFrame:
    """Generate explicitly labeled synthetic Indian INR pricing data for RandomForestRegressor."""
    rng = np.random.default_rng(seed)

    category_base = {
        "Wiring": 520,
        "Switchboard": 280,
        "Fan installation/repair": 330,
        "Lighting": 240,
        "MCB/circuit breaker": 450,
        "Inverter": 560,
        "Electrical appliance connection": 390,
        "General electrical maintenance": 350,
    }
    complexity_mult = {"low": 0.85, "medium": 1.15, "high": 1.65}
    zone_mult = {
        "South Delhi": 1.14,
        "Central Delhi": 1.12,
        "West Delhi": 1.00,
        "North Delhi": 0.96,
        "East Delhi": 0.94,
        "Dwarka/NCR": 1.03,
    }
    urgency_add = {"normal": 0, "urgent": 140, "emergency": 320}
    time_add = {"morning": 0, "afternoon": 0, "evening": 60, "night": 200}

    complexities = ["low", "medium", "high"]
    zones = list(zone_mult.keys())
    urgencies = ["normal", "urgent", "emergency"]
    times = ["morning", "afternoon", "evening", "night"]

    records = []
    for _ in range(n_samples):
        cat = str(rng.choice(CATEGORY_NAMES))
        comp = str(rng.choice(complexities, p=[0.35, 0.45, 0.20]))
        zone = str(rng.choice(zones))
        urg = str(rng.choice(urgencies, p=[0.60, 0.28, 0.12]))
        tod = str(rng.choice(times, p=[0.32, 0.30, 0.26, 0.12]))

        base_dur = {"low": 35, "medium": 60, "high": 110}[comp]
        if cat in ("Wiring", "Inverter"):
            base_dur += 25
        est_duration = int(np.clip(base_dur + rng.normal(0, 12), 20, 200))

        price = (
            category_base[cat] * complexity_mult[comp] * zone_mult[zone]
            + urgency_add[urg]
            + time_add[tod]
            + (est_duration * 2.8)
            + rng.normal(0, 45)
        )
        price = float(np.round(max(180.0, price), -1))

        records.append(
            {
                "service_category": cat,
                "repair_complexity": comp,
                "location_zone": zone,
                "urgency": urg,
                "time_of_service": tod,
                "estimated_duration": est_duration,
                "price_inr": price,
                "dataset_source": "synthetic_starter",
            }
        )

    return pd.DataFrame(records)


def save_synthetic_datasets(artifacts_dir: Path) -> Tuple[Path, Path]:
    """Persist synthetic starter CSVs in artifacts_ml for full auditability."""
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    issue_csv = artifacts_dir / "synthetic_issue_dataset.csv"
    pricing_csv = artifacts_dir / "synthetic_pricing_dataset.csv"
    generate_synthetic_issue_dataset().to_csv(issue_csv, index=False)
    generate_synthetic_pricing_dataset().to_csv(pricing_csv, index=False)
    return issue_csv, pricing_csv
