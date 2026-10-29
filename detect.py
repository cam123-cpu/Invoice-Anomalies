"""Rule-based invoice audit: recompute what each shipment *should* have cost."""
from . import rates
from .models import Finding

TOL = 0.02  # ignore sub-2-cent rounding noise


def detect(shipments, lines):
    by_track = {s.tracking: s for s in shipments}
    seen = set()
    findings = []

    for ln in lines:
        s = by_track.get(ln.tracking)

        if s is None:
            if ln.total > TOL:
                findings.append(Finding(ln.line_id, ln.tracking, "orphan_shipment",
                                        ln.total, 0.0, ln.total))
            continue

        if ln.tracking in seen:
            if ln.total > TOL:
                findings.append(Finding(ln.line_id, ln.tracking, "duplicate_billing",
                                        ln.total, 0.0, ln.total))
            continue
        seen.add(ln.tracking)

        lbs = rates.billable_lbs(s.actual_lbs, s.length, s.width, s.height)

        if s.service == "express" and s.days_late > 0:
            if ln.total > TOL:
                findings.append(Finding(ln.line_id, ln.tracking, "guarantee_not_credited",
                                        ln.total, 0.0, round(ln.total, 2)))
            continue

        exp = rates.price(s.service, s.zone, lbs, s.residential, s.signature)
        over = round(ln.total - exp["total"], 2)
        if over <= TOL:
            continue

        causes = []
        if ln.billed_lbs > lbs:
            causes.append("weight_overbill")
        if ln.billed_zone > s.zone:
            causes.append("zone_misrate")
        if (ln.residential_fee > 0 and not s.residential) or \
           (ln.signature_fee > 0 and not s.signature):
            causes.append("phantom_accessorial")
        if ln.transport > 0 and ln.fuel / ln.transport > rates.FUEL_PCT + 0.005:
            causes.append("fuel_overcharge")
        findings.append(Finding(ln.line_id, ln.tracking, "|".join(causes) or "unexplained",
                                ln.total, exp["total"], over))

    findings.sort(key=lambda f: f.overcharge, reverse=True)
    return findings
