# Phase 1 verification

Phase 1 is published for review on branch `codex/phase-1` in pull request #1.

- The pipeline regenerates the 3,000-row synthetic dataset, processed CSV/JSON outputs, five figures, and README findings from seed 42.
- Persisted data pass all 22 schema, type, sequence, timestamp, range, category, and unit-balance checks.
- All 17 unit tests pass, including negative cases for each validation rule.
- Every notebook code cell executes without an error output.
- README numerical findings are generated from the saved analysis results.
- GitHub Actions repeats the tests, pipeline, deterministic analytical-output check, and notebook execution on pushes and pull requests.

The dataset is synthetic and intended only for demonstration. Phase 2 methods are not included.
