"""Generate the runner-replay integration vectors (pass two, leg 2).

Run, beside an exp1-runner checkout at the RUNNER_HEAD pinned in PINS.json:

    EXP1_RUNNER=~/axilog/exp1-runner python3 tools/gen_integration.py

or with exp1-runner as a sibling directory of this repo. Intended host is
axioma, beside the checkout of record. chain.py itself is Python stdlib and
its frame emission is architecture-independent (SHA-256 over committed
bytes); the aarch64 constraint belongs to the exp1-runner substrate battery
(librig.so and the cshim cross-checks), not to this generator. The head of
the sibling checkout is NOT verifiable from here (a working tree carries no
authoritative head); confirming the checkout is at the pinned RUNNER_HEAD is
the chair's witness step, per PINS.json discipline.

CI does not run this generator (foreign writer). The tamper gate CI holds is
the SHA-256 manifest: golden/integration-manifest.json records the hash of
every committed integration .bin, and tests/test_integration.py asserts hash
match, verdict replay, and byte-determinism. Regenerating here after any
writer change will change the hashes, which is the gate working.

Conviction hierarchy, held from the pass-one commit message: these vectors
confirm integration (the verifier's own reader consumes the writer of record
byte-for-byte); they do not carry the conviction. The hand-derived v-series
remains the primary evidence.

The two pairs:

    iv01  NULL claim, refuter k=6,  n=12  -> UPHELD   (v01 arithmetic)
          claimant chain also carries an AX:FCC:TS:v1 record, exercising
          the reader's tolerance of registered non-C tags on a claimant
          chain, a surface the hand set never touches.
    iv02  NULL claim, refuter k=12, n=12  -> REFUTED  (v02 arithmetic)

Payloads are constructed here, standalone, in the canonical form FCC-1.1
requires; this module deliberately does not import fccverify.buildvec, so
the writer side shares no code with the verifier's test helpers.
"""

import hashlib
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
GOLDEN = os.path.join(REPO, "golden")


def _find_runner():
    cand = os.environ.get("EXP1_RUNNER")
    if cand and os.path.isdir(cand):
        return cand
    sibling = os.path.join(os.path.dirname(REPO), "exp1-runner")
    if os.path.isdir(sibling):
        return sibling
    raise SystemExit(
        "exp1-runner checkout not found: set EXP1_RUNNER or place the "
        "checkout as a sibling of this repo")


RUNNER = _find_runner()
sys.path.insert(0, RUNNER)
from runner import chain  # noqa: E402  the writer of record


def _canon(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def claim_c_payload():
    """Field-complete NULL C, standing parameters (delta 5/100, alpha'
    1/100), canonical per FCC-1.1. Values the verdict path reads are real;
    the rest are the same placeholders the hand vectors carry."""
    return _canon({
        "seed_core": "00" * 32,
        "battery_blob": "64f2f601d3f3e988d77e14bd6e780d402954808c",
        "pool_blob": "12b1478dfdafbf69eed9af669174b0d5ba767e54",
        "estimator_code": "e791b35",
        "decision_rule": {"verdict": "NULL", "delta_num": 5,
                          "delta_den": 100},
        "N": 2500,
        "alpha": {"num": 5, "den": 100},
        "R": {"tiers": ["A", "B"], "alpha_prime_num": 1,
              "alpha_prime_den": 100},
        "snapshot_predicate": "fingerprint-battery-v1",
        "pattern_set_version": "SRS-EC-001@v1",
        "adapter_version": "gateway@1",
        "redactor_version": "redact@1",
        "verifier_commit": "TBD-PASS-TWO",
        "calculus_version": "FCC-001-v0.4.1",
        "spending_schedule": "OBF-3look",
        "episode_completion_rule": "all-or-void",
        "beacon_rule": {"calendars": ["a", "b"], "K": 1, "D": 6},
        "w_min": {"num": 5, "den": 1000},
    })


def write_chain(path, records):
    """Write a chain through the writer of record. EvidenceChain replays an
    existing file on open, so the target is removed first for a clean
    deterministic build."""
    if os.path.exists(path):
        os.remove(path)
    c = chain.EvidenceChain(path)
    try:
        for tag, payload in records:
            c.append(tag, payload)
    finally:
        c.close()


def build_pair(name, k, n, with_ts):
    c_payload = claim_c_payload()
    claim_records = [(chain.TAG_STATE, b'{"state":"open"}')]
    if with_ts:
        claim_records.append((chain.TAG_FCC_TS, _canon(
            {"kind": "ots", "target": "AX:FCC:C:v1",
             "proof": "deadbeef" * 8})))
    claim_records.append((chain.TAG_FCC_C, c_payload))

    c_hash = chain.commit(chain.TAG_FCC_C, c_payload).hex()
    reg = _canon({
        "claim_c_hash": c_hash,
        "alpha_prime_num": 1,
        "alpha_prime_den": 100,
        "n_prime": n,
        "episode_completion_rule": "all-or-void",
        "beacon_rule": {"calendars": ["a", "b"], "K": 1, "D": 6},
    })
    ref_records = [(chain.TAG_STATE, b'{"state":"refuter"}'),
                   (chain.TAG_FCC_REG, reg),
                   (chain.TAG_OBS, _canon({"kind": "snapshot",
                                           "endpoint": "start"}))]
    for i in range(n):
        ref_records.append((chain.TAG_OBS, _canon(
            {"kind": "trial", "success": i < k})))
    ref_records.append((chain.TAG_OBS, _canon({"kind": "snapshot",
                                               "endpoint": "end"})))

    claim_path = os.path.join(GOLDEN, name + ".bin")
    ref_path = os.path.join(GOLDEN, name + ".refuter.bin")
    write_chain(claim_path, claim_records)
    write_chain(ref_path, ref_records)
    return claim_path, ref_path


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    pairs = [
        ("iv01_integration_upheld", 6, 12, True, "UPHELD", None,
         "runner-written pair, k=6 n=12, v01 arithmetic; claimant chain "
         "carries an AX:FCC:TS:v1 record"),
        ("iv02_integration_refuted", 12, 12, False, "REFUTED", None,
         "runner-written pair, k=12 n=12, v02 arithmetic"),
    ]
    manifest = []
    for (name, k, n, with_ts, expected, cause, note) in pairs:
        claim_path, ref_path = build_pair(name, k, n, with_ts)
        manifest.append({
            "name": name + ".bin",
            "sha256": sha256(claim_path),
            "refuter": name + ".refuter.bin",
            "refuter_sha256": sha256(ref_path),
            "expected": expected,
            "cause": cause,
            "note": note,
            "written_by": "exp1-runner chain.py at the RUNNER_HEAD "
                          "pinned in PINS.json",
        })
        print("  wrote %s (k=%d, n=%d)" % (name, k, n))
    with open(os.path.join(GOLDEN, "integration-manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("  manifest: golden/integration-manifest.json")


if __name__ == "__main__":
    main()
