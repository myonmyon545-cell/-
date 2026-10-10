"""Read S10 native DOCX tables. Reference namespace never participates in core comparisons."""
import argparse, hashlib, json, re, unicodedata, zipfile
from pathlib import Path
from xml.etree import ElementTree as E

W={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def digest(b): return hashlib.sha256(b).hexdigest()
def norm(s): return unicodedata.normalize('NFKC',s).replace(',','').strip()
def number(s):
    m=re.match(r'^\s*\(?([-+]?\d+(?:\.\d+)?)',norm(s))
    return float(m.group(1)) if m else None
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--excerpts',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();ex=json.loads(a.excerpts.read_text());raw=a.source.read_bytes()
    assert digest(raw)==ex['source']['sha256'] and len(raw)==ex['source']['size_bytes']
    with zipfile.ZipFile(a.source) as z: root=E.fromstring(z.read('word/document.xml'))
    text=lambda e: ''.join(t.text or '' for t in e.findall('.//w:t',W))
    tables=[[[text(c) for c in r.findall('w:tc',W)] for r in t.findall('w:tr',W)] for t in root.findall('.//w:tbl',W)]
    paras=[text(x) for x in root.findall('.//w:p',W)]
    # Explicit native cells: row and cell indices refer to XML, not visual merged columns.
    maps={}
    years=['R5','R6','R7','R8_planned']
    def put(block,path,t,r,c,part=None): maps[(block,tuple(path))]=(t,r,c,part)
    for y,c in zip(years,range(1,5)):
        for key,r in [('survey',1),('opinion_received',2)]:put('S10-01',[y,key],50,r,c)
        for key,r in [('direct',1),('contracted',2),('total',3),('inbound_entrusted',4)]:put('S10-02',[y,key],54,r,c)
        put('S10-02',[y,'contracted_parenthetical'],54,2,c,'parenthesis')
        put('S10-03',['home_office_percent',y],52,1,c)
        for key,r in [('meetings',1),('decisions',2)]:put('S10-05',[y,key],58,r,c)
    for y,c in [('R7',1),('R8_planned',2)]:put('S10-03',['authorized_contractor_percent',y],53,1,c)
    for y,r in [('R8',1),('R9',2),('R10',3)]:
        for key,c in [('total',1),('authorized',2),('home_office',3),('percent',4),('direct_staff',5)]:put('S10-03',['future_plan',y,key],55,r,c)
    for key,r in [('members',1),('members_per_board',2),('boards',3)]:put('S10-04',[key],57,r,1)
    put('S10-04',['ordinary_meetings_per_week'],57,0,1,'weekly')
    put('S10-04',['daytime_meetings_per_month'],57,0,1,'monthly')
    for c in range(8):
        put('S10-06',['categories',str(c)],59,0,c,'text');put('S10-06',['counts',str(c)],59,1,c)
    put('S10-06',['total'],59,1,8)
    for r in range(1,8):put('S10-07',['categories',str(r-1)],60,r,0,'text')
    for y,c in [('R5',1),('R6',2),('R7',3)]:
        for r in range(1,8):put('S10-07',[y,'counts',str(r-1)],60,r,c)
        put('S10-07',[y,'total'],60,8,c)
    put('S10-07',['R8'],60,8,4,'missing')
    for y,c in [('R5',2),('R6',3),('R7',4)]:
        for key,r in [('board_wait',1),('opinion_wait',2),('survey_wait',3),('reported_total',4)]:put('S10-08',[y,key],61,r,c)
        put('S10-08',[y,'survey_reprinted'],61,3,c,'reprinted')
    for y,region,c in [('R5','city',2),('R5','prefecture',3),('R5','national',4),('R6','city',5),('R6','prefecture',6),('R6','national',7),('R7','city',8)]:
        for key,r in [('recognition',2),('survey',3),('opinion',4),('board_admin',5)]:put('S10-09',[y,region,key],62,r,c)
        put('S10-10',[y,region],62,6,c)
    put('S10-09',['R6','city','survey_original_text'],62,3,5,'text')
    records=[];checks=[]
    def leaves(x,path=()):
        if isinstance(x,dict):
            for k,v in x.items():yield from leaves(v,path+(k,))
        elif isinstance(x,list):
            for k,v in enumerate(x):yield from leaves(v,path+(str(k),))
        else:yield path,x
    for block in ex['records']:
        locs=block['locator'] if isinstance(block['locator'],list) else [block['locator']]
        ts=[x['table_index_0based'] for x in locs if 'table_index_0based' in x]
        native={str(t):tables[t] for t in ts}
        # Preserve exact raw cells and actual year headers for independent comparison.
        checks.append({'id':block['id'],'raw_tables':native,'year_headers':[tables[t][0] for t in ts],
                       'source_sha256':digest(raw),'method':'native XML read; explicit cells where defined; remaining block values retain raw tables for review'})
        for path,value in leaves(block.get('values',{})):
            cell=maps.get((block['id'],path));sr={'input':'S10','tables':ts,'logical_path':list(path)}
            if cell:
                t,r,c,part=cell;s=tables[t][r][c];v=number(s)
                if part=='parenthesis':v=float(re.search(r'\((\d+)\)',norm(s)).group(1))
                if part=='reprinted':v=float(re.search(r'再掲(\d+)',norm(s)).group(1))
                if part=='weekly':v=float(re.search(r'週(\d+)回',norm(s)).group(1))
                if part=='monthly':v=float(re.search(r'月(\d+)回',norm(s)).group(1))
                if part=='text':v=norm(s);value=norm(value)
                if part=='missing':v=None;assert norm(s) in ['','-','−','－']
                assert v==value,(block['id'],path,s,value)
                sr.update(table_index_0based=t,row_index_0based=r,cell_index_0based=c,raw_text=s)
            status='held' if block['id']=='S10-08' or (block['id']=='S10-03' and path[:2]==('future_plan','R8')) else ('missing' if value is None else 'reference_only')
            if block['id']=='S10-03' and path[:1]==('future_plan',):
                unit={'total':'件','authorized':'件','home_office':'件','percent':'％','direct_staff':'人'}[path[-1]]
            elif block['id']=='S10-03':
                unit='％'
            else:
                unit=block.get('unit')
            rec={'id':block['id']+'::'+'.'.join(path),'block_id':block['id'],'title':block['title'],'status':status,
                 'value':value if status=='reference_only' else None,'raw_source_value':value,'source_ref':sr,
                 'source_sha256':digest(raw),'unit':unit,'planned':any('planned' in s for s in path) or path[:1]==('future_plan',),
                 'population':'S10年度業務参考・S01/S02対象と非同一','method_caution':block.get('use'),
                 'comparison_eligible':False,'may_unlock_core_holds':False}
            rec['evidence_sha256']=digest(json.dumps(rec,ensure_ascii=False,sort_keys=True).encode());records.append(rec)
    contexts={str(i):paras[i] for i in [2068,2199,2203,2492,2541,2542]}
    assert '郵送' in contexts['2068'] and '14日' in contexts['2199'] and '市独自' in contexts['2492']
    totals=[]
    for c,y in zip(range(1,5),years):
        calculated=number(tables[54][1][c])+number(tables[54][2][c]);reported=number(tables[54][3][c]);assert calculated==reported
        totals.append({'table':54,'year':y,'computed':calculated,'reported':reported,'status':'PASS','parentheticals_not_added':True})
    calculated=sum(number(v) for v in tables[59][1][:8]);reported=number(tables[59][1][8]);assert calculated==reported
    totals.append({'table':59,'year':'R7_contextual','computed':calculated,'reported':reported,'status':'PASS'})
    for c,y in zip(range(1,4),years[:3]):
        calculated=sum(number(tables[60][r][c]) for r in range(1,8));reported=number(tables[60][8][c]);assert calculated==reported
        totals.append({'table':60,'year':y,'computed':calculated,'reported':reported,'status':'PASS'})
    out={'schema':'care_S10_application/v1','plan_revision':'2.4','source':ex['source'],'blocks':checks,'supplemental_metrics':records,
         'context_paragraphs_0based':contexts,'integer_total_checks':totals,'checks':{'sha256':'PASS','native_tables_read':len({t for b in checks for t in b['raw_tables']}),
         'blocks':11,'explicit_cells_checked':len(maps),'remaining_values_independent_verification':'ROLE20 pending; absent regional columns explicitly missing','core_hold_unlocks':0,
         'C12':{'status':'held','R7_raw_sum':1479+767+2171,'R7_subtract_reprint':1479+767+2171-424,'printed_total':3393,'gap':600},
         'C14':{'status':'held','R8_table54':2920,'R8_table55':2600+324,'gap':4},'C13':'reference_only; own method; publication replacement pending'}}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out['checks'],ensure_ascii=False))
if __name__=='__main__':main()
