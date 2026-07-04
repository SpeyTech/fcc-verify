"""fccverify.exact: exact arithmetic for the verdict path (requirement 3).

Chair-ratified: Python 3 stdlib only, fractions.Fraction in the verdict path,
floats forbidden here. Floats are permitted only in display formatting, never
in a comparison that decides a verdict.

The verdict path needs two things and both are exact rational computations:

  1. The Clopper-Pearson two-sided interval on the success probability p at a
     committed level alpha', to be compared against band edges after the
     A = 2p - 1 transform.

  2. Decidability of "the CP interval is disjoint from the asserted region S"
     without quantile inversion. This is the key move: rather than invert the
     Beta/F quantile (which forces floats), we test the defining inequality of
     the Clopper-Pearson bound directly as a binomial tail sum compared to
     alpha'/2. Both sides are exact rationals, so the comparison is exact.

Clopper-Pearson definition (two-sided, level alpha, k successes in n trials):

  lower bound p_lo is the p solving  sum_{i=k}^{n} C(n,i) p^i (1-p)^(n-i) = a/2
  upper bound p_hi is the p solving  sum_{i=0}^{k} C(n,i) p^i (1-p)^(n-i) = a/2

with p_lo = 0 when k = 0 and p_hi = 1 when k = n.

We never solve for p_lo or p_hi as numbers. To decide a categorical verdict we
only need to know which side of a rational threshold p* the bound lies, and the
tail sum is monotone in p, so:

  p_lo > p*    iff    sum_{i=k}^{n} C(n,i) p*^i (1-p*)^(n-i) > a/2
  p_hi < p*    iff    sum_{i=0}^{k} C(n,i) p*^i (1-p*)^(n-i) > a/2

Each tail sum at a rational p* is an exact Fraction. That is the whole trick:
a verdict is a finite set of exact rational inequalities, no root-finding.

The band on A = 2p - 1 is (-delta, +delta), i.e. p in (p_minus, p_plus) with
p_minus = (1 - delta)/2 and p_plus = (1 + delta)/2. The asserted region S and
its complement are unions of such p-intervals, and disjointness is decided by
the tail-sum inequalities above at the band-edge thresholds.
"""

from fractions import Fraction
from math import comb


def binom_pmf(n: int, k: int, p: Fraction) -> Fraction:
    """Exact C(n,k) p^k (1-p)^(n-k) as a Fraction."""
    return Fraction(comb(n, k)) * (p ** k) * ((1 - p) ** (n - k))


def binom_upper_tail(n: int, k: int, p: Fraction) -> Fraction:
    """sum_{i=k}^{n} C(n,i) p^i (1-p)^(n-i), exact."""
    total = Fraction(0)
    for i in range(k, n + 1):
        total += binom_pmf(n, i, p)
    return total


def binom_lower_tail(n: int, k: int, p: Fraction) -> Fraction:
    """sum_{i=0}^{k} C(n,i) p^i (1-p)^(n-i), exact."""
    total = Fraction(0)
    for i in range(0, k + 1):
        total += binom_pmf(n, i, p)
    return total


def cp_lower_gt(k: int, n: int, p_star: Fraction, alpha: Fraction) -> bool:
    """True iff the Clopper-Pearson lower bound p_lo(k, n, alpha) > p_star.

    p_lo is defined by upper_tail(k..n at p_lo) = alpha/2. The upper tail is
    increasing in p, so for p_star < p_lo the tail is below alpha/2, and for
    p_star > p_lo it is above. Hence p_lo > p_star iff upper_tail at p_star
    < alpha/2. At k = 0, p_lo = 0, so p_lo > p_star is False for p_star >= 0.
    """
    if k == 0:
        return False
    return binom_upper_tail(n, k, p_star) < alpha / 2


def cp_upper_lt(k: int, n: int, p_star: Fraction, alpha: Fraction) -> bool:
    """True iff the Clopper-Pearson upper bound p_hi(k, n, alpha) < p_star.

    p_hi is defined by lower_tail(0..k at p_hi) = alpha/2. The lower tail is
    decreasing in p, so for p_star > p_hi the tail is below alpha/2, and for
    p_star < p_hi it is above. Hence p_hi < p_star iff lower_tail at p_star
    < alpha/2. At k = n, p_hi = 1, so p_hi < p_star is False for p_star <= 1.
    """
    if k == n:
        return False
    return binom_lower_tail(n, k, p_star) < alpha / 2


def band_edges_p(delta: Fraction):
    """The band (-delta, +delta) on A maps to (p_minus, p_plus) on p via
    A = 2p - 1, so p = (A + 1)/2."""
    p_minus = (1 - delta) / 2
    p_plus = (1 + delta) / 2
    return p_minus, p_plus


def a_from_p(p: Fraction) -> Fraction:
    return 2 * p - 1


def ci_disjoint_from_band(k, n, p_minus, p_plus, alpha):
    """True iff the CP interval CI'(k,n,alpha) is disjoint from the closed
    band [p_minus, p_plus], i.e. entirely below p_minus or entirely above
    p_plus. Used for a NULL claim, whose asserted region S is the band.

    Disjoint below: p_hi < p_minus. Disjoint above: p_lo > p_plus.
    Boundary convention: interval contact with the band is NOT disjoint
    (adjudicates toward the claimant), so the comparisons are strict and use
    the same cp_*_lt / cp_*_gt primitives the rest of the path uses.
    """
    return cp_upper_lt(k, n, p_minus, alpha) or cp_lower_gt(k, n, p_plus, alpha)


def ci_disjoint_from_upper(k, n, p_plus, alpha):
    """True iff CI'(k,n,alpha) is disjoint from S = (p_plus, 1], the region a
    THREAT-EXISTS(+) claimant asserts. Disjoint means CI' lies at or below
    p_plus: p_hi < p_plus (strict; contact adjudicates toward the claimant,
    i.e. not disjoint, i.e. UPHELD)."""
    return cp_upper_lt(k, n, p_plus, alpha)


def ci_disjoint_from_lower(k, n, p_minus, alpha):
    """True iff CI'(k,n,alpha) is disjoint from S = [0, p_minus), the region a
    THREAT-EXISTS(-) claimant asserts. Disjoint means CI' lies at or above
    p_minus: p_lo > p_minus (strict)."""
    return cp_lower_gt(k, n, p_minus, alpha)
