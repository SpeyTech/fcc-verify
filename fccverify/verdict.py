"""fccverify.verdict: the FCC-001 v0.4.1 section 6.2 verdict pipeline.

One deterministic program. Given a claimant chain and a refuter chain, it emits
exactly one of:

    UPHELD | REFUTED | INVALID-ATTEMPT | INVALID-CLAIM

with a cause, deterministically, from the committed rules alone.

Written against the specification of record (spec/FCC-001-SPEC-v0.4.1.md), not
against any paraphrase. The order of FCC-6.2 is normative and enforced here:

  Stage 1  claim well-formedness   -> INVALID-CLAIM (FABRICATION, MALFORMED,
                                       UNTIMESTAMPED, BEACON-VIOLATION)
  Stage 2  attempt well-formedness -> INVALID-ATTEMPT (UNREGISTERED,
                                       BEACON-VIOLATION, FABRICATION,
                                       SNAPSHOT-MISMATCH, INCOMPLETE)
  Stage 3  snapshot bracketing     -> presence at attempt start and end, in
                                       order, else INVALID-ATTEMPT
                                       SNAPSHOT-MISMATCH; predicate
                                       unsatisfiable -> ARCHIVAL
  Stage 4  categorical test        -> CI' disjoint from S emits REFUTED, else
                                       UPHELD (FCC-3.2, FCC-6.2)

Committed-parameter disciplines, all from the spec:

  Source of committed parameters (FCC-2, FCC-3.1). delta (the band) and alpha'
  (the refuter level) are the claimant's committed parameters: delta lives in
  C's decision_rule, alpha' in C's R. The verifier reads both from the
  claimant's C exclusively. The refuter genesis echoes alpha' (FCC-7.1); the
  verifier cross-checks that echo for equality and emits INVALID-ATTEMPT on
  mismatch. A refuter cannot choose the band or shop the level upward; if it
  could, S would no longer be the claimant's asserted region and the FCC-3.3
  false-refutation bound would be meaningless.

  The committed-parameter table (Q1, structural). Every refuter-genesis
  parameter that is committed-then-checked is enumerated in one table,
  COMMITTED_PARAMETERS, and enforced by a single loop. A committed parameter
  missing from the table cannot be enforced, and a parameter in the table
  cannot be skipped; the next N'-class omission is impossible to write without
  editing the table itself. Current rows: the C-hash binding, the alpha' echo,
  and exact-N' completeness.

  Exact N' (Q1). The genesis commits N' before data (FCC-7.1); the presented
  trial count must equal it exactly. Below N' is INCOMPLETE. Above N' is
  FABRICATION: a refuter who keeps sampling past its commitment until the
  interval clears the band is running optional continuation, the
  coverage-breaking behaviour the committed-N' rule exists to forbid
  (FCC-2.3's law, mirrored on the refuter side; Theorem 2). Departures from
  the committed N' are adjudicated only through the genesis's own committed
  episode_completion_rule, which is content verification and lands with the
  harness; at this layer the commitment is held literally.

  C canonicality (Q2, FCC-1.1). C is the hash of the RFC 8785 canonical JSON
  of the field set. The verifier re-serialises the parsed payload
  (sorted keys, no whitespace, literal UTF-8) and requires byte equality with
  the presented payload, else MALFORMED. Within the value domain these
  payloads use (BMP strings, integers within the IEEE-754 exact range, no
  floats by the Chair-ratified language ruling, booleans, null, nested objects
  and arrays) that re-serialisation equals RFC 8785 exactly. Without this
  check the genesis binding degrades to whatever bytes the claimant happened
  to emit, and a Tier B reimplementation computing C from the fields could
  not reproduce the claimant's hash.

  Refutation region (FCC-3.2). Let S be the region of A asserted by the
  claimant's verdict. Refuted iff CI' at the refuter's committed alpha' is
  disjoint from S. One definition, both verdicts, both signs:
      NULL              S = the band; disjoint = CI' entirely outside it.
      THREAT-EXISTS(+)  S = (p_plus, 1]; disjoint = p_hi < p_plus.
      THREAT-EXISTS(-)  S = [0, p_minus); disjoint = p_lo > p_minus.

  Boundary convention (normative). Interval contact with S is NOT disjoint: it
  adjudicates toward the claimant (UPHELD). The refuter must clear S strictly.
  A one-trial overlap does not refute. This keeps an underpowered attempt from
  killing a true claim, and is the direction FCC-3.3 requires.

Requirement 5, scoped honestly: fcc-verify checks what a minimal clone can
check. Every check run is recorded in the verdict record's `checks` list with
its outcome, and every check that needs the harness pin (content verification
of beacon, timestamp, and per-episode scoring) is recorded in `deferred` with
the reason. No check is silently skipped; the boundary is machine-stated.
"""

import json
from fractions import Fraction

from fccverify import exact
from fccverify.reader import ReaderError, read_frames
from fccverify.registry import TAG_FCC_C, TAG_FCC_REG, TAG_OBS

# Verdict constants.
UPHELD = "UPHELD"
REFUTED = "REFUTED"
INVALID_ATTEMPT = "INVALID-ATTEMPT"
INVALID_CLAIM = "INVALID-CLAIM"


class Verdict:
    """The verifier's output. Serialises to the AX:FCC:VERDICT:v1 payload and
    prints one word to stdout. `checks` and `deferred` make the minimal-set
    boundary explicit (requirement 5)."""

    def __init__(self, verdict, cause=None):
        self.verdict = verdict
        self.cause = cause
        self.checks = []
        self.deferred = []
        self.annotations = {}

    def check(self, name, outcome, detail=""):
        self.checks.append((name, outcome, detail))

    def defer(self, name, reason):
        self.deferred.append((name, reason))

    def annotate(self, key, value):
        self.annotations[key] = value

    def terminal(self, verdict, cause, check_name, outcome, detail):
        """Set a terminal verdict and record the deciding check in one place,
        so the verdict record has a single author (P6)."""
        self.verdict = verdict
        self.cause = cause
        self.check(check_name, outcome, detail)
        return self

    def as_record(self):
        """Deterministic JSON-serialisable dict for the AX:FCC:VERDICT:v1
        payload. Ordering is fixed; no floats."""
        return {
            "verdict": self.verdict,
            "cause": self.cause,
            "checks": [
                {"name": n, "outcome": o, "detail": d}
                for (n, o, d) in self.checks
            ],
            "deferred": [
                {"name": n, "reason": r} for (n, r) in self.deferred
            ],
            "annotations": self.annotations,
        }

    def __repr__(self):
        c = "" if self.cause is None else " (%s)" % self.cause
        return self.verdict + c


# Fields the claimant C must commit (FCC closure). Eighteen.
REQUIRED_C_FIELDS = (
    "seed_core", "battery_blob", "pool_blob", "estimator_code",
    "decision_rule", "N", "alpha", "R", "snapshot_predicate",
    "pattern_set_version", "adapter_version", "redactor_version",
    "verifier_commit", "calculus_version", "spending_schedule",
    "episode_completion_rule", "beacon_rule", "w_min")

# Fields the refuter genesis (AX:FCC:REG:v1) must commit (FCC-7.1).
REQUIRED_REG_FIELDS = (
    "claim_c_hash", "alpha_prime_num", "alpha_prime_den", "n_prime",
    "episode_completion_rule", "beacon_rule")


def _first_frame(frames, tag):
    for f in frames:
        if f.tag == tag:
            return f
    return None


def _all_frames(frames, tag):
    return [f for f in frames if f.tag == tag]


def _parse_json_payload(frame):
    try:
        return json.loads(frame.payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None


def _is_int(x):
    """A JSON integer. bool is an int subclass in Python and is not one."""
    return isinstance(x, int) and not isinstance(x, bool)


def _canonical_bytes(data):
    """Re-serialise a parsed JSON value in the canonical form of FCC-1.1:
    sorted keys, no insignificant whitespace, literal UTF-8. Within the value
    domain these payloads use (BMP strings, integers within the IEEE-754
    exact range, no floats, booleans, null, nested objects and arrays) this
    equals RFC 8785 exactly; the domain restriction is stated in the module
    docstring. Key ordering by code point equals JCS's UTF-16 ordering inside
    the BMP, and duplicate keys cannot survive a parse-and-reserialise, which
    JCS likewise forbids."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


# --- Stage 1: claim well-formedness -----------------------------------------

def _claim_shape_error(claim_data):
    """Value-shape gate for the C fields the verdict path reads. Returns an
    error string or None. Field presence is closure's job; this is the layer
    below it: the committed parameters must be arithmetic the verdict path
    can consume, else the claim is MALFORMED rather than the verifier
    undefined."""
    dr = claim_data["decision_rule"]
    if not isinstance(dr, dict):
        return "decision_rule is not an object"
    if not isinstance(dr.get("verdict"), str):
        return "decision_rule.verdict is not a string"
    if not _is_int(dr.get("delta_num")) or not _is_int(dr.get("delta_den")):
        return "decision_rule delta is not an integer ratio"
    # Range constraints, enumerated per field (T1). delta strictly inside
    # (0, 1): delta >= 1 makes the band swallow [-1, 1] and a NULL claim
    # unrefutable by construction, the governing principle inverted; delta
    # <= 0 makes NULL unreachable. Positivity comes from delta_num >= 1,
    # the upper bound from delta_num < delta_den.
    if dr["delta_num"] < 1 or dr["delta_den"] < 1:
        return "decision_rule delta is not a positive ratio"
    if dr["delta_num"] >= dr["delta_den"]:
        return "decision_rule delta is not strictly below 1"
    if "sign" in dr and not isinstance(dr["sign"], str):
        return "decision_rule.sign is not a string"
    r = claim_data["R"]
    if not isinstance(r, dict):
        return "R is not an object"
    if not _is_int(r.get("alpha_prime_num")) \
            or not _is_int(r.get("alpha_prime_den")):
        return "R alpha' is not an integer ratio"
    if r["alpha_prime_num"] < 1 or r["alpha_prime_den"] < 1:
        return "R alpha' is not a positive ratio"
    if Fraction(r["alpha_prime_num"], r["alpha_prime_den"]) >= 1:
        return "R alpha' is not below 1"
    return None


def _stage1_claim(frames, v):
    """Returns claim_data on pass, or None with a terminal verdict set.
    Check ladder, coarsest to finest: the record exists and is single, the
    bytes parse, the bytes are canonical (Q2), the fields are present, the
    values are consumable."""
    cs = _all_frames(frames, TAG_FCC_C)
    if len(cs) == 0:
        v.terminal(INVALID_CLAIM, "MALFORMED",
                   "claim.commitment_present", "fail",
                   "no AX:FCC:C:v1 record")
        return None
    v.check("claim.commitment_present", "pass", "")

    # Single commitment rule (Q4), mirroring the refuter's single-genesis
    # rule. First-wins would let a claimant present one C to the reader and
    # another to a human; multiplicity is MALFORMED, never reduced.
    if len(cs) > 1:
        v.terminal(INVALID_CLAIM, "MALFORMED",
                   "claim.commitment_unique", "fail",
                   "%d AX:FCC:C:v1 records; the commitment must be single"
                   % len(cs))
        return None
    v.check("claim.commitment_unique", "pass", "one AX:FCC:C:v1 record")

    claim_data = _parse_json_payload(cs[0])
    if claim_data is None:
        v.terminal(INVALID_CLAIM, "MALFORMED",
                   "claim.commitment_parses", "fail",
                   "C payload not valid JSON")
        return None
    v.check("claim.commitment_parses", "pass", "")

    # Canonical serialisation (Q2, FCC-1.1). Byte equality against the
    # canonical re-serialisation; a non-canonical payload hashes to a C no
    # independent reimplementation can reproduce from the fields.
    if _canonical_bytes(claim_data) != cs[0].payload:
        v.terminal(INVALID_CLAIM, "MALFORMED",
                   "claim.c_canonical", "fail",
                   "C payload is not the RFC 8785 canonical serialisation "
                   "of its own field set")
        return None
    v.check("claim.c_canonical", "pass",
            "C payload byte-equal to its canonical re-serialisation")

    missing = [k for k in REQUIRED_C_FIELDS if k not in claim_data]
    if missing:
        v.terminal(INVALID_CLAIM, "MALFORMED",
                   "claim.field_closure", "fail",
                   "missing: " + ",".join(missing))
        return None
    v.check("claim.field_closure", "pass", "18 fields present")

    shape_err = _claim_shape_error(claim_data)
    if shape_err is not None:
        v.terminal(INVALID_CLAIM, "MALFORMED",
                   "claim.value_shapes", "fail", shape_err)
        return None
    v.check("claim.value_shapes", "pass",
            "decision_rule and R carry consumable committed parameters")
    return claim_data


# --- Stage 2: attempt well-formedness ---------------------------------------
#
# The committed-parameter table. Every genesis parameter that is
# committed-then-checked lives here and is enforced by the single loop in
# _stage2_attempt. Each judge receives the parsed genesis and a context dict
# {claim_c_hash, claim_alpha_prime, k, n} and returns either
# (True, pass_detail) or (False, cause, fail_detail). Adding a committed
# parameter means adding a row; there is no second place to forget.
#
# Judges validate integer operands through _is_int, never bare
# isinstance(_, int): Python booleans are int subclasses, and a bare
# isinstance would let a JSON true in as 1 (A3).

def _judge_binds_claim(reg, ctx):
    """The genesis must commit the hash of the C it attacks (FCC-7.1)."""
    if reg["claim_c_hash"] != ctx["claim_c_hash"]:
        return (False, "FABRICATION",
                "genesis claim_c_hash does not match the claimant C")
    return (True, "genesis commits the claimant C hash")


def _judge_alpha_prime_echo(reg, ctx):
    """The genesis alpha' echo must equal the claimant's committed level
    (P2, R-authoritative). Fraction equality, so 2/200 equals 1/100."""
    if not _is_int(reg["alpha_prime_num"]) \
            or not _is_int(reg["alpha_prime_den"]) \
            or reg["alpha_prime_den"] < 1:
        return (False, "FABRICATION",
                "genesis alpha' is not an integer ratio with a positive "
                "denominator")
    reg_alpha = Fraction(reg["alpha_prime_num"], reg["alpha_prime_den"])
    if reg_alpha != ctx["claim_alpha_prime"]:
        return (False, "FABRICATION",
                "refuter alpha' %s != claimant committed alpha' %s"
                % (reg_alpha, ctx["claim_alpha_prime"]))
    return (True,
            "refuter alpha' echo equals claimant R (R-authoritative)")


def _judge_n_exact(reg, ctx):
    """Exact-N' completeness (Q1). The presented trial count must equal the
    committed N'. Below is INCOMPLETE. Above is FABRICATION: sampling past
    the commitment until the interval clears the band is optional
    continuation, which voids the refuter coverage bound (Theorem 2).
    Departures from the committed N' are adjudicated only through the
    genesis's own committed episode_completion_rule, content that lands with
    the harness; here the commitment is held literally. The spec imposes no
    minimum N' (FCC-3.4); the refuter is held to the N' it chose."""
    n_prime = reg["n_prime"]
    if not _is_int(n_prime) or n_prime < 1:
        return (False, "FABRICATION",
                "genesis n_prime is not a positive integer")
    n = ctx["n"]
    if n < n_prime:
        return (False, "INCOMPLETE",
                "observed n=%d below committed N'=%d" % (n, n_prime))
    if n > n_prime:
        return (False, "FABRICATION",
                "observed n=%d exceeds committed N'=%d; over-run is a "
                "committed-parameter violation (optional continuation), "
                "adjudicable only by the committed episode_completion_rule"
                % (n, n_prime))
    return (True, "observed n=%d equals committed N'=%d" % (n, n_prime))


COMMITTED_PARAMETERS = (
    ("attempt.binds_claim", _judge_binds_claim),
    ("attempt.alpha_prime_echo", _judge_alpha_prime_echo),
    ("attempt.completeness", _judge_n_exact),
)


def _stage2_attempt(refuter_frames, claim_c_hash, claim_alpha_prime, v):
    """Validate the refuter chain against its own genesis and the claim it
    names. Returns {k, n} on pass, or None with a terminal INVALID-ATTEMPT.
    Structural checks first (membership, genesis singularity and closure),
    then the presented evidence is reduced, then every committed parameter is
    judged by the one table loop. Harness-free checks only; content
    verification of beacon/timestamp/scoring is deferred, not skipped."""
    unreg = [f for f in refuter_frames if not f.registered]
    if unreg:
        v.terminal(INVALID_ATTEMPT, "UNREGISTERED",
                   "attempt.registry_membership", "fail",
                   "unregistered tag %r at frame %d"
                   % (unreg[0].tag, unreg[0].index))
        return None
    v.check("attempt.registry_membership", "pass",
            "all attempt tags in DVEC v1.4 registry")

    # Single genesis rule (P5): exactly one AX:FCC:REG:v1 record.
    regs = _all_frames(refuter_frames, TAG_FCC_REG)
    if len(regs) == 0:
        v.terminal(INVALID_ATTEMPT, "FABRICATION",
                   "attempt.genesis_present", "fail",
                   "no AX:FCC:REG:v1 genesis record")
        return None
    if len(regs) > 1:
        v.terminal(INVALID_ATTEMPT, "FABRICATION",
                   "attempt.genesis_unique", "fail",
                   "%d AX:FCC:REG:v1 records; genesis must be single"
                   % len(regs))
        return None
    reg = _parse_json_payload(regs[0])
    if reg is None:
        v.terminal(INVALID_ATTEMPT, "FABRICATION",
                   "attempt.genesis_parses", "fail",
                   "REG payload not valid JSON")
        return None

    missing = [k for k in REQUIRED_REG_FIELDS if k not in reg]
    if missing:
        v.terminal(INVALID_ATTEMPT, "FABRICATION",
                   "attempt.genesis_closure", "fail",
                   "genesis missing: " + ",".join(missing))
        return None
    v.check("attempt.genesis_closure", "pass",
            "genesis commits C hash, alpha', N', completion, beacon")

    # Reduce the presented evidence: per-trial results are AX:OBS:v1 (P5).
    obs = _all_frames(refuter_frames, TAG_OBS)
    trials = [r for r in (_parse_json_payload(f) for f in obs)
              if r is not None and r.get("kind") != "snapshot"]
    if not trials:
        v.terminal(INVALID_ATTEMPT, "INCOMPLETE",
                   "attempt.observations_present", "fail",
                   "no AX:OBS:v1 trial outcome records")
        return None
    k = 0
    n = 0
    for rec in trials:
        if "success" not in rec:
            v.terminal(INVALID_ATTEMPT, "FABRICATION",
                       "attempt.observation_wellformed", "fail",
                       "an AX:OBS:v1 trial record lacks a success field")
            return None
        # F-INC-1: success must be a JSON boolean. Truthiness coercion would
        # import Python semantics into the calculus; a Tier B
        # reimplementation has no licensed coercion for a non-boolean, so
        # two conformant verifiers could disagree. Bare isinstance(_, bool)
        # is total and correct here; do not route this through _is_int,
        # whose job is the opposite exclusion (A3).
        if not isinstance(rec["success"], bool):
            v.terminal(INVALID_ATTEMPT, "FABRICATION",
                       "attempt.observation_wellformed", "fail",
                       "an AX:OBS:v1 trial record's success is not a JSON "
                       "boolean")
            return None
        n += 1
        if rec["success"]:
            k += 1
    v.check("attempt.observations_present", "pass",
            "%d AX:OBS:v1 trial outcome records" % n)

    # The committed-parameter loop (Q1, structural). One table, one loop; a
    # committed parameter cannot be enforced anywhere else, so none can be
    # missed.
    ctx = {"claim_c_hash": claim_c_hash,
           "claim_alpha_prime": claim_alpha_prime,
           "k": k, "n": n}
    for (check_name, judge) in COMMITTED_PARAMETERS:
        result = judge(reg, ctx)
        if result[0]:
            v.check(check_name, "pass", result[1])
        else:
            v.terminal(INVALID_ATTEMPT, result[1], check_name, "fail",
                       result[2])
            return None

    v.defer("attempt.beacon_content",
            "beacon-seed derivation and depth check need input-fed header")
    v.defer("attempt.timestamp_content",
            "OTS predates-genesis check needs input-fed proof")
    v.defer("attempt.scoring_replay",
            "bit-exact replay under the refuter's procedure needs the harness")

    return {"k": k, "n": n}


# --- Stage 3: snapshot bracket presence and order ----------------------------

def _stage3_snapshot(refuter_frames, v):
    """Fingerprint records at attempt start and end (FCC-6.2), in order (Q3):
    a bracket that does not enclose the trials is not a bracket. Frame indices
    carry the order; the first start marker must precede the first trial and
    the last end marker must follow the last trial. Content verification of
    the fingerprints stays deferred; presence and position are checkable
    now."""
    starts = []
    ends = []
    trial_idx = []
    for f in _all_frames(refuter_frames, TAG_OBS):
        rec = _parse_json_payload(f)
        if rec is None:
            continue
        if rec.get("kind") == "snapshot":
            if rec.get("endpoint") == "start":
                starts.append(f.index)
            elif rec.get("endpoint") == "end":
                ends.append(f.index)
        else:
            trial_idx.append(f.index)

    if not starts or not ends:
        v.terminal(INVALID_ATTEMPT, "SNAPSHOT-MISMATCH",
                   "attempt.snapshot_bracket", "fail",
                   "missing fingerprint bracket (need start and end)")
        return False
    if not trial_idx:
        # Stage 2 terminates on zero trials before this stage runs; guard
        # kept so this function is safe standalone.
        v.terminal(INVALID_ATTEMPT, "SNAPSHOT-MISMATCH",
                   "attempt.snapshot_bracket", "fail",
                   "no trials to bracket")
        return False
    if starts[0] >= trial_idx[0]:
        v.terminal(INVALID_ATTEMPT, "SNAPSHOT-MISMATCH",
                   "attempt.snapshot_bracket", "fail",
                   "first start marker (frame %d) does not precede first "
                   "trial (frame %d)" % (starts[0], trial_idx[0]))
        return False
    if ends[-1] <= trial_idx[-1]:
        v.terminal(INVALID_ATTEMPT, "SNAPSHOT-MISMATCH",
                   "attempt.snapshot_bracket", "fail",
                   "last end marker (frame %d) does not follow last "
                   "trial (frame %d)" % (ends[-1], trial_idx[-1]))
        return False
    v.check("attempt.snapshot_bracket", "pass",
            "start marker (frame %d) precedes trials, end marker (frame %d) "
            "follows them" % (starts[0], ends[-1]))
    v.defer("attempt.snapshot_content",
            "predicate satisfaction is content; ARCHIVAL transition needs "
            "the harness")
    return True


# --- Stage 4: categorical test ----------------------------------------------

def _region_of(claim_data):
    """The claimant's asserted region S, derived from C alone (P2): delta,
    verdict, and sign from decision_rule."""
    dr = claim_data["decision_rule"]
    delta = Fraction(dr["delta_num"], dr["delta_den"])
    p_minus, p_plus = exact.band_edges_p(delta)
    return dr["verdict"], dr.get("sign"), p_minus, p_plus


def _stage4_categorical(claim_data, summary, v):
    """FCC-3.2: refuted iff CI' at the claimant's committed alpha' is disjoint
    from S. S and alpha' both from the claimant's C (P2)."""
    k = summary["k"]
    n = summary["n"]
    alpha_prime = Fraction(claim_data["R"]["alpha_prime_num"],
                           claim_data["R"]["alpha_prime_den"])
    verdict_claimed, sign, p_minus, p_plus = _region_of(claim_data)

    if verdict_claimed == "NULL":
        refuted = exact.ci_disjoint_from_band(k, n, p_minus, p_plus,
                                              alpha_prime)
        region = "band [%s, %s]" % (p_minus, p_plus)
    elif verdict_claimed == "THREAT-EXISTS":
        if sign == "+":
            refuted = exact.ci_disjoint_from_upper(k, n, p_plus, alpha_prime)
            region = "(%s, 1]" % p_plus
        elif sign == "-":
            refuted = exact.ci_disjoint_from_lower(k, n, p_minus, alpha_prime)
            region = "[0, %s)" % p_minus
        else:
            v.terminal(INVALID_CLAIM, "MALFORMED",
                       "categorical.threat_sign", "fail",
                       "THREAT-EXISTS claim missing sign in decision_rule")
            return
    else:
        v.terminal(INVALID_CLAIM, "MALFORMED",
                   "categorical.verdict_known", "fail",
                   "unknown claimed verdict %r" % verdict_claimed)
        return

    v.check("categorical.verdict_known", "pass",
            "%s%s, S = %s" % (verdict_claimed,
                              "" if sign is None else "(" + sign + ")",
                              region))
    if refuted:
        v.terminal(REFUTED, None, "categorical.refutation", "pass",
                   "CI' disjoint from S")
    else:
        v.terminal(UPHELD, None, "categorical.refutation", "n/a",
                   "CI' meets S (contact adjudicates toward the claimant)")


# --- Top level --------------------------------------------------------------

def adjudicate(claim_bytes, refuter_bytes=None, attempt_count=None):
    """Adjudicate a claim and an optional refuter chain. Both read through the
    verifier's own reader. Returns a Verdict; the pipeline stops at the first
    terminal stage. The order is FCC-6.2, normative."""
    v = Verdict(UPHELD)

    try:
        frames = list(read_frames(claim_bytes))
        v.check("claim.integrity_replay", "pass",
                "%d frames, commit and link sound" % len(frames))
    except ReaderError as e:
        v.terminal(INVALID_CLAIM, "FABRICATION",
                   "claim.integrity_replay", "fail", str(e))
        v.defer("claim.scoring_replay",
                "full D1 scoring replay needs the harness pin")
        return v

    unregistered = [f for f in frames if not f.registered]
    if unregistered:
        v.terminal(INVALID_CLAIM, "MALFORMED",
                   "claim.registry_membership", "fail",
                   "unregistered tag %r at frame %d"
                   % (unregistered[0].tag, unregistered[0].index))
        return v
    v.check("claim.registry_membership", "pass",
            "all tags in DVEC v1.4 registry")
    v.defer("claim.scoring_replay",
            "RUNG re-derivation from transcripts needs the harness pin; "
            "FABRICATION on scoring is adjudicated with the harness present")
    v.defer("claim.beacon_content",
            "final_seed = H(seed_core || beacon) needs input-fed header")
    v.defer("claim.timestamp_content",
            "OTS predates-beacon check needs input-fed proof")

    claim_data = _stage1_claim(frames, v)
    if claim_data is None:
        return v

    claim_alpha_prime = Fraction(claim_data["R"]["alpha_prime_num"],
                                 claim_data["R"]["alpha_prime_den"])
    claim_c_frame = _first_frame(frames, TAG_FCC_C)
    claim_c_hash = claim_c_frame.commit.hex()

    if attempt_count is not None:
        v.annotate("registered_attempt_count", attempt_count)
        v.annotate("family_bound_note",
                   "family bound k*alpha' is annotation, not a gate (FCC-7.3)")

    if refuter_bytes is None:
        v.check("categorical.attempt_present", "n/a", "no refuter chain")
        return v

    try:
        refuter_frames = list(read_frames(refuter_bytes))
        v.check("attempt.integrity_replay", "pass",
                "%d frames, commit and link sound" % len(refuter_frames))
    except ReaderError as e:
        v.terminal(INVALID_ATTEMPT, "FABRICATION",
                   "attempt.integrity_replay", "fail", str(e))
        return v

    summary = _stage2_attempt(refuter_frames, claim_c_hash,
                              claim_alpha_prime, v)
    if summary is None:
        return v

    if not _stage3_snapshot(refuter_frames, v):
        return v

    _stage4_categorical(claim_data, summary, v)
    return v
