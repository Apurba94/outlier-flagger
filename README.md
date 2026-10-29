# outlier-flagger

**Flag suspicious values in your data with four standard methods (Tukey IQR fences, z-score,
robust modified z-score, Grubbs' test), combine them by voting, and mark the rows for review.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Outliers can be data-entry errors, instrument faults or genuine discoveries; either way they must
be examined and the decision documented before analysis. Ad-hoc thresholds chosen after seeing the
results are a reproducibility problem. Declaring the method and threshold up front, in a script,
makes the procedure transparent and repeatable.

## Methods

| Method | Rule | Notes |
|--------|------|-------|
| `iqr` | outside Q1 - k IQR, Q3 + k IQR (k = 1.5) | distribution-free (Tukey) |
| `z` | abs(z) > 3 | suffers from masking in small samples (the outlier inflates the SD) |
| `mad` | abs(modified z) > 3.5 | robust, uses median and MAD (Iglewicz & Hoaglin) |
| `grubbs` | iterative Grubbs test, alpha = 0.05 | assumes normality |

Combine with `-m iqr -m mad -m grubbs --votes 2` for a conservative consensus.

## Usage

```bash
pip install .
outlier-flagger measurements.csv                       # MAD on all numeric columns
outlier-flagger data.csv -c reaction_time -m iqr -t 3  # extreme outliers only
outlier-flagger data.csv -m iqr -m mad -m z --votes 2 --mark flagged.csv
```

Flagged values are for **review**, never automatic deletion; report how outliers were handled.

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
