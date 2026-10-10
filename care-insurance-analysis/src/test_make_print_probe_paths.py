"""Path-only tests with synthetic bytes; no project data or XLSX generation."""
import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--script', type=Path,
                        default=Path(__file__).resolve().with_name('make_print_probe.py'))
    parser.add_argument('--result', type=Path, required=True)
    args = parser.parse_args()
    script = args.script.resolve()
    data = script.read_bytes()
    compile(data, str(script), 'exec')
    tree = ast.parse(data)
    fixed = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
             and isinstance(n.value, str)
             and (n.value.startswith(('/tmp/', '/workspace/', '/home/', '/root/', '/opt/')))]
    checks = {'syntax': True, 'no_fixed_filesystem_paths': not fixed}
    logs = []
    with tempfile.TemporaryDirectory(prefix='e04_path_unit_') as tmp:
        root = Path(tmp)
        a, b = root/'cwd_a', root/'cwd_b'
        a.mkdir(); b.mkdir(); (root/'inputs').mkdir()
        base = root/'inputs'/'synthetic.xlsx'
        base.write_bytes(b'path test only; deliberately not an Excel ZIP')
        before = base.read_bytes()
        out = root/'output'/'probe.xlsx'
        def run(cwd, argv):
            r = subprocess.run([sys.executable, str(script), *argv], cwd=cwd,
                               capture_output=True, text=True, timeout=10)
            logs.append({'cwd_label': cwd.name, 'args': argv,
                         'exit_code': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr})
            return r
        results = []
        for cwd in (a, b):
            for relative in (False, True):
                inp = os.path.relpath(base, cwd) if relative else str(base)
                dest = os.path.relpath(out, cwd) if relative else str(out)
                r = run(cwd, ['--base', inp, '--out', dest, '--check-paths-only'])
                checks[f'{cwd.name}_{"relative" if relative else "absolute"}'] = r.returncode == 0
                results.append(json.loads(r.stdout) if r.returncode == 0 else {})
        checks['same_resolution_from_two_directories'] = all(
            x == {'base': str(base), 'out': str(out), 'mode': 'paths_only'} for x in results)
        checks['missing_base_rejected'] = run(a, ['--base', '../inputs/missing.xlsx', '--out', str(out), '--check-paths-only']).returncode == 2
        checks['same_path_rejected'] = run(b, ['--base', str(base), '--out', str(base), '--check-paths-only']).returncode == 2
        occupied = root/'occupied.xlsx'; occupied.write_bytes(b'preserve')
        checks['existing_output_rejected'] = run(a, ['--base', str(base), '--out', str(occupied), '--check-paths-only']).returncode == 2
        checks['required_arguments'] = run(b, ['--check-paths-only']).returncode == 2
        checks['no_output_or_directory_created'] = not out.exists() and not out.parent.exists()
        checks['synthetic_input_and_existing_output_unchanged'] = base.read_bytes() == before and occupied.read_bytes() == b'preserve'
    # Remove random temporary roots from the persistent test log.
    for entry in logs:
        entry['args'] = [x.replace(str(root), '<temporary-root>') for x in entry['args']]
        for key in ['stdout', 'stderr']:
            entry[key] = entry[key].replace(str(root), '<temporary-root>').replace(str(script), '<script>')
    report = {'schema': 'care_e20_04_entry_path_check/v1',
              'result': 'PASS_PATH_UNIT_ONLY' if all(checks.values()) else 'FAIL_PATH_UNIT',
              'code_sha256': hashlib.sha256(data).hexdigest(),
              'checks': checks, 'execution': logs,
              'scope': 'Syntax and CLI path resolution only; synthetic non-XLSX bytes. No real workbook processing.',
              'not_run': ['real_data_probe_generation', 'ZIP_regeneration', 'full_pipeline_replay', 'Excel_recalculation', 'Japanese_print_readability', 'candidate_certification'],
              'E20_04_overall': 'NOT_PASS'}
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'result': report['result'], 'code_sha256': report['code_sha256'], 'checks': checks}))
    if not all(checks.values()):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
