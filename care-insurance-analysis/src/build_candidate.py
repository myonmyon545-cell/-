"""Freeze the per-input candidate contract and suppress held comparisons."""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from inspect_inputs import sha, write_json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from verify_handoff import check_package

INPUTS = ('S01', 'S02')


def mid(input_id, logical_id):
    return input_id + '::' + logical_id


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--extraction',type=Path,required=True)
    p.add_argument('--inventory',type=Path,required=True)
    p.add_argument('--definitions',type=Path,required=True)
    p.add_argument('--workbook',type=Path,required=True)
    p.add_argument('--input-manifest',type=Path,required=True)
    p.add_argument('--code-commit',required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--result',type=Path,required=True)
    a=p.parse_args()
    result=json.loads(a.extraction.read_text())
    inv=json.loads(a.inventory.read_text())
    manifest=json.loads(a.input_manifest.read_text())
    if len(inv['metrics'])!=3158 or len(result['records'])!=6316 or len(result['comparisons'])!=1478:
        raise ValueError('fixed candidate coverage mismatch')
    index={(r['input_id'],r['id']):r for r in result['records']}
    metrics=[]
    required=[]
    for sid in INPUTS:
        for m in inv['metrics']:
            name=m['id']
            if sid not in m.get('extraction_status_by_input',{}):
                raise ValueError('input-specific inventory status missing '+sid+' '+name)
            row=index.get((sid,name))
            if row is None:raise ValueError('extracted input record missing '+sid+' '+name)
            stated=m['extraction_status_by_input'][sid]
            if stated['status']!=row['status'] or stated['source_ref']!=row['source_ref']:
                raise ValueError('inventory/record status or source differs '+sid+' '+name)
            if row['input_hash']!=manifest[sid]['sha256'] or row['source_ref']['input']!=sid:
                raise ValueError('input hash or source identity mismatch '+sid+' '+name)
            ident=mid(sid,name);required.append(ident)
            v=row['value'] if row['status']=='valid' else None
            item={key:row[key] for key in ('status','kind','population','unit','period','source_ref','evidence_sha256')}
            item.update({'id':ident,'logical_id':name,'input_id':sid,'value':v,
                         'region':row['region'],'adjustment':row['adjustment'],
                         'row_label':row['row_label'],
                         'raw_source_value':row['source_value'],
                         'reason':row['reason']})
            for key in ('item_id','item_name','population_scope','statistic_kind',
                        'heading_source_ref','focus_exception','certification_kind',
                        'definition','numerator_source_ref','denominator_source_ref',
                        'ratio_basis','region_adjustment_label','source_header_ref',
                        'logical_metric_source_ref','raw_original_value',
                        'hold_override','source_copy_sha256'):
                if key in row:item[key]=row[key]
            if row['status']=='valid':
                if row['kind']=='ratio':
                    item['numerator']=row['numerator'];item['denominator']=row['denominator']
                if row['kind']=='provided':
                    item['verification_scope']=row['verification_scope']
            metrics.append(item)
    package_comparisons=[]
    for c in result['comparisons']:
        city=index[('S01',c['city_id'])]
        other=index[(c['reference_input'],c['reference_id'])]
        parents=[mid('S01',city['id']),mid(c['reference_input'],other['id'])]
        status='valid' if city['status']==other['status']=='valid' else 'held'
        if c['status']!=status:
            raise ValueError('comparison status propagation differs '+c['id'])
        expected=(100 if c['unit']=='pp' else 1)*(city['value']-other['value']) if status=='valid' else None
        if status=='valid' and abs(c['value']-expected)>1e-8:
            raise ValueError('comparison value differs '+c['id'])
        if status=='held' and c['value'] is not None:
            raise ValueError('held comparison has a numeric value '+c['id'])
        package_comparisons.append({'id':'cmp::'+c['id'],'source_id':c['id'],
            'status':status,'value':expected,'unit':c['unit'],'label':c['label'],
            'depends_on':parents,'reason':c.get('reason') or ('比較元/先が保留' if status!='valid' else None),
            'population':c['population'],'adjustment':c['adjustment']})
    if len({c['id'] for c in package_comparisons})!=len(package_comparisons):
        raise ValueError('duplicate comparison id')
    held=[r for r in metrics if r['status']!='valid']
    c10=[r for r in held if r['logical_id'].startswith('II.selection.07.70:')]
    c11=[r for r in held if (r['reason'] or '').startswith('C11')]
    if len(c10)!=36 or len(c11)!=30:
        raise ValueError('C10/C11 held scope incomplete')
    excelsha=sha(a.workbook.read_bytes())
    package={'schema':'care_candidate/v1','plan_revision':'2.2',
       'candidate':{'id':'care-S01-20261009-v1','version':1,'sha256':excelsha},
       'input_hashes':{sid:manifest[sid]['sha256'] for sid in ('S01','S02','S03','S04','S05','S06')},
       'definitions_sha256':sha(a.definitions.read_bytes()),
       'template_sha256':manifest['S01']['sha256'],
       'template_source':'S01原14シート。修正作業コピーはC03の9セルのみ変更',
       'code_commit':a.code_commit,
       'required_metrics':required,'metrics':metrics,
       'comparisons':package_comparisons,
       'hold_policy':{
          'C03':'ROLE20独立PASS。S01作業コピー9セルのみ修正、S02はⅢ件数を出所付き採用',
          'C10':'数値36件を入力別保留。P70見出し異常はS01=644821/S02=618046。地域を推定しない',
          'C11':'比率30件を入力別保留。ゼロ分子3件の0をvalid比較へ渡さない',
          'C04':'日数の正式根拠待ちで比較抑止',
          'C09':'0/0の数式エラーは未算出、0とみなさない',
          'E01':'日本語フォント不足で表示検査は未合格',
       },
       'source_copy_sha256':result['correction_overlays']['C03']['S01_work_copy_sha256'],
       'proposal_report_blob_sha':result['correction_overlays']['ROLE30']['proposal_report_blob_sha'],
       'scope':'20の初回独立評価対象。保留値の結論を出さず、完成・暫定提出と区別する',
    }
    check=check_package(package,expected_revision='2.2',
                        expected_inputs={k:manifest[k]['sha256'] for k in package['input_hashes']},
                        workbook=a.workbook)
    check.update({'comparison_count':len(package_comparisons),
                  'valid_comparisons':sum(c['status']=='valid' for c in package_comparisons),
                  'held_comparisons':sum(c['status']!='valid' for c in package_comparisons),
                  'input_status_coverage':len(metrics),
                  'C10_numeric_held':len(c10),'C11_ratio_held':len(c11),
                  'source_workbook_sha256':excelsha})
    write_json(a.out,package);write_json(a.result,check)
    print(json.dumps(check,ensure_ascii=False))


if __name__=='__main__':
    main()
