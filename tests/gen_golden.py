"""Generate the golden vector chains into golden/ and assert each verdict.

Run: python3 -m tests.gen_golden           (write vectors + manifest)
     python3 -m tests.gen_golden --check    (CI tamper gate: bytes must match)

Every vector's expected verdict is hand-derived in VECTORS.md and asserted here
against the verifier. A vector that does not produce its expected verdict, or a
committed .bin that drifts from the generator, is a build failure.
"""

import json
import os

from fccverify import buildvec, verdict

GOLDEN = os.path.join(os.path.dirname(__file__), "..", "golden")

D_NUM, D_DEN = 5, 100      # delta = 0.05  -> band p in (0.475, 0.525)
AP_NUM, AP_DEN = 1, 100    # alpha' = 0.01


def _write(name, data):
    os.makedirs(GOLDEN, exist_ok=True)
    with open(os.path.join(GOLDEN, name), "wb") as fh:
        fh.write(data)


def _null_claim():
    return buildvec.claim_c_payload("NULL", D_NUM, D_DEN,
                                    alpha_prime_num=AP_NUM,
                                    alpha_prime_den=AP_DEN)


def _threat_claim(sign):
    return buildvec.claim_c_payload("THREAT-EXISTS", D_NUM, D_DEN, sign=sign,
                                    alpha_prime_num=AP_NUM,
                                    alpha_prime_den=AP_DEN)


def _pair(c_payload, k, n, **kw):
    """A (claim_chain, refuter_chain) pair for a categorical vector."""
    claim = buildvec.build_claim_chain(c_payload)
    ch = buildvec.claim_c_hash_of(c_payload)
    ref = buildvec.build_refuter_chain(ch, k, n,
                                       alpha_prime_num=AP_NUM,
                                       alpha_prime_den=AP_DEN, **kw)
    return claim, ref


def vectors():
    """Yield (name, claim_bytes, refuter_bytes, attempt_count, expected_verdict,
    expected_cause, note)."""

    # --- Categorical: NULL ---
    claim, ref = _pair(_null_claim(), 6, 12)
    yield ("v01_upheld_null.bin", claim, ref, 1, "UPHELD", None,
           "NULL, refuter CI' straddles band, unrefuted")

    claim, ref = _pair(_null_claim(), 12, 12)
    yield ("v02_refuted_null_positive.bin", claim, ref, 1, "REFUTED", None,
           "NULL, refuter CI' entirely above band, positive effect")

    claim, ref = _pair(_null_claim(), 0, 12)
    yield ("v03_refuted_null_negative.bin", claim, ref, 1, "REFUTED", None,
           "NULL, refuter CI' entirely below band, negative effect")

    claim, ref = _pair(_null_claim(), 8, 9)
    yield ("v04_boundary_upheld.bin", claim, ref, 1, "UPHELD", None,
           "refuter interval overlaps band by one trial: UPHELD not REFUTED")

    # --- Categorical: THREAT-EXISTS(+) ---
    claim, ref = _pair(_threat_claim("+"), 99, 100)
    yield ("v05_upheld_threat_pos.bin", claim, ref, 1, "UPHELD", None,
           "THREAT(+), refuter confirms effect, CI' meets S=(p_plus,1]")

    # P1 vector: opposite-side REFUTED (the resurrected S2 hole).
    claim, ref = _pair(_threat_claim("+"), 1, 100)
    yield ("v06_refuted_threat_pos_opposite.bin", claim, ref, 1,
           "REFUTED", None,
           "THREAT(+), CI' entirely below band, disjoint from S: REFUTED")

    # P1 vector: band-overlapping but disjoint from S, REFUTED.
    claim, ref = _pair(_threat_claim("+"), 77, 200)
    yield ("v07_refuted_threat_pos_overlap.bin", claim, ref, 1,
           "REFUTED", None,
           "THREAT(+), CI' overlaps band yet disjoint from S=(p_plus,1]: REFUTED")

    # --- Categorical: THREAT-EXISTS(-) ---
    claim, ref = _pair(_threat_claim("-"), 1, 100)
    yield ("v08_upheld_threat_neg.bin", claim, ref, 1, "UPHELD", None,
           "THREAT(-), refuter confirms negative effect, CI' meets S=[0,p_minus)")

    claim, ref = _pair(_threat_claim("-"), 199, 200)
    yield ("v09_refuted_threat_neg_opposite.bin", claim, ref, 1,
           "REFUTED", None,
           "THREAT(-), CI' entirely above band, disjoint from S: REFUTED")

    # --- INVALID-CLAIM ---
    claim, _ = _pair(_null_claim(), 6, 12)
    bad = bytearray(claim)
    bad[-1] ^= 0x01
    yield ("v10_invalid_claim_fabrication.bin", bytes(bad), None, None,
           "INVALID-CLAIM", "FABRICATION",
           "bit-flipped commit: claim chain does not replay")

    rogue = buildvec.build_chain([
        (buildvec.TAG_STATE, b'{"state":"open"}'),
        (b"AX:ROGUE:v1", b'{"x":1}'),
        (buildvec.TAG_FCC_C, _null_claim()),
    ])
    yield ("v11_invalid_claim_unregistered.bin", rogue, None, None,
           "INVALID-CLAIM", "MALFORMED",
           "unregistered tag AX:ROGUE:v1 on the claim chain")

    full = json.loads(_null_claim())
    del full["w_min"]
    short = buildvec._canon(full)
    chain = buildvec.build_chain([
        (buildvec.TAG_STATE, b'{"state":"open"}'),
        (buildvec.TAG_FCC_C, short)])
    yield ("v12_invalid_claim_missing_field.bin", chain, None, None,
           "INVALID-CLAIM", "MALFORMED", "C missing w_min: field closure fails")

    chain = buildvec.build_chain([
        (buildvec.TAG_STATE, b'{"state":"open"}')])
    yield ("v13_invalid_claim_no_commitment.bin", chain, None, None,
           "INVALID-CLAIM", "MALFORMED", "no AX:FCC:C:v1 record present")

    # --- INVALID-ATTEMPT (stage 2) ---
    # UNREGISTERED: attempt carries an off-registry tag.
    c = _null_claim()
    claim = buildvec.build_claim_chain(c)
    ch = buildvec.claim_c_hash_of(c)
    ref = buildvec.build_refuter_chain(ch, 6, 12)
    # splice a rogue frame into the refuter chain
    rogue_ref = (buildvec.frame_bytes(buildvec.TAG_STATE, b'{"state":"refuter"}')
                 + buildvec.frame_bytes(b"AX:ROGUE:v1", b'{"y":1}')
                 + ref[len(buildvec.frame_bytes(buildvec.TAG_STATE,
                                                b'{"state":"refuter"}')):])
    yield ("v14_invalid_attempt_unregistered.bin", claim, rogue_ref, 1,
           "INVALID-ATTEMPT", "UNREGISTERED",
           "attempt carries unregistered tag AX:ROGUE:v1")

    # INCOMPLETE: observed n below the attempt's own committed N'.
    c = _null_claim()
    claim = buildvec.build_claim_chain(c)
    ch = buildvec.claim_c_hash_of(c)
    ref = buildvec.build_refuter_chain(ch, 6, 12, n_prime=100)
    yield ("v15_invalid_attempt_incomplete.bin", claim, ref, 1,
           "INVALID-ATTEMPT", "INCOMPLETE",
           "observed n=12 below committed N'=100")

    # SNAPSHOT-MISMATCH: no fingerprint bracket.
    c = _null_claim()
    claim = buildvec.build_claim_chain(c)
    ch = buildvec.claim_c_hash_of(c)
    ref = buildvec.build_refuter_chain(ch, 6, 12, with_bracket=False)
    yield ("v16_invalid_attempt_snapshot.bin", claim, ref, 1,
           "INVALID-ATTEMPT", "SNAPSHOT-MISMATCH",
           "attempt missing fingerprint bracket (start/end)")

    # FABRICATION: genesis binds the wrong C hash.
    c = _null_claim()
    claim = buildvec.build_claim_chain(c)
    ch = buildvec.claim_c_hash_of(c)
    ref = buildvec.build_refuter_chain(ch, 6, 12,
                                       override_c_hash="00" * 32)
    yield ("v17_invalid_attempt_binding.bin", claim, ref, 1,
           "INVALID-ATTEMPT", "FABRICATION",
           "genesis claim_c_hash does not match the claimant C")

    # FABRICATION: alpha' level-shop (refuter echoes a different alpha').
    c = _null_claim()
    claim = buildvec.build_claim_chain(c)
    ch = buildvec.claim_c_hash_of(c)
    ref = buildvec.build_refuter_chain(ch, 6, 12,
                                       alpha_prime_num=1, alpha_prime_den=2)
    yield ("v18_invalid_attempt_alpha_shop.bin", claim, ref, 1,
           "INVALID-ATTEMPT", "FABRICATION",
           "refuter alpha'=1/2 != claimant committed alpha'=1/100")

    # FABRICATION: over-run past committed N' (Q1, optional continuation).
    # The Chair's exploit numbers: genesis commits N'=12, chain presents
    # n=60 with the interval clear of the band.
    c = _null_claim()
    claim = buildvec.build_claim_chain(c)
    ch = buildvec.claim_c_hash_of(c)
    ref = buildvec.build_refuter_chain(ch, 60, 60, n_prime=12)
    yield ("v19_invalid_attempt_overrun.bin", claim, ref, 1,
           "INVALID-ATTEMPT", "FABRICATION",
           "observed n=60 exceeds committed N'=12: optional continuation")

    # MALFORMED: non-canonical C serialisation (Q2, FCC-1.1). Same field
    # set, indented serialisation, different C hash.
    noncanon = json.dumps(json.loads(_null_claim()), indent=2,
                          sort_keys=True).encode()
    chain = buildvec.build_chain([
        (buildvec.TAG_STATE, b'{"state":"open"}'),
        (buildvec.TAG_FCC_C, noncanon)])
    yield ("v20_invalid_claim_noncanonical.bin", chain, None, None,
           "INVALID-CLAIM", "MALFORMED",
           "C payload not the RFC 8785 canonical serialisation")

    # SNAPSHOT-MISMATCH: bracket present but not enclosing (Q3). Both
    # markers before any trial.
    c = _null_claim()
    claim = buildvec.build_claim_chain(c)
    ch = buildvec.claim_c_hash_of(c)
    ref = buildvec.build_refuter_chain(ch, 12, 12, misorder_bracket=True)
    yield ("v21_invalid_attempt_bracket_order.bin", claim, ref, 1,
           "INVALID-ATTEMPT", "SNAPSHOT-MISMATCH",
           "both fingerprint markers precede the trials: not a bracket")

    # MALFORMED: claim commitment multiplicity (Q4). Two AX:FCC:C:v1
    # records; the single-commitment rule mirrors the refuter genesis rule.
    c_a = _null_claim()
    c_b = buildvec.claim_c_payload("NULL", 1, 100,
                                   alpha_prime_num=AP_NUM,
                                   alpha_prime_den=AP_DEN)
    chain = buildvec.build_chain([
        (buildvec.TAG_STATE, b'{"state":"open"}'),
        (buildvec.TAG_FCC_C, c_a),
        (buildvec.TAG_FCC_C, c_b)])
    yield ("v22_invalid_claim_multiplicity.bin", chain, None, None,
           "INVALID-CLAIM", "MALFORMED",
           "two AX:FCC:C:v1 records; the commitment must be single")

    # MALFORMED: claimant committed parameter with a non-consumable type
    # (R1). alpha' numerator as a JSON string would crash a naive verifier;
    # an exception is not one of the four verdicts.
    c_bad = buildvec.claim_c_payload(
        "NULL", D_NUM, D_DEN,
        extra={"R": {"tiers": ["A", "B"],
                     "alpha_prime_num": "1",
                     "alpha_prime_den": 100}})
    chain = buildvec.build_chain([
        (buildvec.TAG_STATE, b'{"state":"open"}'),
        (buildvec.TAG_FCC_C, c_bad)])
    yield ("v23_invalid_claim_value_shape.bin", chain, None, None,
           "INVALID-CLAIM", "MALFORMED",
           "R alpha' numerator is a string, not an integer")

    # FABRICATION: genesis committed parameter with a non-consumable type
    # (R1, refuter side). n_prime as a JSON string.
    c = _null_claim()
    claim = buildvec.build_claim_chain(c)
    ch = buildvec.claim_c_hash_of(c)

    def _string_n_prime(reg):
        reg["n_prime"] = "12"
        return reg

    ref = buildvec.build_refuter_chain(ch, 12, 12,
                                       mutate_reg=_string_n_prime)
    yield ("v24_invalid_attempt_genesis_type.bin", claim, ref, 1,
           "INVALID-ATTEMPT", "FABRICATION",
           "genesis n_prime is a string, not a positive integer")

    # MALFORMED: delta out of range (T1). delta = 150/100 makes the band
    # swallow [-1, 1]: a NULL claim unrefutable by construction, wearing a
    # conformant verdict. Range constraints are per field, not per
    # discovery; delta must be strictly inside (0, 1).
    c_wide = buildvec.claim_c_payload("NULL", 150, 100,
                                      alpha_prime_num=AP_NUM,
                                      alpha_prime_den=AP_DEN)
    chain = buildvec.build_chain([
        (buildvec.TAG_STATE, b'{"state":"open"}'),
        (buildvec.TAG_FCC_C, c_wide)])
    yield ("v25_invalid_claim_delta_range.bin", chain, None, None,
           "INVALID-CLAIM", "MALFORMED",
           "delta=150/100 not strictly below 1: band swallows [-1, 1]")


def main(check=False):
    manifest = []
    failures = []
    drift = []
    for (name, claim, ref, ac, exp_v, exp_c, note) in vectors():
        if check:
            with open(os.path.join(GOLDEN, name), "rb") as fh:
                on_disk = fh.read()
            if on_disk != claim:
                drift.append(name)
        else:
            _write(name, claim)
            if ref is not None:
                _write(name.replace(".bin", ".refuter.bin"), ref)
        v = verdict.adjudicate(claim, refuter_bytes=ref, attempt_count=ac)
        ok = (v.verdict == exp_v and v.cause == exp_c)
        manifest.append({
            "name": name, "expected": exp_v, "cause": exp_c,
            "got": v.verdict, "got_cause": v.cause, "note": note,
            "has_refuter": ref is not None, "pass": ok})
        if not ok:
            failures.append((name, exp_v, exp_c, v.verdict, v.cause))
        print("  %-4s %-38s %s%s" % (
            "ok" if ok else "FAIL", name, v.verdict,
            "" if v.cause is None else " (%s)" % v.cause))

    if check:
        # also confirm refuter sidecars match
        for (name, claim, ref, ac, *_rest) in vectors():
            if ref is not None:
                rname = name.replace(".bin", ".refuter.bin")
                with open(os.path.join(GOLDEN, rname), "rb") as fh:
                    if fh.read() != ref:
                        drift.append(rname)
    else:
        with open(os.path.join(GOLDEN, "manifest.json"), "w") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)

    if failures:
        print("\n%d vector(s) FAILED" % len(failures))
        for (n, ev, ec, gv, gc) in failures:
            print("  %s: expected %s/%s got %s/%s" % (n, ev, ec, gv, gc))
        raise SystemExit(1)
    if drift:
        print("\n%d committed vector(s) DRIFTED from the generator:" % len(drift))
        for n in drift:
            print("  %s" % n)
        raise SystemExit(1)
    print("\n%d vectors %s" % (
        len(manifest), "match committed bytes" if check else "passed"))


if __name__ == "__main__":
    import sys
    main(check="--check" in sys.argv)
