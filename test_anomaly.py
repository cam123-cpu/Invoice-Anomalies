import unittest

from anomaly import rates
from anomaly.detect import detect
from anomaly.generate import generate, make_line
from anomaly.report import evaluate
from anomaly.models import Shipment


def ship(**kw):
    base = dict(tracking="T1", ship_date="2025-01-01", service="ground", zone=3,
                actual_lbs=5.0, length=10, width=10, height=10, residential=False,
                signature=False, days_late=0)
    base.update(kw)
    return Shipment(**base)


class RateTests(unittest.TestCase):
    def test_dim_weight_beats_actual(self):
        self.assertEqual(rates.billable_lbs(2.0, 20, 20, 20), 58)  # 8000/139 = 57.6

    def test_actual_weight_rounds_up(self):
        self.assertEqual(rates.billable_lbs(3.2, 5, 5, 5), 4)

    def test_minimum_one_lb(self):
        self.assertEqual(rates.billable_lbs(0.2, 2, 2, 2), 1)


class DetectTests(unittest.TestCase):
    def line(self, s, **kw):
        lbs = kw.pop("lbs", rates.billable_lbs(s.actual_lbs, s.length, s.width, s.height))
        return make_line("L1", s.tracking, s.service, kw.pop("zone", s.zone), lbs,
                         kw.pop("res", s.residential), kw.pop("sig", s.signature),
                         kw.pop("fp", rates.FUEL_PCT))

    def test_clean_invoice_not_flagged(self):
        s = ship()
        self.assertEqual(detect([s], [self.line(s)]), [])

    def test_weight_overbill(self):
        s = ship()
        f = detect([s], [self.line(s, lbs=9)])
        self.assertEqual(f[0].types, "weight_overbill")
        self.assertGreater(f[0].overcharge, 0)

    def test_zone_misrate(self):
        s = ship()
        self.assertEqual(detect([s], [self.line(s, zone=5)])[0].types, "zone_misrate")

    def test_phantom_residential(self):
        s = ship()
        self.assertEqual(detect([s], [self.line(s, res=True)])[0].types, "phantom_accessorial")

    def test_fuel_overcharge(self):
        s = ship()
        self.assertEqual(detect([s], [self.line(s, fp=0.18)])[0].types, "fuel_overcharge")

    def test_duplicate_flags_second_line_only(self):
        s = ship()
        a, b = self.line(s), self.line(s)
        b.line_id = "L2"
        f = detect([s], [a, b])
        self.assertEqual([x.line_id for x in f], ["L2"])
        self.assertEqual(f[0].types, "duplicate_billing")

    def test_orphan(self):
        ghost = make_line("L9", "NOPE", "ground", 2, 5, False, False)
        self.assertEqual(detect([], [ghost])[0].types, "orphan_shipment")

    def test_late_express_must_be_credited(self):
        s = ship(service="express", days_late=2)
        self.assertEqual(detect([s], [self.line(s)])[0].types, "guarantee_not_credited")
        credited = make_line("L1", "T1", "express", 3, 1, False, False)
        credited.total = 0.0
        self.assertEqual(detect([s], [credited]), [])

    def test_underbilling_is_not_flagged(self):
        s = ship()
        self.assertEqual(detect([s], [self.line(s, lbs=1)]), [])


class EndToEnd(unittest.TestCase):
    def test_recovers_injected_anomalies(self):
        s, l, t = generate(n=3000, seed=11)
        f = detect(s, l)
        report = evaluate(f, t)
        self.assertIn("precision=1.000", report)
        self.assertIn("recall=1.000", report)

    def test_deterministic(self):
        a = generate(n=200, seed=3)
        b = generate(n=200, seed=3)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
