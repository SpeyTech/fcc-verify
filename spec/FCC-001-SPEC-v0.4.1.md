# FCC-001

## Falsifiable Claim Calculus

**Version:** v0.4.1 — Freeze candidate (cleared)
**Status:** Design review, post-scrutiny round four
**Scope:** Axioma Framework · any measurement publishing a claim about a stochastic system
**Alignment:** DVEC-001 v1.4 (pending, AX:FCC block) · AXIOMA-FRAMEWORK v0.4 §4.4 · epistemic-security paper · Patent GB2521625.0
**Conformant instance zero:** EXP-1 (L0-EXP1-DESIGN.md rev B, at freeze)
**Self-contained:** states its own mathematical content and serialisation. The design document is
cited as rationale only, never normatively.

---

## Revision History

| Version | Status | Notes |
|---------|--------|-------|
| v0.1 | Superseded | Initial draft. Four mathematical defects found in scrutiny. |
| v0.2 | Superseded | Folded scrutiny round one (S1 to S16). Introduced one new defect (V1) and left three (V2 to V4). |
| v0.3 | Superseded | Folded round two: annotation not gating (V1), pinned multi-calendar beacon (V2), calculus law separated from instance parameters (V3), refuter genesis symmetry and M2 dependency (V4). Beacon still admitted subset grinding and reorg instability (W1). |
| v0.4 | Superseded | Folded round three: full-calendar beacon with lag and depth (W1), verifier genesis set (W2), refuter-procedure replay (W3), w_min parameterised (W4), exact binomial power normative (W5). Dead-calendar fallback reopened a smaller grinding menu (X1). |
| v0.4.1 | Freeze candidate (cleared) | Round four found one corner in the round-three fix (X1, the fallback path for a failure mode not yet occurred) and two stale labels (X2, X3). Fallback now commits the reduced calendar set before its heights are knowable, closing the residual menu. Convergence signature: each round's findings smaller than the last, the last living in a fallback for a failure that has not happened. |

---

## 0. Governing Principle

> **A claim is conformant only if a party who wants it false can either replay its evidence or
> mount a refutation whose validity rests on their own confidence coverage and an unpredictable
> post-commitment beacon, adjudicated by a program, not by argument.**

FCC composes with DVEC. DVEC guarantees faithful execution; FCC guarantees a claim about a
stochastic system is falsifiable. FCC Tier 1 replay is a DVEC replay.

## 1. The Commitment Object C (SHALL)

**FCC-1.1** A conformant claim SHALL publish C before any observation, where C is the
domain-separated SHA-256 (tag AX:FCC:C:v1) over the RFC 8785 canonical JSON of the ordered field
set:

    seed_core, battery_blob, pool_blob, estimator_code, decision_rule, N, alpha,
    R, snapshot_predicate, pattern_set_version, adapter_version, redactor_version,
    verifier_commit, calculus_version, spending_schedule, episode_completion_rule,
    beacon_rule, w_min

**FCC-1.2** C SHALL be Dependency-Closed under framework §4.4: every input influencing the verdict
appears in C.

**FCC-1.3** The final seed SHALL derive by the beacon rule (FCC-5.3). Every D1 quantity derives from
final_seed, so evidence provably postdates C.

## 2. The Verdict (SHALL)

**FCC-2.1** The result SHALL be one of THREAT-EXISTS, NULL, INDETERMINATE, against a pre-committed
two-sided band B_band = (-delta, +delta) on A, with a Clopper-Pearson interval as the verdict-bearing
interval and Wilson reported as descriptive only.

**FCC-2.2** THREAT-EXISTS SHALL require the CP interval on A to exclude B_band on one side. NULL SHALL
require the CP interval to lie entirely within B_band. INDETERMINATE SHALL be reported otherwise and
SHALL NOT be rounded.

**FCC-2.3 (reachability invariant, calculus law).** Under a committed sequential design with
alpha-spending, the verdict interval SHALL be the repeated confidence interval at the committed
spending schedule, which retains nominal coverage under optional stopping. The committed N SHALL
satisfy the reachability invariant

    h(N) < delta

where h(N) is the exact Clopper-Pearson repeated-CI final half-width computed from the committed
spending function, so that both verdicts are reachable. The reachability function h and the achieved
window (delta - h(N)) SHALL be computed at freeze and published. C SHALL commit a reachability floor
w_min, and FCC-2.3 SHALL require delta - h(N) >= w_min, freeze blocked otherwise (W4). w_min is a
committed instance parameter, not a calculus constant, so no future instance with a different band
inherits a magic number. Instance-specific values (band, look schedule, N, w_min) live in the
instance mapping, not in this clause (V3).

## 3. The Refutation Condition R (SHALL)

**FCC-3.1** C SHALL commit R: the two tiers (replication against committed code; reproduction against
this specification and golden vectors), the per-attempt refuter level alpha', and the beacon rule for
the refuter genesis.

**FCC-3.2** Let S be the region of A asserted by the claimant's verdict. A verdict SHALL be refuted by
a valid attempt whose Clopper-Pearson interval CI' at the refuter's committed alpha' is disjoint from
S. This one definition covers both verdicts and both signs.

**FCC-3.3** The false-refutation rate of an honest categorical claim SHALL be bounded uniformly by
alpha' from the refuter's coverage alone: P(false refutation) <= P(A not in CI') <= alpha', with no
dependence on the claimant's N, alpha, or interval. For one-sided S the sharper alpha'/2 holds and
MAY be stated as a remark.

**FCC-3.4** No minimum N' SHALL be imposed. The normative power computation SHALL be the exact
binomial form of algebra Theorem 3; the verifier and the published power curve SHALL use it. The
A-scale closed form N' approximately ((z(alpha') + z(beta)) / d)^2, using the half-width z/sqrt(N'),
is quoted as an approximation for sizing only (W5). At d = 0.05, alpha' = 0.01, power 0.90 the exact
computation gives N' approximately 5955.

## 4. Isolation (SHALL, where the claim rests on a redacted surface)

**FCC-4.1** The specification SHALL publish the isolation assumption register: (a) turn taxonomy
completeness, (b) placeholder determinism, (c) no synthesis re-import. Each is named as attack
surface.

**FCC-4.2** (a) and (b) SHALL be witnessed by a machine-checked redaction identity gate on the
control twins. (c) SHALL be witnessed by a runner test.

**FCC-4.3** The manipulation-to-distinguisher channel SHALL factor through the model as a data
processing inequality on regime -> M -> T_red, bounding observable divergence by I(M; E).

## 5. External Timestamping and the Beacon (SHALL)

**FCC-5.1** C SHALL bind to OpenTimestamps as the primary attestation (block-chain). RFC 3161 MAY be
committed alongside for an immediate token where a named authority is wanted. Verification of the
block-chain attestation requires Bitcoin block headers from a node or a named header source; this
operational dependency (M2) SHALL be stated, and no-trusted-party refers to the attestation trust
model, not to the absence of a header source (V4).

**FCC-5.2** Temporal ordering C-before-evidence SHALL rest on the beacon rule, not on chain position,
which is claimant-authored. The timestamp proof and the beacon block reference SHALL be evidence-chain
records.

**FCC-5.3 (beacon rule, subset-grinding and reorg closed).** Three committed elements, because the
minimum-attestation-height rule of v0.3 still handed the claimant a seed menu (W1).

- **Full calendar set committed.** beacon_rule SHALL name the calendar set. The committed proof file
  SHALL carry attestations from the full committed set, which removes subset choice: the claimant
  cannot capture a favourable attestation subset because a proof missing any committed calendar is
  malformed. The minimum attestation height m is then unique, not selected. A committed fallback
  covers a dead calendar (below).
- **Dead-calendar fallback, committed before the unpredictable value (X1).** After 144 blocks without
  attestation from a committed calendar, the claimant MAY proceed on a reduced set, but SHALL first
  write and timestamp a deviation record naming the reduced calendar set, then re-stamp C to that
  reduced set. The full-set rule then applies to the reduced set. Because the reduced set is fixed and
  committed before its attestation heights are knowable, no candidate-m menu exists at any point: the
  claimant cannot choose which calendar to drop for a favourable beacon, because the drop is committed
  before the resulting heights can be computed. The deviation record remains visible on chain. Without
  this ordering the fallback would reopen a smaller copy of the subset-grinding menu (the verifier
  cannot distinguish a genuinely dead calendar from a discarded attestation, so an unconstrained
  fallback is a grind a patient claimant invokes at will). With it, subset grinding is removed on the
  fallback path as on the main path, not merely priced.
- **Committed lag and confirmation depth.** The beacon SHALL be the hash of the block at height
  m + K, with K committed in beacon_rule (K = 1 is sufficient once subset choice is gone). The beacon
  SHALL be usable only once the block at m + K is buried under D confirmations, D committed (D = 6 is
  the conventional depth). The verifier SHALL check the beacon against the canonical chain at depth D.
  This closes reorg instability: a beacon that could change hash under a shallow reorg is not yet
  usable, so the verdict program cannot return different results by run time.
- **Residual stated honestly.** A claimant colluding with miners to reorg the beacon block at depth D
  is theoretically possible and economically priced in block subsidies, the same register entry as
  B2's grinding note. Subset grinding is removed (not priced); reorg collusion is priced.

Why v0.3 was insufficient: at ots-upgrade time block m + 1 already exists for every candidate
attestation subset, so the claimant could compute each candidate beacon, run the D1 pipeline forward
under each candidate final_seed, and commit the subset whose seed they preferred. The ordering
sandwich survived, but determinism across honest verifiers did not, because the committed proof was
claimant-chosen from a menu. Committing the full calendar set forces m, which is the only fix that
removes the choice rather than shrinking it. After this the beacon's remaining assumptions are all
named register lines: B1 (timestamp soundness), B2 (grinding and reorg priced), calendar liveness,
and confirmation depth.

## 6. The Verdict Program (SHALL)

**FCC-6.1** Adjudication SHALL be a deterministic verifier emitting one of UPHELD, REFUTED,
INVALID-ATTEMPT, INVALID-CLAIM from the claimant chain and a refuter chain. Prose adjudication is
non-conformant.

**FCC-6.2** The verifier SHALL check, in order:
- Claim well-formedness: C present, RFC 8785 serialised, OpenTimestamped, beacon-seeded; claimant
  evidence replays bit-exact (Tier 1). Failure SHALL emit INVALID-CLAIM with cause (FABRICATION,
  MALFORMED, UNTIMESTAMPED, BEACON-VIOLATION).
- Attempt well-formedness: the refuter genesis commits C's hash, the refuter alpha', N', the episode
  completion rule, and the beacon rule, is OpenTimestamped and beacon-seeded, and the refuter evidence
  replays bit-exact under the refuter's own committed procedure and code with the refuter's final_seed
  (W3). A refuter who honestly ran a different battery or a Tier B reimplementation replays cleanly
  under their own committed procedure and MUST NOT trip FABRICATION; the cause taxonomy distinguishes
  a non-replaying attempt (FABRICATION) from a validly different one. Failure SHALL emit
  INVALID-ATTEMPT with cause (UNREGISTERED, BEACON-VIOLATION, FABRICATION, SNAPSHOT-MISMATCH,
  INCOMPLETE).
- Snapshot: passing fingerprint records at attempt start and end, else INVALID-ATTEMPT cause
  SNAPSHOT-MISMATCH. Predicate unsatisfiable for all parties transitions the claim to ARCHIVAL.
- Categorical test: recompute CI' at the refuter alpha'; disjoint from S emits REFUTED, else UPHELD.

**FCC-6.3** The verifier SHALL be a D1 component with golden vectors, reproducible by any third party.

## 7. Cross-Chain Refutation Protocol (SHALL)

**FCC-7.1** A refutation attempt SHALL open its own chain whose genesis commits C's hash, the refuter
alpha', N', the episode completion rule, and the beacon rule, OpenTimestamped, before collecting
data. Validity rests on this genesis alone.

**FCC-7.2** The claimant registry committing the refuter head is a courtesy index, not a validity
precondition. A claimant's non-response is itself visible on the public chain and does not impair the
attempt. This removes the registry veto.

**FCC-7.3 (annotation, not gating).** An attempt whose evidence predates its beacon-seeded genesis
SHALL be INVALID-ATTEMPT. The per-attempt verdict at alpha' stands on its own coverage. The count of
attempts is not computable from the two chains alone, so the verifier SHALL accept an optional set of
attempt geneses and SHALL annotate every REFUTED with the cardinality k of that supplied set and the
implied family bound k times alpha', stated as a lower bound whose completeness is the reader's
concern (W2). This keeps the verifier deterministic: its output is a function of its declared inputs,
and the attempt-genesis set is one of them. The count SHALL NOT gate the per-attempt verdict: it is
manipulable in both directions (a claimant could register sham attempts against its own C to inflate
k and shield against refutation; a refuter could split attempts), so it informs and never gates
(V1). The residual is priced by alpha', not corrected away.

## 8. Closure Under Refutation (property, stated not hedged)

A refutation attempt is itself a claim under this calculus with roles swapped. A REFUTED verdict is
therefore itself refutable, and an honest claimant re-asserts under a fresh beacon. False claims fall
at the FCC-3.4 power rate; honest claims survive at the FCC-3.3 rate; the asymmetry compounds toward
the truth in the repeated game. This is the compensating strength for pricing rather than gating
hidden attempts.

## 9. Scope and Honesty (SHALL)

**FCC-9.1** Every claim SHALL bind the tested snapshot, surface, battery, and calculus version.

**FCC-9.2** Snapshot identity SHALL be scoped as evidence, not proof: strong falsifiability while the
snapshot serves and the fingerprint holds, archival afterwards. The fingerprint's limits (no
weight-identity proof, possible vendor special-casing) SHALL be stated.

**FCC-9.3** The specification SHALL NOT claim satisfaction of any named regulation. It MAY state it
produces the integrity record such regulation presupposes.

---

## Conformance Checklist

- [ ] C published, RFC 8785 serialised, Dependency-Closed, beacon-seeded, before evidence (FCC-1, 5)
- [ ] Verdict categorical, Clopper-Pearson, repeated-CI, reachability invariant h(N) < delta (FCC-2)
- [ ] R committed: two tiers, alpha', correct power curve (FCC-3)
- [ ] False-refutation <= alpha' by coverage, CI' disjoint from S (FCC-3)
- [ ] Isolation register published and witnessed (FCC-4)
- [ ] OpenTimestamp, full-calendar beacon with committed lag K and depth D, header dependency (FCC-5)
- [ ] Verifier: four verdicts, refuter replay under refuter procedure, snapshot checked, INCOMPLETE (FCC-6)
- [ ] Cross-chain protocol, refuter-only validity, annotation with supplied genesis set (FCC-7)
- [ ] Reachability floor committed as w_min, exact binomial power normative (FCC-2.3, FCC-3.4)
- [ ] Closure-under-refutation property stated (FCC-8)
- [ ] Scope bound, snapshot as evidence, no regulation-satisfaction claim (FCC-9)
- [ ] DVEC-001 v1.4 AX:FCC block registered (S10, ruled: amendment)

---

## EXP-1 Mapped Clause by Clause (instance parameters live here)

| Clause | EXP-1 instance value | Gap to close |
|--------|----------------------|--------------|
| FCC-1 C | 18 fields; six new (verifier_commit..beacon_rule, w_min) | Add to TBD-F, RFC 8785, AX:FCC:C:v1 tag |
| FCC-2 band | delta = 0.05, three-look OBF | **N = 2500**. Illustrative windows (superseded by the exact freeze computation, not to be cited as authority): 2500 gives about +/-0.009, 1800 about +/-0.003 a knife-edge, CP-corrected floor near N = 2100. The exact CP-RCI computation at freeze governs. |
| FCC-2.3 reachability | w_min = 0.005 (instance value); h(2500) gives delta - h >= w_min | Compute exact CP-RCI half-width at freeze; freeze blocked unless delta - h(N) >= w_min |
| FCC-3 R | alpha' = 0.01; d=0.05 power 0.90 needs N' ~ 5955 | Add R and power curve to TBD-F |
| FCC-4 isolation | redaction gate green; (a)(b) witnessed | runner test for (c) |
| FCC-5 timestamp | OpenTimestamps over C, full-calendar-set beacon at m + K under depth D | build attestation and beacon records, dead-calendar fallback with committed reduced set |
| FCC-6 verifier | absent | build, four verdicts, golden vectors, pin commit |
| FCC-7 cross-chain | chain.py writer exists | add genesis and registration records, refuter replay |
| FCC-8 closure | property | state in prereg |
| FCC-9 scope | rev B scope and fingerprint stated | none |
| Registry | AX:FCC tag block | DVEC-001 v1.4 amendment (below) |

Frozen and unchanged: battery 64f2f601, pool 12b1478d, band delta = 0.05, RUNG statistics, stage 0
gates, harness and experiment commits. Changing at freeze: N (to 2500), interval method (to
Clopper-Pearson), seed derivation (beacon), none a frozen artefact.

## The freeze gate (V3 invariant made operational, W4 parameterised)

Freeze SHALL be blocked unless the exact Clopper-Pearson repeated-CI final half-width, computed from
the committed spending function, gives a reachability window (delta - h(N)) of at least the committed
w_min. EXP-1's instance value is w_min = 0.005. The exact computation at freeze governs; the
following are illustrative only and superseded by it: at delta = 0.05 three-look OBF the gate rejects
N = 2000 (window about 0.004 under CP) and passes N = 2500 (about 0.009), with the CP-corrected floor
near N = 2100. The gate, parameterised by the committed w_min, ensures the knife-edge trap cannot
recur at any future instance whatever its band.

## DVEC-001 v1.4 amendment (S10 ruled: amendment, not mapping)

The FCC record types get their own tag block, not a mapping onto AX:STATE and AX:PROOF, because
domain separation exists to make cross-type collisions impossible at the tag layer. DVEC-001 v1.4
registers the AX:FCC block, proposed tags AX:FCC:C:v1, AX:FCC:TS:v1, AX:FCC:REG:v1,
AX:FCC:VERDICT:v1, under the full DVEC section 0.1 amendment discipline: migration assessment,
re-verification statement, changelog entry, no silent adoption. This unblocks the verifier build and
keeps the closed registry closed by the only legitimate route, versioning it.

## v0.4.1 as freeze candidate (cleared)

Round-four finding folded (X1: the dead-calendar fallback reopened a smaller subset-grinding menu,
now closed by committing the reduced calendar set before its attestation heights are knowable) and
two stale labels corrected (X2 field count, X3 beacon label). The beacon's remaining assumptions are
all named register lines (B1, B2, calendar liveness, confirmation depth). Three rulings from round two
stand: N = 2500, registry amendment (DVEC-001 v1.4 AX:FCC block), fixed-N exact-binomial for instance
zero with e-processes named as the later upgrade path.

The convergence signature is on the record: round one found four mathematical defects, round two one
new defect the fix introduced, round three one corner of the beacon, round four one corner of the
round-three fix living in a fallback for a failure mode that has not occurred. Each round smaller than
the last. Instance zero's job is to be unimpeachable, not elegant: nothing stands between the verdict
program and its critics except the assumption register, and the register is now the noise floor.

This is the cleared freeze candidate. The work now leaves the specification layer: the DVEC-001 v1.4
amendment text, the verifier build with golden vectors, the fingerprint battery, and the freeze packet
with the re-run cost model. At N = 2500 the frontier tier is roughly 8,600 episodes, about USD 1,760
before contingency, inside the GBP 2,000 ceiling with less slack than rev B; re-run the cost model at
freeze against the final cell table.

Spey Systems Ltd (SC889983). Patent GB2521625.0 (retained as dated attribution).
