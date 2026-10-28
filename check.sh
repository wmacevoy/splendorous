#!/bin/sh
# The full check: one recipe for a contributor and for CI, so there is no second one to drift (SE1/O3).
# The interpreter is chosen the way `se` chooses it: python3 where it exists, else python.
# The gate is here, in the script, not only in the workflow: it stops at the first failure.
set -e
cd "$(dirname "$0")"
py=$(command -v python3 2>/dev/null || command -v python)
"$py" -m compileall -q splendorous tests
"$py" -m unittest discover -s tests
echo "check: OK"
