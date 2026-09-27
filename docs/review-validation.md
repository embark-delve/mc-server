> **Baseline review (df94b16).** Subsequent repairs are tracked in [implementation status](implementation-status.md); use the [current README](../README.md) for commands.

# Review validation record

Date: 2026-09-27. Baseline: `df94b16`. No application code was changed, no server was started, no Minecraft EULA was accepted, and no cloud deployment was made. All review deliverables are under `docs/`.

## Scope and environment

Read the Python CLI, manager, both backends, base/interface/factory, utility modules, tests, dependency/build manifests, CI/pre-commit configuration, Docker scripts/image, Kubernetes files, Terraform environment/module, examples, and existing user/developer documentation. Historical conversation archives and historical coverage output were not treated as implementation evidence. No `AGENTS.md` was found beneath the inspected parent directory; `CLAUDE.md` supplied repository conventions.

The working tree was initially clean. The latest commit is dated 2025-03-10. Host observations: macOS arm64; Homebrew Python 3.13.0. `docker` and global `pytest` were not found on PATH. Physical-memory inspection was sandbox-blocked; no host capacity recommendation is based on a measured RAM value.

Created an isolated virtual environment at `/tmp/mc-server-review-20260927`. Dependency download initially failed due to sandbox network restrictions, then succeeded through approved network access. Installed `requirements.txt` plus review tooling. No global Python packages were changed. A temporary copy of relevant source files was used for focused reproductions, lint, types, CLI failure and wheel inspection. The existing test suite ran from the original checkout with coverage disabled; it used temporary directories and left tracked files unchanged.

## Results

| Check | Result | Interpretation |
| --- | --- | --- |
| `python -m pytest -o addopts='' --tb=short -q` | **12 failed, 28 passed, 1 xfailed**, 6.75 seconds | Failing CLI mocks/configuration and duplicate Prometheus registration; idle-thread test already marked expected failure |
| `ruff check . --output-format=concise` in copied source/test tree | **123 errors** | Current Ruff 0.16.9; includes source, tests and primary CLI, not every auxiliary example/script in the repo |
| `mypy src` | **63 errors in 9 files**, 19 source files checked | Mypy 2.3.1 also rejects configured Python 3.8; review environment omitted optional type stubs, which contributes to errors |
| `python -m pip check` | No broken requirements found | Resolver consistency only; does not validate missing project metadata declarations |
| Default `python minecraft-server.py status` | `ValueError: Unsupported server type: paper` | Committed config fails without reaching Docker |
| Default `DockerServer` construction, HTTP listener mocked | Duplicate Prometheus timeseries | Confirms initialization defect independently of restricted socket permissions |
| Documented manager `memory='4G'`, monitoring disabled | Unexpected keyword argument `memory` | README Python API example fails |
| Disabled auto-shutdown plus absent CLI flag represented as false | Becomes enabled | Precedence defect |
| Valid ZIP restore into temporary directory containing only `data/` | Returns false; world file deleted | Destructive restore bug confirmed only on disposable data |
| Mod install/uninstall on temporary Paper profile | Install true; contents `Mock mod file content`; uninstall false | Advertised feature is a mock and metadata mismatch is real |
| Custom data directory Compose generation | Still mounts `./data` | Configured file path and runtime mount disagree |
| Metrics size parse `2GiB` | `2.0` | Unit parsing defect |
| `python -m build --wheel --no-isolation` in copy | Wheel built, missing subpackages; invalid entry point | Build success is not installation success |
| `pip-audit` of review environment | 12 advisory entries for pip 24.2; no reported entries for other audited installed packages | Toolchain bootstrap issue; see limitations below |
| Live Minecraft / Docker / LAN / multi-server tests | **Not run** | Docker unavailable on PATH; no runtime readiness claim |
| Cloud/Kubernetes deployment, container vulnerability scan, full Git-history secret scan | **Not run** | Deferred scope; no claims of clean results |

## Test failure breakdown

Three failures are in `TestMain`: normal main, error handling and unknown-command handling. Their patching does not replace the names already imported by the CLI, so the actual committed configuration is loaded and the unsupported backend error occurs. Nine failures are Docker interface tests that reach duplicate Prometheus registration. One attempted metrics listener was denied by the sandbox; the independent constructor reproduction mocked `start_http_server` and still raised the same duplicate-registration failure.

Fixing those first blockers may reveal additional defects currently hidden behind them. These results are not a complete count of all behavioral bugs. The existing expected failure covers a timing-sensitive auto-shutdown thread, not a successful integration test.

## Packaging evidence

The generated wheel contains these Python files only:

```text
src/__init__.py
src/minecraft_server_manager.py
```

Its console entry is:

```text
minecraft-server = src.minecraft_manager:main
```

There is no `src.minecraft_manager` module in the repository. The wheel lacks `src.commands`, `src.core`, `src.implementations` and `src.utils`; importing the manager therefore also lacks its required package tree. No build/install artifact was added to this repository.

## Dependency audit interpretation

The audit queried PyPI for the versions freshly resolved on this review date, including review tools and the venv's bootstrap pip. It reported **12 records for pip 24.2**, with **six distinct advisory IDs** (some repeated by the service): `PYSEC-2026-1795`, `PYSEC-2026-1796`, `PYSEC-2026-2875`, `PYSEC-2026-2876`, `PYSEC-2026-196`, and `PYSEC-2026-3721`. These are audit-service results, not independently analyzed exploit findings. Upgrade the bootstrap packaging tools when establishing the supported environment; no application dependency CVE is asserted here on the strength of the old lower bounds alone.

The absence of findings for the freshly resolved application packages **does not** establish that an old installation is clean, that every allowed lower-bound version is safe, that the Minecraft image is safe, or that plugins are trustworthy. There is no committed lock to audit as a reproducible deployment. The audit ran before setuptools/wheel were added for the wheel inspection; those later build tools are not covered by its snapshot. Save and scan the final lock and image digest after the rehabilitation work.

## Saved evidence

Machine-readable/report output is in [review-evidence/2026-09-27](review-evidence/2026-09-27/): test results, lint/type reports, default CLI exception, wheel build log, dependency audit JSON and environment versions. The reports retain baseline paths and diagnostic wording for reproducibility. Dependency filenames and tool versions describe the temporary review environment, not an existing deployed server.

The focused restore probe is [review-probes.py](review-evidence/2026-09-27/review-probes.py). Run it with the prepared dependencies from the repository root using:

```sh
python docs/review-evidence/2026-09-27/review-probes.py
```

It modifies only its own temporary directories, does not invoke Docker or AWS. It demonstrates the baseline failures and will intentionally produce different outcomes as the defects are fixed. It is review evidence, not a substitute for regression tests in `tests/`.

## Current upstream references

Consulted 2026-09-27; these pages can change. They support compatibility and operational recommendations, not verification of this project's runtime.

- [Paper setup and Java requirements](https://docs.papermc.io/paper/getting-started/)
- [Image Java tags, architectures and release pinning](https://docker-minecraft-server.readthedocs.io/en/latest/versions/java/)
- [Image server properties and RCON secrets](https://docker-minecraft-server.readthedocs.io/en/latest/configuration/server-properties/)
- [Image Minecraft health checks](https://docker-minecraft-server.readthedocs.io/en/latest/misc/healthcheck/)
- [Image auto-pause](https://docker-minecraft-server.readthedocs.io/en/latest/misc/autopause-autostop/autopause/)
- [Image auto-stop and restart policy](https://docker-minecraft-server.readthedocs.io/en/latest/misc/autopause-autostop/autostop/)
- [Docker port publishing](https://docs.docker.com/get-started/docker-concepts/running-containers/publishing-ports/)
- [Docker Desktop Mac installation](https://docs.docker.com/desktop/setup/install/mac-install/)
- [Python support lifecycle](https://devguide.python.org/versions/)
