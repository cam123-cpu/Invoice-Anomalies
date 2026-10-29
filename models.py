from dataclasses import dataclass


@dataclass
class Shipment:
    """What actually happened (the shipper's own records)."""
    tracking: str
    ship_date: str
    service: str  # "ground" | "express"
    zone: int
    actual_lbs: float
    length: int
    width: int
    height: int
    residential: bool
    signature: bool
    days_late: int


@dataclass
class InvoiceLine:
    """What the carrier billed."""
    line_id: str
    tracking: str
    service: str
    billed_zone: int
    billed_lbs: int
    transport: float
    fuel: float
    residential_fee: float
    signature_fee: float
    total: float


@dataclass
class Truth:
    """Ground-truth label for an injected anomaly (synthetic data only)."""
    line_id: str
    anomaly: str
    overcharge: float


@dataclass
class Finding:
    line_id: str
    tracking: str
    types: str  # "|"-joined root causes
    billed_total: float
    expected_total: float
    overcharge: float
