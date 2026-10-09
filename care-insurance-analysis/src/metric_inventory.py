"""Instantiate the T02 metric inventory from declared tables and source cells."""
import argparse
import json
import re
from pathlib import Path
from inspect_inputs import write_json
from prepare_contract import colnum

def columns(a,b):
    lo,hi=colnum(a),colnum(b)
    return lo,hi

def mapping(tid):
    if tid=='I.population': return {'G':('市','人','通常'),'K':('市','比率','通常'),'N':('県','比率','通常'),'Q':('全国','比率','通常'),'T':('市','比率','通常'),'W':('県','比率','通常'),'Z':('全国','比率','通常')}
    if tid=='I.certification':
        return {c:(r,u,a) for c,r,u,a in [('F','市','人','通常'),('I','市','比率','通常'),('L','市','比率','年齢補正'),('O','県','比率','通常'),('R','全国','比率','通常'),('U','市','比率','通常'),('X','県','比率','通常'),('AA','全国','比率','通常')]}
    if tid=='I.certification.summary': return {'D':('市','比率','通常'),'J':('市','比率','年齢補正'),'Q':('県','比率','通常'),'W':('全国','比率','通常')}
    if tid in {'I.dementia','I.disability'}:
        return {c:(r,u,'通常') for c,r,u in [('G','市','件'),('K','市','比率'),('N','県','件'),('R','県','比率'),('U','全国','件'),('Z','全国','比率')]}
    if tid=='I.first_decision_duplicate' or tid.startswith('III.first_decision') or tid.startswith('III.second_decision'):
        return {c:(r,u,a) for c,r,u,a in [('G','市','件','通常'),('K','市','比率','通常'),('N','県','比率','通常'),('Q','全国','比率','通常'),('U','市','比率','有効期間・年齢補正'),('Y','全国','比率','有効期間・年齢補正')]}
    if tid.startswith('II.score.'):
        return {c:(r,'点',a) for c,r,a in [('G','市','通常'),('K','県','通常'),('O','全国','通常'),('S','市','有効期間・年齢補正'),('W','全国','有効期間・年齢補正')]}
    if tid.startswith('II.selection.'):
        return {c:(r,u,'通常') for c,r,u in [('H','市','件'),('J','市','比率'),('L','県','件'),('N','県','比率'),('P','全国','件'),('R','全国','比率')]}
    if tid.startswith('II.focus.'):
        return {c:('市' if c in ['AB','AC'] else '全国自治体分布','比率','有効期間・年齢補正') for c in ['R','S','T','U','V','W','X','Y','Z','AA','AB','AC']}
    if tid=='III.change.all':
        return {c:(r,u,'通常') for c,r,u in [('H','市','件'),('L','市','比率'),('N','県','件'),('R','県','比率'),('T','全国','件'),('X','全国','比率')]}
    if tid.startswith('III.change.previous_') and tid!='III.change.previous_to_current':
        return {c:(r,u,'通常') for c,r,u in [('K','市','件'),('M','市','件'),('O','市','比率'),('Q','県','件'),('S','県','件'),('U','県','比率'),('W','全国','件'),('Y','全国','件'),('AA','全国','比率')]}
    if tid.startswith('III.change.'):
        return {c:(r,u,'通常') for c,r,u in [('J','市','件'),('L','市','件'),('N','市','比率'),('P','県','件'),('R','県','件'),('T','県','比率'),('V','全国','件'),('X','全国','件'),('Z','全国','比率')]}
    if tid=='III.validity.all':
        return {c:(r,u,'通常') for c,r,u in [('H','市','件'),('L','市','比率'),('O','県','件'),('S','県','比率'),('V','全国','件'),('Z','全国','比率')]}
    if tid.startswith('III.validity.'):
        return {c:(r,u,'通常') for c,r,u in [('K','市','件'),('N','市','比率'),('Q','県','件'),('T','県','比率'),('W','全国','件'),('Z','全国','比率')]}
    if tid.startswith('IV.'):
        return {c:(r,u,'通常') for c,r,u in [('J','市','件'),('N','市','比率'),('P','県','件'),('T','県','比率'),('V','全国','件'),('Z','全国','比率')]}
    raise ValueError('missing mapping: '+tid)

def main():
    p=argparse.ArgumentParser();p.add_argument('--inspection',type=Path,required=True);p.add_argument('--contract',type=Path,required=True)
    a=p.parse_args();defs=json.loads((a.contract/'definitions.json').read_text());book=json.loads((a.inspection/'S01_cells.json').read_text())
    ss={s['name']:s for s in book['sheets']};metrics=[]
    for t in defs['table_inventory']:
        cm=mapping(t['id']); cells=ss[t['sheet']]['cells'];ranges=[]
        for rect in t['ranges']:
            x,y=re.findall(r'([A-Z]+)(\d+)',rect);ranges.append((colnum(x[0]),int(x[1]),colnum(y[0]),int(y[1])))
        for ref,cell in cells.items():
            col,row=re.fullmatch(r'([A-Z]+)(\d+)',ref).groups();row=int(row)
            if col not in cm or not any(l<=colnum(col)<=r and top<=row<=bottom for l,top,r,bottom in ranges):continue
            if not isinstance(cell['value'],(int,float)) and cell['type']!='e':continue
            region,unit,adj=cm[col];status='valid';reason=None
            if t['id'].startswith('IV.days.') and col in ['J','P','V'] and row in [190,208,226]: unit='日'
            if t['id']=='I.first_decision_duplicate' and col=='G':status='held';reason='C03：一次判定件数は独立照合・修正待ち'
            if t['id']=='IV.days.survey' and ref=='J208':status='held';reason='C04：市の調査期間は元送信・集計または個票確認待ち'
            if cell['type']=='e':status='held';reason='C09：軽度変更構成比の分母0により未算出'
            if col in ['R','S','T','U','V','W','X','Y','Z','AA'] and t['id'].startswith('II.focus.'):
                kind='provided';scope='元自治体分布の掲載統計。個票なし再算出不可'
            elif adj!='通常' or unit in ['日','点']:
                kind='provided';scope='提供値の転記・出所照合。個票なし再算出不可'
            else:
                kind='count' if unit in ['件','人'] else 'ratio';scope='T04/T05で内訳・分母照合を行う'
            label=' / '.join(str(cells[c+str(row)]['value']) for c in ['B','C','D','E','P'] if c+str(row) in cells and isinstance(cells[c+str(row)]['value'],str))
            period=defs['stock_basis'] if t['id'].startswith('I.population') or t['id'].startswith('I.certification') else defs['period']
            metrics.append({'id':t['id']+':'+ref,'table_id':t['id'],'requirements':t['requirements'],'source_ref':{'input':'S01','sheet':t['sheet'],'cell':ref},'region':region,'unit':unit,'adjustment':adj,'population':t['population'],'period':period,'row_label':label,'kind':kind,'status':status,'reason':reason,'verification_scope':scope})
    if len({m['id'] for m in metrics})!=len(metrics):raise ValueError('duplicate inventory id')
    result={'schema':'care_metric_inventory/v1','plan_revision':'2.2','required_metrics':[m['id'] for m in metrics],'metrics':metrics,'stage':'definitions only; source values and numerical verdicts not yet computed'}
    write_json(a.contract/'metric_inventory.json',result)
    print(json.dumps({'planned_metrics':len(metrics),'source_tables':len(defs['table_inventory']),'held_metrics':sum(m['status']=='held' for m in metrics)},ensure_ascii=False))

if __name__=='__main__':main()
