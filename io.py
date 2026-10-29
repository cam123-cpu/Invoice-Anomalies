import csv
import dataclasses


def write_csv(path, rows, cls):
    cols = [f.name for f in dataclasses.fields(cls)]
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([getattr(r, c) for c in cols])


def _convert(value, typ):
    if typ is bool:
        return value == "True"
    return typ(value)


def read_csv(path, cls):
    fields = dataclasses.fields(cls)
    with open(path, newline="") as fh:
        return [
            cls(**{f.name: _convert(row[f.name], f.type) for f in fields})
            for row in csv.DictReader(fh)
        ]
