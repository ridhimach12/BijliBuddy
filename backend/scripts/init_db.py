"""Standalone database initialization and demonstration seeding CLI script."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.base import Base
from app.db.seed import seed_database
from app.db.session import SessionLocal, engine


def main() -> None:
    print("Creating BijliBuddy database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        summary = seed_database(db)
        print("Seed summary:", json.dumps(summary, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
