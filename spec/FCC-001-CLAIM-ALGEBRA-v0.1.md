# FCC-001 Claim Algebra: Formal Derivations and Closure

**Version:** v0.1 draft, companion to FCC-001-SPEC and FCC-001-SCRUTINY-2026-07-04.
**Purpose:** every probabilistic guarantee in the calculus, derived from stated assumptions to
stated conclusions, with the assumption register as the explicit boundary of the proof. Where
the scrutiny corrects the design (S1, S2, S3, S5, S6, S7), the corrected form is derived here.
**Convention:** probabilities on the trial space induced by the committed procedure; intervals
are Clopper-Pearson unless stated; z_q denotes the standard normal q-quantile; logarithms in
nats.

---

## 1. Objects

**1.1 Trials.** Under commitment C, the primary cell yields outcomes X_1, ..., X_N in {0,1},
where X_i = 1 iff the pinned distinguisher is correct on pair i.

**Assumption T1 (iid trials).** X_1, ..., X_N are independent with common success probability
p. Grounds: episode pairs in the primary cell are disjoint; schedules, instantiation and
presentation order derive from independent seed streams; regimes are block-randomised across
the run window. T1 is an assumption about the world (the model treats episodes independently
at the measured granularity), stated as attack surface: cross-episode state at the provider
(caching that alters outputs, adaptive serving) would violate it, and the snapshot predicate
plus the gateway's parameter pinning are the mitigations, not proofs.

**1.2 Advantage and band.** A = 2p - 1 in [-1, 1]. Band B = (-delta, +delta), delta = 0.05,
committed in C.

**1.3 Asserted regions.** S_TE+ = (delta, 1], S_TE- = [-1, -delta), S_NULL = (-delta, +delta).

**1.4 Verdict map.** Given a confidence set CI for A at committed level 1 - alpha:

    THREAT-EXISTS(sigma)  iff  CI is a subset of S_TE(sigma)
    NULL                  iff  CI is a subset of S_NULL
    INDETERMINATE         otherwise

INDETERMINATE asserts nothing and is unrefutable by construction.

**1.5 Refutation rule (corrected form, scrutiny S2).** A standing verdict V with asserted
region S_V is refuted by a valid attempt whose confidence set CI' at the attempt's committed
level 1 - alpha' satisfies CI' intersect S_V = empty.

---

## 2. Coverage lemmas

**Lemma 2.1 (exact coverage).** Let X ~ Binomial(N, p) and let [L(X), U(X)] be the
Clopper-Pearson interval at level 1 - alpha, defined by inverting the binomial tail tests at
alpha/2 per tail. Then for every p in [0,1] and every N >= 1,

    P( p in [L(X), U(X)] ) >= 1 - alpha,

and moreover each one-sided miss is bounded:

    P( U(X) < p ) <= alpha/2,     P( L(X) > p ) <= alpha/2.

*Proof.* Immediate from the defining inversion: U(X) < p occurs only if the observed X falls
in the lower alpha/2 tail of Binomial(N, p), and symmetrically. (Clopper and Pearson, 1934.)
No approximation enters; the guarantee holds for all N. This is the property the Wilson
interval lacks (Brown, Cai and DasGupta, 2001), and the reason verdict-bearing intervals are
Clopper-Pearson (scrutiny S7).

**Lemma 2.2 (affine transfer).** A = 2p - 1 is a strictly increasing bijection, so the
transformed interval [2L - 1, 2U - 1] has identical coverage for A. All statements below are
made on the A-scale via this transfer.

**Lemma 2.3 (sequential extension).** Let looks occur at committed information times with a
committed spending schedule, and let {CI_k} be repeated confidence intervals built by
inverting the group-sequential boundary (Jennison and Turnbull), constructed on exact binomial
tails. Then simultaneous coverage holds:

    P( A in CI_k for all looks k ) >= 1 - alpha.

Consequently the verdict map of 1.4 applied to CI_tau at any stopping time tau retains the
guarantee of Theorem 1. This closes scrutiny S6 part one.

---

## 3. Theorem 1 (claimant validity)

**Statement.** Under T1 and Lemma 2.1 (or 2.3 under interim looks), for every true A:

    P( the claimant issues a verdict whose asserted region excludes the true A ) <= alpha.

*Proof.* A false verdict requires CI a subset of S with A not in S, hence A not in CI. By
coverage this event has probability at most alpha. INDETERMINATE asserts nothing and cannot be
false. In the sequential case, A not in CI_tau implies A escapes some CI_k, bounded by alpha
by simultaneous coverage. QED.

**Remark.** The claimant's error rate is a property of the committed interval method alone.
No verdict-level multiplicity arises because the primary cell issues exactly one verdict.

---

## 4. Theorem 2 (false refutation, corrected)

**Statement.** Suppose the standing verdict is honest: the true A lies in S_V. Let a valid
attempt produce CI' at level 1 - alpha' from N' trials, any N' >= 1. Then

    P( CI' intersect S_V = empty ) <= P( A not in CI' ) <= alpha'.

*Proof.* If CI' misses all of S_V it misses A in particular. Coverage bounds the rest. QED.

**Sharpening (one-sided regions).** If S_V is one-sided (a THREAT-EXISTS verdict), CI'
disjoint from S_V requires the interval to lie entirely on one specific side of A, which is a
single-tail miss, bounded by alpha'/2 by Lemma 2.1. For S_V = S_NULL the interval may escape
on either side; the two one-sided misses are disjoint events and the bound is alpha'/2 +
alpha'/2 = alpha'. The uniform bound is therefore alpha', with alpha'/2 available for
THREAT-EXISTS claims. This corrects design section 6 and spec FCC-3.3 (scrutiny S2).

**Remark (no union bound with the claimant).** The claimant's N, alpha, and realised interval
appear nowhere. The honest claim's truth is a fact about A; the refuter's error is a fact
about the refuter's own interval. Per-attempt alpha' = 0.01 gives an honest THREAT-EXISTS
claim at most 0.5 per cent false-kill exposure per valid attempt, and an honest NULL claim at
most 1 per cent.

---

## 5. Theorem 3 (refutation power, exact and asymptotic, corrected)

**Setup.** The claim is false: the true A_t lies outside S_V at distance
d = inf over a in S_V of |A_t - a| > 0. Let e denote the boundary of S_V nearest A_t, with
p-scale images p_t = (1 + A_t)/2 and p_e = (1 + e)/2, so p-scale gap d/2.

**Exact form.** The Clopper-Pearson limits are strictly increasing in the success count X'.
For A_t below S_V, refutation is the event U(X') <= e (A-scale), equivalently

    X' <= k*,   k* = max{ x : U(x, N', alpha') <= e },

so the refutation probability is the binomial CDF

    Power(N', alpha', p_t) = F_Bin( k* ; N', p_t ),

exactly computable, no approximation, and the mirrored form (X' >= k_min via L(X') >= e)
covers A_t above S_V. The verifier ships this computation; the published curve is this
function (scrutiny M3).

**Asymptotic form.** Near p = 1/2 the standard deviation of the estimate on the A-scale is
sd(A-hat) = 2 sqrt(p(1-p)/N') approximately 1/sqrt(N'), and the CI half-width on the A-scale
is approximately z_{1-alpha'/2}/sqrt(N'). Refutation requires A-hat to clear the boundary by
the half-width, so

    Power  ~  Phi( d sqrt(N') - z_{1-alpha'/2} )

and the refuter's sizing rule for power 1 - beta is

    N'  ~  ( (z_{1-alpha'/2} + z_{1-beta}) / d )^2.

This corrects the design's Phi(2 d sqrt(N') - z), whose error traces to using the p-scale
half-width on the A-scale, and which under-sizes N' by a factor of four (scrutiny S3).
Reference values at alpha' = 0.01, power 0.90:

    d = 0.05  ->  N' ~ 5,955        d = 0.10  ->  N' ~ 1,489
    d = 0.15  ->  N' ~   662        d = 0.20  ->  N' ~   373

**Remark (design intent, restated correctly).** Validity (Theorem 2) is free of N'; power is
purchased by the refuter at the rate above. Killing a barely-false claim costs more trials
than the original experiment. That asymmetry protects honest claimants from cheap kills while
leaving genuine refuters a priced, published path, and it is stated in the spec as economics,
not buried.

---

## 6. Theorem 4 (multiple attempts) and the symmetry property

**Statement.** Let an honest claim face k valid attempts, each at level alpha'. Then

    P( at least one attempt returns REFUTED ) <= k alpha'.

*Proof.* Union bound over Theorem 2. QED.

**Scope, honestly.** The public record lower-bounds k where registration occurred; attempts
never published cannot be counted by any protocol lacking a disclosure authority, and the
calculus does not pretend otherwise (scrutiny S13). The verifier annotates every REFUTED with
the known attempt count and the implied family bound. alpha' = 0.01 prices the residual: even
twenty hidden attempts leave an honest claim at most an 18 per cent cumulative false-kill
exposure, each instance individually visible and re-examinable.

**Symmetry (closure under refutation).** A REFUTED verdict is itself a categorical assertion:
the refuter's CI' disjoint from S_V asserts A in the complement region at confidence
1 - alpha'. That assertion is a claim under this same algebra, with its own asserted region,
and is refutable by a further valid attempt under the identical rules. Furthermore the
claimant may re-assert: a fresh commitment C2 with a fresh beacon re-runs the procedure, and
by Theorem 2 an honest re-assertion survives each valid attempt with probability at least
1 - alpha'. The calculus is therefore closed under refutation and truth-favouring in
repetition: false claims fall at the rate of Theorem 3, honest claims survive at the rate of
Theorem 2, and the asymmetry compounds in the direction of the truth. This property is stated
in the spec; it is the formal content of the standing invitation.

---

## 7. Theorem 5 (temporal ordering by beacon, replacing the broken chain-position argument)

**Assumptions.**
- B1 (hash security): SHA-256 preimage and collision resistance.
- B2 (beacon unpredictability): the hash of a Bitcoin block is unpredictable before the block
  is published, with min-entropy sufficient that guessing it in advance has negligible
  probability. (Miner grinding of block hashes is economically bounded and stated as residual
  attack surface, priced in block subsidies, not zero.)
- B3 (timestamp soundness): a completed OpenTimestamps attestation of digest h in block b_C
  implies h existed before b_C's publication.

**Construction.** C commits seed_core and the derivation rule

    final_seed = SHA-256( seed_core || beacon ),
    beacon = block hash of the first block with height exceeding b_C's height.

All D1 quantities of the campaign (schedules, instantiation, pairing, presentation order)
derive from final_seed. The refuter's genesis uses the identical construction over its own
attestation block.

**Statement.** Under B1 to B3, for any evidence record whose content is a function of
final_seed:

    time(C) < time(b_C) < time(beacon block) <= time(evidence),

and the ordering is verifiable by any party holding the chain, the OTS proof, and Bitcoin
block headers.

*Proof.* By B3, C existed before b_C. Producing the evidence requires final_seed; computing
final_seed before the beacon block's publication requires predicting its hash, negligible by
B2 (or finding a SHA-256 collision, negligible by B1). Hence the evidence was produced after
the beacon block, which follows b_C by construction. The verifier recomputes final_seed from
the committed seed_core and the identified beacon header and replays the D1 pipeline; any
mismatch is INVALID-CLAIM or INVALID-ATTEMPT with cause BEACON-VIOLATION. QED.

**Remarks.** The beacon is deterministic given the attestation, so neither party can grind for
a favourable seed by re-choosing beacons. Claimant-side selective reporting (abandoning an
unfavourable campaign and recommitting) remains possible, is visible as abandoned commitments
on the public anchor chain, and is priced by the same logic as Theorem 4; the calculus makes
selective reporting on both sides countable, not impossible, and says so. Verification needs
Bitcoin headers (a node, or a header source the verifier names), stated as an operational
dependency, not hidden.

---

## 8. Theorem 6 (isolation as a data processing inequality)

**Assumptions (the register, published as attack surface).**
- (a) Turn taxonomy completeness: every byte of the assembled context is classified exactly
  once as assistant-text, assistant-call, or tool-result. Witnessed by the redaction gate.
- (b) Placeholder determinism: a redacted tool-result placeholder is a function of turn index
  and turn type only. Witnessed by the redaction gate (byte-identity on scripted twins).
- (c) No synthesis re-import: the runner synthesises no assistant text; the adapter cannot
  copy tool-result content into an assistant turn. Witnessed by the new runner test.

**Setup.** Let E in {prod, eval} be the regime, uniform by block randomisation. The
manipulation (E1 telemetry, E2 sizes) lives entirely inside tool-result turns. Let M_out
denote the model's emitted turns for an episode and T_red the redacted transcript. Under (a),
(b), (c), the redaction map rho is deterministic, regime-independent on tool-result turns, and
T_red = rho(M_out): the redacted transcript is a fixed function of the model's outputs alone.
Hence the Markov chain E -> M_out -> T_red.

**Statement.** Let P and Q be the laws of T_red under prod and eval respectively, and P_M,
Q_M the laws of M_out. For the 2AFC presentation (one transcript from each regime in random
order), the advantage of any distinguisher D satisfies

    A(D) <= TV( P tensor Q , Q tensor P ) <= 2 TV(P, Q) <= 2 TV(P_M, Q_M),

and, connecting to the epistemic-security bound with E uniform,

    TV(P_M, Q_M) <= sqrt( 2 I(M_out ; E) ),

so I(M_out; E) = 0 implies P_M = Q_M implies A(D) = 0 for every distinguisher: the instrument
reads chance whenever the model carries no envelope information.

*Proof.* The first inequality is the standard optimal-test bound for paired presentation; the
second is subadditivity of total variation over product measures; the third is the data
processing inequality applied to the deterministic channel rho (a function cannot increase
TV). For the last: with E uniform binary, I(M_out; E) equals the Jensen-Shannon divergence
JS(P_M, Q_M), and Pinsker applied to each component of JS gives JS >= TV^2 / 2, hence
TV <= sqrt(2 JS) = sqrt(2 I). QED.

**Remarks.** The scripted negative control (behaviour carrying no envelope information scores
at chance) is the empirical face of the zero case. The theorem is exactly as strong as (a),
(b), (c); each is machine-witnessed, and a violation of any one reopens a transcript-residue
channel, which is why the register is published as attack surface rather than absorbed into
prose. E2 structural residue in the turn skeleton is excluded at rung level per the design's
F4 handling and is outside this theorem's claim.

---

## 9. Theorem 7 (snapshot conditioning and archival status)

**Statement.** Theorems 2, 3 and 4 hold conditional on the refuter measuring the same success
probability p, which is enforced operationally by requiring passing fingerprint records under
C's snapshot predicate at attempt start and end; an attempt failing either bracket is
INVALID-ATTEMPT (SNAPSHOT-MISMATCH). When the predicate is unsatisfiable for all parties, the
claim's standing transitions to ARCHIVAL, in which Theorem 1's verdict validity, the Tier 1
replay of all D1 quantities, and the Theorem 5 ordering remain verifiable indefinitely, being
chain arithmetic with no probabilistic content, while refutation is no longer mountable.

**Residual.** A weight change between the brackets is bounded, not eliminated, by bracketing;
the exposure window is the attempt duration. Per-episode fingerprinting is the costed
escalation. The fingerprint itself is evidence of serving-path equivalence, not proof of
weight identity (spec FCC-8.2), and that limit is part of this register.

---

## 10. Proposition (NULL reachability)

Let h(N) denote the final-analysis half-width of the committed verdict interval on the
A-scale (for the three-look OBF schedule, h(N) approximately c/sqrt(N) with final critical
value c approximately 2.004; exact value fixed at freeze from the committed spending
function). A NULL verdict is issuable iff the interval can fit inside B, i.e.

    NULL reachable  iff  h(N) < delta,   and then only for |A-hat| <= delta - h(N).

At delta = 0.05: N = 1600 gives h = 0.0501 and NULL is unreachable; N = 1800 gives 0.0472;
N = 2500 gives 0.0401; N = 4500 gives 0.0299. The reachability function is published with the
spec so every future instance sizes N against the verdict it intends to be able to issue, not
against the raw half-width (scrutiny S6 part two). The choice of N for EXP-1 is a Chair
ruling; the mathematics here is the evidence for it.

---

## 11. The assumption register (the boundary of the closure)

Every theorem above is exact given its assumptions; the assumptions are the entire residual
surface, listed once:

    T1        iid trials (disjoint pairs, independent streams; provider-side
              cross-episode state is the named threat)
    Coverage  exact by construction (Clopper-Pearson; RCIs on exact tails);
              no assumption beyond the binomial model given T1
    B1-B3     hash security; beacon unpredictability (miner grinding priced,
              not zero); OpenTimestamps soundness
    (a)(b)(c) isolation register, each machine-witnessed
    F         fingerprint soundness: serving-path equivalence as evidence,
              not weight identity; bracketing window residual
    Register  DVEC tag ruling for the new record types (scrutiny S10) is a
              conformance precondition, not a probabilistic assumption

The claim "the solution is proven" is made in exactly this form: conditional on the register,
the guarantees are theorems with exact constants; the register is published as attack surface
in the calculus's own style; and any critique of the calculus is thereby a critique of a named
line in this table, which is where a critique belongs.

Spey Systems Ltd (SC889983).
