"""Seed data script for EHAZOP platform.

This script populates the database with initial data:
- Default guideword libraries for different study types
- Default risk matrix
- Demo user accounts
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.core.security import get_password_hash

settings = get_settings()


async def seed_guideword_libraries(db):
    """Seed default guideword libraries."""
    from app.models.guideword import GuidewordLibrary, Guideword
    
    # Generic HAZOP guidewords
    generic_library = GuidewordLibrary(
        name="Generic HAZOP Guidewords",
        description="Standard HAZOP guidewords for process safety studies",
        study_type="generic",
        category="fault",
        is_default=True,
    )
    db.add(generic_library)
    await db.flush()

    generic_guidewords = [
        ("NO", "None/Nothing", "No or none of the design intent is achieved", "No {parameter}"),
        ("MORE", "More", "More of a variable than intended", "More {parameter}"),
        ("LESS", "Less", "Less of a variable than intended", "Less {parameter}"),
        ("AS_WELL_AS", "As Well As", "Addition of design intent", "As well as {parameter}"),
        ("PART_OF", "Part Of", "Only part of design intent is achieved", "Part of {parameter}"),
        ("REVERSE", "Reverse", "Logical opposite of design intent achieved", "Reverse of {parameter}"),
        ("OTHER", "Other", "Something different from design intent", "Other than {parameter}"),
    ]

    for i, (code, name, desc, template) in enumerate(generic_guidewords):
        gw = Guideword(
            library_id=generic_library.id,
            code=code,
            name=name,
            description=desc,
            deviation_template=template,
            order_index=i,
        )
        db.add(gw)

    # EHAZOP guidewords
    ehazop_library = GuidewordLibrary(
        name="EHAZOP Electrical Guidewords",
        description="Guidewords for electrical HAZOP studies",
        study_type="EHAZOP",
        category="operational-mode",
        is_default=False,
    )
    db.add(ehazop_library)
    await db.flush()

    ehazop_guidewords = [
        ("NO_POWER", "No Power", "Loss of power supply", "No power to {component}"),
        ("BACKFEED", "Backfeed", "Power flowing in reverse direction", "Backfeed to {component}"),
        ("ISLANDING", "Islanding", "Isolation of part of the network", "Islanding of {component}"),
        ("OVERVOLTAGE", "Overvoltage", "Voltage exceeds rated value", "Overvoltage at {component}"),
        ("UNDERVOLTAGE", "Undervoltage", "Voltage below rated value", "Undervoltage at {component}"),
        ("OVERCURRENT", "Overcurrent", "Current exceeds rated value", "Overcurrent in {component}"),
        ("EARTH_FAULT", "Earth Fault", "Unintended connection to earth", "Earth fault on {component}"),
        ("PHASE_LOSS", "Phase Loss", "Loss of one or more phases", "Phase loss in {component}"),
        ("SYNC_LOSS", "Synchronism Loss", "Loss of synchronism", "Loss of synchronism at {component}"),
    ]

    for i, (code, name, desc, template) in enumerate(ehazop_guidewords):
        gw = Guideword(
            library_id=ehazop_library.id,
            code=code,
            name=name,
            description=desc,
            deviation_template=template,
            order_index=i,
        )
        db.add(gw)

    # SYSOP guidewords
    sysop_library = GuidewordLibrary(
        name="SYSOP Operability Guidewords",
        description="Guidewords for system operability studies",
        study_type="SYSOP",
        category="system",
        is_default=False,
    )
    db.add(sysop_library)
    await db.flush()

    sysop_guidewords = [
        ("STARTUP_FAIL", "Startup Failure", "System fails to start", "Startup failure of {system}"),
        ("SHUTDOWN_FAIL", "Shutdown Failure", "System fails to shutdown", "Shutdown failure of {system}"),
        ("OPERATE_FAIL", "Operating Failure", "System fails during operation", "Operating failure of {system}"),
        ("MAINTENANCE", "Maintenance Issue", "Maintenance not possible", "Maintenance issue with {system}"),
        ("ISOLATION", "Isolation Failure", "Cannot isolate for maintenance", "Isolation failure of {system}"),
    ]

    for i, (code, name, desc, template) in enumerate(sysop_guidewords):
        gw = Guideword(
            library_id=sysop_library.id,
            code=code,
            name=name,
            description=desc,
            deviation_template=template,
            order_index=i,
        )
        db.add(gw)

    print("✓ Guideword libraries seeded")


async def seed_risk_matrix(db):
    """Seed default risk matrix."""
    from app.models.risk import RiskMatrix

    # Default 5x5 risk matrix
    matrix_data = [
        [1, 2, 3, 4, 5],   # Severity 1 - Negligible
        [2, 4, 6, 8, 10],  # Severity 2 - Minor
        [3, 6, 9, 12, 15], # Severity 3 - Moderate
        [4, 8, 12, 16, 20],# Severity 4 - Major
        [5, 10, 15, 20, 25],# Severity 5 - Catastrophic
    ]

    risk_bands = [
        {"name": "Low", "min_score": 0, "max_score": 5, "color": "green"},
        {"name": "Medium", "min_score": 6, "max_score": 10, "color": "yellow"},
        {"name": "High", "min_score": 11, "max_score": 15, "color": "orange"},
        {"name": "Very High", "min_score": 16, "max_score": 25, "color": "red"},
    ]

    severity_scale = [
        {"level": 1, "name": "Negligible", "description": "No injury, minimal impact"},
        {"level": 2, "name": "Minor", "description": "Minor injuries, limited damage"},
        {"level": 3, "name": "Moderate", "description": "Moderate injuries, significant damage"},
        {"level": 4, "name": "Major", "description": "Major injuries, extensive damage"},
        {"level": 5, "name": "Catastrophic", "description": "Fatalities, total loss"},
    ]

    likelihood_scale = [
        {"code": "A", "name": "Rare", "description": "May only occur in exceptional circumstances"},
        {"code": "B", "name": "Unlikely", "description": "Could occur but not expected"},
        {"code": "C", "name": "Possible", "description": "Might occur occasionally"},
        {"code": "D", "name": "Likely", "description": "Will probably occur"},
        {"code": "E", "name": "Almost Certain", "description": "Expected to occur frequently"},
    ]

    matrix = RiskMatrix(
        name="Standard P/A/E/R Risk Matrix",
        description="Standard 5x5 risk matrix with People, Asset, Environment, Reputation categories",
        categories=["People", "Asset", "Environment", "Reputation"],
        severity_scale=severity_scale,
        likelihood_scale=likelihood_scale,
        risk_bands=risk_bands,
        matrix_data=matrix_data,
        is_default=True,
    )
    db.add(matrix)

    print("✓ Risk matrix seeded")


async def seed_demo_users(db):
    """Seed demo user accounts."""
    from app.models.user import User

    users = [
        {
            "email": "admin@ehazop.local",
            "password": "admin123",
            "full_name": "System Administrator",
            "role": "admin",
        },
        {
            "email": "facilitator@ehazop.local",
            "password": "facilitator123",
            "full_name": "John Facilitator",
            "role": "facilitator",
        },
        {
            "email": "scribe@ehazop.local",
            "password": "scribe123",
            "full_name": "Jane Scribe",
            "role": "scribe",
        },
        {
            "email": "participant@ehazop.local",
            "password": "participant123",
            "full_name": "Bob Participant",
            "role": "participant",
        },
    ]

    for user_data in users:
        # Check if user exists
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.email == user_data["email"])
        )
        if result.scalar_one_or_none():
            continue

        user = User(
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
        )
        db.add(user)

    print("✓ Demo users seeded")


async def seed_demo_study(db):
    """Create a demo study."""
    from app.models.user import User, Study, StudyMembership
    from sqlalchemy import select

    # Get admin user
    result = await db.execute(select(User).where(User.email == "admin@ehazop.local"))
    admin = result.scalar_one_or_none()
    if not admin:
        print("✗ Admin user not found, skipping demo study")
        return

    # Check if demo study exists
    result = await db.execute(select(Study).where(Study.name == "Demo EHAZOP Study"))
    if result.scalar_one_or_none():
        print("✓ Demo study already exists")
        return

    study = Study(
        name="Demo EHAZOP Study",
        study_type="EHAZOP",
        facility="Demo Power Plant",
        status="draft",
        revision=1,
        confidentiality="internal",
        description="A demonstration EHAZOP study for testing the platform",
        created_by_id=admin.id,
        facilitator_id=admin.id,
    )
    db.add(study)
    await db.flush()

    # Add admin as facilitator
    membership = StudyMembership(
        user_id=admin.id,
        study_id=study.id,
        role="facilitator",
    )
    db.add(membership)

    print("✓ Demo study seeded")


async def main():
    """Run all seeding functions."""
    print("Starting database seeding...")

    async with async_session_factory() as db:
        try:
            await seed_guideword_libraries(db)
            await seed_risk_matrix(db)
            await seed_demo_users(db)
            await seed_demo_study(db)
            await db.commit()
            print("\n✓ All seeding completed successfully!")
            print("\nDemo accounts:")
            print("  admin@ehazop.local / admin123")
            print("  facilitator@ehazop.local / facilitator123")
            print("  scribe@ehazop.local / scribe123")
            print("  participant@ehazop.local / participant123")
        except Exception as e:
            await db.rollback()
            print(f"\n✗ Seeding failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())