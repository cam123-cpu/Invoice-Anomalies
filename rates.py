"""A fictional carrier rate card. All numbers are made up for this project."""
import math

DIM_DIVISOR = 139
FUEL_PCT = 0.115
ACCESSORIAL = {"residential": 5.10, "signature": 6.25}
_GROUND = {1: 8.40, 2: 8.95, 3: 9.70, 4: 10.60, 5: 11.80, 6: 13.20, 7: 14.90, 8: 16.80}
BASE = {
    "ground": _GROUND,
    "express": {z: round(v * 2.1, 2) for z, v in _GROUND.items()},
}
PER_LB = {"ground": 0.42, "express": 1.15}


def billable_lbs(actual: float, length: int, width: int, height: int) -> int:
    """Greater of actual and dimensional weight, rounded up to the next lb."""
    dim = length * width * height / DIM_DIVISOR
    return max(1, math.ceil(max(actual, dim)))


def transport(service: str, zone: int, lbs: int) -> float:
    return round(BASE[service][zone] + PER_LB[service] * lbs, 2)


def price(service, zone, lbs, residential, signature, fuel_pct=FUEL_PCT) -> dict:
    t = transport(service, zone, lbs)
    fuel = round(t * fuel_pct, 2)
    res = ACCESSORIAL["residential"] if residential else 0.0
    sig = ACCESSORIAL["signature"] if signature else 0.0
    return {
        "transport": t,
        "fuel": fuel,
        "residential_fee": res,
        "signature_fee": sig,
        "total": round(t + fuel + res + sig, 2),
    }
