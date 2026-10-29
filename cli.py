import argparse
import os

from . import generate as gen
from .detect import detect
from .io import read_csv, write_csv
from .models import Finding, InvoiceLine, Shipment, Truth
from .report import evaluate, summarize


def main(argv=None):
    p = argparse.ArgumentParser(prog="anomaly", description="Carrier invoice audit toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="create synthetic shipments/invoices")
    g.add_argument("--n", type=int, default=5000)
    g.add_argument("--seed", type=int, default=7)
    g.add_argument("--rate", type=float, default=0.08)
    g.add_argument("--out", default="data")
    d = sub.add_parser("detect", help="audit invoices against shipments")
    d.add_argument("--data", default="data")
    d.add_argument("--evaluate", action="store_true", help="score against truth.csv")
    a = p.parse_args(argv)

    if a.cmd == "generate":
        os.makedirs(a.out, exist_ok=True)
        s, l, t = gen.generate(a.n, a.seed, a.rate)
        write_csv(f"{a.out}/shipments.csv", s, Shipment)
        write_csv(f"{a.out}/invoices.csv", l, InvoiceLine)
        write_csv(f"{a.out}/truth.csv", t, Truth)
        print(f"wrote {len(s)} shipments, {len(l)} invoice lines, {len(t)} injected anomalies")
    else:
        s = read_csv(f"{a.data}/shipments.csv", Shipment)
        l = read_csv(f"{a.data}/invoices.csv", InvoiceLine)
        f = detect(s, l)
        write_csv(f"{a.data}/findings.csv", f, Finding)
        print(summarize(f, sum(x.total for x in l)))
        if a.evaluate:
            print("\n" + evaluate(f, read_csv(f"{a.data}/truth.csv", Truth)))


if __name__ == "__main__":
    main()
