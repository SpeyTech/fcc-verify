# Golden vectors: hand derivation

Every vector in `golden/` has its expected verdict derived here by hand, from
the specification (`spec/FCC-001-SPEC-v0.4.1.md`), so a reader confirms the
verdict without running the verifier. The conviction comes from the derivation;
the program is checked against it.

The refutation rule is FCC-3.2, verbatim: let S be the region of A asserted by
the claimant's verdict; a verdict is refuted by a valid attempt whose
Clopper-Pearson interval CI' at the committed alpha' is disjoint from S. One
definition, both verdicts, both signs. This document does not paraphrase it into
a per-verdict rule; the earlier "within band" paraphrase for THREAT-EXISTS was
wrong and is not repeated.

Standing parameters for the categorical vectors:

    delta        = 0.05           committed by the claimant in C.decision_rule
    band on A    = (-0.05, +0.05)
    band on p    = (0.475, 0.525) since p = (A + 1)/2
    alpha'       = 0.01           committed by the claimant in C.R
    method       = Clopper-Pearson, exact, two-sided at alpha'

Both delta and alpha' come from the claimant's C. The refuter chain carries no
band and no free alpha': its genesis echoes alpha' and the verifier requires
that echo to equal C.R, else INVALID-ATTEMPT. A refuter cannot move S.

The asserted region S by verdict:

    NULL              S = the band [0.475, 0.525]
    THREAT-EXISTS(+)  S = (0.525, 1]      effect asserted, positive
    THREAT-EXISTS(-)  S = [0, 0.475)      effect asserted, negative

Disjointness, decided by exact tail sums (no quantile inversion):

    from the band     p_hi < 0.475  or  p_lo > 0.525
    from (0.525, 1]   p_hi < 0.525
    from [0, 0.475)   p_lo > 0.475

Boundary convention (normative, lifted into verdict.py): interval contact with
S is not disjoint. It adjudicates toward the claimant, UPHELD. The refuter must
clear S strictly.

---

## Categorical: NULL

**v01 UPHELD.** Refuter k = 6, n = 12, dead on chance. CI' at alpha' = 0.01 is
wide and straddles 0.5, meeting the band. Not disjoint. The claimant said no
effect; the refuter found none. UPHELD.

**v02 REFUTED, positive.** Refuter k = 12, n = 12. p_lo solves p^12 = 0.005, so
p_lo = 0.6431 > 0.525. CI' entirely above the band, disjoint from S. REFUTED.

**v03 REFUTED, negative.** Refuter k = 0, n = 12. By symmetry p_hi = 0.3569 <
0.475. CI' entirely below the band, disjoint. REFUTED. Present so the suite
refutes on both polarities.

**v04 BOUNDARY, UPHELD.** Refuter k = 8, n = 9. p_lo sits just below 0.525: the
interval overlaps the band by the last trial. k = 9 would give p_lo =
0.005^(1/9) = 0.5623 > 0.525 and refute. At k = 8 it does not. Contact is not
disjoint, so UPHELD. A verifier that rounded this to REFUTED would let an
underpowered attempt kill a true claim.

## Categorical: THREAT-EXISTS(+), S = (0.525, 1]

**v05 UPHELD.** Refuter k = 99, n = 100. CI' is high, above 0.525, so it meets
S. The refuter's own data agrees the effect exists. Not disjoint. UPHELD.

**v06 REFUTED, opposite side.** Refuter k = 1, n = 100. CI' is near zero,
entirely below the band, so p_hi < 0.525 and CI' is disjoint from S = (0.525,
1]. REFUTED. This is the case the earlier within-band paraphrase got wrong: it
returned UPHELD because CI' was not inside the band, when the spec asks only
whether CI' is disjoint from S, which it is. The claimant asserted a positive
effect; the refuter demonstrated the opposite, and that refutes.

**v07 REFUTED, band-overlapping but disjoint.** Refuter k = 77, n = 200. CI'
reaches down through the band (p_lo below 0.475) but its upper end is below
0.525, so p_hi < 0.525 and CI' is disjoint from S = (0.525, 1]. REFUTED. An
interval can overlap the band and still be disjoint from a one-sided S; the
rule is disjointness from S, not position relative to the band.

## Categorical: THREAT-EXISTS(-), S = [0, 0.475)

**v08 UPHELD.** Refuter k = 1, n = 100. CI' is near zero, inside S = [0,
0.475), meeting the asserted region. The refuter confirms the negative effect.
Not disjoint. UPHELD.

**v09 REFUTED, opposite side.** Refuter k = 199, n = 200. CI' is high, p_lo >
0.475, disjoint from S = [0, 0.475). The claimant asserted a negative effect;
the refuter demonstrated a positive one. REFUTED.

## INVALID-CLAIM

**v10 FABRICATION.** A valid NULL chain with the final commit byte flipped. The
reader recomputes each commit and the last no longer matches; the chain does not
replay. INVALID-CLAIM (FABRICATION). The categorical test is never reached.

**v11 MALFORMED, unregistered tag.** A structurally valid chain carrying an
`AX:ROGUE:v1` frame, not in the DVEC v1.4 registry. INVALID-CLAIM (MALFORMED).

**v12 MALFORMED, missing field.** A chain whose C omits `w_min`, one of the
eighteen committed fields. Field closure fails. INVALID-CLAIM (MALFORMED).

**v13 MALFORMED, no commitment.** A chain with a state frame and no C record.
Nothing to adjudicate. INVALID-CLAIM (MALFORMED).

## INVALID-ATTEMPT (stage 2)

The attempt chain carries its genesis as `AX:FCC:REG:v1` (committing C's hash,
alpha', N', the completion rule, the beacon rule) and its per-trial outcomes as
`AX:OBS:v1`, with two snapshot fingerprint records bracketing the trials.

**v14 UNREGISTERED.** The attempt chain carries an `AX:ROGUE:v1` frame.
INVALID-ATTEMPT (UNREGISTERED).

**v15 INCOMPLETE.** The genesis commits N' = 100 but the attempt delivers n =
12 trials. Below its own committed count. INVALID-ATTEMPT (INCOMPLETE). The spec
imposes no minimum N' (FCC-3.4); the refuter is held to the N' it chose. The
completeness rule is exact equality (Q1): below N' is INCOMPLETE here, above N'
is FABRICATION (v19).

**v16 SNAPSHOT-MISMATCH.** The attempt omits the fingerprint bracket (no start
and end snapshot records). INVALID-ATTEMPT (SNAPSHOT-MISMATCH). Presence is
checked here; predicate satisfaction is content and deferred to the harness.

**v17 FABRICATION, binding.** The genesis commits a `claim_c_hash` that does not
match the claimant C the attempt is run against. The attempt is not bound to
this claim. INVALID-ATTEMPT (FABRICATION).

**v18 FABRICATION, level shop.** The genesis echoes alpha' = 1/2 while the
claimant committed alpha' = 1/100. A refuter choosing a large alpha' buys a high
false-kill rate; R is authoritative and the echo must match. INVALID-ATTEMPT
(FABRICATION).

**v19 FABRICATION, over-run (Q1).** The genesis commits N' = 12; the chain
presents n = 60 trials with the interval clear of the band. Sampling past the
commitment until the interval clears is optional continuation: the refuter's
coverage guarantee (FCC-3.3, Theorem 2) holds only under the committed design,
and a stopping rule of "keep going until disjoint" makes disjointness a foregone
conclusion rather than evidence. Same attack family as the v18 level shop: a
committed parameter departed from after commitment. INVALID-ATTEMPT
(FABRICATION). Below N' remains INCOMPLETE (v15); the completeness rule is
exact equality, and departures are adjudicable only by the committed
episode_completion_rule, which is harness content.

**v20 MALFORMED, non-canonical C (Q2).** The same eighteen fields serialised
with indentation. FCC-1.1 mandates C as the hash of the RFC 8785 canonical JSON
of the field set; an indented payload hashes to a C that no independent
reimplementation computing from the fields can reproduce, so the genesis
binding and the Tier B story degrade to whatever bytes the claimant happened to
emit. The verifier re-serialises the parsed payload canonically and requires
byte equality. INVALID-CLAIM (MALFORMED). Within the value domain these
payloads use (BMP strings, integers in the IEEE-754 exact range, no floats by
the language ruling), the check equals JCS exactly.

**v21 SNAPSHOT-MISMATCH, bracket order (Q3).** Both fingerprint markers placed
before any trial. Presence without ordering is not a bracket: a bracket that
does not enclose the trials witnesses nothing about the snapshot during the
attempt. Frame indices carry the order; the first start marker must precede the
first trial and the last end marker must follow the last. Here the end marker
(frame 3) precedes every trial. INVALID-ATTEMPT (SNAPSHOT-MISMATCH).

**v22 MALFORMED, commitment multiplicity (Q4).** Two AX:FCC:C:v1 records on the
claimant chain. First-wins reduction would let a claimant present one C to the
verifier and another to a human reader. The single-commitment rule mirrors the
refuter's single-genesis rule. INVALID-CLAIM (MALFORMED).

**v23 MALFORMED, value shape (R1, claimant side).** A field-complete C whose
R.alpha_prime_num is the JSON string "1". The round-two verifier raised
TypeError on this input; an exception is not one of the four verdicts FCC-6.1
mandates, so a hostile claimant could crash the verdict program rather than
receive a verdict. The committed parameters the verdict path reads
(decision_rule and R) must be consumable arithmetic. INVALID-CLAIM (MALFORMED).

**v24 FABRICATION, genesis type (R1, refuter side).** A genesis whose n_prime
is the JSON string "12". Same crash class as v23, refuter side: the round-two
completeness comparison raised TypeError. A committed parameter that cannot be
compared is not a commitment. INVALID-ATTEMPT (FABRICATION).

**v25 MALFORMED, delta range (T1).** A field-complete NULL claim committing
delta = 150/100. The band on p becomes (-0.25, 1.25), which contains every
Clopper-Pearson interval at any evidence: cp_upper_lt at a negative threshold
and cp_lower_gt at a threshold above 1 are both permanently false, so no valid
attempt can ever be disjoint from S. An unrefutable claim wearing a conformant
verdict inverts the governing principle. Demonstrated against the round-three
tree: k = 200, n = 200 returned UPHELD. delta must be strictly inside (0, 1);
delta <= 0 (already excluded by positivity) would make NULL unreachable, the
opposite degeneracy. Range constraints are enumerated per field in the shape
gate, R1's table argument applied to ranges. INVALID-CLAIM (MALFORMED).

**v26 FABRICATION, observation shape (F-INC-1).** Twelve trial records whose
success is the JSON string "yes". Pass one scored success by Python
truthiness, so the pair adjudicated REFUTED with k = 12, demonstrated against
the signed pass-one tree; the JSON number 1 behaved identically. A Tier B
reimplementation has no licensed coercion for a non-boolean, so two
conformant verifiers could disagree on the same bytes. The gate, not the
coercion, is pinned: success must be a JSON boolean, else INVALID-ATTEMPT
(FABRICATION). Genuine booleans adjudicate unchanged.

---

## Coverage

    verdict          vectors
    UPHELD           v01, v04, v05, v08
    REFUTED          v02 (+), v03 (-), v06, v07, v09
    INVALID-CLAIM    v10 (FABRICATION),
                     v11/v12/v13/v20/v22/v23/v25 (MALFORMED)
    INVALID-ATTEMPT  v14 (UNREGISTERED), v15 (INCOMPLETE),
                     v16/v21 (SNAPSHOT-MISMATCH),
                     v17/v18/v19/v24/v26 (FABRICATION)

Both REFUTED polarities present for NULL (v02, v03). Both THREAT signs present
(v05 to v09) with the opposite-side and band-overlap disjointness cases that the
one-definition rule requires. The boundary control (v04) fixes the tie-break.
The committed-parameter perimeter is covered on both sides of N' (v15 below,
v19 above), on canonicality (v20), on multiplicity for both chains (v22
claimant, the single-genesis rule refuter), on type consumability for both
chains (v23, v24), on the range degeneracies that make a claim unrefutable
or unreachable by construction (v25), and on evidence shape (v26). The four
INVALID-ATTEMPT causes reachable without the harness are covered;
BEACON-VIOLATION content stays deferred, named in the verdict record, and
lands with the harness pin.

---

## Integration vectors

Written by exp1-runner chain.py at the RUNNER_HEAD pinned in PINS.json, via
the committed tools/gen_integration.py. They confirm integration: the
verifier's own reader (reimplemented from the frame format of record,
sharing no code with the writer) consumes the writer of record
byte-for-byte. They do not carry the conviction; the hand-derived v-series
above remains the primary evidence. CI cannot regenerate them (foreign
writer), so the gate is the SHA-256 manifest in
golden/integration-manifest.json plus verdict replay and byte-determinism,
enforced by tests/test_integration.py.

**iv01 UPHELD.** NULL claim, standing parameters (delta = 5/100, alpha' =
1/100); refuter k = 6, n = 12, N' = 12. The v01 arithmetic exactly: CI' at
alpha' straddles the band, not disjoint, UPHELD. The claimant chain also
carries an AX:FCC:TS:v1 record between the state frame and C, exercising the
reader's tolerance of registered non-C tags on a claimant chain, a surface
no hand vector touches.

**iv02 REFUTED.** Same claim; refuter k = 12, n = 12, N' = 12. The v02
arithmetic exactly: p_lo solves p^12 = 0.005, p_lo = 0.6431 > 0.525, CI'
entirely above the band, disjoint, REFUTED.
