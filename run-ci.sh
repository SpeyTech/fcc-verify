#!/bin/sh
# fcc-verify CI: golden vectors, determinism, exact arithmetic. Stdlib only.
# ax-rtm-verify.py is N/A here: this repo has no RTM, it is the verifier.
set -e
echo "== exact arithmetic =="
python3 -m tests.test_exact
echo
echo "== golden vectors: committed bytes match generator =="
python3 -m tests.gen_golden --check
echo
echo "== golden replay + determinism =="
python3 -m tests.test_verify
echo
echo "CI green"
