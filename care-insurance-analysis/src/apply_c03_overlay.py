"""Apply independently approved C03 provenance to aggregate work results."""
import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from inspect_inputs import workbook_cells, sha, write_json

ROLE20_REPORT_BLOB='8a62a506c6ea56688e7231b44470cabd35d5912a'
ROLE20_EVIDENCE_COMMIT='b5b14b75d8329850b441640ff5b92408a9ccca81'
CORRECTION=[66,255,198,432,259,190,230,157,1787]
S02_CORRECTION=[66,246,174,436,216,203,269,140,1750]
LABEL_ROWS=[(513+i,128+i) for i in range(9)]
RATIO_COLUMNS=['K','N','Q','U','Y']

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--inspection',type=Path,required=True)
    p.add_argument('--source-copy',type=Path,required=True)
    p.add_argument('--calculation',type=Path,required=True)
    a=p.parse_args()
    source_copy_sha=sha(a.source_copy.read_bytes())
    copybook=workbook_cells(a.source_copy)
    proof={sid:json.loads((a.inspection/(sid+'_cells.json')).read_text()) for sid in ['S01','S02']}
    final_data={sid:{s['name']:s['cells'] for s in proof[sid]['sheets']} for sid in ['S01','S02']}
    copy_data={s['name']:s['cells'] for s in copybook['sheets']}
    old_sheet='Ⅰ基礎情報';new_sheet='Ⅲ審査判定データ（一次・二次判定）'
    c03_evidence={'S01':{},'S02':{}}
    count_checks=[]
    for sid in ['S01','S02']:
        raw=final_data[sid][old_sheet]
        iii=final_data[sid][new_sheet]
        before=[raw['G'+str(r)]['value'] for r,_ in LABEL_ROWS]
        proposed=[iii['G'+str(r)]['value'] for _,r in LABEL_ROWS]
        labels_ok=all(raw['C'+str(i)]['value']==iii['C'+str(j)]['value'] for i,j in LABEL_ROWS)
        ratios_ok=all(abs(raw[col+str(i)]['value']-iii[col+str(j)]['value'])<=1e-10
                      for i,j in LABEL_ROWS for col in RATIO_COLUMNS)
        expected=CORRECTION if sid=='S01' else S02_CORRECTION
        if not labels_ok or proposed!=expected or not ratios_ok:
            raise ValueError(sid+': C03 source proof no longer matches ROLE=20 PASS')
        if sid=='S01':
            patched=[copy_data[old_sheet]['G'+str(i)]['value'] for i,_ in LABEL_ROWS]
            if patched!=CORRECTION:raise ValueError('S01 copy does not contain the C03 correction')
        else:
            patched=proposed
        if sum(patched[:-1])!=patched[-1]:raise ValueError(sid+': corrected parts do not sum to total')
        c03_evidence[sid]={'original_I_counts':before,'verified_III_counts':proposed,'effective_analysis_counts':patched,
                           'labels_match':labels_ok,'ratio_columns_match':ratios_ok,'parts_sum':sum(patched[:-1]),
                           'I_total':patched[-1],'IV_total_checks':{r:final_data[sid]['Ⅳ事務データ'][r]['value'] for r in ['J189','J207','J225']},
                           'source_copy_sha256':source_copy_sha if sid=='S01' else None,
                           'cell_inventory_json_sha256':sha((a.inspection/(sid+'_cells.json')).read_bytes())}
        c03_evidence[sid]['input_sha256']=json.loads((a.inspection/'input_manifest.json').read_text())[sid]['sha256']
        if any(c03_evidence[sid]['IV_total_checks'][r]!=patched[-1] for r in ['J189','J207','J225']):
            raise ValueError(sid+': IV total cross-check failed')
        count_checks.extend({'input':sid,'cell':'G'+str(i),'sumcheck':'PASS'} for i,_ in LABEL_ROWS)
    calc=a.calculation
    extracted=calc/'extracted_values.json'
    data=json.loads(extracted.read_text())
    (calc/'extracted_values_pre_c03.json').write_bytes(extracted.read_bytes())
    old_by_id={}
    patch_checks=[]
    for sid in ['S01','S02']:
        source_sheet=old_sheet if sid=='S01' else new_sheet
        for idx,(logical_row,iii_row) in enumerate(LABEL_ROWS):
            m=next(x for x in data['records'] if x['input_id']==sid and x['id']=='I.first_decision_duplicate:G'+str(logical_row))
            if m['status']!='held' or not (m['reason'] or '').startswith('C03'):
                raise ValueError('Unexpected pre-C03 state: '+sid+' '+m['id'])
            logical_ref=copy.deepcopy(m['source_ref'])
            original_value=m['source_value']
            effective_ref={'input':sid,'sheet':source_sheet,'cell':'G'+str(logical_row if sid=='S01' else iii_row)}
            effective_value=(copy_data[old_sheet][effective_ref['cell']]['value'] if sid=='S01'
                             else final_data[sid][new_sheet][effective_ref['cell']]['value'])
            expected=(CORRECTION if sid=='S01' else S02_CORRECTION)[idx]
            if effective_value!=expected:raise ValueError('C03 effective value mismatch: '+sid+' '+m['id'])
            old_by_id[(sid,m['id'])]=original_value
            m['logical_metric_source_ref']=logical_ref
            m['source_ref']=effective_ref
            m['source_value']=effective_value
            m['raw_original_value']=original_value
            m['value']=effective_value
            m['status']='valid';m['reason']=None;m['kind']='count'
            m['verification_scope']=('S01作業コピーのⅠセルへC03を適用し、同コピーのⅢ値・5割合列・Ⅳ合計を照合' if sid=='S01'
                                     else 'S02原本は不変更。C03比較値は同資料Ⅲ一次判定表から出所付きで取得')
            m['independent_review']={'report_role':'20','report_blob_sha':ROLE20_REPORT_BLOB,'evidence_source_commit':ROLE20_EVIDENCE_COMMIT,'issue':'C03','verdict':'PASS'}
            m['source_copy_sha256']=source_copy_sha if sid=='S01' else None
            evidence={'input_id':sid,'input_sha256':m['input_hash'],'logical_metric_source_ref':logical_ref,
                      'actual_value_source_ref':effective_ref,'raw_original_value':original_value,'effective_value':effective_value,
                      'source_copy_sha256':source_copy_sha if sid=='S01' else None,
                      'independent_role20_report_blob_sha':ROLE20_REPORT_BLOB,'issue':'C03'}
            m['evidence_sha256']=hashlib.sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            patch_checks.append({'input':sid,'id':m['id'],'value':effective_value,'source_ref':effective_ref,'verdict':'PASS'})
    data['correction_overlays']={'C03':{'status':'applied_to_S01_work_copy_and_analysis_view','original_source_modified':False,
      'role20_report_blob_sha':ROLE20_REPORT_BLOB,'role20_evidence_source_commit':ROLE20_EVIDENCE_COMMIT,
      'S01_work_copy_sha256':source_copy_sha,'S02_original_modified':False,'per_input_evidence':c03_evidence,
      'scope':'Ⅰ!G513:G521の論理指標。S01は修正済み作業コピー、S02は変更せずⅢ!G128:G136を比較値に使用'}}
    for r in data['records']:
        if r['table_id']=='I.first_decision_duplicate' and r['unit']=='件' and r['source_ref']['cell'].startswith('G'):
            if r['status']!='valid':raise ValueError('C03 metric remains held: '+r['input_id']+' '+r['id'])
    by={(m['input_id'],m['id']):m for m in data['records']}
    c03_comparisons=[]
    for idx,(logical_row,iii_row) in enumerate(LABEL_ROWS):
        sid01=next(x for x in data['records'] if x['input_id']=='S01' and x['id']=='I.first_decision_duplicate:G'+str(logical_row))
        sid02=next(x for x in data['records'] if x['input_id']=='S02' and x['id']=='I.first_decision_duplicate:G'+str(logical_row))
        if sid01['status']!='valid' or sid02['status']!='valid':raise ValueError('C03 comparison dependency is held')
        c03_comparisons.append({'id':sid01['id']+':提供期間差','city_id':sid01['id'],'reference_id':sid02['id'],
          'reference_input':'S02','label':'提供期間差','unit':'件','status':'valid','value':sid01['value']-sid02['value'],
          'adjustment':'通常','population':'一次判定結果の有効ケース','ratio_basis':'',
          'source_provenance':{'S01':sid01['source_ref'],'S02':sid02['source_ref'],'issue':'C03'}})
    data['comparisons'].extend(c03_comparisons)
    write_json(extracted,data)
    numeric_path=calc/'numeric_checks.json';numeric=json.loads(numeric_path.read_text())
    numeric['checks'].extend([{'input':x['input'],'id':x['id'],'check':'integer_count','verdict':'PASS','correction_issue':'C03'} for x in patch_checks])
    numeric['counts']=dict(Counter(x['check'] for x in numeric['checks']))
    numeric['unexpected_issues']=data['unexpected_issues']
    write_json(numeric_path,numeric)
    summary={'status':'PASS','role20_report_blob_sha':ROLE20_REPORT_BLOB,'scope':'C03 overlay into T04/T05 work results only; source inputs unchanged',
             'source_copy_sha256':source_copy_sha,'input_values_patched':patch_checks,'input_total_checks':c03_evidence,
             'period_comparisons':c03_comparisons,'valid_comparisons':len(c03_comparisons)}
    write_json(calc/'c03_overlay_check.json',summary)
    print(json.dumps({'verdict':'PASS','C03_values_updated':len(patch_checks),'input_total_checks':2,'period_comparisons':len(c03_comparisons),'S01_source_sha256':json.loads((a.inspection/'input_manifest.json').read_text())['S01']['sha256'],'S01_work_copy_sha256':source_copy_sha},ensure_ascii=False))

if __name__=='__main__':main()
