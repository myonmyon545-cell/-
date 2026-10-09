"""T04/T05 extraction and aggregate checks; never rewrites source workbooks."""
import argparse
import collections
import json
from pathlib import Path
from inspect_inputs import write_json, sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--inspection',type=Path,required=True);p.add_argument('--contract',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    inv=json.loads((a.contract/'metric_inventory.json').read_text());defs=json.loads((a.contract/'definitions.json').read_text());manifest=json.loads((a.inspection/'input_manifest.json').read_text())
    data={sid:{s['name']:s for s in json.loads((a.inspection/(sid+'_cells.json')).read_text())['sheets']} for sid in ['S01','S02']}
    tables={t['id']:t for t in defs['table_inventory']}
    def v(sid,sh,ref):return data[sid][sh]['cells'].get(ref,{}).get('value')
    def ratio_refs(m):
        tid=m['table_id'];sh=m['source_ref']['sheet'];ref=m['source_ref']['cell'];col=''.join(filter(str.isalpha,ref));row=int(''.join(filter(str.isdigit,ref)))
        if m['adjustment']!='通常':return None
        t=tables[tid]
        if tid=='I.population' and col in ['K','T']:return sh,'G'+str(row),'G130' if col=='K' else 'G129'
        if tid=='I.certification' and col in ['I','U']:return sh,'F'+str(row),'F261' if col=='I' else 'F260'
        if tid=='I.certification.summary' and col=='D':return sh,{287:'F261',324:'F262',355:'F263'}[row],'F260'
        if tid in ['I.dementia','I.disability']:
            cnt={'K':'G','R':'N','Z':'U'}.get(col)
            if cnt:return sh,cnt+str(row),cnt+('390' if tid=='I.dementia' else '452')
        if tid=='I.first_decision_duplicate' and col=='K':return 'Ⅲ審査判定データ（一次・二次判定）','G'+str(row-385),'G136'
        if tid in ['III.first_decision','III.second_decision'] and col=='K':return sh,'G'+str(row),'G136' if tid=='III.first_decision' else 'G199'
        if tid.startswith('II.selection.'):
            cnt={'J':'H','N':'L','R':'P'}.get(col)
            if cnt:return sh,cnt+str(row),[cnt+str(r) for r in t['data_rows']]
        if tid=='III.change.all':
            cnt={'L':'H','R':'N','X':'T'}.get(col)
            if cnt:return sh,cnt+str(row),cnt+'67'
        if tid.startswith('III.change.previous_') and tid!='III.change.previous_to_current':
            cnt={'O':'K','U':'Q','AA':'W'}.get(col)
            if cnt:return sh,cnt+str(row),cnt+str(int(''.join(filter(str.isdigit,t['ranges'][0].split(':')[0]))))
        if tid.startswith('III.change.'):
            cnt={'N':'J','T':'P','Z':'V'}.get(col)
            if not cnt:return None
            if tid.endswith('severe_within') or tid.endswith('mild_within'):return sh,cnt+str(row),{'N':'L','T':'R','Z':'X'}[col]+str(row)
            total={'severity_composition':101,'mild_composition':109,'new_application':369,'renewal':430,'category_change':491,'previous_to_current':552}.get(tid.split('.')[-1])
            if total:return sh,cnt+str(row),cnt+str(total)
        if tid=='III.validity.all':
            cnt={'L':'H','S':'O','Z':'V'}.get(col)
            if cnt:return sh,cnt+str(row),cnt+'72'
        if tid.startswith('III.validity.'):
            cnt={'N':'K','T':'Q','Z':'W'}.get(col)
            end=t['ranges'][0].split(':')[1];total=int(''.join(filter(str.isdigit,end)))
            if cnt:return sh,cnt+str(row),cnt+str(total)
        if tid in ['IV.insured','IV.application'] or tid.startswith('IV.days.'):
            cnt={'N':'J','T':'P','Z':'V'}.get(col)
            if cnt:return sh,cnt+str(row),cnt+('153' if tid=='IV.application' else '132')
        return None
    records=[];checks=[];unexpected=[]
    for sid in ['S01','S02']:
        for m in inv['metrics']:
            row=dict(m);row['input_id']=sid;row['source_ref']={**m['source_ref'],'input':sid};sh=m['source_ref']['sheet'];ref=m['source_ref']['cell'];cell=data[sid][sh]['cells'].get(ref,{})
            value=cell.get('value');row.update({'source_value':value,'value':None if cell.get('type')=='e' else value,'source_formula':cell.get('formula'),'shared_formula':cell.get('formula_attributes'),'input_hash':manifest[sid]['sha256'],'numerator':None,'denominator':None})
            if sid=='S02':row['period']='2025年1月（同じストック）' if m['table_id'].startswith(('I.population','I.certification')) else '2024-10-01～2025-03-31（申請日基準、2025-06-30格納締切）'
            if m['table_id']=='IV.days.survey' and ref=='J208':row['status']='held';row['reason']='C04：市調査期間は両提供期間とも確認待ち'
            if value is None:row['status']='missing';row['reason']='比較先の同セルが未掲載';row['value']=None
            if cell.get('type')=='e':row['status']='held';row['reason']='元表の数式エラー。0として扱わない'
            if m['table_id']=='II.selection.07.70' and row['unit']=='件':
                row['status']='held';row['reason']='C10：薬の内服の選択件数が同表の割合・有効件数と不整合'
            if row['status']=='valid' and row['unit'] in ['件','人']:
                if not isinstance(value,(int,float)) or value<0 or value%1!=0:row['status']='held';row['reason']='件数の整数性不一致';unexpected.append({'input':sid,'id':row['id'],'reason':row['reason']})
                else:checks.append({'input':sid,'id':row['id'],'check':'integer_count','verdict':'PASS'})
            refs=ratio_refs(m)
            if row['status']=='valid' and row['unit']=='比率' and refs:
                rsh,nr,dr=refs;num=v(sid,rsh,nr);denvalues=[v(sid,rsh,x) for x in dr] if isinstance(dr,list) else [v(sid,rsh,dr)]
                den=sum(denvalues) if all(isinstance(x,(int,float)) for x in denvalues) else None
                row.update({'numerator':num,'denominator':den,'calculation_sources':{'sheet':rsh,'numerator':nr,'denominator':dr}})
                if den is None or not isinstance(num,(int,float)):row['kind']='provided';row['verification_scope']='分子・分母が提供されていないため出所・転記照合のみ'
                elif den==0:row['status']='held';row['reason']='分母0で未算出';row['value']=None
                elif abs(value-num/den)>1e-10:
                    if sid=='S02' and m['table_id']=='I.certification' and ref in ['U264','U265','U266','U267','U268','U269','U270'] and abs(value-round(value,4))<1e-12 and abs(value-num/den)<=0.00005:
                        row['kind']='ratio';row['value']=num/den;row['calculated_value']=num/den;row['source_precision']='提供値は比率小数4桁。丸め区間で一致し、比較用値は元件数から算出'
                        checks.append({'input':sid,'id':row['id'],'check':'ratio_display_interval','verdict':'PASS','absolute_error':abs(value-num/den),'source_half_unit':0.00005})
                    else:
                        issue='C10' if m['table_id']=='II.selection.07.70' else 'C11'
                        row['status']='held';row['reason']=issue+'：掲載比率と同表の件数からの再計算が不一致';unexpected.append({'issue':issue,'input':sid,'id':row['id'],'source':value,'calculated':num/den,'numerator':num,'denominator':den,'calculation_sources':row['calculation_sources']})
                else:row['kind']='ratio';row['calculated_value']=num/den;checks.append({'input':sid,'id':row['id'],'check':'ratio','verdict':'PASS','absolute_error':abs(value-num/den)})
            elif row['status']=='valid' and row['unit']=='比率':row['kind']='provided';row['verification_scope']='提供比率・分布統計・補正値の出所と転記の確認。再算出なし'
            if row['kind']=='provided' and row['status']=='valid':checks.append({'input':sid,'id':row['id'],'check':'provided_transcription','verdict':'PASS','scope':row['verification_scope']})
            evidence={'input_hash':row['input_hash'],'source':{'sheet':sh,'cell':ref},'period':row['period'],'population':row['population'],'adjustment':row['adjustment'],'source_value':value}
            row['evidence_sha256']=sha(json.dumps(evidence,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode())
            records.append(row)
    lookup={(m['input_id'],m['id']):m for m in records};comparisons=[]
    grouped=collections.defaultdict(list)
    for m in records:
        col=''.join(filter(str.isalpha,m['source_ref']['cell']));basis=''
        if m['table_id']=='I.population' and m['unit']=='比率':basis='65歳以上人口分母' if col in ['K','N','Q'] else '総人口分母'
        if m['table_id']=='I.certification' and m['unit']=='比率':basis='65歳以上人口分母' if col in ['U','X','AA'] else '第1号認定者分母'
        if m['input_id']=='S01':grouped[(m['table_id'],''.join(filter(str.isdigit,m['source_ref']['cell'])),m['unit'],m['adjustment'],basis)].append(m)
    for key,group in grouped.items():
        city=[m for m in group if m['region']=='市'];county=[m for m in group if m['region']=='県'];nation=[m for m in group if m['region']=='全国']
        if key[2] not in ['比率','日','点']:continue
        # Some tables publish two different denominators in a single row. Use
        # declared column meaning rather than joining all same-row city cells.
        if len(city)!=1:continue
        c=city[0]
        for label,peers in [('県差',county),('全国差',nation),('提供期間差',[lookup[('S02',c['id'])]])]:
            if len(peers)!=1:continue
            r=peers[0];status='valid' if c['status']==r['status']=='valid' else 'held';factor=100 if key[2]=='比率' else 1
            comparisons.append({'id':c['id']+':'+label,'city_id':c['id'],'reference_id':r['id'],'reference_input':r['input_id'],'label':label,'unit':'pp' if key[2]=='比率' else key[2],'status':status,'value':factor*(c['value']-r['value']) if status=='valid' else None,'adjustment':key[3],'population':c['population'],'ratio_basis':key[4],'reason':None if status=='valid' else '比較元または比較先が保留・欠損。比較の結論を出さない'})
    result={'schema':'care_extraction/v1','plan_revision':'2.2','source_tables':len(tables),'target_records':len(inv['metrics']),'records':records,'comparisons':comparisons,'unexpected_issues':unexpected,'scope':'提供集計値の抽出、整数性・計算可能比率の照合、同条件の差。独立評価・表示・候補保存の合格ではない'}
    write_json(a.out/'extracted_values.json',result);write_json(a.out/'numeric_checks.json',{'checks':checks,'unexpected_issues':unexpected,'counts':dict(collections.Counter(x['check'] for x in checks))})
    print(json.dumps({'target_records':len(inv['metrics']),'all_records':len(records),'valid':sum(m['status']=='valid' for m in records),'held_or_missing':sum(m['status']!='valid' for m in records),'comparisons':len(comparisons),'valid_comparisons':sum(c['status']=='valid' for c in comparisons),'checks':dict(collections.Counter(x['check'] for x in checks)),'unexpected_issues':unexpected},ensure_ascii=False))

if __name__=='__main__':main()
