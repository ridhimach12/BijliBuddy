"""Electrical hazard detection and customer safety guidance (strictly non-diagnostic)."""

from typing import Dict, List

from app.core.constants import EMERGENCY_HELPLINES

CRITICAL_HAZARD_PATTERNS = [
    ("spark", "Visible electrical sparks or arcing reported"),
    ("sparking", "Active sparking reported"),
    ("sparks", "Electrical sparks reported"),
    ("burning", "Burning smell or overheating component reported"),
    ("burnt", "Burnt electrical wiring or switchboard reported"),
    ("smoke", "Smoke emitting from electrical equipment"),
    ("fire", "Possible electrical fire hazard"),
    ("flame", "Open flame near electrical fixture"),
    ("shock", "Electric shock sensation or leakage current reported"),
    ("electrocut", "Severe electric shock hazard reported"),
    ("current lag", "Live leakage current reported"),
    ("exposed wire", "Exposed or bare electrical wire reported"),
    ("bare wire", "Bare uninsulated wire reported"),
    ("live wire", "Live exposed conductor reported"),
    ("melting", "Melting insulation or switchboard plastic"),
    ("melted", "Melted electrical fixture"),
    ("blast", "Short-circuit blast or flash reported"),
    ("arcing", "Electrical arcing reported"),
]

ELEVATED_HAZARD_PATTERNS = [
    ("wet", "Moisture or water near electrical fixture"),
    ("water", "Water contact risk near electrical wiring"),
    ("hot switch", "Overheating switch or socket"),
    ("crackling", "Crackling sound inside switchboard or wall"),
    ("buzzing loudly", "Loud electrical buzzing inside panel"),
    ("short circuit", "Potential short circuit condition"),
]

IMAGE_UPLOAD_DISCLAIMER = (
    "Uploaded photos are stored only for visual reference by your assigned electrician. "
    "BijliBuddy AI does NOT diagnose live electrical hazards from images."
)


def assess_electrical_hazard(description: str, urgency: str = "normal") -> Dict:
    """Detect immediate electrical hazard indicators in text and return safe emergency guidance.

    Never instructs customers to perform dangerous DIY electrical repairs.
    """
    text = (description or "").lower()
    matched_triggers: List[str] = []
    reasons: List[str] = []

    severity = "none"
    for keyword, reason in CRITICAL_HAZARD_PATTERNS:
        if keyword in text:
            matched_triggers.append(keyword)
            if reason not in reasons:
                reasons.append(reason)
            severity = "critical"

    for keyword, reason in ELEVATED_HAZARD_PATTERNS:
        if keyword in text:
            matched_triggers.append(keyword)
            if reason not in reasons:
                reasons.append(reason)
            if severity == "none":
                severity = "elevated"

    if urgency == "emergency" and severity == "none":
        severity = "elevated"
        reasons.append("Customer marked request as an emergency")

    hazard_detected = severity != "none"

    if severity == "critical":
        instructions = [
            "Stay well away from the sparking, smoking, or exposed area and keep children and pets clear.",
            "Do NOT touch exposed wires, wet switches, metal appliances, or attempt any DIY repair.",
            "Turn off the main power MCB/isolator ONLY if the distribution box is dry, undamaged, and safe to reach.",
            (
                f"If there is active smoke, fire, or danger, evacuate immediately and call National Emergency "
                f"({EMERGENCY_HELPLINES['national_emergency']}), Fire ({EMERGENCY_HELPLINES['fire_service']}), "
                f"or your Delhi electricity authority: BSES Rajdhani ({EMERGENCY_HELPLINES['bses_rajdhani']}), "
                f"BSES Yamuna ({EMERGENCY_HELPLINES['bses_yamuna']}), or Tata Power DDL ({EMERGENCY_HELPLINES['tata_power_ddl']})."
            ),
        ]
    elif severity == "elevated":
        instructions = [
            "Avoid touching the affected switchboard, wet surface, or appliance until inspected by a qualified electrician.",
            "Do NOT open live switchboards or strip wires yourself.",
            "Switch off the dedicated MCB or unplug dry appliances only if completely safe to do so.",
            f"For urgent utility line faults, contact {EMERGENCY_HELPLINES['national_emergency']} or your local DISCOM helpline.",
        ]
    else:
        instructions = [
            "Do not open live electrical panels or touch bare conductors while waiting for your electrician.",
            "Keep the area dry and accessible for safe inspection.",
        ]

    return {
        "hazard_detected": hazard_detected,
        "severity": severity,
        "matched_triggers": sorted(set(matched_triggers)),
        "reasons": reasons,
        "safety_instructions": instructions,
        "emergency_helplines": EMERGENCY_HELPLINES,
        "image_disclaimer": IMAGE_UPLOAD_DISCLAIMER,
    }
