"""Secure one-time CLI utility to provision a real BijliBuddy admin account.

Usage (from backend/):
    python scripts/create_admin.py --email admin@yourdomain.com --name "Platform Admin" --phone +919800000000

Security notes:
- Password is NEVER passed as a CLI argument and NEVER hardcoded.
- Provide the password privately via the hidden interactive prompt or the ADMIN_PASSWORD
  environment variable at execution time.
- Passwords and password hashes are never logged or printed.
"""

import argparse
import getpass
import os
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.constants import normalize_indian_phone  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.models import User  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402

MIN_ADMIN_PASSWORD_LENGTH = 10


def validate_admin_password(password: str) -> str:
    """Validate that the privately supplied admin password meets minimum security length."""
    if not password or len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Admin password must be at least {MIN_ADMIN_PASSWORD_LENGTH} characters."
        )
    return password


def create_admin_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    phone: str,
    password: str,
) -> User:
    """Create a non-demo admin user in the database without exposing credentials."""
    clean_email = (email or "").strip().lower()
    if not clean_email or "@" not in clean_email or "." not in clean_email.split("@", 1)[-1]:
        raise ValueError("Please provide a valid admin email address.")

    clean_name = (full_name or "").strip()
    if len(clean_name) < 2:
        raise ValueError("Admin full name must be at least 2 characters.")

    normalized_phone = normalize_indian_phone(phone)
    validated_password = validate_admin_password(password)

    if db.query(User).filter(User.email == clean_email).first():
        raise ValueError(f"An account with email '{clean_email}' already exists.")
    if db.query(User).filter(User.phone == normalized_phone).first():
        raise ValueError("An account with this phone number already exists.")

    admin_user = User(
        email=clean_email,
        phone=normalized_phone,
        full_name=clean_name,
        password_hash=hash_password(validated_password),
        role="admin",
        is_active=True,
        is_demo=False,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user


def _resolve_field(cli_value: Optional[str], env_var: str, prompt_text: str) -> str:
    value = (cli_value or os.environ.get(env_var) or "").strip()
    if value:
        return value
    return input(prompt_text).strip()


def _resolve_private_password() -> str:
    env_password = os.environ.get("ADMIN_PASSWORD", "")
    if env_password:
        return validate_admin_password(env_password)

    first = getpass.getpass(
        f"Enter admin password (min {MIN_ADMIN_PASSWORD_LENGTH} chars, input hidden): "
    )
    confirm = getpass.getpass("Confirm admin password: ")
    if first != confirm:
        raise ValueError("Entered passwords did not match.")
    return validate_admin_password(first)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Provision a real BijliBuddy admin user with a privately supplied password."
    )
    parser.add_argument("--email", help="Admin email address (or set ADMIN_EMAIL)")
    parser.add_argument("--name", help="Admin full name (or set ADMIN_FULL_NAME)")
    parser.add_argument("--phone", help="Admin 10-digit Indian mobile number (or set ADMIN_PHONE)")
    args = parser.parse_args(argv)

    # Validate runtime settings (including production DB/JWT checks) before connecting.
    get_settings()
    Base.metadata.create_all(bind=engine)

    email = _resolve_field(args.email, "ADMIN_EMAIL", "Admin email: ")
    full_name = _resolve_field(args.name, "ADMIN_FULL_NAME", "Admin full name: ")
    phone = _resolve_field(args.phone, "ADMIN_PHONE", "Admin mobile (+91XXXXXXXXXX): ")
    password = _resolve_private_password()

    db = SessionLocal()
    try:
        user = create_admin_user(
            db,
            email=email,
            full_name=full_name,
            phone=phone,
            password=password,
        )
        print(
            f"Admin account created successfully: id={user.id} email={user.email} role={user.role}"
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
