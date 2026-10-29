"""Univariate outlier detection methods (pure Python)."""
import math
import statistics


def _quantile(sorted_vals, q):
    pos = (len(sorted_vals) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def iqr_outliers(values, k=1.5):
    """Tukey fences: below Q1 - k*IQR or above Q3 + k*IQR. Returns (indices, (low, high))."""
    s = sorted(values)
    q1, q3 = _quantile(s, 0.25), _quantile(s, 0.75)
    lo, hi = q1 - k * (q3 - q1), q3 + k * (q3 - q1)
    return [i for i, v in enumerate(values) if v < lo or v > hi], (lo, hi)


def zscore_outliers(values, threshold=3.0):
    """|z| > threshold using mean and SD (sensitive to the outliers themselves)."""
    if len(values) < 3:
        return [], []
    m, s = statistics.fmean(values), statistics.stdev(values)
    if s == 0:
        return [], [0.0] * len(values)
    z = [(v - m) / s for v in values]
    return [i for i, x in enumerate(z) if abs(x) > threshold], z


def mad_outliers(values, threshold=3.5):
    """Modified z-score (Iglewicz & Hoaglin): 0.6745 * (x - median) / MAD, robust to outliers."""
    med = statistics.median(values)
    mad = statistics.median([abs(v - med) for v in values])
    if mad == 0:
        meanad = statistics.fmean([abs(v - med) for v in values])
        if meanad == 0:
            return [], [0.0] * len(values)
        mz = [(v - med) / (1.253314 * meanad) for v in values]
    else:
        mz = [0.6745 * (v - med) / mad for v in values]
    return [i for i, x in enumerate(mz) if abs(x) > threshold], mz


# Two-sided critical values of Grubbs' test at alpha = 0.05 for n = 3..30 (tabulated).
_GRUBBS_05 = {3: 1.155, 4: 1.481, 5: 1.715, 6: 1.887, 7: 2.020, 8: 2.126, 9: 2.215, 10: 2.290, 11: 2.355, 12: 2.412,
              13: 2.462, 14: 2.507, 15: 2.549, 16: 2.585, 17: 2.620, 18: 2.651, 19: 2.681, 20: 2.709, 21: 2.733,
              22: 2.758, 23: 2.781, 24: 2.802, 25: 2.822, 26: 2.841, 27: 2.859, 28: 2.876, 29: 2.893, 30: 2.908}


def _grubbs_critical(n):
    if n in _GRUBBS_05:
        return _GRUBBS_05[n]
    # large-n approximation via the normal quantile (adequate for n > 30)
    t = statistics.NormalDist().inv_cdf(1 - 0.05 / (2 * n))
    return (n - 1) / math.sqrt(n) * math.sqrt(t * t / (n - 2 + t * t))


def grubbs_test(values):
    """Iterative two-sided Grubbs test (alpha 0.05). Assumes approximate normality. Returns outlier indices."""
    idx = list(range(len(values)))
    out = []
    while len(idx) >= 3:
        vals = [values[i] for i in idx]
        m, s = statistics.fmean(vals), statistics.stdev(vals)
        if s == 0:
            break
        j = max(range(len(vals)), key=lambda k: abs(vals[k] - m))
        g = abs(vals[j] - m) / s
        if g > _grubbs_critical(len(vals)):
            out.append(idx.pop(j))
        else:
            break
    return sorted(out)


METHODS = {"iqr": lambda v, t: iqr_outliers(v, t or 1.5)[0], "z": lambda v, t: zscore_outliers(v, t or 3.0)[0],
           "mad": lambda v, t: mad_outliers(v, t or 3.5)[0], "grubbs": lambda v, t: grubbs_test(v)}


def flag_columns(header, rows, columns=None, method="mad", threshold=None, min_votes=1, methods=None):
    """Flag outliers in numeric columns. With methods=[...] a value is flagged when at least
    `min_votes` methods agree. Returns list of dicts: row (1-based data row), column, value, methods."""
    use = methods or [method]
    out = []
    for j, name in enumerate(header):
        if columns and name not in columns:
            continue
        pairs = []
        for i, r in enumerate(rows):
            try:
                pairs.append((i, float(r[j])))
            except (ValueError, IndexError):
                continue
        if len(pairs) < 4:
            continue
        vals = [v for _, v in pairs]
        votes = {}
        for m in use:
            for k in METHODS[m](vals, threshold):
                votes.setdefault(k, []).append(m)
        for k, ms in sorted(votes.items()):
            if len(ms) >= min_votes:
                out.append({"row": pairs[k][0] + 1, "column": name, "value": vals[k], "methods": ms})
    return out
