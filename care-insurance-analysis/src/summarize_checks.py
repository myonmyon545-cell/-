"""Save aggregate-only evidence and the actual extraction hold scope."""
import argparse
import collections
import json
from pathlib import Path
from inspect_inputs import write_json, sha

def main():
    p=argparse.ArgumentParser()
    for key in ['inspection','contract','calculation','out']:
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    defs=json.loads((a.contract/'definitions.json').read_text())
    inv=json.loads((a.contract/'metric_inventory.json').read_text())
    result=json.loads((a.calculation/'extracted_values.json').read_text())
    data={sid:{s['name']:s['cells'] for s in json.loads((a.inspection/(sid+'_cells.json')).read_text())['sheets']} for sid in ['S01','S02']}
    totals=[]
    def total(sid,sh,name,cell,parts):
        values=[data[sid][sh][x]['value'] for x in parts]
        expected=data[sid][sh][cell]['value']
        verdict='PASS' if all(type(v) in [int,float] and v>=0 and v%1==0 for v in values) and sum(values)==expected else 'HELD'
        totals.append({'input':sid,'sheet':sh,'id':name,'total_cell':cell,'total':expected,'part_cells':parts,'parts':values,'sum':sum(values),'verdict':verdict})
    basic='Ⅰ基礎情報';decision='Ⅲ審査判定データ（一次・二次判定）';change='Ⅲ審査判定データ（変更率）';office='Ⅳ事務データ'
    for sid in data:
        for name,end,rows in [('certification',261,range(264,271)),('mild',262,range(264,267)),('severe',263,range(267,271))]:
            total(sid,basic,name,'F'+str(end),['F'+str(r) for r in rows])
        for c in ['G','N','U']:
            for name,end,rows in [('dementia_all',390,range(393,401)),('dementia_II+',391,range(395,401)),('dementia_III+',392,range(397,401)),('disability_all',452,range(454,463)),('disability_B+',453,range(459,463))]:
                total(sid,basic,name+':'+c,c+str(end),[c+str(r) for r in rows])
        for name,end,rows in [('first_decision',136,range(128,136)),('second_decision',199,range(191,199))]:
            total(sid,decision,name,'G'+str(end),['G'+str(r) for r in rows])
        for c in ['J','P','V']:
            total(sid,change,'severe_composition:'+c,c+'101',[c+str(r) for r in range(102,109)])
            total(sid,change,'mild_composition:'+c,c+'109',[c+str(r) for r in range(110,117)])
            total(sid,office,'insured:'+c,c+'132',[c+str(r) for r in range(129,132)])
            total(sid,office,'application:'+c,c+'153',[c+str(r) for r in range(150,153)])
        for t in defs['table_inventory']:
            if not t['id'].startswith('III.validity.'):continue
            start,end=t['ranges'][0].split(':');lo=int(''.join(filter(str.isdigit,start)));hi=int(''.join(filter(str.isdigit,end)))
            for c in (['H','O','V'] if t['id']=='III.validity.all' else ['K','Q','W']):
                total(sid,t['sheet'],t['id']+':'+c,c+str(hi),[c+str(r) for r in range(lo,hi)])
    held=[{'input':r['input_id'],'id':r['id'],'source_ref':r['source_ref'],'status':r['status'],'reason':r['reason'],'source_value':r['source_value']} for r in result['records'] if r['status']!='valid']
    by_input={(r['input_id'],r['id']):r for r in result['records']}
    for m in inv['metrics']:
        per_input={}
        for sid in ['S01','S02']:
            r=by_input.get((sid,m['id']))
            if r is None:raise ValueError('missing input-specific metric '+sid+' '+m['id'])
            per_input[sid]={'status':r['status'],'reason':r['reason'],
                            'source_ref':r['source_ref'],'input_sha256':r['input_hash']}
        m['extraction_status_by_input']=per_input
        m['status']='valid' if all(x['status']=='valid' for x in per_input.values()) else 'held'
        m['reason']=None if m['status']=='valid' else '入力別statusを参照。共有状態からvalidへ戻さない'
        m['status_resolution']='input_id+id+source_ref+input_sha256; input-specific status required'
    inv['stage']='input-specific source-cell inventory; independent candidate review pending'
    write_json(a.out/'metric_inventory.json',inv)
    checks=json.loads((a.contract/'startup_checks.json').read_text())
    for issue,need in [('C10','S01/S02の薬の内服について正式な元送信・集計表と列定義'),('C11','変更率の正式な対象・除外ケース定義と申請区分別の元集計結果')]:
        mismatches=[x for x in result['unexpected_issues'] if x.get('issue')==issue]
        affected=[x for x in held if (x['reason'] or '').startswith(issue)]
        checks[issue]={'status':'HELD','affected_cells':affected,'mismatches':mismatches,
                       'needs':need,'hold_propagation_applied':True,'formal_value_correction_applied':False}
    if 'ROLE30' in result.get('correction_overlays',{}):
        role30=result['correction_overlays']['ROLE30']
        checks['E20-01']={'status':'APPLIED_AWAITING_INDEPENDENT_CANDIDATE_REVIEW',
                          'focus_tables':role30['focus_metrics']//18,
                          'focus_metrics':role30['focus_metrics'],
                          'certification_metrics':role30['certification_metrics'],
                          'proposal_report_blob_sha':role30['proposal_report_blob_sha']}
        checks['C10']['header_issue']=role30['C10_header_issue']
        checks['C10']['numeric_held_by_input']={'S01':18,'S02':18}
        checks['C11']['zero_numerator_new_held']=3
        if len(checks['C10']['affected_cells'])!=36 or len(checks['C11']['affected_cells'])!=30:
            raise ValueError('ROLE30 C10/C11 hold scope mismatch')
    if 'C03' in result.get('correction_overlays',{}):
        c03=result['correction_overlays']['C03']
        checks['C03'].update({'status':'PASS_WORK_COPY','applied':True,
                               'source_copy_sha256':c03['S01_work_copy_sha256'],
                               'originals_modified':False,
                               'role20_report_blob_sha':c03['role20_report_blob_sha']})
    checks['numeric_coverage']={'required_source_cells':len(inv['metrics']),'extracted_values':len(result['records']),'held_or_missing':len(held),'comparisons':len(result['comparisons']),'valid_comparisons':sum(x['status']=='valid' for x in result['comparisons']),'scope':'ROLE=10 aggregate calculation; not independent evaluation or release approval'}
    write_json(a.out/'startup.json',checks)
    numeric=json.loads((a.calculation/'numeric_checks.json').read_text())
    independent=json.loads((a.calculation/'independent_extraction_check.json').read_text())
    summary={'schema':'care_calculation_checks/v1','plan_revision':'2.2',**checks['numeric_coverage'],'numeric_checks':numeric['counts'],'count_total_checks':len(totals),'count_total_pass':sum(x['verdict']=='PASS' for x in totals),'count_total_held':[x for x in totals if x['verdict']!='PASS'],'independent_source_read':independent,'held_source_cells':held,'unexpected_issues':result['unexpected_issues'],'definitions_sha256':sha((a.contract/'definitions.json').read_bytes()),'results_sha256':sha((a.calculation/'extracted_values.json').read_bytes())}
    write_json(a.out/'calculation_summary.json',summary)
    write_json(a.calculation/'count_total_checks.json',{'checks':totals,'scope':'Explicit aggregate totals only; no individual cases reconstructed'})
    print(json.dumps({k:v for k,v in summary.items() if k in ['extracted_values','count_total_checks','count_total_pass','count_total_held','held_or_missing','comparisons','valid_comparisons']},ensure_ascii=False))

if __name__=='__main__':main()
