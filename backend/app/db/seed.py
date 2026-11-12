"""Deterministic demonstration seed data for BijliBuddy.

NOTE: All accounts, profiles, bookings, and ratings seeded here are explicitly marked
as synthetic demonstration data (is_demo=True).
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import (
    CATEGORY_NAMES,
    DELHI_LOCALITIES,
    LOCALITY_MAP,
    SERVICE_CATEGORIES_CONFIG,
    TIME_SLOTS,
)
from app.core.security import hash_password
from app.db.models import (
    Availability,
    Booking,
    CustomerProfile,
    ElectricianProfile,
    ElectricianSkill,
    Notification,
    Payment,
    Review,
    ServiceCategory,
    ServiceRequest,
    User,
)

DEMO_CUSTOMERS = [
    ("Ananya Sharma", "ananya.sharma@bijlibuddy.demo", "+919811001101", "Saket", "B-42, Press Enclave Road, Saket"),
    ("Vikram Malhotra", "vikram.malhotra@bijlibuddy.demo", "+919811001102", "Dwarka", "Flat 304, Sector 12 Pocket B, Dwarka"),
    ("Priya Nair", "priya.nair@bijlibuddy.demo", "+919811001103", "Lajpat Nagar", "C-18, Lajpat Nagar II"),
    ("Arjun Khanna", "arjun.khanna@bijlibuddy.demo", "+919811001104", "Rohini", "Plot 19, Sector 9, Rohini"),
    ("Meera Iyer", "meera.iyer@bijlibuddy.demo", "+919811001105", "Connaught Place", "Suite 11, Tolstoy Marg, Connaught Place"),
    ("Siddharth Verma", "siddharth.verma@bijlibuddy.demo", "+919811001106", "Janakpuri", "A-2/85, Janakpuri"),
    ("Kavita Joshi", "kavita.joshi@bijlibuddy.demo", "+919811001107", "Mayur Vihar", "Pocket 4, Mayur Vihar Phase 1"),
    ("Nikhil Kapoor", "nikhil.kapoor@bijlibuddy.demo", "+919811001108", "Hauz Khas", "E-15, Hauz Khas Enclave"),
]

# 22 realistic Delhi electricians with varied skills, experience, locality, availability & verification status
DEMO_ELECTRICIANS = [
    ("Ramesh Kumar Verma", "ramesh.verma@bijlibuddy.demo", "+919899100001", "Saket", 9, 8.0, True, "verified", "DL-WIRE-2021-101", ["MCB/circuit breaker", "Wiring", "Inverter"], 199),
    ("Suresh Pal", "suresh.pal@bijlibuddy.demo", "+919899100002", "Malviya Nagar", 7, 7.0, True, "verified", "DL-WIRE-2022-102", ["Switchboard", "Fan installation/repair", "Lighting"], 149),
    ("Manoj Tiwari", "manoj.tiwari@bijlibuddy.demo", "+919899100003", "Hauz Khas", 11, 9.0, True, "verified", "DL-WIRE-2019-103", ["Wiring", "MCB/circuit breaker", "General electrical maintenance"], 249),
    ("Deepak Chauhan", "deepak.chauhan@bijlibuddy.demo", "+919899100004", "Lajpat Nagar", 5, 6.5, True, "verified", "DL-WIRE-2023-104", ["Electrical appliance connection", "Switchboard", "MCB/circuit breaker"], 179),
    ("Harish Rawat", "harish.rawat@bijlibuddy.demo", "+919899100005", "Greater Kailash", 12, 8.5, True, "verified", "DL-WIRE-2018-105", ["Inverter", "Wiring", "Electrical appliance connection"], 249),
    ("Ajay Singh", "ajay.singh@bijlibuddy.demo", "+919899100006", "Vasant Kunj", 6, 7.5, False, "verified", "DL-WIRE-2022-106", ["MCB/circuit breaker", "Wiring", "Switchboard"], 199),
    ("Rajendra Prasad", "rajendra.prasad@bijlibuddy.demo", "+919899100007", "Connaught Place", 14, 10.0, True, "verified", "DL-WIRE-2017-107", ["Wiring", "MCB/circuit breaker", "General electrical maintenance", "Inverter"], 249),
    ("Imran Khan", "imran.khan@bijlibuddy.demo", "+919899100008", "Karol Bagh", 8, 7.0, True, "verified", "DL-WIRE-2020-108", ["Switchboard", "Lighting", "Fan installation/repair"], 179),
    ("Pradeep Sharma", "pradeep.sharma@bijlibuddy.demo", "+919899100009", "Dwarka", 10, 9.0, True, "verified", "DL-WIRE-2020-109", ["Inverter", "Electrical appliance connection", "MCB/circuit breaker"], 199),
    ("Nitin Yadav", "nitin.yadav@bijlibuddy.demo", "+919899100010", "Dwarka", 4, 6.0, True, "pending", "DL-WIRE-2025-110", ["Fan installation/repair", "Lighting", "Switchboard"], 149),
    ("Santosh Mishra", "santosh.mishra@bijlibuddy.demo", "+919899100011", "Janakpuri", 9, 8.0, True, "verified", "DL-WIRE-2021-111", ["Wiring", "Switchboard", "Electrical appliance connection"], 199),
    ("Vikas Gupta", "vikas.gupta@bijlibuddy.demo", "+919899100012", "Rajouri Garden", 6, 7.0, True, "verified", "DL-WIRE-2022-112", ["Lighting", "Fan installation/repair", "General electrical maintenance"], 169),
    ("Pankaj Kashyap", "pankaj.kashyap@bijlibuddy.demo", "+919899100013", "Rohini", 8, 8.5, True, "verified", "DL-WIRE-2021-113", ["MCB/circuit breaker", "Inverter", "Wiring"], 199),
    ("Sunil Bhardwaj", "sunil.bhardwaj@bijlibuddy.demo", "+919899100014", "Pitampura", 5, 6.0, False, "verified", "DL-WIRE-2023-114", ["Electrical appliance connection", "Switchboard"], 179),
    ("Mohit Saini", "mohit.saini@bijlibuddy.demo", "+919899100015", "Civil Lines", 3, 6.5, True, "pending", "DL-WIRE-2025-115", ["Lighting", "Fan installation/repair", "Switchboard"], 149),
    ("Rakesh Negi", "rakesh.negi@bijlibuddy.demo", "+919899100016", "Mayur Vihar", 10, 8.0, True, "verified", "DL-WIRE-2020-116", ["Wiring", "MCB/circuit breaker", "Inverter"], 199),
    ("Dinesh Solanki", "dinesh.solanki@bijlibuddy.demo", "+919899100017", "Preet Vihar", 7, 7.5, True, "verified", "DL-WIRE-2021-117", ["Electrical appliance connection", "General electrical maintenance", "Switchboard"], 179),
    ("Karan Mehra", "karan.mehra@bijlibuddy.demo", "+919899100018", "Saket", 2, 5.5, True, "pending", "DL-APP-2026-118", ["Fan installation/repair", "Lighting"], 149),
    ("Lokesh Rathore", "lokesh.rathore@bijlibuddy.demo", "+919899100019", "Karol Bagh", 4, 6.0, True, "verified", "DL-WIRE-2024-119", ["Inverter", "MCB/circuit breaker", "General electrical maintenance"], 179),
    ("Ashish Maurya", "ashish.maurya@bijlibuddy.demo", "+919899100020", "Rohini", 1, 5.0, True, "unverified", None, ["Switchboard", "Lighting"], 149),
    ("Gaurav Pathak", "gaurav.pathak@bijlibuddy.demo", "+919899100021", "Lajpat Nagar", 6, 7.0, False, "pending", "DL-APP-2026-121", ["Electrical appliance connection", "Inverter"], 189),
    ("Tariq Ahmed", "tariq.ahmed@bijlibuddy.demo", "+919899100022", "Mayur Vihar", 2, 6.0, True, "unverified", None, ["Fan installation/repair", "General electrical maintenance", "Switchboard"], 149),
]

SAMPLE_ISSUES = [
    ("Main MCB tripping repeatedly when AC starts", "MCB/circuit breaker", "high", "urgent", 550),
    ("Bedroom switchboard sparking and plastic smell", "Switchboard", "high", "emergency", 480),
    ("Ceiling fan running slow and humming loudly", "Fan installation/repair", "low", "normal", 320),
    ("Concealed wiring fault in kitchen socket line", "Wiring", "high", "urgent", 720),
    ("Install 3 false ceiling LED panel lights", "Lighting", "low", "normal", 360),
    ("Inverter not charging battery during mains power", "Inverter", "medium", "normal", 540),
    ("Install 16A AC stabilizer and power point", "Electrical appliance connection", "medium", "normal", 450),
    ("Complete home earthing and voltage fluctuation audit", "General electrical maintenance", "medium", "normal", 420),
]

REVIEW_COMMENTS = [
    "Reached on time in Delhi traffic and diagnosed the MCB trip neatly.",
    "Very polite, explained the fault clearly and used proper insulated tools.",
    "Clean switchboard installation, transparent charges matching estimate.",
    "Fixed the fan capacitor quickly without unnecessary part replacement.",
    "Thorough wiring inspection and safe earthing fix.",
    "Good workmanship, arrived slightly late due to rain but resolved fully.",
]


def ensure_service_categories(db: Session) -> Tuple[Dict[str, ServiceCategory], int]:
    """Ensure all configured ServiceCategory rows exist idempotently."""
    categories_by_name: Dict[str, ServiceCategory] = {
        cat.name: cat for cat in db.query(ServiceCategory).all()
    }
    created = 0
    for cfg in SERVICE_CATEGORIES_CONFIG:
        if cfg["name"] not in categories_by_name:
            cat = ServiceCategory(
                name=cfg["name"],
                slug=cfg["slug"],
                description=cfg["description"],
                base_price_inr=cfg["base_price_inr"],
                estimated_duration_mins=cfg["estimated_duration_mins"],
                safety_level=cfg["safety_level"],
                icon_name=cfg["icon_name"],
            )
            db.add(cat)
            categories_by_name[cfg["name"]] = cat
            created += 1
    if created > 0:
        db.flush()
    return categories_by_name, created


def seed_database(db: Session) -> Dict[str, int]:
    """Seed required categories always; seed synthetic demo users/data in non-production only."""
    # 1. Service Categories (8 required domain categories) — always initialized idempotently
    categories_by_name, categories_created = ensure_service_categories(db)

    is_production = get_settings().ENVIRONMENT.strip().lower() == "production"
    if is_production:
        if categories_created > 0:
            db.commit()
        return {
            "categories": len(categories_by_name),
            "categories_created": categories_created,
            "customers": 0,
            "electricians": 0,
            "bookings": 0,
            "admin_created": 0,
            "production_demo_skipped": 1,
        }

    existing_users = db.query(User).count()
    if existing_users > 0:
        if categories_created > 0:
            db.commit()
        return {
            "already_seeded": 1,
            "categories": len(categories_by_name),
            "categories_created": categories_created,
        }

    rng = random.Random(42)
    demo_password_hash = hash_password("Demo@1234")

    # 2. Admin account (development/non-production only; production admins are provisioned explicitly)
    admin_user = User(
        email="admin@bijlibuddy.demo",
        phone="+919810000001",
        full_name="BijliBuddy Operations Admin",
        password_hash=demo_password_hash,
        role="admin",
        is_active=True,
        is_demo=True,
    )
    db.add(admin_user)
    db.flush()

    # 3. Customers (8 demo households)
    customer_users: List[User] = []
    for name, email, phone, locality, address in DEMO_CUSTOMERS:
        loc_info = LOCALITY_MAP[locality]
        u = User(
            email=email,
            phone=phone,
            full_name=name,
            password_hash=demo_password_hash,
            role="customer",
            is_active=True,
            is_demo=True,
        )
        db.add(u)
        db.flush()
        cp = CustomerProfile(
            user_id=u.id,
            address=address,
            locality=locality,
            zone=loc_info["zone"],
            latitude=loc_info["latitude"] + rng.uniform(-0.004, 0.004),
            longitude=loc_info["longitude"] + rng.uniform(-0.004, 0.004),
        )
        db.add(cp)
        customer_users.append(u)
    db.flush()

    # 4. Electricians (22 demo electricians with skills & weekly availability)
    electrician_profiles: List[ElectricianProfile] = []
    now = datetime.now(timezone.utc)

    for (
        name, email, phone, locality, exp, radius, avail, ver_status, cred_id, skill_names, visit_fee
    ) in DEMO_ELECTRICIANS:
        loc_info = LOCALITY_MAP[locality]
        u = User(
            email=email,
            phone=phone,
            full_name=name,
            password_hash=demo_password_hash,
            role="electrician",
            is_active=True,
            is_demo=True,
        )
        db.add(u)
        db.flush()

        ep = ElectricianProfile(
            user_id=u.id,
            bio=f"Independent Delhi electrician based in {locality} with {exp} years of residential wiring, MCB & appliance experience.",
            experience_years=exp,
            service_radius_km=radius,
            locality=locality,
            zone=loc_info["zone"],
            address=f"Near Main Market, {locality}, New Delhi - {loc_info['pincode']}",
            latitude=round(loc_info["latitude"] + rng.uniform(-0.006, 0.006), 5),
            longitude=round(loc_info["longitude"] + rng.uniform(-0.006, 0.006), 5),
            is_available=avail,
            working_hours_start="08:00",
            working_hours_end="21:00",
            verification_status=ver_status,
            credential_id=cred_id,
            verification_notes=(
                "Demo credential verified by Admin"
                if ver_status == "verified"
                else "Awaiting admin credential review" if ver_status == "pending" else None
            ),
            verified_by_admin_id=admin_user.id if (admin_user is not None and ver_status == "verified") else None,
            verified_at=(now - timedelta(days=rng.randint(15, 90))) if ver_status == "verified" else None,
            base_visit_fee_inr=visit_fee,
            total_earnings_inr=0.0,
        )
        db.add(ep)
        db.flush()

        for s_name in skill_names:
            cat = categories_by_name[s_name]
            db.add(
                ElectricianSkill(
                    electrician_id=ep.id,
                    category_id=cat.id,
                    proficiency_level="expert" if exp >= 5 else "intermediate",
                    years_experience=max(1, min(exp, exp - rng.randint(0, 2))),
                )
            )

        for day in range(7):
            db.add(
                Availability(
                    electrician_id=ep.id,
                    day_of_week=day,
                    start_time="08:00",
                    end_time="21:00",
                    is_active=(day != 6 or rng.random() > 0.25),
                )
            )
        electrician_profiles.append(ep)

    db.flush()

    # 5. Historical ServiceRequests, Bookings, Reviews & Sandbox Payments (68 jobs over last 28 days)
    earnings_acc: Dict[int, float] = {ep.id: 0.0 for ep in electrician_profiles}
    booking_count = 0

    for i in range(68):
        cust = customer_users[i % len(customer_users)]
        cust_prof = db.query(CustomerProfile).filter(CustomerProfile.user_id == cust.id).first()
        # Distribute across Delhi localities while weighting active neighborhoods
        loc_info = DELHI_LOCALITIES[(i * 3 + rng.randint(0, 2)) % len(DELHI_LOCALITIES)]
        issue_desc, cat_name, complexity, urgency, base_price = SAMPLE_ISSUES[i % len(SAMPLE_ISSUES)]

        # Bias toward experienced verified electricians for historical volume, keeping 2 newcomers (idx 19, 21) low-volume
        if i % 17 == 0:
            ep = electrician_profiles[17]  # 2yr pending newcomer
        else:
            ep = electrician_profiles[i % 17]

        days_ago = rng.randint(0, 27)
        hour_choices = [9, 10, 11, 14, 15, 16, 18, 19, 20, 22]
        chosen_hour = hour_choices[i % len(hour_choices)]
        created_dt = (now - timedelta(days=days_ago)).replace(
            hour=chosen_hour, minute=rng.randint(0, 50), second=0, microsecond=0
        )

        if 6 <= chosen_hour < 12:
            slot_bucket = TIME_SLOTS[0]
        elif 12 <= chosen_hour < 17:
            slot_bucket = TIME_SLOTS[1]
        elif 17 <= chosen_hour < 21:
            slot_bucket = TIME_SLOTS[2]
        else:
            slot_bucket = TIME_SLOTS[3]

        sr = ServiceRequest(
            customer_id=cust.id,
            description=f"{issue_desc} ({loc_info['name']})",
            selected_category=cat_name,
            ai_predicted_category=cat_name,
            ai_confidence=round(rng.uniform(0.78, 0.96), 3),
            ai_suggested_service_type=f"{cat_name} Inspection & Repair",
            urgency=urgency,
            repair_complexity=complexity,
            address=cust_prof.address if cust_prof else f"Sector Road, {loc_info['name']}",
            locality=loc_info["name"],
            zone=loc_info["zone"],
            latitude=loc_info["latitude"] + rng.uniform(-0.005, 0.005),
            longitude=loc_info["longitude"] + rng.uniform(-0.005, 0.005),
            hazard_detected=("spark" in issue_desc.lower()),
            hazard_warnings=["Stay clear of sparking board"] if "spark" in issue_desc.lower() else [],
            ai_base_price_inr=float(base_price),
            ai_price_lower_inr=float(round(base_price * 0.85, -1)),
            ai_price_upper_inr=float(round(base_price * 1.25, -1)),
            status="booked",
            created_at=created_dt,
        )
        db.add(sr)
        db.flush()

        # Assign realistic status distribution: 52 completed, 5 active/accepted, 4 pending, 4 cancelled, 3 rejected
        if i < 52:
            status = "completed"
        elif i < 56:
            status = "accepted" if i % 2 == 0 else "in_progress"
        elif i < 61:
            status = "pending"
        elif i < 65:
            status = "cancelled"
        else:
            status = "rejected"

        quote = float(round(base_price + rng.choice([-40, 0, 50, 100]), -1))
        on_time = rng.random() > 0.12 if status == "completed" else None

        booking = Booking(
            service_request_id=sr.id,
            customer_id=cust.id,
            electrician_id=ep.id,
            status=status,
            ai_estimate_snapshot_inr=float(base_price),
            electrician_quote_inr=quote if status != "pending" else None,
            final_amount_inr=quote if status == "completed" else None,
            estimated_arrival_mins=rng.randint(15, 42),
            match_score=round(rng.uniform(76.0, 96.5), 1),
            match_explanation={
                "summary": f"Matched in {loc_info['name']} for {cat_name}",
                "reasons": [
                    f"Specializes in {cat_name}",
                    f"Located near {ep.locality}",
                ],
            },
            scheduled_slot="Morning 10AM-12PM" if chosen_hour < 12 else "Same Day",
            time_slot_bucket=slot_bucket,
            customer_notes="Please call on arrival at apartment gate.",
            electrician_notes="Standard inspection & repair completed." if status == "completed" else None,
            cancellation_reason="Customer rescheduled" if status == "cancelled" else None,
            on_time_completed=on_time,
            accepted_at=(created_dt + timedelta(minutes=8)) if status in ("completed", "accepted", "in_progress", "cancelled") else None,
            started_at=(created_dt + timedelta(minutes=35)) if status in ("completed", "in_progress") else None,
            completed_at=(created_dt + timedelta(minutes=95)) if status == "completed" else None,
            created_at=created_dt,
        )
        db.add(booking)
        db.flush()
        booking_count += 1

        if status == "completed":
            earnings_acc[ep.id] += quote
            rating_val = rng.choices([5, 4, 3], weights=[62, 30, 8])[0]
            db.add(
                Review(
                    booking_id=booking.id,
                    customer_id=cust.id,
                    electrician_id=ep.id,
                    rating=rating_val,
                    comment=REVIEW_COMMENTS[i % len(REVIEW_COMMENTS)],
                    was_on_time=bool(on_time),
                    created_at=created_dt + timedelta(hours=2),
                )
            )
            db.add(
                Payment(
                    booking_id=booking.id,
                    customer_id=cust.id,
                    amount_inr=quote,
                    payment_method=rng.choice(["sandbox_upi", "cash_on_completion"]),
                    status="demo_paid",
                    is_sandbox=True,
                    transaction_ref=f"DEMO-TXN-{1000 + booking.id}",
                    created_at=created_dt + timedelta(hours=2),
                )
            )

    for ep in electrician_profiles:
        ep.total_earnings_inr = round(earnings_acc[ep.id], 2)

    # Seed sample notifications for featured customer, electrician, and admin
    db.add(
        Notification(
            user_id=customer_users[0].id,
            title="Welcome to BijliBuddy (Demo)",
            message="Describe any electrical issue to get AI classification, INR pricing, and top Delhi electricians.",
            type="system",
        )
    )
    db.add(
        Notification(
            user_id=electrician_profiles[0].user_id,
            title="Pending Booking Requests",
            message="Check your Incoming Requests tab to accept or quote new local household jobs.",
            type="booking_update",
        )
    )
    if admin_user is not None:
        db.add(
            Notification(
                user_id=admin_user.id,
                title="4 Electricians Pending Credential Verification",
                message="Review pending technician credentials in the Verification Queue before marking verified.",
                type="verification",
            )
        )

    db.commit()
    return {
        "categories": len(categories_by_name),
        "categories_created": categories_created,
        "customers": len(customer_users),
        "electricians": len(electrician_profiles),
        "bookings": booking_count,
        "admin_created": 1,
    }
