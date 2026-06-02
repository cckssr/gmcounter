"""GM Counter dead-time and statistics analyser.

Usage:
    python scripts/analyse_deadtime.py <file.csv> [options]
    python scripts/analyse_deadtime.py data.csv --plot
    python scripts/analyse_deadtime.py data.csv --plot results.png --bins 60
"""

import argparse
import csv
import math
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def load_csv(path: Path) -> list[float]:
    """Load inter-event times (µs) from a GMCounter CSV export."""
    values = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        val_col = 1
        for i, h in enumerate(header):
            if "value" in h.lower() or "µs" in h.lower() or "us" in h.lower():
                val_col = i
                break
        for row in reader:
            if len(row) > val_col:
                try:
                    v = float(row[val_col])
                    if v > 0:
                        values.append(v)
                except ValueError:
                    pass
    return values


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------


def percentile(sorted_values: list[float], p: float) -> float:
    n = len(sorted_values)
    i = (n - 1) * p / 100
    lo, hi = int(i), min(int(i) + 1, n - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (i - lo)


def basic_stats(values: list[float]) -> dict:
    n = len(values)
    s = sorted(values)
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(var)
    skew = (sum((x - mean) ** 3 for x in values) / n) / (std**3) if std > 0 else 0.0
    cv = std / mean  # coefficient of variation (=1 for pure exponential)

    return {
        "n": n,
        "min": s[0],
        "max": s[-1],
        "mean": mean,
        "median": percentile(s, 50),
        "std": std,
        "skew": skew,
        "cv": cv,
        "p1": percentile(s, 1),
        "p5": percentile(s, 5),
        "p25": percentile(s, 25),
        "p75": percentile(s, 75),
        "p95": percentile(s, 95),
        "p99": percentile(s, 99),
        "rate_cps": 1e6 / mean,
    }


# ---------------------------------------------------------------------------
# Dead-time estimation
# ---------------------------------------------------------------------------


def mle_shifted_exp(values: list[float]) -> tuple[float, float]:
    """Maximum-likelihood estimate for a shifted exponential (non-paralyzable model).

    The measured inter-arrival PDF is:
        f(t) = λ · exp(−λ(t − τ))   for t ≥ τ

    MLE:   τ̂ = min(tᵢ)  (biased; see bias_correction below)
           λ̂ = 1 / (mean(tᵢ) − τ̂)

    Returns (tau_µs, lambda_per_µs).
    """
    tau = min(values)
    lam = 1.0 / (sum(values) / len(values) - tau)
    return tau, lam


def bias_corrected_tau(tau: float, lam: float, n: int) -> float:
    """The MLE τ̂ = min(t) underestimates the true τ by ~1/(n·λ).

    Apply first-order bias correction.
    """
    return tau - 1.0 / (n * lam)


def deadtime_loss(measured_cps: float, tau_s: float) -> dict | None:
    """Non-paralyzable model.

    m = n / (1 + n·τ)  →  n = m / (1 - m·τ).
    Returns None if m·τ ≥ 1 (saturated detector).
    """
    if measured_cps * tau_s >= 1.0:
        return None
    true_cps = measured_cps / (1.0 - measured_cps * tau_s)
    loss_frac = (true_cps - measured_cps) / true_cps
    return {"true_cps": true_cps, "loss_frac": loss_frac}


def histogram_onset_tau(values: list[float], bins: int = 200) -> float:
    """Estimate dead time from the rising edge of the inter-arrival histogram.

    Finds the leftmost bin whose count exceeds 5 % of the peak bin.
    """
    mn, mx = min(values), max(values)
    w = (mx - mn) / bins
    counts = [0] * bins
    for v in values:
        i = min(int((v - mn) / w), bins - 1)
        counts[i] += 1
    peak = max(counts)
    threshold = peak * 0.05
    for i, c in enumerate(counts):
        if c >= threshold:
            return mn + i * w
    return mn


def reduced_chi2(values: list[float], tau: float, lam: float, bins: int = 60) -> float:
    """Reduced χ² of the shifted-exponential fit against the histogram."""
    n = len(values)
    mn, mx = min(values), max(values)
    w = (mx - mn) / bins
    observed = [0] * bins
    for v in values:
        i = min(int((v - mn) / w), bins - 1)
        observed[i] += 1

    chi2, dof = 0.0, 0
    for i, obs in enumerate(observed):
        t_lo = mn + i * w
        t_hi = t_lo + w
        if t_hi <= tau:
            continue
        t_lo_eff = max(t_lo, tau)
        expected = n * (
            math.exp(-lam * (t_lo_eff - tau)) - math.exp(-lam * (t_hi - tau))
        )
        if expected > 5:
            chi2 += (obs - expected) ** 2 / expected
            dof += 1

    return chi2 / max(dof - 2, 1)


# ---------------------------------------------------------------------------
# ASCII histogram
# ---------------------------------------------------------------------------


def ascii_histogram(values: list[float], bins: int = 40, bar_width: int = 50) -> str:
    mn, mx = min(values), max(values)
    w = (mx - mn) / bins
    counts = [0] * bins
    for v in values:
        i = min(int((v - mn) / w), bins - 1)
        counts[i] += 1
    peak = max(counts)
    lines = [f"  {'Range (µs)':<22}  {'Count':>7}  Bar"]
    lines.append("  " + "─" * 80)
    for i, c in enumerate(counts):
        lo = mn + i * w
        hi = lo + w
        bar = "█" * int(c / peak * bar_width)
        lines.append(f"  {lo:>9.0f} – {hi:<9.0f}  {c:>7,}  {bar}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Matplotlib plot (optional)
# ---------------------------------------------------------------------------


def render_plot(
    values: list[float], tau: float, lam: float, tau_bc: float, output: str | None
) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("  [matplotlib / numpy not installed — skipping plot]")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    n = len(values)

    for ax, log in zip(axes, [False, True]):
        ax.hist(
            values, bins=100, density=True, alpha=0.65, color="steelblue", label="Data"
        )
        t = np.linspace(tau, max(values), 800)
        pdf = lam * np.exp(-lam * (t - tau))
        ax.plot(
            t, pdf, "r-", lw=2, label=f"Shifted exp fit\nτ={tau:.1f} µs  λ={lam:.5g}/µs"
        )
        ax.axvline(
            tau, color="tomato", ls="--", lw=1.5, label=f"τ (MLE) = {tau:.1f} µs"
        )
        ax.axvline(
            tau_bc,
            color="orange",
            ls=":",
            lw=1.5,
            label=f"τ (bias-corr.) = {tau_bc:.1f} µs",
        )
        ax.set_xlabel("Inter-event time (µs)")
        ax.set_ylabel("Probability density" + (" (log)" if log else ""))
        ax.set_title("Inter-event time distribution" + (" — log scale" if log else ""))
        if log:
            ax.set_yscale("log")
        ax.legend(fontsize=8)

    plt.suptitle(f"GM Counter Dead-Time Analysis  —  n={n:,} events", fontsize=12)
    plt.tight_layout()

    if output:
        plt.savefig(output, dpi=150, bbox_inches="tight")
        print(f"  Saved plot: {output}")
    else:
        plt.show()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse GM counter inter-event CSV for dead-time and statistics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("csv", type=Path, help="Input CSV file (GMCounter export)")
    parser.add_argument(
        "--bins",
        type=int,
        default=40,
        metavar="N",
        help="Number of bins in ASCII histogram (default: 40)",
    )
    parser.add_argument(
        "--plot",
        nargs="?",
        const="",
        metavar="FILE",
        help="Show matplotlib plot (optionally save to FILE.png)",
    )
    parser.add_argument(
        "--no-ascii", action="store_true", help="Suppress ASCII histogram"
    )
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"Error: file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    # ── Load ──────────────────────────────────────────────────────────────
    print(f"\nLoading {args.csv} …")
    values = load_csv(args.csv)
    if not values:
        print("Error: no valid data found in file.", file=sys.stderr)
        sys.exit(1)
    print(f"Loaded {len(values):,} inter-event intervals.\n")

    # ── Basic statistics ───────────────────────────────────────────────────
    st = basic_stats(values)
    print("━" * 62)
    print("  BASIC STATISTICS")
    print("━" * 62)
    print(f"  Count               : {st['n']:>12,}")
    print(f"  Min          (µs)   : {st['min']:>12.3f}")
    print(f"  Max          (µs)   : {st['max']:>12.3f}")
    print(f"  Mean         (µs)   : {st['mean']:>12.3f}")
    print(f"  Median       (µs)   : {st['median']:>12.3f}")
    print(f"  Std dev      (µs)   : {st['std']:>12.3f}")
    print(f"  Coeff. of variation : {st['cv']:>12.4f}  (1.0 = pure Poisson)")
    print(f"  Skewness            : {st['skew']:>12.4f}")
    print()
    print(f"  Percentiles (µs):")
    print(
        f"    p1 / p5 / p25     : {st['p1']:>10.1f}  {st['p5']:>10.1f}  {st['p25']:>10.1f}"
    )
    print(
        f"    p75 / p95 / p99   : {st['p75']:>10.1f}  {st['p95']:>10.1f}  {st['p99']:>10.1f}"
    )
    print()
    print(f"  Observed mean rate  : {st['rate_cps']:>12.3f}  cps")

    # ── Dead-time estimation ───────────────────────────────────────────────
    tau_mle, lam = mle_shifted_exp(values)
    tau_bc = bias_corrected_tau(tau_mle, lam, st["n"])
    tau_hist = histogram_onset_tau(values)
    chi2r = reduced_chi2(values, tau_mle, lam)

    print()
    print("━" * 62)
    print("  DEAD-TIME ESTIMATION")
    print("━" * 62)
    print()
    print("  Model: non-paralyzable (Type I), shifted-exponential inter-arrival")
    print()
    print(f"  [A] MLE minimum-statistic")
    print(f"      τ̂  (biased)       = {tau_mle:>10.3f}  µs")
    print(f"      τ̂  (bias-correct) = {tau_bc:>10.3f}  µs  [recommended]")
    print(f"      λ̂  (true rate)    = {lam:>10.6f} /µs  =  {lam * 1e6:,.2f} cps")
    print()
    print(f"  [B] Histogram onset (5 % of peak)")
    print(f"      τ estimate        = {tau_hist:>10.3f}  µs")
    print()
    print(f"  Reduced χ² of shifted-exp fit : {chi2r:.3f}")
    if chi2r < 2.0:
        verdict = "good fit — non-paralyzable model is consistent"
    elif chi2r < 5.0:
        verdict = "moderate fit — slight deviation (pile-up, paralysis, or multi-mode?)"
    else:
        verdict = "poor fit — model may not apply; consider paralyzable model"
    print(f"  Verdict: {verdict}")

    # ── Dead-time loss correction ──────────────────────────────────────────
    print()
    print("━" * 62)
    print("  RATE CORRECTION  (non-paralyzable, τ = bias-corrected MLE)")
    print("━" * 62)
    tau_s = tau_bc * 1e-6
    result = deadtime_loss(st["rate_cps"], tau_s)
    if result:
        print(f"  Measured rate  m    = {st['rate_cps']:>12.3f}  cps")
        print(
            f"  True rate      n    = {result['true_cps']:>12.3f}  cps  [n = m/(1−m·τ)]"
        )
        print(f"  Dead-time loss      = {result['loss_frac'] * 100:>11.3f}  %")
        print(f"  Correction factor   = {result['true_cps'] / st['rate_cps']:>12.4f}x")
    else:
        print("  Detector appears saturated (m·τ ≥ 1); correction not applicable.")

    # ── Poisson-process test ───────────────────────────────────────────────
    print()
    print("━" * 62)
    print("  POISSON-PROCESS DIAGNOSTICS")
    print("━" * 62)
    cv_dev = abs(st["cv"] - 1.0)
    print(f"  Coeff. of variation CV = {st['cv']:.4f}  (ideal Poisson: 1.000)")
    print(f"  |CV − 1|               = {cv_dev:.4f}")
    if cv_dev < 0.05:
        print("  => Consistent with a Poisson process.")
    elif cv_dev < 0.15:
        print("  => Slight departure from Poisson (dead-time or pile-up effect).")
    else:
        print("  => Significant departure from Poisson — check source/setup.")

    # ── ASCII histogram ────────────────────────────────────────────────────
    if not args.no_ascii:
        print()
        print("━" * 62)
        print("  INTER-EVENT TIME DISTRIBUTION")
        print("━" * 62)
        print(ascii_histogram(values, bins=args.bins))

    # ── Plot ───────────────────────────────────────────────────────────────
    if args.plot is not None:
        print()
        print("━" * 62)
        print("  PLOT")
        print("━" * 62)
        output = args.plot if args.plot else None
        render_plot(values, tau_mle, lam, tau_bc, output)

    print()


if __name__ == "__main__":
    main()
