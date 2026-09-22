# Personal cluster safety

- On hosts matching `slurm-login-*`, never directly run pytest, training,
  compilation, data processing, or `pixi install`. Submit compute through
  SLURM with explicit CPU and memory requests. Lightweight inspection, Git,
  editing, configuration validation, and job submission/monitoring are okay.
- In Hangar, launch commands that need secrets through `./bin/flappy run --`
  and confirm that Doppler loaded nonzero secrets before trusting the run.
- Do not explicitly choose a SLURM partition unless the user or experiment
  requires one. Prefer the cluster default.
- Before large launches, compare valid scheduler topologies. Change topology
  only when it is not an experimental variable.
- On Together, ensure submitted jobs export `SLURM_CPU_BIND=none` before a
  launcher creates a nested `srun`; partial-node allocations can otherwise
  fail before Python starts with "CPU binding outside of job step allocation".
- Never materialize the same shared Pixi environment concurrently. Before any
  multi-job suite or multi-node UFO launch, run `pixi install --locked` exactly
  once, then scope `PIXI_NO_INSTALL=true`, `PIXI_FROZEN=true`,
  `UFO_SKIP_PIXI_INSTALL=1`, and `pixi run --as-is` to the launcher,
  orchestrator supervisor, and every submitted job. This includes
  `ufo-all-tests` / `ufo-gpu-test` child jobs, even when each child uses only
  one node; `UFO_SKIP_PIXI_INSTALL` alone does not stop the supervisor's outer
  `pixi run ufo-submit` from reconciling the environment.
- `pixi install --locked` removes the optional DeepEP install from `.pixi`.
  DeepEP is built in place under `third_party/DeepEP`; for DeepEP launches,
  export that directory on `PYTHONPATH` and set `EP_NCCL_ROOT_DIR` to the
  Pixi environment root instead of reinstalling into `.pixi`. Without the
  explicit NCCL root, DeepEP can mix pip's NCCL headers with Pixi's newer
  device headers during JIT compilation.
- Use `ufo-test-changed` for uncommitted UFO edits and
  `ufo-test-changed-main` for committed branch changes.
- After submission, monitor long jobs for at least 3-5 minutes and verify
  increasing progress counters and nonzero throughput before reporting them
  healthy.
- Use `mktemp -d` instead of fixed shared paths under `/tmp`.
