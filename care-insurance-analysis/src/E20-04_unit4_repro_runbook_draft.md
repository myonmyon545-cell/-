# E20-04 unit 4 — reproducibility procedure draft

Status: draft for the next reproduction-ZIP revision; this file is not yet included in the saved ZIP. It documents the ZIP v2 code snapshot (`manifest.json` code_commit `ec639575cee766ab31e56bb013cb35d00bf167f5`) inspected against GitHub main `11573220bd30c2047d8fc39ccd1559ba8b2329e4` on 2026-10-12. Do not mix files from the two snapshots without recording their hashes.

## Inputs and placement

The ZIP does not contain source originals. Retrieve each source from ChatGPT Library by the stable ID below, place it in an external `sources/` directory, and calculate SHA256 from the downloaded bytes before running anything. These IDs and hashes come from `src/input_manifest.json` in the pinned bundle. No source workbook, PDF, DOCX, individual record, or authentication material belongs in GitHub.

| ID | Library ID | SHA256 |
|---|---|---|
| S01 | `libfile_2f275b2a53d481919fb7d942fbecc486` | `5721ee2b38cb8f55f973f149fe32f67dcfe5453645fcfdccdb934b169bcd2a2d` |
| S02 | `libfile_0d9cfee943ec819188518e4922ce620e` | `9b29b315bf310770295e8fe60ba2953362f3cff21b3d78adfe255c42f2c26304` |
| S03 | `libfile_1a33a04a77e4819197bfdf49e7cd8099` | `e4207ce1b47673fd6ec24e9184ea32a285698dcd0762bff612f01ce4f908c08f` |
| S04 | `libfile_348a1421657c8191938bc42e4a79b9ea` | `d879ed1d222d43deb1d1f962e66e8b6d72eadac355596980e78d5ad0a49ec800` |
| S05 | `libfile_f40c9f4e1d0081919fb497f31e737856` | `87d0353e8a53a432146a0e918dc1bd0ed32e8b3884dcb3cdc162994cb037c8d1` |
| S06 | `libfile_b7623c4ffd6881919e938f89942286f3` | `b74b37c05a97d053ef46f16f380177f5a0724151dac5daff1c4076290671e524` |

The pinned `replay_v2.py` also requires S10 by the SHA in `references/S10_excerpts.json`: Library ID `libfile_292453196e588191a056e2f761753670`, SHA256 `a8050346212a34760cfa2c8be7add995f3f59c3f9bfb6118ca7dc3cca3227bd2`. Keep it separate as an additional annual reference input. The runner indexes files by SHA, so a source filename is not used to identify the input; do not alter bytes. Obtain with the Library file tool / approved Library download route, then compare SHA before proceeding.

## Environment and working directory

Unzip the saved bundle into any writable bundle directory. Keep original inputs in a separate `sources/` directory and choose a new empty output directory, for example `./replay-unit4`. Use the existing Codex primary runtime (environment variables `CODEX_PRIMARY_RUNTIME_PYTHON`, `CODEX_PRIMARY_RUNTIME_NODE`, `CODEX_PRIMARY_RUNTIME_NODE_MODULES`). Observed versions on 2026-10-12 are Python 3.12.14, Node v24.19.0, `@oai/artifact-tool` 2.8.85, pandas 2.2.3, openpyxl 3.1.5, xlrd 2.0.1, lxml 6.1.1, Pillow 12.3.0, LibreOfficeDev 26.8.0.0.alpha0. Pin/record the actual environment used for each replay; these observed versions are not a claim of cross-platform compatibility.

## Actual full replay entry point (not run in unit 4)

From the directory containing the unzipped bundle, after all seven inputs have been SHA-verified and `./replay-unit4` is confirmed new/empty:

```bash
"$CODEX_PRIMARY_RUNTIME_PYTHON" src/replay_v2.py --bundle . --sources ./sources --node "$CODEX_PRIMARY_RUNTIME_NODE" --node-modules "$CODEX_PRIMARY_RUNTIME_NODE_MODULES" --out ./replay-unit4
```

These flags were checked against `src/replay_v2.py`. That script verifies required input SHA values, runs `replay_pipeline.py`, `integrate_s10.py`, `summary_v2.py`, the Node `summary_v2.mjs` author, and `graft_v2.py`; then compares workbook structure/logical OOXML parts and S10 output to the retained package. The runner creates numerical and Excel outputs under `--out`; do not run this command as a path-only test. Its assertions are stop conditions: missing input SHA, subcommand failure, workbook structure/chart count mismatch, logical package difference, or S10 result mismatch stops the run. Save stdout/stderr and resulting checks in the chosen output directory.

`replay_v2.py` does not expose a `--check-paths-only`, `--tmpdir`, or configurable internal temporary-directory argument. `replay_pipeline.py` accepts only `--inspection`, `--sources`, `--source-copy`, `--proposal`, `--comparison`, `--out`; its temporary workspace is created under the parent of `--out`. The source modules' CLI flags are defined in their `argparse` blocks; do not pass extra options. Current main's `make_print_probe.py` is a separate three-sheet print-QA helper, not part of the saved ZIP v2. It accepts required `--base`, `--out` and optional `--check-paths-only`; that mode only resolves/rejects paths and does not open a workbook.

## Native recalculation and print review (separate gates)

`src/run_native_trial.py` is a separate invasive-on-copy native LibreOffice trial. Its CLI is `--bundle`, `--node`, `--node-modules`, `--soffice`, `--out` (all required); it writes trial copies under `--out`. It was not run in unit 4. Do not equate the v2 assembly replay with recalculation or save/reopen validation. Native Japanese glyph/print readability is also a separate visual check and remains HELD. The completed analysis workbook remains subject to the 15-sheet requirement; the print probe is scoped to its three affected sheets.

## Scope and omissions

This draft describes commands but is not an execution record. Unit 4 ran only source/path inspection and the `make_print_probe.py --check-paths-only` path check in two empty temporary work directories. It did not generate Excel, replay the full pipeline, recalculate, save/reopen a recalculated workbook, render Japanese text, update the reproduction ZIP, or certify a candidate. The existing ZIP contains fixed historical paths in `inspection/input_manifest.json` and `checks/native_check.json`; the inventory and proposed neutral replacements are in the paired unit-4 check JSON. These files should be normalized before a future ZIP revision.
