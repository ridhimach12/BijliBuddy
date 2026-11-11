"""Authentication endpoints: register, login, current user, and demo account hints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import CATEGORY_NAMES, LOCALITY_MAP
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.models import (
    Availability,
    CustomerProfile,
    ElectricianProfile,
    ElectricianSkill,
    ServiceCategory,
    User,
)
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserRegisterRequest, UserSummary
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _build_user_summary(user: User) -> UserSummary:
    locality = None
    zone = None
    verification_status = None
    electrician_profile_id = None

    if user.role == "customer" and user.customer_profile:
        locality = user.customer_profile.locality
        zone = user.customer_profile.zone
    elif user.role == "electrician" and user.electrician_profile:
        locality = user.electrician_profile.locality
        zone = user.electrician_profile.zone
        verification_status = user.electrician_profile.verification_status
        electrician_profile_id = user.electrician_profile.id

    return UserSummary(
        id=user.id,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        role=user.role,
        is_demo=user.is_demo,
        locality=locality,
        zone=zone,
        verification_status=verification_status,
        electrician_profile_id=electrician_profile_id,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new customer or independent electrician account."""
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    loc_info = LOCALITY_MAP.get(payload.locality, LOCALITY_MAP["Connaught Place"])

    user = User(
        email=payload.email.lower(),
        phone=payload.phone,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
        is_demo=False,
    )
    db.add(user)
    db.flush()

    if payload.role == "customer":
        db.add(
            CustomerProfile(
                user_id=user.id,
                address=payload.address.strip() or f"{loc_info['name']}, New Delhi",
                locality=loc_info["name"],
                zone=loc_info["zone"],
                latitude=loc_info["latitude"],
                longitude=loc_info["longitude"],
            )
        )
        create_notification(
            db,
            user.id,
            "Welcome to BijliBuddy",
            "Describe any electrical issue to get AI diagnostics, INR pricing, and verified nearby electricians.",
            notif_type="system",
        )
    else:
        # Never mark newly registered electrician as verified; must await Admin approval
        verification_status = "pending" if payload.credential_id else "unverified"
        ep = ElectricianProfile(
            user_id=user.id,
            bio=payload.bio.strip()
            or f"Independent electrician serving {loc_info['name']} and nearby Delhi localities.",
            experience_years=payload.experience_years,
            service_radius_km=payload.service_radius_km,
            locality=loc_info["name"],
            zone=loc_info["zone"],
            address=payload.address.strip() or f"{loc_info['name']}, New Delhi",
            latitude=loc_info["latitude"],
            longitude=loc_info["longitude"],
            is_available=True,
            verification_status=verification_status,
            credential_id=payload.credential_id.strip() if payload.credential_id else None,
            base_visit_fee_inr=199,
        )
        db.add(ep)
        db.flush()

        requested_skills = [s for s in payload.skills if s in CATEGORY_NAMES] or [
            "General electrical maintenance"
        ]
        cats = db.query(ServiceCategory).filter(ServiceCategory.name.in_(requested_skills)).all()
        for cat in cats:
            db.add(
                ElectricianSkill(
                    electrician_id=ep.id,
                    category_id=cat.id,
                    proficiency_level="intermediate",
                    years_experience=max(1, payload.experience_years),
                )
            )
        for day in range(7):
            db.add(
                Availability(
                    electrician_id=ep.id,
                    day_of_week=day,
                    start_time="08:00",
                    end_time="21:00",
                    is_active=True,
                )
            )
        create_notification(
            db,
            user.id,
            "Profile Created — Pending Admin Verification",
            "Your profile is live in matching results, and your credentials are queued for Admin verification.",
            notif_type="verification",
        )

    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(access_token=token, user=_build_user_summary(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email & password and issue JWT."""
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is deactivated.",
        )

    token = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(access_token=token, user=_build_user_summary(user))


@router.get("/me", response_model=UserSummary)
def get_me(current_user: User = Depends(get_current_user)):
    """Return currently authenticated user summary."""
    return _build_user_summary(current_user)


@router.get("/demo-accounts")
def get_demo_accounts():
    """Return non-admin synthetic demonstration login hints in non-production environments only."""
    if get_settings().ENVIRONMENT.strip().lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo accounts endpoint is disabled in production.",
        )

    return {
        "notice": "Explicitly labeled non-admin synthetic demonstration accounts (development only).",
        "accounts": [
            {
                "role": "customer",
                "label": "Demo Customer (Ananya Sharma — Saket)",
                "email": "ananya.sharma@bijlibuddy.demo",
                "password": "Demo@1234",
            },
            {
                "role": "electrician",
                "label": "Demo Electrician (Ramesh Kumar Verma — Saket, Verified)",
                "email": "ramesh.verma@bijlibuddy.demo",
                "password": "Demo@1234",
            },
        ],
    }
