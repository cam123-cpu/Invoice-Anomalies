from collections import defaultdict


def summarize(findings, total_billed):
    over = sum(f.overcharge for f in findings)
    by_type = defaultdict(lambda: [0, 0.0])
    for f in findings:
        by_type[f.types][0] += 1
        by_type[f.types][1] += f.overcharge
    out = [f"Billed: ${total_billed:,.2f} | Flagged lines: {len(findings)} | "
           f"Disputable: ${over:,.2f} ({over / total_billed:.2%} of spend)", "",
           f"{'root cause':<28}{'lines':>7}{'$ overcharge':>15}"]
    for t, (n, d) in sorted(by_type.items(), key=lambda kv: -kv[1][1]):
        out.append(f"{t:<28}{n:>7}{d:>15,.2f}")
    # Pareto: how many disputes capture 80% of the dollars?
    running, target = 0.0, 0.8 * over
    for i, f in enumerate(findings, 1):
        running += f.overcharge
        if running >= target:
            out.append(f"\nTop {i} of {len(findings)} findings capture 80% of recoverable dollars.")
            break
    return "\n".join(out)


def evaluate(findings, truth):
    pred = {f.line_id: f for f in findings}
    true = {t.line_id: t for t in truth}
    tp = set(pred) & set(true)
    precision = len(tp) / len(pred) if pred else 1.0
    recall = len(tp) / len(true) if true else 1.0
    type_ok = sum(true[i].anomaly in pred[i].types.split("|") for i in tp)
    dollars = sum(true[i].overcharge for i in tp) / (sum(t.overcharge for t in truth) or 1)
    out = [f"precision={precision:.3f} recall={recall:.3f} "
           f"root-cause accuracy={type_ok / len(tp) if tp else 1:.3f} "
           f"dollar recall={dollars:.3f}", "", "per-type recall:"]
    per = defaultdict(lambda: [0, 0])
    for t in truth:
        per[t.anomaly][1] += 1
        per[t.anomaly][0] += t.line_id in pred
    for k, (hit, tot) in sorted(per.items()):
        out.append(f"  {k:<26}{hit}/{tot}")
    return "\n".join(out)
