"""Generate synthetic shipments + carrier invoices with injected billing errors."""
import math
import random

from . import rates
from .models import InvoiceLine, Shipment, Truth

ANOMALIES = [
    "weight_overbill",
    "zone_misrate",
    "phantom_accessorial",
    "fuel_overcharge",
    "duplicate_billing",
    "orphan_shipment",
]


def make_line(line_id, tracking, service, zone, lbs, residential, signature,
              fuel_pct=rates.FUEL_PCT) -> InvoiceLine:
    p = rates.price(service, zone, lbs, residential, signature, fuel_pct)
    return InvoiceLine(line_id, tracking, service, zone, lbs, p["transport"], p["fuel"],
                       p["residential_fee"], p["signature_fee"], p["total"])


def generate(n=5000, seed=7, anomaly_rate=0.08):
    rng = random.Random(seed)
    shipments, lines, truth = [], [], []
    counter = 0

    def lid():
        nonlocal counter
        counter += 1
        return f"L{counter:07d}"

    for i in range(n):
        service = rng.choices(["ground", "express"], [0.85, 0.15])[0]
        s = Shipment(
            tracking=f"1Z{rng.randrange(10**8):08d}{i:06d}",
            ship_date=f"2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
            service=service,
            zone=rng.randint(1, 8),
            actual_lbs=round(min(70.0, max(0.2, rng.lognormvariate(1.4, 0.9))), 1),
            length=rng.randint(6, 30), width=rng.randint(6, 24), height=rng.randint(4, 20),
            residential=rng.random() < 0.35,
            signature=rng.random() < 0.10,
            days_late=(rng.choices([0, 1, 2, 3], [0.93, 0.04, 0.02, 0.01])[0]
                       if service == "express" else 0),
        )
        shipments.append(s)
        lbs = rates.billable_lbs(s.actual_lbs, s.length, s.width, s.height)

        kind = None
        if s.service == "express" and s.days_late > 0:
            if rng.random() < 0.5:  # carrier correctly refunds the late delivery
                lines.append(InvoiceLine(lid(), s.tracking, s.service, s.zone, lbs,
                                         0.0, 0.0, 0.0, 0.0, 0.0))
                continue
            kind = "guarantee_not_credited"
        elif rng.random() < anomaly_rate:
            kind = rng.choice(ANOMALIES)

        zone, bl, res, sig, fp = s.zone, lbs, s.residential, s.signature, rates.FUEL_PCT
        if kind == "weight_overbill":
            bl = lbs + rng.randint(1, max(1, math.ceil(lbs * 0.3)))
        elif kind == "zone_misrate":
            if s.zone == 8:
                kind = None
            else:
                zone = min(8, s.zone + rng.randint(1, 2))
        elif kind == "phantom_accessorial":
            if not s.residential:
                res = True
            elif not s.signature:
                sig = True
            else:
                kind = None
        elif kind == "fuel_overcharge":
            fp = rates.FUEL_PCT + rng.uniform(0.03, 0.08)

        line = make_line(lid(), s.tracking, s.service, zone, bl, res, sig, fp)
        lines.append(line)
        expected = 0.0 if kind == "guarantee_not_credited" else rates.price(
            s.service, s.zone, lbs, s.residential, s.signature)["total"]
        if kind in ("weight_overbill", "zone_misrate", "phantom_accessorial",
                    "fuel_overcharge", "guarantee_not_credited"):
            truth.append(Truth(line.line_id, kind, round(line.total - expected, 2)))
        elif kind == "duplicate_billing":
            dup = make_line(lid(), s.tracking, s.service, s.zone, lbs, s.residential, s.signature)
            lines.append(dup)
            truth.append(Truth(dup.line_id, kind, dup.total))
        elif kind == "orphan_shipment":
            ghost = make_line(lid(), f"1ZORPH{rng.randrange(10**8):08d}", "ground",
                              rng.randint(1, 8), rng.randint(1, 30), False, False)
            lines.append(ghost)
            truth.append(Truth(ghost.line_id, kind, ghost.total))
    return shipments, lines, truth
