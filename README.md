# fcc-verify

The FCC-001 verdict program.

**The SDK is how you make a claim; fcc-verify is how your enemy checks it. They
share a specification, not code.**

fcc-verify reads a claim made under the Falsifiable Claim Calculus (FCC-001
v0.4.1), optionally a refutation attempt against it, and returns one word:

    UPHELD | REFUTED | INVALID-ATTEMPT | INVALID-CLAIM

The verdict follows from the committed procedure and the committed refutation
condition alone. It is deterministic: the same inputs give the same verdict and
a byte-identical verdict record, on any machine, forever. There is no model
call, no network fetch in the verdict path, and no floating point in any
comparison that decides a verdict.

## Why this exists

A measurement about a stochastic system, "this model does not condition on the
execution envelope", is only falsifiable if the procedure and the refutation
condition are fixed before the data and cannot be moved after it. FCC-001 fixes
them in a commitment. fcc-verify is the program that checks a claim against its
own commitment, run by whoever wants the claim dead. If it says UPHELD, the
claim survived a check its enemies could run themselves.

## Requires

Python 3.8 or later. Standard library only. No dependencies, by design: a
hostile cloner needs an interpreter and nothing else.

## Clone to verdict

    git clone https://github.com/SpeyTech/fcc-verify
    cd fcc-verify
    python3 -m tests.gen_golden          # build and check the golden vectors
    python3 -m fccverify.cli golden/v02_refuted_null_positive.bin \
        --refuter golden/v02_refuted_null_positive.refuter.bin
    # prints: REFUTED

The exit code carries the verdict for scripting: 0 UPHELD, 2 REFUTED, 3
INVALID-ATTEMPT, 4 INVALID-CLAIM.

## Verifying a real claim

    python3 -m fccverify.cli CLAIM.bin \
        --refuter REFUTER.bin \
        --beacon BEACON_HEADER.json \
        --timestamp CLAIM.ots \
        --record verdict.json

`CLAIM.bin` and `REFUTER.bin` are evidence chains in the FCC-001 frame format.
The verifier reads them with its own reader, reimplemented from the frame
format of record; it does not import the claimant's writer.

Beacon and timestamp material are input-fed, never fetched by this program:

- **Beacon.** The claim commits to a public randomness beacon (a Bitcoin block
  at a committed height plus lag, under a committed confirmation depth). Supply
  the block header as JSON. Obtain it from any source you trust and can check
  independently: mempool.space, a full node's `getblockheader`, or a pruned
  node. The verifier recomputes the final seed from it; it does not trust your
  source, only the header's own proof of work and the committed height.
- **Timestamp.** The claim's commitment is timestamped so it cannot be
  backdated. Supply the OpenTimestamps proof (`.ots`) or an RFC 3161 token. The
  verifier checks the commitment predates the beacon; it does not contact a
  calendar server.

If you omit either, the verifier records the corresponding check as deferred in
the verdict record rather than skipping it silently. A verdict record always
enumerates exactly what was checked and what was deferred.

## What the verdict record tells you

Each run emits a record (the `AX:FCC:VERDICT:v1` payload) listing every check
run with its outcome, and every check deferred with the reason. This is the
honest scope boundary: fcc-verify checks what a minimal clone can check from
the chain and the input-fed material. The checks that need the full measurement
harness, re-deriving per-episode outcomes from transcripts, are named in the
`deferred` list, not passed over.

## Layout

    fccverify/reader.py    own verifying frame reader (spec of record)
    fccverify/registry.py  DVEC v1.4 evidence tag set, membership check
    fccverify/exact.py     exact Clopper-Pearson by binomial tail sums
    fccverify/verdict.py   the FCC-001 6.2 verdict pipeline
    fccverify/cli.py       command-line entry point
    spec/                  FCC-001-SPEC-v0.4.1.md, the specification of
                           record, and FCC-001-CLAIM-ALGEBRA-v0.1.md, the
                           formal derivations behind it
    golden/                committed vectors, one per verdict and cause,
                           plus the runner-written integration pairs and
                           their hash manifest
    tools/                 gen_integration.py, the integration-vector
                           writer harness (runs beside an exp1-runner
                           checkout, not in CI)
    PINS.json              foreign trees this suite was derived against
    VECTORS.md             hand derivation of every vector

## Pass two

Pass one built the verdict program and the hand-derived golden vectors.
Pass two pins the foreign trees (PINS.json: axioma-spec for the registry of
record, exp1-runner for the writer), commits the claim algebra beside the
spec so a Tier B refuter has the proofs next to the text they implement,
and adds the runner-replay integration vectors iv01 and iv02, written by
the actual exp1-runner chain.py and gated by SHA-256 manifest since CI
cannot run the foreign writer. The conviction hierarchy is unchanged: the
hand-derived vectors are the primary evidence, derived from the
specification in VECTORS.md; the integration pairs confirm the verifier's
independently reimplemented reader consumes the writer of record
byte-for-byte, nothing more. The head of the commit that closes pass two is
the verifier_commit harvested into the EXP-1 C at freeze, which is why it
cannot be pinned here: the pin certifies the suite, so it must postdate it.

## Licence

AGPL-3.0. The verifier is meant to be cloned, read, and run by adversaries;
the licence keeps it that way.
