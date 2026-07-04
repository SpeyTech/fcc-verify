"""fccverify.cli: the command-line verdict program.

Usage:
    python3 -m fccverify.cli CLAIM.bin [--refuter REFUTER.bin]
        [--beacon BEACON.json] [--timestamp OTS.json]
        [--attempt-count K] [--record OUT.json]

Reads the claimant chain and, if supplied, the refuter chain, through the
verifier's own reader (requirement 2). The refuter chain carries its genesis as
AX:FCC:REG:v1 and its per-trial outcomes as AX:OBS:v1; the verdict path reduces
it (there is no separate summary transport). Beacon and timestamp material are
input-fed, never network-fed (requirement 4).

Emits exactly one word to stdout: UPHELD, REFUTED, INVALID-ATTEMPT, or
INVALID-CLAIM. The full verdict record goes to --record if given, else to
stderr. Exit codes: UPHELD 0, REFUTED 2, INVALID-ATTEMPT 3, INVALID-CLAIM 4.
"""

import argparse
import json
import sys

from fccverify import verdict

EXIT = {
    verdict.UPHELD: 0,
    verdict.REFUTED: 2,
    verdict.INVALID_ATTEMPT: 3,
    verdict.INVALID_CLAIM: 4,
}


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="fccverify", description="FCC-001 v0.4.1 verdict program.")
    ap.add_argument("claim", help="claimant chain (.bin)")
    ap.add_argument("--refuter", help="refuter chain (.bin)")
    ap.add_argument("--beacon", help="beacon block header (.json), input-fed")
    ap.add_argument("--timestamp", help="OTS proof (.json/.ots), input-fed")
    ap.add_argument("--attempt-count", type=int,
                    help="registered attempt count k for annotation")
    ap.add_argument("--record", help="write verdict record JSON here")
    args = ap.parse_args(argv)

    with open(args.claim, "rb") as fh:
        claim_bytes = fh.read()
    refuter_bytes = None
    if args.refuter:
        with open(args.refuter, "rb") as fh:
            refuter_bytes = fh.read()

    v = verdict.adjudicate(claim_bytes, refuter_bytes=refuter_bytes,
                           attempt_count=args.attempt_count)

    # Beacon and timestamp are input-fed. Presence recorded here; content
    # derivation lands with the harness pin. Absence is deferred, not skipped.
    if args.beacon:
        v.check("claim.beacon_input_present", "pass", args.beacon)
    if args.timestamp:
        v.check("claim.timestamp_input_present", "pass", args.timestamp)

    _emit(v.verdict, v.as_record(), args.record)
    return EXIT[v.verdict]


def _emit(word, record, record_path):
    sys.stdout.write(word + "\n")
    sys.stdout.flush()
    blob = json.dumps(record, indent=2, sort_keys=True)
    if record_path:
        with open(record_path, "w") as fh:
            fh.write(blob + "\n")
    else:
        sys.stderr.write(blob + "\n")


if __name__ == "__main__":
    sys.exit(main())
