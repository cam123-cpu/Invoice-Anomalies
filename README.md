# invoice-anomaly-detector

Audit carrier invoices against shipment records and surface overcharges, ranked by dollar impact.
Runs entirely on **synthetic data** (fictional rate card, generated shipments); no employer data or logic is included.

## Quickstart (Python 3.9+, no dependencies)
```bash
python -m anomaly generate --n 5000 --seed 7   # writes data/{shipments,invoices,truth}.csv
python -m anomaly detect --evaluate            # writes data/findings.csv + prints report
python -m unittest discover -s tests -t .
```

## How it works
1. **Generator** builds shipments and a correct invoice for each, then injects errors at ~8%: weight overbilling,
   zone mis-rating, phantom accessorials, inflated fuel surcharge, duplicate billing, invoices for shipments that
   don't exist, and late express deliveries that should have been refunded.
2. **Detector** recomputes the expected cost of every shipment (dimensional vs. actual weight, zone rate, fuel,
   accessorials), flags lines that exceed it by more than a 2-cent rounding tolerance, and attributes root causes.
3. **Report** groups disputable dollars by cause and shows a Pareto cut (how many disputes cover 80% of the money).
4. **Evaluation** scores detection against injected ground truth (precision, recall, root-cause accuracy, dollar recall).

## Honest limitations
- Scores are ~1.0 because the detector and generator share the same rate logic. That is a correctness check,
  not a claim about real-world accuracy. Real invoices have messy data, contract-specific discounts, and
  carrier-side rounding rules.
- Rule-based only. Natural next steps: noisy/ambiguous cases, per-customer discount tiers, a statistical layer
  (e.g. robust z-scores on charge-per-lb by lane) for errors with no rule, and a dispute-priority score that
  weighs dollar value against likelihood of recovery.

## Ideas to extend
- Add "benign noise" (rounding variance, address corrections) and measure the precision/recall tradeoff.
- Carrier contract versions with effective dates.
- A small web UI or Streamlit dashboard for findings.
