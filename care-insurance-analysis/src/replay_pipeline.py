"""One independent full pipeline replay for Q11; no source workbook writes."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from inspect_inputs import sha, write_json


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--inspection',type=Path,required=True)
    ap.add_argument('--sources',type=Path,required=True)
    ap.add_argument('--source-copy',type=Path,required=True)
    ap.add_argument('--proposal',type=Path,required=True)
    ap.add_argument('--comparison',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    root=Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='care_replay_',dir=a.out.parent) as d:
        base=Path(d);contract=base/'contract';calculation=base/'calculation';checks=base/'checks'
        for script,arguments in [
            ('prepare_contract.py',['--inspection',str(a.inspection),'--out',str(contract)]),
            ('metric_inventory.py',['--inspection',str(a.inspection),'--contract',str(contract)]),
            ('calculate.py',['--inspection',str(a.inspection),'--contract',str(contract),'--out',str(calculation)]),
            ('verify_extraction.py',['--sources',str(a.sources),'--calculation',str(calculation)]),
            ('apply_c03_overlay.py',['--inspection',str(a.inspection),'--source-copy',str(a.source_copy),'--calculation',str(calculation)]),
            ('apply_role30.py',['--proposal',str(a.proposal),'--inspection',str(a.inspection),
                               '--contract',str(contract),'--calculation',str(calculation),
                               '--checks',str(base/'role30_apply.json')]),
            ('summarize_checks.py',['--inspection',str(a.inspection),'--contract',str(contract),
                                   '--calculation',str(calculation),'--out',str(checks)]),
        ]:
            subprocess.run([sys.executable,str(root/script),*arguments],check=True,
                           capture_output=True,text=True)
        targets={
            'definitions':(contract/'definitions.json',a.comparison/'contract/definitions.json'),
            'inventory':(checks/'metric_inventory.json',a.comparison/'final_checks/metric_inventory.json'),
            'extracted':(calculation/'extracted_values.json',a.comparison/'calculation/extracted_values.json'),
            'numeric':(calculation/'numeric_checks.json',a.comparison/'calculation/numeric_checks.json'),
            'summary':(checks/'calculation_summary.json',a.comparison/'final_checks/calculation_summary.json'),
            'role30_check':(base/'role30_apply.json',a.comparison/'role30_apply_check.json'),
        }
        differences={}
        hashes={}
        for name,(left,right) in targets.items():
            hashes[name]={'replay':sha(left.read_bytes()),'current':sha(right.read_bytes())}
            if hashes[name]['replay']!=hashes[name]['current']:
                differences[name]=hashes[name]
        report={'status':'PASS' if not differences else 'FAIL','scope':'T01/T02/T04/T05の再現可能な集計・状態処理。候補Excelのバイト再現ではない',
                'inputs_unchanged':True,'files_compared':len(targets),'hashes':hashes,'differences':differences}
        write_json(a.out,report)
        print(json.dumps({'status':report['status'],'files_compared':len(targets),'differences':differences},
                         ensure_ascii=False))
        if differences:raise SystemExit(1)


if __name__=='__main__':
    main()
