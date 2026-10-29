import csv
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from outlier_flagger.cli import main
from outlier_flagger.core import flag_columns, grubbs_test, iqr_outliers, mad_outliers, zscore_outliers

DATA = [10.0, 11.0, 9.5, 10.2, 10.8, 9.9, 10.1, 10.4, 35.0, 10.3]


class MethodTests(unittest.TestCase):
    def test_iqr(self):
        idx, (lo, hi) = iqr_outliers(DATA)
        self.assertEqual(idx, [8])
        self.assertLess(hi, 35)

    def test_zscore_masking_effect(self):
        # with n=10 a single outlier cannot exceed |z|=3 (max is (n-1)/sqrt(n)=2.85): z-score misses it
        self.assertEqual(zscore_outliers(DATA)[0], [])
        self.assertEqual(zscore_outliers(DATA, 2.5)[0], [8])

    def test_mad_is_robust(self):
        idx, mz = mad_outliers(DATA)
        self.assertEqual(idx, [8])
        self.assertGreater(mz[8], 3.5)

    def test_grubbs(self):
        self.assertEqual(grubbs_test(DATA), [8])
        self.assertEqual(grubbs_test([1, 2, 3, 4, 5]), [])

    def test_constant_values(self):
        self.assertEqual(mad_outliers([5, 5, 5, 5])[0], [])
        self.assertEqual(zscore_outliers([5, 5, 5, 5])[0], [])


class ColumnTests(unittest.TestCase):
    def test_flag_columns_with_votes(self):
        header = ["id", "x", "y"]
        rows = [[str(i), str(v), "1"] for i, v in enumerate(DATA)] + [["10", "NA", "1"]]
        flags = flag_columns(header, rows, methods=["iqr", "mad", "z"], min_votes=2)
        self.assertEqual([(f["row"], f["column"], f["methods"]) for f in flags], [(9, "x", ["iqr", "mad"])])

    def test_cli_mark(self):
        with tempfile.TemporaryDirectory() as d:
            p, out = os.path.join(d, "d.csv"), os.path.join(d, "marked.csv")
            with open(p, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["x"])
                w.writerows([[v] for v in DATA])
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                main([p, "-m", "iqr", "--mark", out])
            with open(out, encoding="utf-8") as fh:
                marked = list(csv.reader(fh))
            self.assertEqual(marked[9], ["35.0", "x"])


if __name__ == "__main__":
    unittest.main()
