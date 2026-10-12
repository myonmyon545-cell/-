"""Full v2 assembly replay from a validated, retained numeric run."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as E

from inspect_inputs import sha, workbook_cells, write_json
from replay_pipeline import STAGE_ID, verify_extraction_manifest


def _run(script, args, log):
    argv = [sys.executable, str(script), *map(str, args)]
    start = datetime.now(timezone.utc).isoformat()
    p = subprocess.run(argv, check=False, capture_output=True, text=True)
    log.append({'command': argv, 'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr,
                'started_at_utc': start, 'ended_at_utc': datetime.now(timezone.utc).isoformat()})
    return p


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--sources', type=Path, required=True)
    p.add_argument('--node', type=Path, required=True)
    p.add_argument('--node-modules', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--retain-dir', type=Path, required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--code-commit', required=True)
    a = p.parse_args()
    a.out = a.out.resolve()
    if a.out.exists():
        raise FileExistsError('output directory already exists: ' + str(a.out))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.mkdir()
    src = Path(__file__).resolve().parent
    b = a.bundle.resolve()
    expected_manifest = json.loads((b / 'src/input_manifest.json').read_text(encoding='utf-8'))
    s10ref = json.loads((b / 'references/S10_excerpts.json').read_text(encoding='utf-8'))
    expected = {k: v['sha256'] for k, v in expected_manifest.items() if k in ['S01','S02','S03','S04','S05','S06']}
    expected['S10'] = s10ref['source']['sha256']
    files = {sha(f.read_bytes()): f for f in a.sources.iterdir() if f.is_file()}
    if not all(h in files for h in expected.values()):
        raise ValueError('required source SHA256 missing')

    historical_proposal = b / 'historical/role30_initial.json'
    work_copy = b / 'candidate/S01_C03_作業コピー_保持試験.xlsx'
    input_identity = {'sources': {
        sid: {'library_file_id': (s10ref['source']['library_file_id'] if sid == 'S10' else expected_manifest[sid]['library_file_id']),
              'sha256': digest} for sid, digest in expected.items()},
        'C03_work_copy': {'relative_path': 'candidate/S01_C03_作業コピー_保持試験.xlsx',
                          'sha256': sha(work_copy.read_bytes())},
        'ROLE30_proposal': {'relative_path': 'historical/role30_initial.json',
                            'sha256': sha(historical_proposal.read_bytes())},
        'bundle_manifest_sha256': sha((b / 'src/input_manifest.json').read_bytes())}
    input_identity_path = a.out / 'input_identity.json'
    write_json(input_identity_path, input_identity)
    pipeline_report_path = a.out / 'numeric_replay.json'
    orchestration_log = []
    def save_orchestration_log():
        write_json(a.out / 'orchestration_log.json',
                   {'run_id': a.run_id, 'stage_id': STAGE_ID, 'commands': orchestration_log})
    pipeline = _run(src / 'replay_pipeline.py', [
        '--inspection', b / 'inspection', '--sources', a.sources,
        '--source-copy', work_copy, '--proposal', historical_proposal,
        '--comparison', b / 'baseline', '--out', pipeline_report_path,
        '--run-id', a.run_id, '--retain-dir', a.retain_dir.resolve(),
        '--input-identity', input_identity_path, '--code-commit', a.code_commit], orchestration_log)
    save_orchestration_log()
    run_dir = a.retain_dir.resolve() / a.run_id / STAGE_ID
    run_manifest_path = run_dir / 'run_manifest.json'
    extraction_path = run_dir / 'outputs/calculation/extracted_values.json'
    if not run_manifest_path.is_file():
        raise RuntimeError('replay pipeline did not retain a run manifest')
    checked = verify_extraction_manifest(extraction_path, run_manifest_path, a.run_id)
    replay_report = json.loads(pipeline_report_path.read_text(encoding='utf-8'))
    if pipeline.returncode and not (checked['manifest'].get('complete') and checked['manifest'].get('comparison_set',{}).get('complete')):
        raise subprocess.CalledProcessError(pipeline.returncode, pipeline_report_path, output=pipeline.stdout, stderr=pipeline.stderr)

    s10_output = a.out / 'S10_application.json'
    r = _run(src / 'integrate_s10.py', ['--source', files[expected['S10']], '--excerpts', b / 'references/S10_excerpts.json', '--out', s10_output], orchestration_log)
    save_orchestration_log()
    if r.returncode: raise subprocess.CalledProcessError(r.returncode, r.args, output=r.stdout, stderr=r.stderr)
    summary_path = a.out / 'summary_tables.json'
    r = _run(src / 'summary_v2.py', ['--extraction', extraction_path, '--run-manifest', run_manifest_path,
        '--expected-run-id', a.run_id, '--expected-stage-id', STAGE_ID,
        '--supplement', s10_output, '--out', summary_path], orchestration_log)
    save_orchestration_log()
    if r.returncode: raise subprocess.CalledProcessError(r.returncode, r.args, output=r.stdout, stderr=r.stderr)
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    expected_provenance = {'run_id': a.run_id, 'stage_id': STAGE_ID,
                           'extraction_sha256': checked['extraction_sha256'],
                           'manifest_sha256': checked['manifest_sha256']}
    if summary.get('input_provenance') != expected_provenance:
        raise ValueError('summary output provenance does not match consumed run manifest')
    write_json(a.out / 'orchestration_log.json', {'run_id': a.run_id, 'stage_id': STAGE_ID, 'commands': orchestration_log})

    with tempfile.TemporaryDirectory(prefix='care_v2_author_') as tmp:
        author = Path(tmp)
        (author / 'node_modules').symlink_to(a.node_modules.resolve(), target_is_directory=True)
        builder = author / 'summary_v2.mjs'
        builder.write_bytes((src / 'summary_v2.mjs').read_bytes())
        argv = [str(a.node), str(builder), str(summary_path.resolve()), str((a.out/'author').resolve())]
        rp = subprocess.run(argv, check=False, capture_output=True, text=True)
        orchestration_log.append({'command':argv,'exit_code':rp.returncode,'stdout':rp.stdout,'stderr':rp.stderr,
            'started_at_utc':datetime.now(timezone.utc).isoformat(),'ended_at_utc':datetime.now(timezone.utc).isoformat()})
        save_orchestration_log()
        if rp.returncode: raise subprocess.CalledProcessError(rp.returncode,argv,output=rp.stdout,stderr=rp.stderr)
    r = _run(src / 'graft_v2.py', ['--source-copy', work_copy, '--donor', a.out/'author/summary_donor.xlsx',
        '--notes', a.out/'author/local_notes.json', '--tables', summary_path,
        '--out', a.out/'candidate_v2.xlsx', '--checks', a.out/'preservation.json'], orchestration_log)
    save_orchestration_log()
    if r.returncode: raise subprocess.CalledProcessError(r.returncode,r.args,output=r.stdout,stderr=r.stderr)

    original=b/'candidate/介護保険解析_候補_v2.xlsx'; replay=a.out/'candidate_v2.xlsx'
    ow=workbook_cells(original); rw=workbook_cells(replay)
    if not (ow['sheets']==rw['sheets'] and ow['chart_count']==rw['chart_count']==148):
        raise ValueError('workbook structure differs from fixed candidate')
    def logical(f):
        with zipfile.ZipFile(f) as z:
            return {n:E.tostring(E.fromstring(z.read(n))) if n.endswith(('.xml','.rels')) else z.read(n)
                    for n in z.namelist() if n!='docProps/core.xml'}
    left,right=logical(original),logical(replay)
    differences=[n for n in set(left)|set(right) if left.get(n)!=right.get(n)]
    s10a=json.loads(s10_output.read_text(encoding='utf-8'))
    s10b=json.loads((b/'checks/S10_application.json').read_text(encoding='utf-8'))
    if s10a!=s10b: raise ValueError('S10 native read differs from fixed check')
    verdict='PASS' if replay_report.get('status')=='PASS' and not differences else 'FAIL'
    report={'status':verdict,'scope':'isolated assembly replay; not production acceptance',
        'run_id':a.run_id,'stage_id':STAGE_ID,'numeric_replay_status':replay_report.get('status'),
        'source_manifest_sha256':checked['manifest_sha256'],'source_extraction_sha256':checked['extraction_sha256'],
        'candidate_sha256':sha(original.read_bytes()),'replay_sha256':sha(replay.read_bytes()),
        'logical_part_differences':differences,
        'all_values_formulas_notes_print_and_chart_parts_equal':not differences,
        'S10_native_read_replayed':True,'zip_timestamps_not_compared':True,
        'note':'Summary input was the retained extraction artifact verified against this run manifest; baseline was comparison-only.'}
    write_json(a.out/'full_replay.json',report)
    write_json(a.out/'orchestration_log.json',{'run_id':a.run_id,'stage_id':STAGE_ID,'commands':orchestration_log})
    print(json.dumps(report,ensure_ascii=False))
    if verdict!='PASS': raise SystemExit(1)


if __name__=='__main__':
    main()
