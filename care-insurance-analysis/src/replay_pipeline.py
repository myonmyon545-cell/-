"""Replay final numeric stages into an immutable, provenance-bound run folder."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

STAGE_ID = 'post_C03_post_ROLE30_final_numeric'
EXPECTED_COUNTS = {'record_count': 6316, 'comparison_count': 1478}
OUTPUTS = {
    'definitions': ('contract/definitions.json', 'definitions.json'),
    'inventory': ('final_checks/metric_inventory.json', 'metric_inventory.json'),
    'extracted': ('calculation/extracted_values.json', 'extracted_values.json'),
    'numeric': ('calculation/numeric_checks.json', 'numeric_checks.json'),
    'summary': ('final_checks/calculation_summary.json', 'calculation_summary.json'),
    'role30_check': ('role30_apply_check.json', 'role30_apply_check.json'),
}


def safe_run_id(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{7,127}', value or ''):
        raise ValueError('run_id must be a unique 8-128 character safe identifier')
    return value


def count_payload(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    return {
        'record_count': len(data.get('records', [])),
        'comparison_count': len(data.get('comparisons', [])),
    }


def artifact_entry(path, relative_path, processing_stage):
    payload = path.read_bytes()
    entry = {'relative_path': relative_path, 'sha256': sha(payload),
             'size_bytes': len(payload), 'processing_stage': processing_stage}
    if path.name == 'extracted_values.json':
        entry.update(count_payload(path))
    return entry


def reserve_run_directory(retain_root, run_id, stage_id=STAGE_ID):
    run_id = safe_run_id(run_id)
    if stage_id != STAGE_ID:
        raise ValueError('unsupported processing stage: ' + str(stage_id))
    retain_root = Path(retain_root).resolve()
    retain_root.mkdir(parents=True, exist_ok=True)
    run_parent = retain_root / run_id
    run_parent.mkdir(exist_ok=False)
    run_dir = run_parent / stage_id
    run_dir.mkdir(exist_ok=False)
    return run_dir


def comparison_id_set(data):
    rows = data.get('comparisons', [])
    ids = []
    for row in rows:
        ident = row.get('id')
        if ident is None:
            ident = '|'.join(str(row.get(k, '')) for k in ('city_id', 'label', 'reference_input', 'reference_id'))
        ids.append(str(ident))
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate comparison IDs')
    return sorted(ids)


def compare_id_sets(actual, baseline, required_count=None):
    """Baseline supplies comparison keys only; never supplies summary values."""
    actual_ids = set(comparison_id_set(actual))
    expected_ids = set(comparison_id_set(baseline))
    return {
        'expected_count': len(expected_ids), 'actual_count': len(actual_ids),
        'missing_ids': sorted(expected_ids - actual_ids),
        'extra_ids': sorted(actual_ids - expected_ids),
        'required_count': required_count,
        'complete': actual_ids == expected_ids and (required_count is None or len(actual_ids)==required_count),
        'expected_id_set_sha256': sha('\n'.join(sorted(expected_ids)).encode('utf-8')),
        'actual_id_set_sha256': sha('\n'.join(sorted(actual_ids)).encode('utf-8')),
    }


def verify_extraction_manifest(extraction_path, manifest_path, expected_run_id, expected_stage_id=STAGE_ID):
    extraction_path = Path(extraction_path).resolve()
    manifest_path = Path(manifest_path).resolve()
    if 'baseline' in extraction_path.parts:
        raise ValueError('baseline extraction cannot be used as summary input')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('run_id') != expected_run_id:
        raise ValueError('run_id mismatch')
    if manifest.get('stage_id') != expected_stage_id or expected_stage_id != STAGE_ID:
        raise ValueError('wrong processing stage')
    if manifest.get('complete') is not True:
        raise ValueError('run manifest is not complete')
    if manifest.get('comparison_set', {}).get('complete') is not True:
        raise ValueError('comparison set is incomplete')
    if manifest.get('record_set', {}).get('complete') is not True:
        raise ValueError('record set is incomplete')
    rel = None
    entry = None
    for candidate in manifest.get('artifacts', []):
        if candidate.get('name') == 'extracted':
            rel, entry = candidate.get('relative_path'), candidate
            break
    if not rel or entry is None:
        raise ValueError('manifest lacks final extraction artifact')
    expected_path = (manifest_path.parent / rel).resolve()
    if extraction_path != expected_path:
        raise ValueError('extraction path does not match manifest artifact')
    if not extraction_path.is_file():
        raise ValueError('extraction file missing')
    raw = extraction_path.read_bytes()
    if sha(raw) != entry.get('sha256') or len(raw) != entry.get('size_bytes'):
        raise ValueError('extraction bytes differ from manifest')
    data = json.loads(raw.decode('utf-8'))
    counts = count_payload(extraction_path)
    if counts['record_count'] != entry.get('record_count') or counts['comparison_count'] != entry.get('comparison_count'):
        raise ValueError('extraction counts differ from manifest')
    if counts != manifest.get('counts'):
        raise ValueError('extraction counts differ from run manifest')
    if counts != manifest.get('contract_counts'):
        raise ValueError('extraction counts do not meet the fixed stage contract')
    if manifest.get('comparison_set', {}).get('actual_count') != counts['comparison_count']:
        raise ValueError('comparison set count differs from extraction')
    if manifest.get('record_set', {}).get('actual_count') != counts['record_count']:
        raise ValueError('record set count differs from extraction')
    return {'manifest': manifest, 'manifest_sha256': sha(manifest_path.read_bytes()),
            'extraction_sha256': sha(raw), 'extraction': data, 'counts': counts,
            'manifest_path': str(manifest_path), 'extraction_path': str(extraction_path)}


def _copy_available(paths, run_dir, output_directory='outputs'):
    artifacts = []
    out_root = run_dir / output_directory
    for name, (source_rel, dest_name) in OUTPUTS.items():
        src = paths.get(name)
        if src is None or not Path(src).is_file():
            continue
        if name in ('definitions',): dest_rel = 'contract/' + dest_name
        elif name in ('inventory', 'summary'): dest_rel = 'final_checks/' + dest_name
        elif name in ('extracted', 'numeric'): dest_rel = 'calculation/' + dest_name
        else: dest_rel = dest_name
        dest = out_root / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        artifacts.append({'name': name, **artifact_entry(dest, output_directory + '/' + dest_rel, STAGE_ID)})
    extracted=next((item for item in artifacts if item['name']=='extracted'),None)
    if extracted:
        for item in artifacts:
            item.setdefault('record_count',extracted['record_count'])
            item.setdefault('comparison_count',extracted['comparison_count'])
    return artifacts


def persist_run_evidence(run_dir, manifest, command_log):
    """Write artifacts first, then the manifest and complete subprocess transcript."""
    write_json(Path(run_dir) / 'run_manifest.json', manifest)
    write_json(Path(run_dir) / 'subprocess_log.json', command_log)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inspection', type=Path, required=True)
    ap.add_argument('--sources', type=Path, required=True)
    ap.add_argument('--source-copy', type=Path, required=True)
    ap.add_argument('--proposal', type=Path, required=True)
    ap.add_argument('--comparison', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--retain-dir', type=Path, required=True)
    ap.add_argument('--input-identity', type=Path, required=True)
    ap.add_argument('--code-commit', required=True)
    a = ap.parse_args()
    run_id = safe_run_id(a.run_id)
    a.out = a.out.resolve()
    if a.out.exists():
        raise FileExistsError('report output already exists: ' + str(a.out))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    run_dir = reserve_run_directory(a.retain_dir, run_id)
    root = Path(__file__).resolve().parent
    identity = {}
    stages, pathmap, log, artifacts = [], {}, [], []
    stage_succeeded=False
    status = 'FAIL'
    report = {'status': 'FAIL', 'run_id': run_id, 'stage_id': STAGE_ID}
    try:
        identity = json.loads(a.input_identity.read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory(prefix='care_replay_work_', dir=a.out.parent) as tmp:
            base = Path(tmp); contract=base/'contract'; calculation=base/'calculation'; checks=base/'checks'
            pathmap.update({'definitions':contract/'definitions.json','inventory':checks/'metric_inventory.json',
                'extracted':calculation/'extracted_values.json','numeric':calculation/'numeric_checks.json',
                'summary':checks/'calculation_summary.json','role30_check':base/'role30_apply.json'})
            try:
              commands = [
                ('prepare_contract.py',['--inspection',str(a.inspection),'--out',str(contract)]),
                ('metric_inventory.py',['--inspection',str(a.inspection),'--contract',str(contract)]),
                ('calculate.py',['--inspection',str(a.inspection),'--contract',str(contract),'--out',str(calculation)]),
                ('verify_extraction.py',['--sources',str(a.sources),'--calculation',str(calculation)]),
                ('apply_c03_overlay.py',['--inspection',str(a.inspection),'--source-copy',str(a.source_copy),'--calculation',str(calculation)]),
                ('apply_role30.py',['--proposal',str(a.proposal),'--inspection',str(a.inspection),
                    '--contract',str(contract),'--calculation',str(calculation),'--checks',str(base/'role30_apply.json')]),
                ('summarize_checks.py',['--inspection',str(a.inspection),'--contract',str(contract),
                    '--calculation',str(calculation),'--out',str(checks)]),
              ]
              for script, arguments in commands:
                argv=[sys.executable,str(root/script),*arguments]
                started=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
                p=subprocess.run(argv,check=False,capture_output=True,text=True)
                record={'command':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,
                        'started_at_utc':started,'ended_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
                log.append(record); stages.append({'script':script,'exit_code':p.returncode})
                if p.returncode:
                    raise subprocess.CalledProcessError(p.returncode, argv, output=p.stdout, stderr=p.stderr)
              actual=json.loads(pathmap['extracted'].read_text(encoding='utf-8'))
              baseline=json.loads((a.comparison/'calculation/extracted_values.json').read_text(encoding='utf-8'))
              comparison_set=compare_id_sets(actual,baseline,EXPECTED_COUNTS['comparison_count'])
              actual_records={(r.get('input_id'),r.get('id')) for r in actual.get('records',[])}
              expected_records={(r.get('input_id'),r.get('id')) for r in baseline.get('records',[])}
              record_set={'expected_count':len(expected_records),'actual_count':len(actual_records),
                  'missing_ids':sorted(expected_records-actual_records),'extra_ids':sorted(actual_records-expected_records),
                  'complete':actual_records==expected_records and len(actual_records)==EXPECTED_COUNTS['record_count']}
              hashes={}
              for name,(source_rel,baseline_rel) in OUTPUTS.items():
                  left=pathmap[name]; right=a.comparison/baseline_rel
                  hashes[name]={'replay':sha(left.read_bytes()),'baseline':sha(right.read_bytes())}
              differences={k:v for k,v in hashes.items() if v['replay']!=v['baseline']}
              report={'status':'PASS' if not differences and comparison_set['complete'] else 'FAIL',
                  'scope':'numeric replay comparison; baseline used only for comparison',
                  'inputs_unchanged':True,'files_compared':len(hashes),'hashes':hashes,
                  'differences':differences,'run_id':run_id,'stage_id':STAGE_ID,
                  'comparison_set':comparison_set,'record_set':record_set}
              status=report['status']
              stage_succeeded=bool(comparison_set['complete'] and record_set['complete'])
            except Exception as exc:
              report.update({'status':'FAIL','error_type':type(exc).__name__,'error':str(exc)})
              raise
            finally:
              artifacts=_copy_available(pathmap,run_dir,'pending')
    except Exception as exc:
        report.update({'status':'FAIL','error_type':type(exc).__name__,'error':str(exc)})
        comparison_set=locals().get('comparison_set',{'complete':False,'expected_count':None,'actual_count':None,'missing_ids':[],'extra_ids':[]})
        record_set=locals().get('record_set',{'complete':False,'expected_count':None,'actual_count':None,'missing_ids':[],'extra_ids':[]})
    if stage_succeeded and len(artifacts)==len(OUTPUTS):
        os.replace(run_dir/'pending',run_dir/'outputs')
        for item in artifacts:
            if item['relative_path'].startswith('pending/'):
                item['relative_path']='outputs/'+item['relative_path'][len('pending/'):]
    counts={'record_count':0,'comparison_count':0}
    ext=next((x for x in artifacts if x['name']=='extracted'),None)
    if ext:
        counts={'record_count':ext.get('record_count',0),'comparison_count':ext.get('comparison_count',0)}
    executed_scripts=['prepare_contract.py','metric_inventory.py','calculate.py','verify_extraction.py',
        'apply_c03_overlay.py','apply_role30.py','summarize_checks.py']
    code_files=[Path(__file__),root/'replay_v2.py',root/'summary_v2.py',root/'inspect_inputs.py']
    code_files += [root/name for name in executed_scripts]
    manifest={'schema':'care_numeric_run_manifest/v1','run_id':run_id,'stage_id':STAGE_ID,
        'status':status,'complete':bool(ext and len(artifacts)==len(OUTPUTS) and
            (run_dir/'outputs').is_dir() and all(x['exit_code']==0 for x in stages)),
        'comparison_set':comparison_set,'record_set':record_set,'counts':counts,
        'contract_counts':EXPECTED_COUNTS,'artifacts':artifacts,
        'code_identity':{'commit':a.code_commit,'files':{p.name:sha(p.read_bytes()) for p in code_files}},
        'input_identity':identity,'subprocesses':stages,
        'created_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
    persist_run_evidence(run_dir,manifest,{'run_id':run_id,'stage_id':STAGE_ID,'commands':log})
    report['run_manifest_relative']=str(Path(run_id)/STAGE_ID/'run_manifest.json')
    write_json(a.out,report)
    print(json.dumps({'status':report['status'],'run_id':run_id,'stage_id':STAGE_ID,
                      'files_compared':report.get('files_compared',0),'error':report.get('error')},ensure_ascii=False))
    if not manifest['complete'] or not comparison_set.get('complete') or not record_set.get('complete'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
