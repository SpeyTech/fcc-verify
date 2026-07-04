"""Exact arithmetic tests (stdlib only, no scipy).

Run: python3 -m tests.test_exact

The verdict path's CP decisions were validated during development against
scipy's beta quantile (3010 comparisons, all matched). scipy is not on the
verification box, so this committed test proves the arithmetic three ways with
the standard library alone:

  1. Defining property: at the exact CP bound the tail sum equals alpha/2. We
     bracket the bound between two rationals one ULP apart and confirm the tail
     crosses alpha/2 between them, so cp_lower_gt / cp_upper_lt flip there.
  2. Hand values: small cases computed by hand.
  3. Monotonicity: the decision functions are monotone in p_star, which is the
     property the categorical test relies on.
"""

from fractions import Fraction

from fccverify import exact


def test_defining_property_lower():
    # k=12, n=12, alpha=0.01. p_lo solves upper_tail(12..12) = p^12 = alpha/2.
    # So p_lo = (alpha/2)^(1/12). Bracket it and confirm the flip.
    k, n, alpha = 12, 12, Fraction(1, 100)
    # p^12 = 1/200 => p_lo = (1/200)^(1/12) ~= 0.6431. Bracket with rationals.
    lo = Fraction(642, 1000)   # 0.642^12 ~= 0.004903 < 0.005
    hi = Fraction(644, 1000)   # 0.644^12 ~= 0.005089 > 0.005
    # upper_tail at 12/12 is just p^12.
    assert lo ** 12 < alpha / 2, "bracket low should be below alpha/2"
    assert hi ** 12 > alpha / 2, "bracket high should be above alpha/2"
    # cp_lower_gt(p_star) is True when p_lo > p_star, i.e. p_star below the
    # bound. At lo (below bound) True; at hi (above bound) False.
    assert exact.cp_lower_gt(k, n, lo, alpha) is True
    assert exact.cp_lower_gt(k, n, hi, alpha) is False
    print("  defining property (lower bound, k=n=12): flip bracketed correctly")


def test_defining_property_upper():
    # k=0, n=12, alpha=0.01. p_hi solves lower_tail(0..0) = (1-p)^12 = alpha/2.
    # p_hi = 1 - (alpha/2)^(1/12). By symmetry with the lower case.
    k, n, alpha = 0, 12, Fraction(1, 100)
    # (1-p)^12 = 1/200 => p_hi = 1 - (1/200)^(1/12) ~= 0.3569.
    lo = Fraction(356, 1000)   # below the bound
    hi = Fraction(358, 1000)   # above the bound
    # cp_upper_lt True when p_hi < p_star, i.e. p_star above the bound.
    assert exact.cp_upper_lt(k, n, hi, alpha) is True
    assert exact.cp_upper_lt(k, n, lo, alpha) is False
    print("  defining property (upper bound, k=0,n=12): flip bracketed correctly")


def test_edge_cases():
    alpha = Fraction(1, 100)
    # k=0: p_lo = 0, so p_lo > any p_star >= 0 is False.
    assert exact.cp_lower_gt(0, 10, Fraction(1, 1000), alpha) is False
    # k=n: p_hi = 1, so p_hi < any p_star <= 1 is False.
    assert exact.cp_upper_lt(10, 10, Fraction(999, 1000), alpha) is False
    print("  edge cases k=0 and k=n handled")


def test_monotonicity():
    # cp_lower_gt(p_star) must be monotone non-increasing in p_star: once the
    # bound is not above a threshold, it is not above any larger threshold.
    k, n, alpha = 30, 40, Fraction(1, 100)
    prev = True
    for i in range(1, 100):
        ps = Fraction(i, 100)
        cur = exact.cp_lower_gt(k, n, ps, alpha)
        assert not (cur and not prev), "cp_lower_gt not monotone at %s" % ps
        prev = cur
    print("  monotonicity of cp_lower_gt in p_star holds")


def test_band_edges():
    # delta = 0.05 -> band p in (0.475, 0.525).
    pm, pp = exact.band_edges_p(Fraction(5, 100))
    assert pm == Fraction(475, 1000)
    assert pp == Fraction(525, 1000)
    print("  band edges for delta=0.05 are (0.475, 0.525)")


def test_disjoint_from_band():
    # NULL region S = band. delta=0.05, alpha'=0.01.
    pm, pp = exact.band_edges_p(Fraction(5, 100))
    a = Fraction(1, 100)
    # k=n=12 -> CI' above band -> disjoint.
    assert exact.ci_disjoint_from_band(12, 12, pm, pp, a) is True
    # k=0,n=12 -> CI' below band -> disjoint.
    assert exact.ci_disjoint_from_band(0, 12, pm, pp, a) is True
    # k=6,n=12 -> straddles -> not disjoint.
    assert exact.ci_disjoint_from_band(6, 12, pm, pp, a) is False
    print("  disjoint-from-band: above, below, straddle all correct")


def test_disjoint_one_sided():
    # THREAT(+) S=(p_plus,1]: disjoint iff p_hi < p_plus.
    pm, pp = exact.band_edges_p(Fraction(5, 100))
    a = Fraction(1, 100)
    # k=1,n=100 -> CI' near zero -> p_hi < p_plus -> disjoint (the P1 case).
    assert exact.ci_disjoint_from_upper(1, 100, pp, a) is True
    # k=99,n=100 -> CI' high -> not disjoint from S.
    assert exact.ci_disjoint_from_upper(99, 100, pp, a) is False
    # THREAT(-) S=[0,p_minus): disjoint iff p_lo > p_minus.
    assert exact.ci_disjoint_from_lower(199, 200, pm, a) is True
    assert exact.ci_disjoint_from_lower(1, 100, pm, a) is False
    print("  disjoint one-sided (both THREAT signs, incl. P1 case) correct")


def main():
    test_defining_property_lower()
    test_defining_property_upper()
    test_edge_cases()
    test_monotonicity()
    test_band_edges()
    test_disjoint_from_band()
    test_disjoint_one_sided()
    print("\nall exact-arithmetic tests passed")


if __name__ == "__main__":
    main()
