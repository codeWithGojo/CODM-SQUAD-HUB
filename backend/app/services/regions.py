"""African country reference data used by signup and ranking scopes."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.user import Region


AFRICAN_REGIONS: tuple[tuple[str, str, str], ...] = (
    ("DZ", "Algeria", "North Africa"),
    ("AO", "Angola", "Central Africa"),
    ("BJ", "Benin", "West Africa"),
    ("BW", "Botswana", "Southern Africa"),
    ("BF", "Burkina Faso", "West Africa"),
    ("BI", "Burundi", "East Africa"),
    ("CV", "Cabo Verde", "West Africa"),
    ("CM", "Cameroon", "Central Africa"),
    ("CF", "Central African Republic", "Central Africa"),
    ("TD", "Chad", "Central Africa"),
    ("KM", "Comoros", "East Africa"),
    ("CG", "Republic of the Congo", "Central Africa"),
    ("CD", "Democratic Republic of the Congo", "Central Africa"),
    ("CI", "Cote d'Ivoire", "West Africa"),
    ("DJ", "Djibouti", "East Africa"),
    ("EG", "Egypt", "North Africa"),
    ("GQ", "Equatorial Guinea", "Central Africa"),
    ("ER", "Eritrea", "East Africa"),
    ("SZ", "Eswatini", "Southern Africa"),
    ("ET", "Ethiopia", "East Africa"),
    ("GA", "Gabon", "Central Africa"),
    ("GM", "Gambia", "West Africa"),
    ("GH", "Ghana", "West Africa"),
    ("GN", "Guinea", "West Africa"),
    ("GW", "Guinea-Bissau", "West Africa"),
    ("KE", "Kenya", "East Africa"),
    ("LS", "Lesotho", "Southern Africa"),
    ("LR", "Liberia", "West Africa"),
    ("LY", "Libya", "North Africa"),
    ("MG", "Madagascar", "East Africa"),
    ("MW", "Malawi", "East Africa"),
    ("ML", "Mali", "West Africa"),
    ("MR", "Mauritania", "West Africa"),
    ("MU", "Mauritius", "East Africa"),
    ("MA", "Morocco", "North Africa"),
    ("MZ", "Mozambique", "East Africa"),
    ("NA", "Namibia", "Southern Africa"),
    ("NE", "Niger", "West Africa"),
    ("NG", "Nigeria", "West Africa"),
    ("RW", "Rwanda", "East Africa"),
    ("ST", "Sao Tome and Principe", "Central Africa"),
    ("SN", "Senegal", "West Africa"),
    ("SC", "Seychelles", "East Africa"),
    ("SL", "Sierra Leone", "West Africa"),
    ("SO", "Somalia", "East Africa"),
    ("ZA", "South Africa", "Southern Africa"),
    ("SS", "South Sudan", "East Africa"),
    ("SD", "Sudan", "North Africa"),
    ("TZ", "Tanzania", "East Africa"),
    ("TG", "Togo", "West Africa"),
    ("TN", "Tunisia", "North Africa"),
    ("UG", "Uganda", "East Africa"),
    ("ZM", "Zambia", "Southern Africa"),
    ("ZW", "Zimbabwe", "Southern Africa"),
)


def region_id(code: str) -> uuid.UUID:
    """Return a stable identifier so seeded environments share the same IDs."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"https://codmsquadhub.africa/regions/{code.lower()}")


def seed_regions(db: Session) -> int:
    """Insert any missing countries; safe to rerun in local/dev startup."""
    existing = {code for (code,) in db.query(Region.code).all()}
    missing = [
        Region(id=region_id(code), code=code, name=name, zone=zone)
        for code, name, zone in AFRICAN_REGIONS
        if code not in existing
    ]
    if missing:
        db.add_all(missing)
        db.commit()
    return len(missing)
