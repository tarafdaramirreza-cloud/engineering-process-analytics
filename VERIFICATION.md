# Phase 1 verification — synthetic demonstration data

- Executed with Python 3.12 in a newly created virtual environment using requirements.txt versions.
- Pipeline: passed 26 validation checks on the persisted 3,000-row CSV.
- Tests: 4 passed, covering reproducibility, schema/count, bounds/unit balance, and rejection of invalid data.
- Notebook: all code cells executed; no error outputs.
- README: headline values independently checked against saved CSV means; findings are generated from the analysis results.
- Figures: all four PNGs inspected for labels, units, layout, and synthetic-data disclosure.
- Local environment: notebook first failed because the sandbox blocks the default IPython home cache. Rerun succeeded with IPYTHONDIR, MPLCONFIGDIR, and JUPYTER_CONFIG_DIR pointing to writable work directories. Windows emitted a nonfatal ZeroMQ event-loop warning.
- Git checkout could not be established: bundled Git first failed to locate its HTTPS helper; after locating it, Windows TLS credential initialization failed. Deliverables are local files, not a Git checkout or a published GitHub commit.
- Phase 2 has not been started.
