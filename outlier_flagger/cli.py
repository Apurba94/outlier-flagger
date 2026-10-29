"""Command-line interface for outlier-flagger."""
import argparse
import csv
import json
import sys

from .core import METHODS, flag_columns


def main(argv=None):
    ap = argparse.ArgumentParser(prog="outlier-flagger", description="Flag outliers in numeric CSV columns.")
    ap.add_argument("csvfile")
    ap.add_argument("-c", "--column", action="append", help="only these columns (repeatable)")
    ap.add_argument("-m", "--method", action="append", choices=sorted(METHODS),
                    help="method(s): iqr, z, mad (default), grubbs; repeat to combine")
    ap.add_argument("-t", "--threshold", type=float, help="method threshold (k for IQR, |z| for z/mad)")
    ap.add_argument("--votes", type=int, default=1, help="minimum number of methods that must agree")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--mark", help="write a copy of the CSV with an 'outlier_flags' column")
    args = ap.parse_args(argv)
    with open(args.csvfile, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    methods = args.method or ["mad"]
    flags = flag_columns(header, data, args.column, methods=methods, threshold=args.threshold, min_votes=args.votes)
    if args.json:
        print(json.dumps(flags, indent=2))
    else:
        for f in flags:
            print("row %-5d %-20s %12g  [%s]" % (f["row"], f["column"], f["value"], ",".join(f["methods"])))
        print("%d outlier value(s) flagged with %s" % (len(flags), "+".join(methods)), file=sys.stderr)
    if args.mark:
        by_row = {}
        for f in flags:
            by_row.setdefault(f["row"], []).append(f["column"])
        with open(args.mark, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(header + ["outlier_flags"])
            for i, r in enumerate(data, 1):
                w.writerow(r + [";".join(by_row.get(i, []))])
    return 0
